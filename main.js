// GuessTube · 看画面猜英文
// 数据来自 data/videos.js（window.VIDEO_DATA），用户记录存在 localStorage
'use strict';

const DATA = window.VIDEO_DATA || { videos: [] };
const videos = DATA.videos;
const byId = Object.fromEntries(videos.map(v => [v.id, v]));
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ---------- 本地存储 ----------
const read = (k, d) => { try { return JSON.parse(localStorage.getItem('gt-' + k)) ?? d; } catch { return d; } };
const write = (k, v) => { try { localStorage.setItem('gt-' + k, JSON.stringify(v)); } catch { toast('浏览器存储不可用，本次记录不会保存'); } };
let history = read('history', []);      // [id]
let later = read('later', []);          // [id]
let results = read('results', {});      // id -> {score,total,at}
let prefs = read('prefs', { theme: 'dark' });
let verdict = read('verdict', {});     // id -> 'keep' | 'drop'（你筛选的结果）

// ---------- 图标 ----------
const P = {
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  home: '<path d="m3 11 9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/>',
  scenes: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>',
  later: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  check: '<path d="m5 12 5 5 9-10"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  theme: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
  replay: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
};
const icon = n => `<svg viewBox="0 0 24 24" aria-hidden="true">${P[n] || ''}</svg>`;
$('#menu').innerHTML = icon('menu');
$('#search-button').innerHTML = icon('search');
$('#theme').innerHTML = icon('theme');

const NAV = [
  ['/', '首页', 'home'],
  ['/scenes', '场景', 'scenes'],
  ['/history', '看过的', 'history'],
  ['/later', '稍后看', 'later'],
];

// ---------- 工具 ----------
const mmss = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
const LEVEL = { 1: '入门', 2: '中等', 3: '较难' };
const scenes = [...new Set(videos.map(v => v.scene))];

function toast(s) {
  const t = $('#toast');
  t.textContent = s; t.classList.add('show');
  clearTimeout(toast.timer); toast.timer = setTimeout(() => t.classList.remove('show'), 2400);
}

function route() {
  const h = location.hash.startsWith('#/') ? location.hash.slice(1) : '/';
  return new URL(h, 'https://x.invalid');
}

function card(v) {
  const r = results[v.id], vd = verdict[v.id];
  const badge = (vd ? `<span class="vd ${vd}">${vd === 'keep' ? '✓ 保留' : '✗ 不要'}</span>` : '') + (r ? `<span class="done">${r.score}/${r.total}</span>` : '');
  const saved = later.includes(v.id);
  return `<a class="card ${vd === 'drop' ? 'dropped' : ''}" href="#/watch/${v.id}">
    <div class="thumb"><img src="https://i.ytimg.com/vi/${v.id}/mqdefault.jpg" alt="" loading="lazy">
      <button class="save ${saved ? 'active' : ''}" data-save="${v.id}" aria-label="稍后看">${icon(saved ? 'check' : 'later')}</button>
      ${badge}<span class="duration">${mmss(v.seconds)}</span></div>
    <div class="info"><h3>${esc(v.title)}</h3>
      <div class="sub">${esc(v.channel)} · ${esc(v.scene)}</div></div></a>`;
}

const grid = list => list.length ? `<div class="grid">${list.map(card).join('')}</div>` : '<div class="status">这里还没有视频</div>';

// ---------- 页面 ----------
let player = null;

function render() {
  const u = route();
  const path = u.pathname.replace(/\/$/, '') || '/';
  const q = (u.searchParams.get('q') || '').toLowerCase();
  player = null;
  document.querySelectorAll('nav a').forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + path));
  let html = '';

  if (path === '/') {
    const sc = u.searchParams.get('scene') || '';
    const st = u.searchParams.get('st') ?? 'todo';
    const stOk = v => st === 'all' || (st === 'todo' ? !verdict[v.id] : verdict[v.id] === st);
    let list = videos.filter(v => (!sc || v.scene === sc) && stOk(v));
    if (q) list = list.filter(v => (v.title + v.scene + v.channel).toLowerCase().includes(q));
    const chip = (k, val, label, cur) => `<a class="pill ${cur === val ? 'active' : ''}" href="#/?${new URLSearchParams({ ...(sc && k !== 'scene' ? { scene: sc } : {}), ...(k !== 'st' ? { st } : {}), ...(val ? { [k]: val } : {}) })}">${label}</a>`;
    const n = k => videos.filter(v => k === 'todo' ? !verdict[v.id] : verdict[v.id] === k).length;
    html = `<div class="toolbar">${chip('scene', '', '全部', sc)}${scenes.map(s => chip('scene', s, esc(s), sc)).join('')}</div>
      <div class="toolbar">${chip('st', 'todo', `未筛 ${n('todo')}`, st)}${chip('st', 'keep', `保留 ${n('keep')}`, st)}${chip('st', 'drop', `不要 ${n('drop')}`, st)}${chip('st', 'all', `全部 ${videos.length}`, st)}
      <span class="grow"></span><button class="pill" id="export">导出筛选结果</button></div>
      ${q ? `<h2>搜索 “${esc(q)}”</h2>` : ''}${grid(list)}`;
  } else if (path === '/scenes') {
    html = `<h2>场景</h2><div class="areas">${scenes.map(s => {
      const list = videos.filter(v => v.scene === s);
      const done = list.filter(v => results[v.id]).length;
      return `<a class="area" href="#/?scene=${encodeURIComponent(s)}"><h3>${esc(s)}</h3><span class="sub">${list.length} 个 · 做过 ${done}</span></a>`;
    }).join('')}</div>`;
  } else if (path === '/history') {
    html = `<h2>看过的</h2>${history.length ? `<div class="toolbar"><button class="pill" id="clear-history">清空记录</button></div>` : ''}${grid(history.slice().reverse().map(id => byId[id]).filter(Boolean))}`;
  } else if (path === '/later') {
    html = `<h2>稍后看</h2>${grid(later.slice().reverse().map(id => byId[id]).filter(Boolean))}`;
  } else if (path.startsWith('/watch/')) {
    const v = byId[path.slice(7)];
    if (!v) { html = '<div class="status">找不到这个视频</div>'; }
    else {
      if (history.at(-1) !== v.id) { history = history.filter(x => x !== v.id).concat(v.id).slice(-300); write('history', history); }
      const start = +u.searchParams.get('t') || 0;
      html = `<div class="watch"><section class="primary">
        <div class="player"><div id="yt"></div></div>
        <h1>${esc(v.title)}</h1>
        <div class="owner"><span class="sub">${esc(v.scene)} · ${LEVEL[v.level] || ''} · ${mmss(v.seconds)} · ${esc(v.channel)}</span>
          <div class="actions"><button class="pill keep ${verdict[v.id] === 'keep' ? 'active' : ''}" data-verdict="keep">✓ 保留</button>
          <button class="pill drop ${verdict[v.id] === 'drop' ? 'active' : ''}" data-verdict="drop">✗ 不要</button>
          <button class="pill" id="replay">${icon('replay')}从头再看</button>
          <button class="pill" data-watchsave="${v.id}">${icon('later')}${later.includes(v.id) ? '已加入' : '稍后看'}</button></div></div>
        ${v.questions?.length ? `<div id="quiz" class="quiz"><div class="waiting"><b>先别看字幕，完整看完这一段</b>
          <p>看完会自动出题。画面里发生了什么、他们大概在说什么，先在心里猜一猜。</p>
          <button class="pill" id="start-quiz">我看完了，开始答题</button></div></div>` : `<p class="notice">点「保留」或「不要」后自动跳到下一个没筛过的视频。</p>`}
      </section><aside class="related">${videos.filter(x => x.id !== v.id && x.scene === v.scene).concat(videos.filter(x => x.scene !== v.scene)).slice(0, 10).map(card).join('')}</aside></div>`;
      $('#view').innerHTML = html;
      bind();
      mountPlayer(v, start);
      if ($('#start-quiz')) $('#start-quiz').onclick = () => showQuiz(v);
      document.querySelectorAll('[data-verdict]').forEach(b => b.onclick = () => judge(v, b.dataset.verdict));
      $('#replay').onclick = () => { player?.seekTo?.(0, true); player?.playVideo?.(); };
      window.scrollTo(0, 0);
      return;
    }
  } else {
    html = '<div class="status">页面不存在</div>';
  }
  $('#view').innerHTML = html;
  bind();
}

// ---------- 播放器（YouTube IFrame API） ----------
let ytReady = null;
function loadYT() {
  if (ytReady) return ytReady;
  ytReady = new Promise(res => {
    window.onYouTubeIframeAPIReady = res;
    const s = document.createElement('script');
    s.src = 'https://www.youtube.com/iframe_api';
    s.onerror = () => toast('播放器加载失败，检查一下代理');
    document.head.appendChild(s);
  });
  return ytReady;
}

function mountPlayer(v, start) {
  loadYT().then(() => {
    if (!$('#yt')) return;
    player = new YT.Player('yt', {
      videoId: v.id,
      playerVars: { cc_load_policy: 0, iv_load_policy: 3, rel: 0, modestbranding: 1, playsinline: 1, start, hl: 'en' },
      events: {
        onReady: e => { try { e.target.unloadModule('captions'); e.target.unloadModule('cc'); } catch {} },
        onStateChange: e => {
          if (e.data === 1) { try { e.target.unloadModule('captions'); } catch {} }   // 播放时再关一次字幕
          if (e.data === 0 && v.questions?.length && !$('#quiz .q')) showQuiz(v);                          // 播完自动出题
        },
        onError: e => toast(`这个视频放不了（错误 ${e.data}），建议点「不要」`),
      },
    });
  });
}

const seek = t => { if (player?.seekTo) { player.seekTo(Math.max(0, t - 0.5), true); player.playVideo(); window.scrollTo({ top: 0, behavior: 'smooth' }); } };

// ---------- 答题 ----------
function showQuiz(v) {
  const box = $('#quiz');
  if (!box) return;
  box.innerHTML = `<h2>猜一猜</h2>${v.questions.map((q, i) => `
    <div class="q" data-i="${i}"><div class="qhead"><b>${i + 1}. ${esc(q.q)}</b>
      ${q.t != null ? `<button class="link" data-seek="${q.t}">▶ 重听 ${mmss(q.t)}</button>` : ''}</div>
      ${q.options.map((o, j) => `<label class="opt"><input type="radio" name="q${i}" value="${j}"><span>${esc(o)}</span></label>`).join('')}
      <div class="explain"></div></div>`).join('')}
    <button class="pill primary-btn" id="submit">交卷，看答案</button>`;
  bind();
  $('#submit').onclick = () => grade(v);
}

function grade(v) {
  let score = 0;
  v.questions.forEach((q, i) => {
    const el = document.querySelector(`.q[data-i="${i}"]`);
    const picked = el.querySelector('input:checked');
    const ok = picked && +picked.value === q.answer;
    if (ok) score++;
    el.classList.add(ok ? 'right' : 'wrong');
    el.querySelectorAll('.opt').forEach((o, j) => { if (j === q.answer) o.classList.add('answer'); });
    el.querySelectorAll('input').forEach(x => x.disabled = true);
    el.querySelector('.explain').innerHTML = (ok ? '✓ ' : '✗ ') + esc(q.explain || '');
  });
  results[v.id] = { score, total: v.questions.length, at: Date.now() };
  write('results', results);
  $('#submit').remove();
  $('#quiz').insertAdjacentHTML('beforeend', `
    <div class="score">${score} / ${v.questions.length}</div>
    ${v.summary ? `<p class="summary">${esc(v.summary)}</p>` : ''}
    <h2>原文对照</h2><p class="notice">点任意一句，跳到那一刻重听。</p>
    <div class="transcript">${v.lines.map(l => `<button class="line" data-seek="${l.t}"><span class="ts">${mmss(l.t)}</span><span><b>${esc(l.en)}</b><i>${esc(l.zh)}</i></span></button>`).join('')}</div>`);
  bind();
  $('#quiz').scrollIntoView({ behavior: 'smooth' });
}

// ---------- 筛选 ----------
function judge(v, k) {
  if (verdict[v.id] === k) delete verdict[v.id]; else verdict[v.id] = k;   // 再点一次 = 撤销
  write('verdict', verdict);
  if (!verdict[v.id]) { render(); return; }
  toast(k === 'keep' ? '已保留' : '已标记不要');
  const i = videos.indexOf(v);
  const next = videos.slice(i + 1).concat(videos.slice(0, i)).find(x => !verdict[x.id]);
  location.hash = next ? '#/watch/' + next.id : '#/?st=keep';
}

function exportVerdict() {
  const keep = videos.filter(v => verdict[v.id] === 'keep').map(v => v.id);
  const drop = videos.filter(v => verdict[v.id] === 'drop').map(v => v.id);
  const t = `GuessTube 筛选结果（共 ${videos.length}，保留 ${keep.length}，不要 ${drop.length}，未筛 ${videos.length - keep.length - drop.length}）\n保留：${keep.join(' ')}\n不要：${drop.join(' ')}`;
  navigator.clipboard.writeText(t).then(() => toast('已复制，粘贴发给 Claude 就行'), () => prompt('复制下面的内容', t));
}

// ---------- 事件 ----------
function bind() {
  document.querySelectorAll('[data-save]').forEach(b => b.onclick = e => {
    e.preventDefault(); e.stopPropagation();
    const id = b.dataset.save;
    later = later.includes(id) ? later.filter(x => x !== id) : later.concat(id);
    write('later', later); toast(later.includes(id) ? '已加入稍后看' : '已移出稍后看'); render();
  });
  document.querySelectorAll('[data-watchsave]').forEach(b => b.onclick = () => {
    const id = b.dataset.watchsave;
    later = later.includes(id) ? later.filter(x => x !== id) : later.concat(id);
    write('later', later); b.innerHTML = icon('later') + (later.includes(id) ? '已加入' : '稍后看');
  });
  document.querySelectorAll('[data-seek]').forEach(b => b.onclick = () => seek(+b.dataset.seek));
  if ($('#export')) $('#export').onclick = exportVerdict;
  const ch = $('#clear-history');
  if (ch) ch.onclick = () => { history = []; write('history', history); render(); };
}

$('nav').innerHTML = NAV.map(([h, t, i]) => `<a href="#${h}">${icon(i)}<span>${t}</span></a>`).join('');
$('#search').onsubmit = e => { e.preventDefault(); location.hash = '#/?q=' + encodeURIComponent($('#query').value.trim()); };
$('#menu').onclick = () => document.body.classList.toggle(innerWidth <= 800 ? 'drawer' : 'collapsed');
$('#scrim').onclick = () => document.body.classList.remove('drawer');
function setTheme(t) { prefs.theme = t; write('prefs', prefs); document.documentElement.dataset.theme = t; }
$('#theme').onclick = () => setTheme(prefs.theme === 'dark' ? 'light' : 'dark');
setTheme(prefs.theme);
addEventListener('hashchange', () => { document.body.classList.remove('drawer'); render(); });
render();
