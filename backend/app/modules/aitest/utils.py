"""
AI 测试模块工具函数

提供报告统计等可复用的工具函数。
"""

from __future__ import annotations

from typing import Any


def compute_pass_rate(passed: int, total: int) -> float:
    """计算通过率，保留两位小数"""
    if total <= 0:
        return 0.0
    return round(passed / total * 100, 2)


def compute_case_stats(cases: list[Any]) -> dict[str, int]:
    """
    计算用例统计信息

    Args:
        cases: 用例列表，每个用例需要有 status 属性

    Returns:
        包含 total, passed, failed, blocked 的字典
    """
    total = len(cases)
    passed = sum(1 for c in cases if c.status == 'approved')
    failed = sum(1 for c in cases if c.status not in ('approved',))
    blocked = sum(1 for c in cases if c.status == 'rejected')
    return {
        'total': total,
        'passed': passed,
        'failed': failed,
        'blocked': blocked,
        'pass_rate': compute_pass_rate(passed, total),
    }


def compute_module_stats(cases: list[Any]) -> list[dict[str, Any]]:
    """
    计算模块分布统计

    Args:
        cases: 用例列表，每个用例需要有 module 和 status 属性

    Returns:
        模块统计列表
    """
    module_map: dict[str, dict] = {}
    for c in cases:
        mod = c.module or '未分类'
        if mod not in module_map:
            module_map[mod] = {'total': 0, 'passed': 0, 'failed': 0}
        module_map[mod]['total'] += 1
        if c.status == 'approved':
            module_map[mod]['passed'] += 1
        else:
            module_map[mod]['failed'] += 1

    return [
        {
            'module': mod,
            'total': data['total'],
            'passed': data['passed'],
            'failed': data['failed'],
            'pass_rate': compute_pass_rate(data['passed'], data['total']),
        }
        for mod, data in sorted(module_map.items())
    ]


def compute_failed_cases(cases: list[Any]) -> list[dict[str, Any]]:
    """
    提取失败用例列表

    Args:
        cases: 用例列表，每个用例需要有 status, case_id, title, module 属性

    Returns:
        失败用例列表
    """
    return [
        {
            'case_id': c.case_id,
            'title': c.title,
            'module': c.module or '未分类',
            'reason': getattr(c, 'reason', ''),
        }
        for c in cases
        if c.status != 'approved'
    ]
