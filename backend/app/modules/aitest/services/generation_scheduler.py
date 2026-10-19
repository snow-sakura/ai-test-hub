"""
生成任务调度器 & SSE 流事件总线

- StreamBroker：任务级事件总线。生产者 O(1) 追加事件并保留历史，
  支持多消费者、任意时刻接入回放、断线重连（修复 SSE 丢事件/无法重连问题）。
  与 asyncio.Queue 的 put/put_nowait 接口兼容，可直接替换旧队列。
- GenerationScheduler：进程内生成任务调度器。
  * 免费模型（billing_type=free）→ 全局并发 1，任务按提交顺序串行执行；
  * 付费模型（billing_type=paid）→ 全局并发 PAID_MODEL_CONCURRENCY，任务并行执行。
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

# 任务结束后事件历史的保留时间（秒），超时后清理，防止内存泄漏
BROKER_RETENTION_SECONDS = 10 * 60


class StreamBroker:
    """任务 SSE 事件总线（生产者/消费者分离，支持回放与重连）"""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.done = False
        self.closed_at: float | None = None
        self._cond = asyncio.Condition()
        self._wake_event = asyncio.Event()

    async def put(self, event: dict[str, Any] | None) -> None:
        """兼容 asyncio.Queue.put；event=None 表示流结束"""
        await self.publish(event)

    def put_nowait(self, event: dict[str, Any] | None) -> None:
        """兼容 asyncio.Queue.put_nowait（供同步回调直接调用）"""
        # 同步路径：追加事件后唤醒等待者（无 await 的 notify 不安全，
        # 这里通过 call_soon 调度一次唤醒）
        self._append(event)
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon(self._wake)
        except RuntimeError:
            pass

    def _wake(self) -> None:
        # 同步唤醒路径：置位 Event，等待者被唤醒后再持锁复查
        self._wake_event.set()

    def _append(self, event: dict[str, Any] | None) -> None:
        if event is None:
            self.done = True
            self.closed_at = time.monotonic()
        else:
            self.events.append(event)
        # 统一唤醒等待中的消费者（publish / put_nowait 两条路径共用）
        self._wake_event.set()

    async def publish(self, event: dict[str, Any] | None) -> None:
        """发布事件；None 为结束哨兵"""
        async with self._cond:
            self._append(event)
            self._cond.notify_all()

    async def stream(self, start_index: int = 0):
        """异步生成器：从 start_index 回放历史，然后增量等待直到结束哨兵"""
        index = max(0, start_index)
        while True:
            # 1) 有未读历史则先吐出
            if index < len(self.events):
                event = self.events[index]
                index += 1
                yield event
                continue
            # 2) 历史读完且已结束 → 退出
            if self.done:
                yield None
                return
            # 3) 等待新事件（Event 可被同步 put_nowait 安全唤醒）
            self._wake_event.clear()
            if index >= len(self.events) and not self.done:
                if not self._wake_event.is_set():
                    try:
                        await asyncio.wait_for(self._wake_event.wait(), timeout=30)
                    except asyncio.TimeoutError:
                        pass  # 心跳式轮询，避免永久挂起

    def is_expired(self) -> bool:
        return (
            self.done
            and self.closed_at is not None
            and (time.monotonic() - self.closed_at) > BROKER_RETENTION_SECONDS
        )


# ======================================================================
# 调度器
# ======================================================================

@dataclass
class _QueuedJob:
    task_db_id: int
    task_uid: str
    billing: str  # free / paid
    runner: Callable[[], Awaitable[None]]
    broker: StreamBroker
    seq: int = 0
    cancelled: bool = False


@dataclass
class SchedulerSnapshot:
    """调度器状态快照（用于 API 返回）"""
    free_running: int = 0
    free_queued: int = 0
    free_max: int = 1
    paid_running: int = 0
    paid_queued: int = 0
    paid_max: int = 4


class GenerationScheduler:
    """
    全局生成任务调度器。

    使用方式::

        await scheduler.submit(job)

    免费模型并发固定为 1（单任务序列）；付费模型并发由配置决定。
    """

    def __init__(self) -> None:
        from app.config import settings
        self.paid_max = max(1, int(getattr(settings, "PAID_MODEL_CONCURRENCY", 4)))
        self._limits: dict[str, int] = {"free": 1, "paid": self.paid_max}
        self._running: dict[str, int] = {"free": 0, "paid": 0}
        self._waiting: dict[str, list[_QueuedJob]] = {"free": [], "paid": []}
        self._seq = 0
        self._tasks: set[asyncio.Task] = set()

    # ---- 对外接口 ----

    def position_of(self, task_uid: str) -> int | None:
        """返回任务在等待队列中的位置（0 起），不在队列返回 None"""
        for waiting in self._waiting.values():
            for i, job in enumerate(waiting):
                if job.task_uid == task_uid:
                    return i
        return None

    def queue_depth(self, billing: str) -> int:
        key = "paid" if billing == "paid" else "free"
        return len(self._waiting[key])

    def snapshot(self) -> SchedulerSnapshot:
        return SchedulerSnapshot(
            free_running=self._running["free"],
            free_queued=len(self._waiting["free"]),
            free_max=self._limits["free"],
            paid_running=self._running["paid"],
            paid_queued=len(self._waiting["paid"]),
            paid_max=self._limits["paid"],
        )

    async def submit(self, job: _QueuedJob) -> None:
        """提交任务：有空位直接启动；否则进入等待队列并推送位次事件"""
        billing = "paid" if job.billing == "paid" else "free"
        job.billing = billing
        self._seq += 1
        job.seq = self._seq

        if (
            self._running[billing] + len(self._waiting[billing])
            < self._limits[billing]
        ):
            self._launch(job)
        else:
            self._waiting[billing].append(job)
            self._emit_positions(billing)

    def cancel(self, task_uid: str) -> bool:
        """取消排队中的任务（运行中的由管线/端点自行处理）"""
        for billing, waiting in self._waiting.items():
            for job in waiting:
                if job.task_uid == task_uid:
                    job.cancelled = True
                    try:
                        waiting.remove(job)
                    except ValueError:
                        pass
                    self._emit_positions(billing)
                    return True
        return False

    async def shutdown(self) -> None:
        for task in list(self._tasks):
            task.cancel()

    # ---- 内部 ----

    def _launch(self, job: _QueuedJob) -> None:
        # 同步占用名额，避免同一事件循环批次内重复启动超限
        self._running[job.billing] += 1
        task = asyncio.create_task(self._run(job))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def _start_next(self, billing: str) -> None:
        """释放名额后按 FIFO 启动等待任务，并刷新位次"""
        while (
            self._waiting[billing]
            and self._running[billing] < self._limits[billing]
        ):
            job = self._waiting[billing].pop(0)
            if job.cancelled:
                continue
            self._launch(job)
        self._emit_positions(billing)

    def _emit_positions(self, billing: str) -> None:
        """向所有排队任务的 SSE 流推送位次事件"""
        waiting = self._waiting[billing]
        for i, job in enumerate(waiting):
            job.broker.put_nowait({
                "type": "queue_position",
                "billing": billing,
                "position": i,
                "queue_size": len(waiting),
            })

    async def _run(self, job: _QueuedJob) -> None:
        billing = job.billing
        try:
            if job.cancelled:
                job.broker.put_nowait({"type": "cancelled"})
                job.broker.put_nowait(None)
                return
            await job.runner()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("生成任务执行异常: %s", job.task_uid)
        finally:
            self._running[billing] -= 1
            self._start_next(billing)


_scheduler: GenerationScheduler | None = None


def get_scheduler() -> GenerationScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = GenerationScheduler()
    return _scheduler


# ---- 全局 broker 注册表 ----

_brokers: dict[str, StreamBroker] = {}


def get_broker(task_uid: str) -> StreamBroker | None:
    broker = _brokers.get(task_uid)
    if broker is not None and broker.is_expired():
        _brokers.pop(task_uid, None)
        return None
    return broker


def create_broker(task_uid: str) -> StreamBroker:
    # 清理过期 broker
    for uid in [u for u, b in _brokers.items() if b.is_expired()]:
        _brokers.pop(uid, None)
    broker = StreamBroker()
    _brokers[task_uid] = broker
    return broker


def remove_broker(task_uid: str) -> None:
    _brokers.pop(task_uid, None)
