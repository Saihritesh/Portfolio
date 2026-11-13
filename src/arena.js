/* ---------------------------------------------------------------------------
 * The Courtyard Siege: a wave-survival mini-game outside the castle gate.
 * Ogres lumber in from both sides and smash with clubs; from wave 3 dragons
 * circle overhead, spit fireballs and swoop low enough to be slashed.
 * All positions are native room pixels (360x225), drawn at 4x like the rooms.
 * ------------------------------------------------------------------------- */

const A = (p) => '/assets/' + p;
const SCORES_KEY = 'coc-arena-scores';
const NAME_KEY = 'coc-arena-name';

// Knight physics
const SPEED = 80, JUMP_V = 200, GRAVITY = 600;
const SLASH_T = [0.07, 0.16, 0.28], SLASH_REACH = 24, SLASH_UP = 44;
const MAX_HP = 5, INVULN = 1.2;
const X_MIN = 10, X_MAX = 350, GATE_X = 336;

// Enemy sprite anchors (see tools/arena_art.py)
const OGRE = { w: 48, h: 48, cx: 22 };
const MAX_WAVES = 5;
// The Dread Wyrm (tools/wyrm_art.py): 160x112 sprite, positioned by its centre (80, 56).
// Boxes are relative to that centre for the right-facing sprite; mirrored when facing left.
const WYRM = {
  w: 160, h: 112, hp: 30,
  head: { l: 36, r: 72, t: -34, b: -6 },      // crit spot: 2 damage, needs a jump when it's grounded
  chest: { l: -20, r: 32, t: -10, b: 24 },
  body: { l: -44, r: 52, t: -22, b: 38 },     // contact damage during the dive
  mouth: { x: 68, y: -18 },
  groundOffset: 40,                             // centre sits this far above the floor when it has slammed down
  // per phase (1..3): hover time, grounded (vulnerable) time, dive telegraph, fireballs per rain, flame waves per sweep
  tune: [null, { hover: 1.3, down: 1.35, tele: 0.8, rain: 7, waves: 1 }, { hover: 0.9, down: 1.0, tele: 0.6, rain: 10, waves: 2 }, { hover: 0.5, down: 0.75, tele: 0.45, rain: 14, waves: 3 }],
  // attack order per phase: there's always a dive (the only opening) within every two attacks
  seq: [null, ['rain', 'dive', 'sweep', 'dive'], ['sweep', 'dive', 'rain', 'dive', 'summon', 'dive'], ['rain', 'dive', 'sweep', 'dive', 'rain', 'dive', 'summon']],
};
const DRAGON = { w: 64, h: 48, cx: 32, cy: 26 };

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const rand = (a, b) => a + Math.random() * (b - a);
const pad = (n, w = 5) => String(n).padStart(w, '0');

const IMG = {
  ogre: (pose, dir) => A(`sprites/ogre_${pose}_${dir > 0 ? 'right' : 'left'}.png`),
  dragon: (pose, dir) => A(`sprites/dragon_${pose}_${dir > 0 ? 'right' : 'left'}.png`),
  fireball: (f) => A(`sprites/fireball_${f}.png`),
  boss: (pose, dir) => A(`sprites/boss_${pose}_${dir > 0 ? 'right' : 'left'}.png`),
  heart: (full) => A(`sprites/heart_${full ? 'full' : 'empty'}.png`),
};
['walk1', 'walk2', 'windup', 'smash'].forEach((p) => [1, -1].forEach((d) => { new Image().src = IMG.ogre(p, d); }));
['fly1', 'fly2', 'fly3', 'breathe'].forEach((p) => [1, -1].forEach((d) => { new Image().src = IMG.dragon(p, d); }));
[1, 2].forEach((f) => { new Image().src = IMG.fireball(f); });
['fly1', 'fly2', 'fly3', 'breathe'].forEach((p) => [1, -1].forEach((d) => { new Image().src = IMG.boss(p, d); }));

export function loadScores() {
  try { return JSON.parse(localStorage.getItem(SCORES_KEY) || '[]'); } catch { return []; }
}
function saveScores(list) { localStorage.setItem(SCORES_KEY, JSON.stringify(list.slice(0, 5))); }
function qualifies(score) {
  const list = loadScores();
  return score > 0 && (list.length < 5 || score > list[list.length - 1].s);
}

export function createArena({ keys, S, FLOOR, SPRITES, HK, HK_CX, reduced, onExit }) {
  let root, layer, knightEl, knightImg, heartsEl, scoreEl, bestEl, bannerEl, panelEl;
  let st = null;          // whole game state, rebuilt on enter/start

  const fresh = () => ({
    phase: 'ready',       // ready | play | paused | over | initials
    t: 0, hitstop: 0, shake: 0,
    k: { x: 60, jy: 0, vy: 0, kvx: 0, facing: 1, walking: false, slash: -1, slashHit: false, hp: MAX_HP, inv: 0 },
    enemies: [], shots: [], fx: [],
    wave: 0, queue: [], spawnT: 0, betweenT: 0, boss: null, won: false, next: null,
    score: 0, combo: 1, comboT: 0, kills: 0,
    initials: (localStorage.getItem(NAME_KEY) || 'AAA').split(''), cursor: 0, newRank: -1,
  });

  // drifting clouds between the sky layer and the scene: [sprite, native y, seconds per crossing, start offset]
  // sprite sizes come from tools/tree_art.py CLOUDS (w, h in native px)
  const CLOUD_SIZE = { 1: [84, 26], 2: [120, 32], 3: [60, 20], 4: [100, 28], 5: [70, 22] };
  const CLOUDS = [[2, 18, 150, 20], [1, 44, 120, 85], [4, 70, 170, 60], [3, 96, 105, 30], [5, 30, 135, 115]];

  /* ---------------- DOM ---------------- */
  function build(roomEl) {
    roomEl.innerHTML = `
      <div class="arena">
        <div class="art" style="background-image:url(${A('rooms/courtyard_sky.png')})"></div>
        <div class="ar-clouds" aria-hidden="true">${CLOUDS.map(([n, y, dur, del]) => `<img class="pix ar-cloud" src="${A(`sprites/cloud_${n}.png`)}" alt="" style="top:${y * 4}px;width:${CLOUD_SIZE[n][0] * 4}px;height:${CLOUD_SIZE[n][1] * 4}px;animation-duration:${dur}s;animation-delay:-${del}s">`).join('')}</div>
        <div class="art" role="img" aria-label="Pixel art: the courtyard outside the castle gate, under the giant tree" style="background-image:url(${A('rooms/courtyard_fg.png')})"></div>
        <div class="ar-layer"></div>
        <div class="ar-hearts" aria-label="Health"></div>
        <div class="ar-score px"><div class="wave"></div><div class="pts"></div></div>
        <div class="ar-best px"><span class="lbl">HIGH SCORE</span><span class="val"></span></div>
        <div class="ar-bossbar" hidden><span class="px">THE DREAD WYRM</span><div class="bar"><div></div></div></div>
        <div class="ar-banner px" hidden></div>
        <div class="frame ar-panel" hidden></div>
        <div class="px controls"><span><b>◄ ►</b> MOVE</span><span><b>SPACE</b> JUMP</span><span><b>X</b> SLASH</span><span><b>ESC</b> PAUSE</span><span><b>N</b> MUSIC</span></div>
      </div>`;
    root = roomEl.querySelector('.arena');
    layer = root.querySelector('.ar-layer');
    heartsEl = root.querySelector('.ar-hearts');
    scoreEl = root.querySelector('.ar-score');
    bestEl = root.querySelector('.ar-best .val');
    bannerEl = root.querySelector('.ar-banner');
    panelEl = root.querySelector('.ar-panel');
    knightEl = document.createElement('div');
    knightEl.className = 'ar-knight';
    knightEl.innerHTML = `<div class="shadow"></div><img class="pix" alt="The knight" style="width:${HK * S}px;height:${HK * S}px">`;
    knightImg = knightEl.querySelector('img');
    layer.appendChild(knightEl);
    heartsEl.innerHTML = Array.from({ length: MAX_HP }, () => `<img class="pix" alt="" src="${IMG.heart(true)}">`).join('');
  }

  function enter(roomEl) {
    st = fresh();
    build(roomEl);
    st.k.x = GATE_X - 20; st.k.facing = -1;
    showReady();
    hud();
  }

  /* ---------------- panels ---------------- */
  function scoreTable(highlight = -1) {
    const list = loadScores();
    if (!list.length) return `<div class="ar-empty">No champions yet. Be the first.</div>`;
    return `<ol class="ar-table">${list.map((r, i) => `<li class="${i === highlight ? 'new' : ''}"><span>${i + 1}.</span><span>${esc(r.n)}</span><span>${pad(r.s)}</span><span>${r.won ? 'WIN' : 'W' + r.w}</span></li>`).join('')}</ol>`;
  }
  function panel(html) { panelEl.innerHTML = html; panelEl.hidden = false; }
  function hidePanel() { panelEl.hidden = true; }

  function showReady() {
    st.phase = 'ready';
    panel(`
      <div class="px ar-title">THE COURTYARD SIEGE</div>
      <p>Ogres and dragons gather at the gate. Survive five waves, and then face what commands them.</p>
      <ul class="ar-tips"><li><b>X</b> slash · two hits fell an ogre</li><li>When an ogre raises its club, strike first or get clear</li><li>Dragons swoop low to attack: that's your chance. Jump or slash their fireballs</li><li>The Dread Wyrm can only be wounded after it slams down. Jump to strike its head</li></ul>
      <div class="px ar-sub">TOP KNIGHTS</div>${scoreTable()}
      <div class="ar-actions"><button type="button" class="btn blink" data-act="start">ENTER · BEGIN</button><button type="button" class="btn btn-dark" data-act="exit">ESC · BACK INSIDE</button></div>`);
    wirePanel();
  }
  function showPause() {
    st.phase = 'paused';
    panel(`<div class="px ar-title">PAUSED</div>
      <div class="ar-actions"><button type="button" class="btn" data-act="resume">ENTER · RESUME</button><button type="button" class="btn btn-dark" data-act="exit">ESC · LEAVE THE SIEGE</button></div>`);
    wirePanel();
  }
  function showOver() {
    st.phase = 'over';
    const rank = st.newRank;
    const head = st.won ? `<div class="px ar-title won">THE CASTLE STANDS</div><p class="ar-center">The Dread Wyrm has fallen. Knight Saihritesh holds the gate.</p>`
      : `<div class="px ar-title fallen">YOU HAVE FALLEN</div>${st.boss ? `<p class="ar-center">The Dread Wyrm had ${st.boss.hp} of ${WYRM.hp} life left.</p>` : ''}`;
    panel(`${head}
      <div class="ar-final"><span class="px">SCORE ${pad(st.score)}</span><span class="px">${st.won ? 'VICTORY' : st.boss ? 'FINAL BATTLE' : 'WAVE ' + st.wave}</span><span class="px">FOES ${st.kills}</span></div>
      <div class="px ar-sub">TOP KNIGHTS</div>${scoreTable(rank)}
      <div class="ar-actions"><button type="button" class="btn blink" data-act="start">ENTER · FIGHT AGAIN</button><button type="button" class="btn btn-dark" data-act="exit">ESC · BACK INSIDE</button></div>`);
    wirePanel();
  }
  function showInitials() {
    st.phase = 'initials';
    const letters = st.initials.map((c, i) => `<span class="slot ${i === st.cursor ? 'on' : ''}">${esc(c)}</span>`).join('');
    panel(`<div class="px ar-title${st.won ? ' won' : ''}">${st.won ? 'VICTORY · ' : ''}NEW HIGH SCORE</div>
      <div class="ar-final"><span class="px">SCORE ${pad(st.score)}</span><span class="px">WAVE ${st.wave}</span></div>
      <p>Carve your initials into the gate. Type letters, ◄ ► or ▲ ▼ to change them, ENTER to confirm.</p>
      <div class="px ar-initials">${letters}</div>
      <div class="ar-actions"><button type="button" class="btn" data-act="confirm">ENTER · CONFIRM</button></div>`);
    wirePanel();
  }
  function wirePanel() {
    panelEl.querySelectorAll('[data-act]').forEach((b) => b.addEventListener('click', () => act(b.dataset.act)));
  }
  function act(a) {
    if (a === 'start') startGame();
    else if (a === 'resume') { hidePanel(); st.phase = 'play'; }
    else if (a === 'exit') leave();
    else if (a === 'confirm') confirmInitials();
  }
  function leave() {
    st.phase = 'gone';
    onExit();
  }

  /* ---------------- flow ---------------- */
  function startGame() {
    const keep = st.initials;
    st = Object.assign(fresh(), { initials: keep });
    layer.querySelectorAll('.ent, .ar-pop, .spark').forEach((e) => e.remove());
    root.querySelector('.ar-bossbar').hidden = true;
    st.phase = 'play';
    st.k.x = 180;
    hidePanel();
    nextWave();
    hud();
  }

  function nextWave() {
    st.wave += 1;
    const w = st.wave;
    const ogres = 2 + w;
    const dragons = w >= 3 ? Math.min(3, Math.floor((w - 1) / 2)) : 0;
    st.queue = [...Array(ogres).fill('ogre'), ...Array(dragons).fill('dragon')].sort(() => Math.random() - 0.5);
    if (st.queue[0] === 'dragon' && ogres) st.queue.push(st.queue.shift());   // open each wave with an ogre
    st.spawnT = 1.4;
    banner(`WAVE ${w}`, 1.6);
    hud();
  }

  function banner(text, secs, cls = '') {
    bannerEl.textContent = text;
    bannerEl.className = 'ar-banner px ' + cls;
    bannerEl.hidden = false;
    st.bannerT = secs;
  }

  function gameOver() {
    st.k.hp = 0;
    if (qualifies(st.score)) { st.cursor = 0; showInitials(); }
    else { st.newRank = -1; showOver(); }
  }

  function confirmInitials() {
    const n = st.initials.join('').replace(/[^A-Z]/g, 'A').slice(0, 3);
    localStorage.setItem(NAME_KEY, n);
    const list = loadScores();
    const entry = { n, s: st.score, w: st.wave, won: st.won, d: Date.now() };
    list.push(entry);
    list.sort((a, b) => b.s - a.s || a.d - b.d);
    saveScores(list);
    st.newRank = list.slice(0, 5).indexOf(entry);
    showOver();
    hud();
  }

  /* ---------------- spawning ---------------- */
  function spawn(type) {
    const side = Math.random() < 0.5 ? -1 : 1;              // -1: enters from the left
    const el = document.createElement('img');
    el.className = 'pix ent ' + type;
    el.alt = '';
    layer.insertBefore(el, type === 'dragon' ? null : knightEl);
    if (type === 'ogre') {
      el.style.width = OGRE.w * S + 'px'; el.style.height = OGRE.h * S + 'px';
      st.enemies.push({ type, el, x: side < 0 ? -24 : 384, dir: -side, hp: 2, state: 'walk', t: 0, flash: 0,
        speed: Math.min(46, 20 + st.wave * 2.5), windup: Math.max(0.38, 0.62 - st.wave * 0.02) });
    } else {
      el.style.width = DRAGON.w * S + 'px'; el.style.height = DRAGON.h * S + 'px';
      const baseY = rand(38, 66);
      st.enemies.push({ type, el, x: side < 0 ? -40 : 400, y: baseY, baseY, dir: -side, hp: 3, state: 'fly', t: 0, flash: 0,
        breathT: rand(1.4, 2.4), swoopT: rand(3.5, 6), entered: false });
    }
  }

  function onScreen(type) { return st.enemies.filter((e) => e.type === type && e.state !== 'dying').length; }

  /* ---------------- combat helpers ---------------- */
  function hurtKnight(fromX) {
    const k = st.k;
    if (k.inv > 0 || st.phase !== 'play') return;
    k.hp -= 1;
    k.inv = INVULN;
    k.kvx = (k.x >= fromX ? 1 : -1) * 150;
    k.vy = Math.max(k.vy, 90);
    k.slash = -1;
    st.shake = 0.25;
    st.combo = 1; st.comboT = 0;
    hud();
    if (k.hp <= 0) gameOver();
  }

  function addScore(base, x, y) {
    const pts = base * st.combo;
    st.score += pts;
    popText(`+${pts}`, x, y);
    hud();
  }

  function kill(e) {
    e.state = 'dying'; e.t = 0;
    st.kills += 1;
    st.combo = st.comboT > 0 ? Math.min(5, st.combo + 1) : 1;
    st.comboT = 3;
    addScore(e.type === 'ogre' ? 100 : 300, e.x, e.type === 'ogre' ? FLOOR - 44 : e.y - 16);
  }

  function popText(text, x, y) {
    const el = document.createElement('div');
    el.className = 'ar-pop px'; el.textContent = text;
    el.style.left = x * S + 'px'; el.style.top = y * S + 'px';
    layer.appendChild(el);
    setTimeout(() => el.remove(), 900);
  }
  function spark(x, y) {
    const el = document.createElement('div');
    el.className = 'spark';
    el.style.left = x * S + 'px'; el.style.top = y * S + 'px';
    layer.appendChild(el);
    setTimeout(() => el.remove(), 400);
  }

  // The knight's strike: one check per swing, on the strike frame.
  function strike() {
    const k = st.k;
    const x0 = k.facing > 0 ? k.x - 4 : k.x - SLASH_REACH;
    const x1 = k.facing > 0 ? k.x + SLASH_REACH : k.x + 4;
    const yTop = FLOOR - k.jy - SLASH_UP, yBot = FLOOR - k.jy + 2;
    let landed = false;
    for (const e of st.enemies) {
      if (e.state === 'dying') continue;
      if (e.type === 'boss') { if (strikeBoss(e, x0, x1, yTop, yBot)) landed = true; continue; }
      const box = e.type === 'ogre'
        ? { l: e.x - 11, r: e.x + 11, t: FLOOR - 38, b: FLOOR }
        : { l: e.x - 20, r: e.x + 20, t: e.y - 11, b: e.y + 11 };
      if (box.r < x0 || box.l > x1 || box.b < yTop || box.t > yBot) continue;
      landed = true;
      e.hp -= 1; e.flash = 0.15;
      spark((Math.max(box.l, x0) + Math.min(box.r, x1)) / 2, Math.max(box.t, yTop) + 10);
      if (e.hp <= 0) { kill(e); continue; }
      if (e.type === 'ogre') { e.state = 'stagger'; e.t = 0; e.x += k.facing * 8; }
      else if (e.state === 'swoop') { e.state = 'rise'; e.t = 0; }
    }
    for (const f of st.shots) {
      if (f.dead || f.ground) continue;                     // ground flames must be jumped
      if (f.x >= x0 - 4 && f.x <= x1 + 4 && f.y >= yTop - 4 && f.y <= yBot) {
        f.dead = true; landed = true;
        spark(f.x, f.y);
        addScore(25, f.x, f.y - 6);
      }
    }
    if (landed) st.hitstop = 0.05;
  }

  /* ---------------- update ---------------- */
  function update(dt) {
    if (!st || st.phase === 'gone') return;
    if (st.bannerT > 0) { st.bannerT -= dt; if (st.bannerT <= 0) bannerEl.hidden = true; }
    if (st.phase === 'paused' || st.phase === 'over' || st.phase === 'initials') return;
    if (st.hitstop > 0) { st.hitstop -= dt; return; }
    st.t += dt;
    if (st.shake > 0) st.shake -= dt;

    updateKnight(dt);
    if (st.phase === 'ready') {
      if (st.k.x >= GATE_X && keys.has('right')) leave();
      return;
    }

    // waves
    if (st.queue.length) {
      st.spawnT -= dt;
      const ogreCap = Math.min(5, 2 + Math.floor(st.wave / 2));
      const next = st.queue[0];
      const room = next === 'ogre' ? onScreen('ogre') < ogreCap : onScreen('dragon') < 2;
      if (st.spawnT <= 0 && room) {
        spawn(st.queue.shift());
        st.spawnT = Math.max(0.7, 2.2 - st.wave * 0.15);
      }
    } else if (!st.enemies.length && !st.betweenT && !st.boss) {
      const bonus = 250 * st.wave;
      st.score += bonus;
      st.k.hp = Math.min(MAX_HP, st.k.hp + 1);
      if (st.wave >= MAX_WAVES) {
        banner('THE SKY DARKENS...', 3, 'boss');
        st.betweenT = 3.4; st.next = 'boss';
      } else {
        banner(`WAVE CLEAR  +${bonus}`, 2.2, 'clear');
        st.betweenT = 2.6; st.next = 'wave';
      }
      hud();
    }
    if (st.betweenT) { st.betweenT -= dt; if (st.betweenT <= 0) { st.betweenT = 0; st.next === 'boss' ? spawnBoss() : nextWave(); } }
    if (st.comboT > 0) { st.comboT -= dt; if (st.comboT <= 0) { st.combo = 1; hud(); } }

    for (const e of st.enemies) ({ ogre: updateOgre, dragon: updateDragon, boss: updateBoss })[e.type](e, dt);
    st.enemies = st.enemies.filter((e) => {
      if (e.gone) { e.el.remove(); return false; }
      return true;
    });
    updateShots(dt);
  }

  function updateKnight(dt) {
    const k = st.k;
    if (k.inv > 0) k.inv -= dt;
    let dir = 0;
    if (keys.has('left')) dir -= 1;
    if (keys.has('right')) dir += 1;
    const rooted = k.slash >= 0 && k.jy === 0;
    k.walking = dir !== 0 && !rooted;
    if (dir) k.facing = dir;
    if (k.walking) k.x += dir * SPEED * dt;
    if (k.kvx) {                                            // knockback slides and decays
      k.x += k.kvx * dt;
      k.kvx *= Math.exp(-7 * dt);
      if (Math.abs(k.kvx) < 4) k.kvx = 0;
    }
    k.x = Math.max(X_MIN, Math.min(X_MAX, k.x));
    if (k.vy || k.jy > 0) {
      k.jy += k.vy * dt;
      k.vy -= GRAVITY * dt;
      if (k.jy <= 0) { k.jy = 0; k.vy = 0; }
    }
    if (k.slash >= 0) {
      k.slash += dt;
      if (!k.slashHit && k.slash >= SLASH_T[0]) { k.slashHit = true; if (st.phase === 'play') strike(); }
      if (k.slash >= SLASH_T[2]) k.slash = -1;
    }
  }

  function updateOgre(e, dt) {
    const k = st.k;
    e.t += dt;
    if (e.flash > 0) e.flash -= dt;
    if (e.state === 'dying') { if (e.t > 0.6) e.gone = true; return; }
    const dx = k.x - e.x;
    if (e.state === 'walk') {
      e.dir = dx >= 0 ? 1 : -1;
      // don't walk through a fellow ogre that's already closer to the knight
      const blocked = st.enemies.some((o) => o !== e && o.type === 'ogre' && o.state !== 'dying'
        && Math.sign(o.x - e.x) === e.dir && Math.abs(o.x - e.x) < 18 && Math.abs(k.x - o.x) < Math.abs(dx));
      if (Math.abs(dx) > 20) { if (!blocked) e.x += e.dir * e.speed * dt; }
      else if (k.jy < 30) { e.state = 'windup'; e.t = 0; }
    } else if (e.state === 'windup') {
      if (e.t >= e.windup) {
        e.state = 'smash'; e.t = 0;
        const reach = (k.x - e.x) * e.dir;
        if (reach > -6 && reach < 34 && k.jy < 12) hurtKnight(e.x);
        st.shake = Math.max(st.shake, 0.12);
      }
    } else if (e.state === 'smash') {
      if (e.t >= 0.3) { e.state = 'recover'; e.t = 0; }
    } else if (e.state === 'recover' || e.state === 'stagger') {
      if (e.t >= (e.state === 'recover' ? 0.7 : 0.35)) { e.state = 'walk'; e.t = 0; }
    }
  }

  function updateDragon(e, dt) {
    const k = st.k;
    e.t += dt;
    if (e.flash > 0) e.flash -= dt;
    if (e.state === 'dying') {
      e.vy = (e.vy || 0) + 260 * dt; e.y += e.vy * dt;
      if (e.y > FLOOR + 30 || e.t > 1.4) e.gone = true;
      return;
    }
    if (!e.entered && e.x > 30 && e.x < 330) e.entered = true;
    if (e.entered && ((e.x < 24 && e.dir < 0) || (e.x > 336 && e.dir > 0))) e.dir *= -1;
    const swoopY = FLOOR - 30;
    if (e.state === 'fly' || e.state === 'breathe') {
      e.x += e.dir * 34 * dt;
      e.y = e.baseY + Math.sin(e.t * 2.2) * 6;
      e.breathT -= dt; e.swoopT -= dt;
      if (e.state === 'breathe' && e.t >= 0.4) e.state = 'fly';
      if (e.state === 'fly' && e.breathT <= 0 && e.entered) {
        e.state = 'breathe'; e.t = 0; e.fired = false;
        e.breathT = Math.max(1.2, rand(1.8, 2.6) - st.wave * 0.08);
      }
      if (e.state === 'breathe' && !e.fired && e.t >= 0.15) {
        e.fired = true;
        const mx = e.x + e.dir * 27, my = e.y - 6;
        const ddx = k.x - mx, ddy = (FLOOR - k.jy - 16) - my;
        const len = Math.hypot(ddx, ddy) || 1, sp = 90 + st.wave * 3;
        shoot(mx, my, (ddx / len) * sp, (ddy / len) * sp);
      }
      if (e.state === 'fly' && e.swoopT <= 0 && e.entered) {
        e.state = 'swoop'; e.t = 0; e.fromY = e.y;
        e.dir = k.x >= e.x ? 1 : -1;
      }
    } else if (e.state === 'swoop') {
      // dive toward the ground, skim along it, then climb away
      e.x += e.dir * 70 * dt;
      e.y = e.t < 0.7 ? e.fromY + (swoopY - e.fromY) * Math.sin((e.t / 0.7) * Math.PI / 2) : swoopY;
      if (Math.abs(k.x - e.x) < 16 && Math.abs((FLOOR - k.jy - 17) - e.y) < 22) hurtKnight(e.x);
      if (e.t > 1.5 || e.x < 6 || e.x > 354) { e.state = 'rise'; e.t = 0; }
    } else if (e.state === 'rise') {
      e.x += e.dir * 40 * dt;
      e.y += (e.baseY - e.y) * Math.min(1, dt * 2.5);
      if (Math.abs(e.y - e.baseY) < 2) { e.state = 'fly'; e.t = 0; e.swoopT = rand(4.5, 7); }
    }
  }

  /* ---------------- the Dread Wyrm ---------------- */
  function box(e, b) {                                      // a WYRM box in world space
    return e.dir > 0 ? { l: e.x + b.l, r: e.x + b.r, t: e.y + b.t, b: e.y + b.b }
                     : { l: e.x - b.r, r: e.x - b.l, t: e.y + b.t, b: e.y + b.b };
  }
  const overlap = (a, x0, x1, y0, y1) => !(a.r < x0 || a.l > x1 || a.b < y0 || a.t > y1);

  function spawnBoss() {
    const el = document.createElement('img');
    el.className = 'pix ent boss'; el.alt = 'The Dread Wyrm';
    el.style.width = WYRM.w * S + 'px'; el.style.height = WYRM.h * S + 'px';
    layer.insertBefore(el, layer.firstChild);              // behind the knight and everything else
    const b = { type: 'boss', el, x: 460, y: 50, dir: -1, hp: WYRM.hp, phase: 1, state: 'enter', t: 0, flash: 0, step: 0, fired: 0 };
    st.boss = b; st.enemies.push(b);
    root.querySelector('.ar-bossbar').hidden = false;
    banner('THE DREAD WYRM', 2.4, 'boss');
    hud();
  }

  function strikeBoss(b, x0, x1, yTop, yBot) {
    const head = box(b, WYRM.head), chest = box(b, WYRM.chest);
    const hitHead = overlap(head, x0, x1, yTop, yBot), hitChest = overlap(chest, x0, x1, yTop, yBot);
    if (!hitHead && !hitChest) return false;
    const at = hitHead ? head : chest;
    const sx = (Math.max(at.l, x0) + Math.min(at.r, x1)) / 2, sy = Math.max(at.t, yTop) + 6;
    if (b.state !== 'grounded') { spark(sx, sy); popText('CLANG', sx, sy - 8); return true; }   // armoured while airborne
    const dmg = hitHead ? 2 : 1;
    b.hp = Math.max(0, b.hp - dmg); b.flash = 0.12;
    spark(sx, sy);
    addScore(50 * dmg, sx, sy - 6);
    if (b.hp <= 0) { b.state = 'dying'; b.t = 0; st.enemies.forEach((o) => { if (o !== b && o.state !== 'dying') { o.state = 'dying'; o.t = 0; } }); }
    hud();
    return true;
  }

  function nextAttack(b) {
    const seq = WYRM.seq[b.phase];
    const a = seq[b.step++ % seq.length];
    b.t = 0; b.fired = 0;
    if (a === 'rain') b.state = 'rain';
    else if (a === 'sweep') { b.state = 'sweepDown'; b.fromY = b.y; }
    else if (a === 'summon') b.state = 'roar';
    else { b.state = 'divePrep'; b.fromY = b.y; }
  }

  function updateBoss(b, dt) {
    const k = st.k, T = WYRM.tune[b.phase];
    b.t += dt;
    if (b.flash > 0) b.flash -= dt;
    if (b.state === 'dying') {
      b.y += 40 * dt;
      if (b.t > 2.4) { b.gone = true; victory(); }
      return;
    }
    // phase changes at two thirds and one third of its life
    const want = b.hp <= WYRM.hp / 3 ? 3 : b.hp <= (WYRM.hp * 2) / 3 ? 2 : 1;
    if (want > b.phase && b.state !== 'grounded') {
      b.phase = want; b.step = 0; b.state = 'roar'; b.t = 0;
      banner(want === 2 ? 'THE WYRM GROWS FURIOUS' : 'THE WYRM IS ENRAGED', 2, 'boss');
      st.shake = 0.5;
    }
    const face = () => { b.dir = k.x >= b.x ? 1 : -1; };
    switch (b.state) {
      case 'enter':
        b.x += (250 - b.x) * Math.min(1, dt * 1.4); b.y = 50 + Math.sin(b.t * 2) * 5; face();
        if (b.t > 2.6) { b.state = 'hover'; b.t = 0; }
        break;
      case 'hover': {
        const tx = k.x < 180 ? 262 : 98;                       // hang back on the far side of the knight
        b.x += Math.sign(tx - b.x) * Math.min(Math.abs(tx - b.x), 70 * dt);
        b.y += (54 + Math.sin(st.t * 2) * 6 - b.y) * Math.min(1, dt * 3);
        face();
        if (b.t > T.hover) nextAttack(b);
        break;
      }
      case 'rain': {                                         // a spread of fireballs from the jaws
        face();
        const dur = b.phase === 3 ? 1.2 : 1.6;
        const due = Math.floor((b.t / dur) * T.rain);
        while (b.fired < Math.min(due, T.rain)) {
          b.fired += 1;
          const mx = b.x + b.dir * WYRM.mouth.x, my = b.y + WYRM.mouth.y;
          const tx = k.x + rand(-46, 46), ty = FLOOR - 10;
          const len = Math.hypot(tx - mx, ty - my) || 1, sp = 100 + b.phase * 22;
          shoot(mx, my, ((tx - mx) / len) * sp, ((ty - my) / len) * sp);
        }
        if (b.t > dur + 0.2) { b.state = 'hover'; b.t = 0; }
        break;
      }
      case 'sweepDown':                                      // drop low, glowing, then breathe along the ground
        b.y = b.fromY + (112 - b.fromY) * Math.min(1, b.t / 0.6); face();
        if (b.t > 0.6) { b.state = 'sweep'; b.t = 0; b.fired = 0; }
        break;
      case 'sweep': {
        const due = Math.min(T.waves, Math.floor(b.t / 0.5) + 1);
        while (b.fired < due) {
          b.fired += 1;
          const mx = b.x + b.dir * (WYRM.mouth.x - 8);
          groundFlame(mx, b.dir * (125 + b.phase * 20));
        }
        if (b.t > T.waves * 0.5 + 0.4) { b.state = 'rise'; b.t = 0; b.fromY = b.y; }
        break;
      }
      case 'divePrep':                                       // climb and flare: the telegraph
        b.y = b.fromY + (24 - b.fromY) * Math.min(1, b.t / 0.4); face();
        b.tx = k.x;                                          // locks on at the last moment
        if (b.t > T.tele) { b.state = 'dive'; b.t = 0; b.sx = b.x; b.sy = b.y; b.tx = Math.max(60, Math.min(300, k.x)); }
        break;
      case 'dive': {
        const p = Math.min(1, b.t / 0.32);
        b.x = b.sx + (b.tx - b.sx) * p; b.y = b.sy + ((FLOOR - WYRM.groundOffset) - b.sy) * p * p;
        const body = box(b, WYRM.body);
        if (overlap(body, k.x - 7, k.x + 7, FLOOR - k.jy - 34, FLOOR - k.jy)) hurtKnight(b.x);
        if (p >= 1) {
          b.state = 'grounded'; b.t = 0; st.shake = 0.35;
          if (Math.abs(k.x - b.x) < 30 && k.jy < 16) hurtKnight(b.x);       // the slam itself
          if (b.phase >= 2) { groundFlame(b.x - 30, -150); groundFlame(b.x + 30, 150); }   // shockwaves
        }
        break;
      }
      case 'grounded':                                       // the opening: chest and head in reach
        b.y = (FLOOR - WYRM.groundOffset);
        if (b.t > T.down) { b.state = 'rise'; b.t = 0; b.fromY = b.y; }
        break;
      case 'rise':
        b.y = b.fromY + (54 - b.fromY) * Math.min(1, b.t / 0.6);
        if (b.t > 0.6) {
          if (b.phase === 3 && Math.random() < 0.5) nextAttack(b);   // enraged: no breathing room
          else { b.state = 'hover'; b.t = 0; }
        }
        break;
      case 'roar':                                           // summons ogres; can't be hurt
        b.y += (48 - b.y) * Math.min(1, dt * 3); face();
        if (b.t > 1.3) {
          for (let i = 0; i < b.phase; i++) spawn('ogre');
          b.state = 'hover'; b.t = 0;
        }
        break;
    }
  }

  function groundFlame(x, vx) {
    const el = document.createElement('img');
    el.className = 'pix ent fireball ground'; el.alt = '';
    el.style.width = 14 * S + 'px'; el.style.height = 14 * S + 'px';
    layer.appendChild(el);
    st.shots.push({ el, x, y: FLOOR - 7, vx, vy: 0, t: 0, ground: true });
  }

  function victory() {
    st.won = true;
    const bonus = 10000 + st.k.hp * 1000;
    st.score += bonus;
    banner(`VICTORY  +${bonus}`, 3, 'clear');
    hud();
    setTimeout(() => {
      if (st.phase !== 'play') return;
      if (qualifies(st.score)) { st.cursor = 0; showInitials(); } else { st.newRank = -1; showOver(); }
    }, 2200);
  }

  function shoot(x, y, vx, vy) {
    const el = document.createElement('img');
    el.className = 'pix ent fireball'; el.alt = '';
    el.style.width = 14 * S + 'px'; el.style.height = 14 * S + 'px';
    layer.appendChild(el);
    st.shots.push({ el, x, y, vx, vy, t: 0 });
  }

  function updateShots(dt) {
    const k = st.k;
    for (const f of st.shots) {
      if (f.dead) continue;
      f.t += dt;
      if (!f.ground) f.vy += 40 * dt;
      f.x += f.vx * dt; f.y += f.vy * dt;
      const ky0 = FLOOR - k.jy - 34, ky1 = FLOOR - k.jy;
      if (f.ground) {                                         // rolls along the floor: jump it
        if (Math.abs(f.x - k.x) < 9 && k.jy < 12) { f.dead = true; spark(f.x, f.y); hurtKnight(f.x); }
        else if (f.x < -20 || f.x > 380) f.dead = true;
        continue;
      }
      if (Math.abs(f.x - k.x) < 8 && f.y > ky0 - 4 && f.y < ky1 + 2) { f.dead = true; spark(f.x, f.y); hurtKnight(f.x); }
      else if (f.y >= FLOOR - 3) { f.dead = true; spark(f.x, FLOOR - 4); }
      else if (f.x < -20 || f.x > 380) f.dead = true;
    }
    st.shots = st.shots.filter((f) => { if (f.dead) { f.el.remove(); return false; } return true; });
  }

  /* ---------------- render ---------------- */
  function hud() {
    if (!root) return;
    heartsEl.querySelectorAll('img').forEach((h, i) => {
      const full = i < st.k.hp;
      const src = IMG.heart(full);
      if (!h.src.endsWith(src)) h.src = src;
    });
    scoreEl.querySelector('.wave').textContent = st.phase === 'ready' ? 'COURTYARD' : st.boss ? 'FINAL BATTLE' : `WAVE ${st.wave} / ${MAX_WAVES}`;
    const bb = root.querySelector('.ar-bossbar');
    bb.hidden = !st.boss;
    if (st.boss) bb.querySelector('.bar div').style.width = (st.boss.hp / WYRM.hp) * 100 + '%';
    scoreEl.querySelector('.pts').innerHTML = `SCORE ${pad(st.score)}${st.combo > 1 ? `<span class="combo">x${st.combo} COMBO</span>` : ''}`;
    const best = loadScores()[0];
    bestEl.textContent = best ? `${best.n}  ${pad(best.s)}` : '-----';
  }

  function render() {
    if (!st || !root || st.phase === 'gone') return;
    const k = st.k;
    // knight
    const R = k.facing > 0;
    let src;
    if (k.slash >= 0) src = (R ? SPRITES.slashR : SPRITES.slashL)[k.slash < SLASH_T[0] ? 0 : k.slash < SLASH_T[1] ? 1 : 2];
    else if (k.walking || k.jy > 0) src = (R ? SPRITES.walkR : SPRITES.walkL)[k.jy > 0 ? 0 : Math.floor(st.t * 8) % 4];
    else src = R ? SPRITES.idleR : SPRITES.idleL;
    if (knightImg.dataset.src !== src) { knightImg.src = src; knightImg.dataset.src = src; }
    const ax = (R ? HK_CX : HK - 1 - HK_CX) + 0.5;
    knightImg.style.transform = `translate(${Math.round(k.x) * S - ax * S}px, ${(FLOOR - Math.round(k.jy)) * S - HK * S}px)`;
    knightEl.querySelector('.shadow').style.transform = `translate(${Math.round(k.x) * S - 40}px, ${FLOOR * S - 6}px)`;
    knightImg.style.opacity = k.inv > 0 && Math.floor(k.inv * 12) % 2 ? 0.35 : 1;

    // enemies
    for (const e of st.enemies) {
      let pose;
      if (e.type === 'ogre') {
        pose = e.state === 'windup' ? 'windup' : (e.state === 'smash' || e.state === 'dying' || (e.state === 'recover' && e.t < 0.25)) ? 'smash'
          : Math.floor(e.t * 4) % 2 ? 'walk2' : 'walk1';
        if (e.state === 'stagger') pose = 'walk1';
        const ax2 = (e.dir > 0 ? OGRE.cx : OGRE.w - 1 - OGRE.cx) + 0.5;
        const sink = e.state === 'dying' ? Math.min(1, e.t / 0.6) * 10 : 0;
        e.el.style.transform = `translate(${Math.round(e.x) * S - ax2 * S}px, ${(FLOOR - OGRE.h + sink) * S}px)`;
        e.el.style.opacity = e.state === 'dying' ? 1 - Math.min(1, e.t / 0.6) : 1;
        // telegraph: the ogre glows while winding up
        e.el.classList.toggle('telegraph', e.state === 'windup');
      } else if (e.type === 'boss') {
        const breathing = e.state === 'rain' || e.state === 'sweep';
        pose = breathing ? 'breathe' : e.state === 'grounded' ? 'fly2' : ['fly1', 'fly2', 'fly3', 'fly2'][Math.floor(e.t * (e.state === 'dive' ? 14 : 7)) % 4];
        e.el.style.transform = `translate(${Math.round(e.x - WYRM.w / 2) * S}px, ${Math.round(e.y - WYRM.h / 2) * S}px)`;
        e.el.style.opacity = e.state === 'dying' ? (Math.floor(e.t * 10) % 2 ? 0.4 : 1) * (1 - Math.min(1, e.t / 2.4)) : 1;
        e.el.classList.toggle('telegraph', e.state === 'divePrep' || e.state === 'sweepDown' || e.state === 'roar');
        e.el.classList.toggle('open', e.state === 'grounded');
      } else {
        pose = e.state === 'breathe' ? 'breathe' : ['fly1', 'fly2', 'fly3', 'fly2'][Math.floor(e.t * 8) % 4];
        if (e.state === 'swoop') pose = 'fly2';
        const ax2 = (e.dir > 0 ? DRAGON.cx : DRAGON.w - 1 - DRAGON.cx);
        e.el.style.transform = `translate(${Math.round(e.x - ax2) * S}px, ${Math.round(e.y - DRAGON.cy) * S}px)`;
        e.el.style.opacity = e.state === 'dying' ? 1 - Math.min(1, e.t / 1.4) : 1;
      }
      const img = IMG[e.type](pose, e.dir);
      if (e.el.dataset.src !== img) { e.el.src = img; e.el.dataset.src = img; }
      e.el.classList.toggle('hit', e.flash > 0);
    }
    for (const f of st.shots) {
      const img = IMG.fireball(Math.floor(f.t * 10) % 2 + 1);
      if (f.el.dataset.src !== img) { f.el.src = img; f.el.dataset.src = img; }
      f.el.style.transform = `translate(${Math.round(f.x - 7) * S}px, ${Math.round(f.y - 7) * S}px)`;
    }
    // screen shake
    if (st.shake > 0 && !reduced && st.phase === 'play') root.style.transform = `translate(${Math.round(rand(-1, 1)) * S}px, ${Math.round(rand(-1, 1)) * S}px)`;
    else if (root.style.transform) root.style.transform = '';
  }

  /* ---------------- input ---------------- */
  function jump() {
    if (!st || !['ready', 'play'].includes(st.phase)) return;
    if (st.k.jy === 0) st.k.vy = JUMP_V;
  }
  function slash() {
    if (!st || !['ready', 'play'].includes(st.phase)) return;
    if (st.k.slash >= 0) return;
    st.k.slash = 0; st.k.slashHit = false;
  }
  function confirm() {
    if (!st) return;
    if (st.phase === 'ready' || st.phase === 'over') startGame();
    else if (st.phase === 'paused') act('resume');
    else if (st.phase === 'initials') confirmInitials();
  }

  // Returns true when the arena consumed the key (left/right are left to the shared key set).
  function key(e) {
    if (!st) return false;
    const k = e.key;
    if (st.phase === 'initials') {
      if (/^[a-z]$/i.test(k)) { st.initials[st.cursor] = k.toUpperCase(); st.cursor = Math.min(2, st.cursor + 1); showInitials(); }
      else if (k === 'Backspace' || k === 'ArrowLeft') { st.cursor = Math.max(0, st.cursor - 1); showInitials(); }
      else if (k === 'ArrowRight') { st.cursor = Math.min(2, st.cursor + 1); showInitials(); }
      else if (k === 'ArrowUp' || k === 'ArrowDown') {
        const c = st.initials[st.cursor].charCodeAt(0) - 65;
        st.initials[st.cursor] = String.fromCharCode(65 + ((c + (k === 'ArrowUp' ? 1 : 25)) % 26)); showInitials();
      }
      else if (k === 'Enter') confirmInitials();
      return true;
    }
    if (k === 'Escape') {
      if (st.phase === 'play') showPause();
      else leave();
      return true;
    }
    if (k === 'Enter') { confirm(); return true; }
    const l = k.toLowerCase();
    if (l === ' ' || l === 'arrowup' || l === 'w') { if (!e.repeat) jump(); return true; }
    if (l === 'x') { if (!e.repeat) slash(); return true; }
    if (l === 'e') { confirm(); return true; }
    if (l === 'm') return true;
    return false;
  }

  // Dev-only testing hook (stripped from production builds): jump to a wave, read state.
  const debug = { boss: () => { st.queue = []; st.enemies.forEach((e) => e.el.remove()); st.enemies = []; st.wave = MAX_WAVES; spawnBoss(); }, state: () => st, wave: (n) => { st.wave = n - 1; st.queue = []; st.enemies.forEach((e) => { e.el.remove(); }); st.enemies = []; nextWave(); } };
  const typing = () => !!st && st.phase === 'initials';             // letters are being typed for a high score
  return { enter, update, render, key, jump, slash, confirm, typing, debug };
}
