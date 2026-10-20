/* AI-HUB Demo 交互模块
 * 1) 生成序列模拟器：复刻后端「免费串行 / 付费并行」调度逻辑
 * 2) 演示数据存储：GitHub Gist（可用 PAT 保存/更新自己的 Gist；公开 Gist 可直接读取）
 */
(function () {
  'use strict';

  var GIST_API = 'https://api.github.com/gists';
  var STORE_KEY = 'aihub-demo-records';

  var state = {
    records: [],
    batchSeq: 0,
    gistId: '',
    token: '',
  };

  // ---------- 工具 ----------
  function $(sel) { return document.querySelector(sel); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function nowStr() {
    var d = new Date();
    function p(n) { return n < 10 ? '0' + n : '' + n; }
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
      ' ' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds());
  }
  function uid(prefix) {
    return prefix + '-' + Math.random().toString(36).slice(2, 8).toUpperCase();
  }

  // ---------- 本地存储（无 token 时的兜底） ----------
  function loadLocal() {
    try {
      var raw = localStorage.getItem(STORE_KEY);
      state.records = raw ? JSON.parse(raw) : [];
    } catch (e) { state.records = []; }
  }
  function saveLocal() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(state.records)); } catch (e) { /* ignore */ }
  }

  // ---------- 渲染 ----------
  function renderBoard(tasks) {
    var box = $('#demo-board');
    if (!box) return;
    if (!tasks.length) {
      box.innerHTML = '<div class="empty">尚未提交序列，请在左侧输入需求</div>';
      return;
    }
    var done = tasks.filter(function (t) { return t.status === 'completed'; }).length;
    var failed = tasks.filter(function (t) { return t.status === 'failed'; }).length;
    var running = tasks.filter(function (t) { return t.status === 'running'; }).length;
    var queued = tasks.filter(function (t) { return t.status === 'queued'; }).length;
    var pct = Math.round(((done + failed) / tasks.length) * 100);
    var mode = tasks[0].mode;
    var html = '<div class="bhead"><div class="bid">' + esc(tasks[0].batch) + '</div>' +
      '<span class="bmode ' + (mode === 'parallel' ? 'par' : 'ser') + '">' +
      (mode === 'parallel' ? '付费模型 · 并行执行（最多 4 路）' : '免费模型 · 单任务序列（严格串行）') +
      '</span></div>' +
      '<div class="bstats"><span class="ok">完成 ' + done + '</span><span class="run">进行 ' + running +
      '</span><span class="wait">排队 ' + queued + '</span>' +
      (failed ? '<span class="bad">失败 ' + failed + '</span>' : '') + '</div>' +
      '<div class="bbar"><i style="width:' + pct + '%"></i></div>' +
      '<ul class="blist">';
    tasks.forEach(function (t, i) {
      var cls = t.status === 'completed' ? 'done' : (t.status === 'running' ? 'run' : (t.status === 'failed' ? 'bad' : 'wait'));
      var label = { queued: '排队中', running: '生成中', completed: '已完成', failed: '失败' }[t.status] || t.status;
      var sub = t.status === 'queued'
        ? '# 排队第 ' + (t.queuePosition + 1) + ' 位'
        : (t.status === 'completed' ? t.cases + ' 条用例' : '进度 ' + t.progress + '%');
      html += '<li class="' + cls + '"><span class="seq">' + (i + 1) + '</span>' +
        '<span class="ti">' + esc(t.title) + '</span>' +
        '<span class="st">' + label + '</span>' +
        '<span class="sb">' + esc(sub) + '</span></li>';
    });
    html += '</ul>';
    box.innerHTML = html;
  }

  function renderRecords() {
    var box = $('#demo-records');
    if (!box) return;
    if (!state.records.length) {
      box.innerHTML = '<div class="empty">暂无记录</div>';
      return;
    }
    var html = '<table><thead><tr><th>任务</th><th>需求</th><th>模式</th><th>状态</th><th>用例</th><th>时间</th></tr></thead><tbody>';
    state.records.slice().reverse().forEach(function (r) {
      html += '<tr><td>' + esc(r.id) + '</td><td>' + esc(r.title) + '</td><td>' +
        (r.mode === 'parallel' ? '并行' : '串行') + '</td><td>' + esc(r.status) + '</td><td>' +
        r.cases + '</td><td>' + esc(r.createdAt) + '</td></tr>';
    });
    html += '</tbody></table>';
    box.innerHTML = html;
  }

  // ---------- 调度模拟（与后端一致的语义） ----------
  function simulate(tasks, mode, onDone) {
    var tick = 0;
    var timer = setInterval(function () {
      tick += 5;
      var running = tasks.filter(function (t) { return t.status === 'running'; });
      var queued = tasks.filter(function (t) { return t.status === 'queued'; });

      // 排队位次实时收缩
      queued.forEach(function (t, i) { t.queuePosition = i; });

      running.forEach(function (t) {
        t.progress = Math.min(100, t.progress + 5);
        if (t.progress >= 100) {
          t.status = 'completed';
          t.cases = 4 + Math.floor(Math.random() * 4);
          t.createdAt = nowStr();
          state.records.push({
            id: t.id, batch: t.batch, title: t.title, mode: t.mode,
            status: t.status, cases: t.cases, createdAt: t.createdAt,
          });
          saveLocal();
        }
      });

      // 调度：串行每次启动 1 个；并行每次启动最多 4 个
      var capacity = mode === 'parallel' ? 4 : 1;
      var freeSlots = capacity - tasks.filter(function (t) { return t.status === 'running'; }).length;
      if (freeSlots > 0) {
        queued.slice(0, freeSlots).forEach(function (t) {
          t.status = 'running';
          t.progress = 5;
        });
      }

      renderBoard(tasks);
      renderRecords();

      var finished = tasks.every(function (t) { return t.status === 'completed'; });
      if (finished) {
        clearInterval(timer);
        if (onDone) onDone();
      }
    }, 420);
  }

  // ---------- 仓库数据源（GitHub 公开读取，无需授权） ----------
  function loadFromRepo() {
    var status = $('#gist-status');
    status.textContent = '正在从 GitHub 仓库读取演示数据…';
    return fetch('data/records.json', { cache: 'no-store' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        var list = data.records || [];
        state.records = state.records.concat(list);
        saveLocal();
        renderRecords();
        status.textContent = '✅ 已从 GitHub 仓库读取 ' + list.length +
          ' 条演示记录（数据源：raw.githubusercontent.com）';
      })
      .catch(function (e) {
        status.textContent = '❌ 读取失败：' + e.message;
      });
  }

  // ---------- Gist 存储 ----------
  function gistHeaders() {
    var h = { 'Content-Type': 'application/json' };
    if (state.token) h.Authorization = 'token ' + state.token;
    return h;
  }

  function saveToGist() {
    var status = $('#gist-status');
    var payload = {
      description: 'AI-HUB Demo 生成记录',
      public: false,
      files: {
        'aihub-records.json': {
          content: JSON.stringify({ updatedAt: nowStr(), records: state.records }, null, 2),
        },
      },
    };
    var url = state.gistId ? GIST_API + '/' + state.gistId : GIST_API;
    var method = state.gistId ? 'PATCH' : 'POST';
    status.textContent = '正在保存到 GitHub Gist…';
    fetch(url, { method: method, headers: gistHeaders(), body: JSON.stringify(payload) })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (g) {
        state.gistId = g.id;
        status.textContent = '✅ 已保存到 Gist：' + g.id + '（可分享 https://gist.github.com/' + g.id + '）';
      })
      .catch(function (e) {
        status.textContent = '❌ 保存失败：' + e.message + '（未填写 PAT 时请使用本地存储）';
      });
  }

  function loadFromGist() {
    var status = $('#gist-status');
    var id = ($('#gist-id').value || '').trim() || state.gistId;
    if (!id) { status.textContent = '请填写 Gist ID'; return; }
    status.textContent = '正在读取 Gist…';
    fetch(GIST_API + '/' + id, { headers: gistHeaders() })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (g) {
        var f = g.files && g.files['aihub-records.json'];
        if (!f) throw new Error('Gist 中没有 aihub-records.json');
        var data = JSON.parse(f.content);
        state.records = data.records || [];
        state.gistId = g.id;
        saveLocal();
        renderRecords();
        status.textContent = '✅ 已从 Gist 读取 ' + state.records.length + ' 条记录';
      })
      .catch(function (e) { status.textContent = '❌ 读取失败：' + e.message; });
  }

  // ---------- 初始化 ----------
  function init() {
    loadLocal();
    renderRecords();
    renderBoard([]);
    loadFromRepo();

    var form = $('#demo-form');
    if (!form) return;

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var lines = ($('#demo-reqs').value || '').split('\n')
        .map(function (s) { return s.trim(); })
        .filter(function (s) { return s.length > 0; });
      if (!lines.length) { alert('请至少输入一条需求'); return; }
      var mode = ($('#demo-model').value === 'paid') ? 'parallel' : 'serial';
      var batch = 'BATCH-' + Math.random().toString(36).slice(2, 8).toUpperCase();
      var tasks = lines.map(function (l) {
        return {
          id: uid('AI'), batch: batch, title: l.slice(0, 22), mode: mode,
          status: 'queued', progress: 0, cases: 0, queuePosition: 0,
        };
      });
      simulate(tasks, mode, function () {
        var s = $('#gist-status');
        s.textContent = '序列完成，记录已加入本地；可「保存到 GitHub Gist」持久化。';
      });
    });

    var saveBtn = $('#gist-save');
    if (saveBtn) saveBtn.addEventListener('click', function () {
      state.token = ($('#gist-token').value || '').trim();
      state.gistId = ($('#gist-id').value || '').trim();
      saveToGist();
    });
    var loadBtn = $('#gist-load');
    if (loadBtn) loadBtn.addEventListener('click', function () {
      state.token = ($('#gist-token').value || '').trim();
      loadFromGist();
    });
    var repoBtn = $('#repo-load');
    if (repoBtn) repoBtn.addEventListener('click', loadFromRepo);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
