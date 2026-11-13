import './style.css';
import CONTENT from './content.json';
import { createArena } from './arena.js';
import { createMusic } from './music.js';

/* ---------------------------------------------------------------------------
 * Knight for Hire
 * Title screen (layered parallax intro) -> six walkable rooms.
 * All positions are in native room pixels (360x225) and drawn at 4x (1440x900).
 * ------------------------------------------------------------------------- */

const S = 4;              // room scale
const FLOOR = 196;        // native floor line
const ROOM_W = 360;
const SPEED = 80;         // native px per second
const WALK_FPS = 8;
const NEAR = 16;          // native px: how close the knight must be to interact
const EDGE_L = 14, EDGE_R = ROOM_W - 14;
const A = (p) => '/assets/' + p;

// Torch glow positions (native) from source/gen_screens.py
const TORCHES = {
  gate: [[104, 92], [256, 92]],
  treasury: [[150, 86], [210, 86], [66, 96], [294, 96]],
  library: [[160, 96], [200, 96]],
  armory: [[118, 100], [242, 100]],
  chronicle: [[121, 96], [209, 96], [303, 96], [55, 96]],
  trophy: [[121, 96], [209, 96], [303, 96], [55, 96]],
  throne: [[66, 96], [294, 96], [160, 84], [200, 84], [146, 156], [214, 156]],   // last two: the gold candelabra
};
const ROOM_NAMES = { gate: 'Gate Hall', treasury: 'Treasury', library: 'Library', armory: 'Armory', chronicle: 'Chronicle', throne: 'Throne', trophy: 'Trophy' };
const EXIT_TO = { 'GATE HALL': 'gate', 'THE TREASURY': 'treasury', TREASURY: 'treasury', LIBRARY: 'library', 'THE LIBRARY': 'library', ARMORY: 'armory', 'THE ARMORY': 'armory', 'CHRONICLE HALL': 'chronicle', 'THRONE ROOM': 'throne', COURTYARD: 'intro', ENTRANCE: 'intro', 'TROPHY ROOM': 'trophy' };
const ROOM_KEYS = Object.keys(CONTENT.rooms);

const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const hash = (x, y) => { const s = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453; return s - Math.floor(s); };
const rnd = (i, a, b) => hash(i * a, b);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const h = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; };

// Preload every sprite so frame swaps never flash.
// Room knight: the heavy side-view set from tools/knight_heavy.py. All frames are
// 60x60 native with the body centred on column HK_CX (mirrored for left-facing).
const HK = 60, HK_CX = 22;
const SPRITES = {
  idleR: A('sprites/hk_idle_right.png'),
  idleL: A('sprites/hk_idle_left.png'),
  seated: A('sprites/knight_seated_front.png'),
  walkR: [1, 2, 3, 4].map((n) => A(`sprites/hk_walk_right_${n}.png`)),
  walkL: [1, 2, 3, 4].map((n) => A(`sprites/hk_walk_left_${n}.png`)),
  slashR: [1, 2, 3].map((n) => A(`sprites/hk_slash_right_${n}.png`)),
  slashL: [1, 2, 3].map((n) => A(`sprites/hk_slash_left_${n}.png`)),
};
// Slash timing: wind-up, strike, follow-through (seconds, cumulative ends)
const SLASH_T = [0.07, 0.16, 0.28];
const SLASH_REACH = 24;   // native px in front of the knight
[SPRITES.idleR, SPRITES.idleL, SPRITES.seated, ...SPRITES.walkR, ...SPRITES.walkL, ...SPRITES.slashR, ...SPRITES.slashL,
  ...ROOM_KEYS.map((k) => A(`rooms/${k}.png`))].forEach((src) => { new Image().src = src; });

const app = document.getElementById('app');

/* ============================== INTRO ============================== */
const HSTARS = [[185, 151], [226, 159], [255, 161], [175, 167], [145, 194], [188, 194], [192, 196], [172, 197], [128, 204], [132, 207], [128, 208], [241, 209], [244, 209], [163, 211], [156, 212], [230, 212], [252, 213], [190, 214], [250, 216], [249, 217], [128, 218], [238, 218], [217, 219], [236, 219], [234, 220], [232, 221], [181, 222], [231, 222], [223, 225], [217, 232], [212, 236], [172, 247], [224, 250], [244, 253], [218, 259]];

// Tiny pixel-art SVGs from character grids (crisp at any size).
function pixelSVG(grid, pal, cls = '') {
  const w = grid[0].length, hgt = grid.length;
  let rects = '';
  grid.forEach((row, y) => [...row].forEach((c, x) => { if (pal[c]) rects += `<rect x="${x}" y="${y}" width="1" height="1" fill="${pal[c]}"/>`; }));
  return `<svg class="${cls}" viewBox="0 0 ${w} ${hgt}" shape-rendering="crispEdges" aria-hidden="true">${rects}</svg>`;
}
const SWORD = ['....................................', '.................................K..', '...............................KKWK.', '..............................KWWK..', '.............................KWfvK..', '...........................KKWfvK...', '..........................KWWfvK....', '.........................KWLfvK.....', '........................KWLfwvK.....', '.......................KWLfwvK......', '.....................KKWLfwvK.......', '....................KWLLfwvK........', '...................KWLLfwvK.........', '..................KWLLfwwK..........', '.................KWLLfwwvK..........', '................KWLLfwwvK...........', '...............KWLLfwwvK............', '..............KWLLfwwvK.............', '.............KWLLfwwvK..............', '.......K....KWLLfwwvK...............', '......KgK..KWLLfwwvK................', '.....KggGKKWLLfwwvK.................', '......KgGGWLLfwwvK..................', '.......KgGGLfwwvK...................', '........KgGGwwvK....................', '........KBgGGvK.....................', '.......KBBbgGGK.....................', '.....KKbBBKKgGGK....................', '....KGBbBK..KgggK...................', '...KGRRbK....KgK....................', '...KGRRGK.....K.....................', '....KGGK............................', '.....KK.............................', '....................................', '....................................', '....................................'];
const SWORD_PAL = { K: '#05070F', W: '#FFFFFF', L: '#DCE0EE', f: '#9AA2BC', w: '#6E7894', v: '#4A5270', G: '#E0A640', g: '#8A6020', B: '#6E4628', b: '#4A2E1C', R: '#D04A5E' };
const STAR = ['...#...', '...#...', '..#o#..', '##ooo##', '..#o#..', '...#...', '...#...'];
const STAR_PAL = { '#': '#FFD27A', o: '#FFF3C4' };

// Hairline wall cracks (native px). 'k' = crack; a faint lit edge is added to its lower right.
const CRACK_SHAPES = [
  ['...k....', '...k....', '..k.....', '..kk....', '.k..k...', '.k...k..', 'k.....k.', 'k.......'],
  ['k.......', '.kk.....', '...k....', '...kkk..', '..k...k.', '..k....k', '.k......', '........'],
  ['....k...', '...k....', '...k.k..', '..k...k.', '..k.....', '.k......', '.k......', 'k.......'],
  // 3: a big one, branching
  ['......k.......', '......k.......', '.....k........', '.....kk.......', '....k..k......', '....k...kk....', '...k......k...', '...k.......k..', '..kk.......k..', '..k.k.......k.', '.k...........k', '.k............', 'k.............', 'k.............'],
  // 4: a hairline nick
  ['..k..', '.k...', '.kk..', 'k..k.', '.....'],
].map((g) => g.map((row, y) => [...row].map((c, x) => (c === 'k' ? 'k' : (g[y - 1]?.[x - 1] === 'k' ? 'h' : '.'))).join('')));
const CRACK_PAL = { k: '#05070F', h: 'rgba(120,136,190,.32)' };
// [x, y, shape, mirrored] per room: at most three, on bare wall only
const CRACKS = {
  chronicle: [[100, 150, 3, 0], [172, 166, 4, 1], [282, 150, 2, 0]],
  library: [[60, 62, 2, 1], [120, 40, 4, 0], [266, 66, 3, 0]],
  treasury: [[68, 164, 3, 0], [132, 30, 4, 0], [284, 170, 0, 1]],
  armory: [[62, 98, 4, 1], [178, 118, 2, 0], [292, 96, 1, 1]],
  trophy: [[14, 66, 3, 0], [108, 160, 4, 0], [246, 164, 1, 1]],
  throne: [[60, 58, 3, 0], [284, 140, 4, 1]],
  gate: [[62, 106, 3, 1], [176, 38, 4, 0], [270, 120, 0, 0]],
};

// The maximalist title: giant extruded gold KNIGHT, a crimson FOR HIRE ribbon, swords, rays, sparkles.
function titleBlock() {
  const word = [...'KNIGHT'].map((ch, i) => `<span class="ltr" style="animation-delay:-${(i * 0.18).toFixed(2)}s"><span class="ext">${ch}</span><span class="fill" style="animation-delay:-${(i * 0.12).toFixed(2)}s">${ch}</span></span>`).join('');
  const sparkles = [[4, 18, 5], [12, 62, 3], [22, 6, 4], [78, 4, 4], [90, 52, 5], [96, 16, 3], [70, 70, 3], [30, 74, 4], [50, -6, 3], [86, 84, 3]]
    .map(([x, y, sz], i) => `<span class="spark-star" style="left:${x}%;top:${y}%;width:${sz * 7}px;height:${sz * 7}px;animation-delay:-${(i * 0.37).toFixed(2)}s">${pixelSVG(STAR, STAR_PAL)}</span>`).join('');
  return `
    <div class="title-max">
      <div class="rays" aria-hidden="true"></div>
      <div class="px kicker-plaque"><span class="gem"></span>SAIHRITESH'S PORTFOLIO<span class="gem"></span></div>
      <h1 class="px t-max" aria-label="Knight for Hire">
        <span class="t-word" aria-hidden="true">${word}</span>
        <span class="ribbon-wrap" aria-hidden="true">
          <span class="sword l">${pixelSVG(SWORD, SWORD_PAL)}</span>
          <span class="ribbon"><span class="ribbon-text">FOR HIRE</span></span>
          <span class="sword r">${pixelSVG(SWORD, SWORD_PAL)}</span>
        </span>
      </h1>
      ${sparkles}
    </div>`;
}

function buildIntro() {
  const stars = HSTARS.map((p, i) =>
    `<div class="twinkle" style="left:${(p[0] + 180) * 3}px;top:${p[1] * 3}px;animation-delay:-${(rnd(i, 3.3, 5) * 3).toFixed(2)}s"></div>`).join('');
  let flies = '';
  for (let i = 0; i < 14; i++) {
    const r = rnd(i, 6.0, 2);
    flies += `<div class="firefly" style="left:${Math.round(620 + i * 52 + r * 30)}px;top:${Math.round(600 + rnd(i, 4.2, 9) * 330)}px;animation-delay:-${(r * 7).toFixed(2)}s;animation-duration:${(6 + r * 4).toFixed(1)}s"></div>`;
  }
  const el = h(`
    <section id="intro" aria-label="Title screen">
      <div class="layer" data-f="-4"><div class="stage2">
        <div class="lyr l-sky" role="img" aria-label="Pixel art: a spired castle beneath a giant tree on a moonlit night"></div>
        <div class="moon-halo"></div>
        ${stars}
      </div></div>
      <div class="layer" data-f="-14"><div class="stage2">
        <div class="lyr l-fg"></div>
        <div class="lyr l-win"></div>
      </div></div>
      <div class="fog" style="bottom:15%;height:12%;background:linear-gradient(transparent,rgba(140,150,220,.12) 50%,transparent)"></div>
      <div class="fog" style="bottom:2%;height:10%;background:linear-gradient(transparent,rgba(140,150,220,.1) 50%,transparent);animation-duration:28s"></div>
      <div class="layer" data-f="-30"><div class="stage2">
        <div class="hero-knight">
          <div class="shadow"></div>
          <div style="position:relative;animation:breathe 2.4s steps(2) infinite">
            <div class="blade"></div>
            <img class="pix" src="${SPRITES.idleR}" alt="The knight, sword raised">
          </div>
        </div>
        ${flies}
      </div></div>
      <div class="intro-shade"></div>
      <div class="intro-ui">
        ${titleBlock()}
        <div class="tagline">Saihritesh of PES University: AI/ML engineer, sworn to ship what he builds.</div>
        <button type="button" class="btn blink" id="start">&gt; PRESS START</button>
      </div>
    </section>`);
  app.appendChild(el);

  const fit = () => {
    const sc = window.innerHeight / 972;
    el.querySelectorAll('.stage2').forEach((s) => { s.style.transform = `scale(${sc.toFixed(4)})`; });
  };
  fit();
  window.addEventListener('resize', fit);

  const layers = [...el.querySelectorAll('.layer')];
  let lx = 0, ly = 0;
  el.addEventListener('mousemove', (e) => {
    if (reduced) return;
    const nx = (e.clientX / window.innerWidth) * 2 - 1;
    const ny = (e.clientY / window.innerHeight) * 2 - 1;
    if (Math.abs(nx - lx) < 0.04 && Math.abs(ny - ly) < 0.04) return;
    lx = nx; ly = ny;
    layers.forEach((l) => { const f = +l.dataset.f; l.style.transform = `translate(${Math.round(nx * f)}px,${Math.round(ny * f * 0.4)}px)`; });
  });

  el.querySelector('#start').addEventListener('click', () => enterCastle());
  return el;
}

let intro = null;
let mode = 'intro';

function enterCastle(room = 'chronicle', side = 'left') {   // the castle tour starts in the Chronicle Hall
  if (mode === 'game') return;
  mode = 'game';
  game.root.hidden = false;
  loadRoom(room, side);
  if (intro) {
    intro.classList.add('leaving');
    setTimeout(() => { intro.hidden = true; intro.classList.remove('leaving'); }, reduced ? 0 : 500);
  }
  game.root.focus();
}

function backToIntro() {
  mode = 'intro';
  syncMusic();
  intro.hidden = false;
  game.root.hidden = true;
  history.replaceState(null, '', location.pathname);
  intro.querySelector('#start').focus();
}

/* ============================== GAME ============================== */
const game = {
  root: null, view: null, room: null,
  key: null, x: 60, jy: 0, vy: 0, facing: 1, walking: false, t: 0,
  slash: -1, slashHit: false, // seconds into the current slash, -1 when not slashing
  target: null,           // { x, then: fn } for click-to-walk
  popup: null, popupObj: -1, seated: false, saved: false,
  nearIdx: -1, mapOpen: false, busy: false,
  gateClosed: localStorage.getItem('coc-gate') !== 'open',   // sealed until the lever is struck
  keys: new Set(),
  visited: new Set(JSON.parse(localStorage.getItem('coc-visited') || '[]')),
};

function buildGame() {
  const root = h(`
    <main id="game" tabindex="-1" hidden>
      <div class="viewport">
        <div class="room"></div>
        <div class="hud-status">
          <div class="portrait" aria-hidden="true"></div>
          <div style="display:flex;flex-direction:column;gap:6px">
            <span class="px name">KNIGHT SAIHRITESH</span>
            <div class="hp"><span class="px">HP</span><div class="bar"><div></div></div></div>
          </div>
        </div>
        <div class="plaque"><div class="px title"></div><span class="px sub"></span></div>
        <button type="button" class="minimap" aria-label="Open castle map">
          <span class="px">MAP · M</span>
          <div class="grid">${CONTENT.map.map((m) => `<div class="cell ${m.room === 'throne' ? 'throne' : ''}" data-room="${m.room}" style="grid-column:${m.grid_column};grid-row:${m.grid_row}"></div>`).join('')}</div>
        </button>
        <div class="px controls"><span><b>◄ ►</b> MOVE</span><span><b>SPACE</b> JUMP</span><span><b>X</b> SLASH</span><span><b>E</b> INTERACT</span><span><b>M</b> MAP</span><span><b>N</b> MUSIC</span></div>
        <div class="fader"></div>
      </div>
      <div class="touch" aria-hidden="true">
        <div class="grp"><button class="btn btn-dark" data-k="left">◄</button><button class="btn btn-dark" data-k="right">►</button></div>
        <div class="grp"><button class="btn btn-dark" data-k="jump">▲</button><button class="btn btn-dark" data-k="slash">X</button><button class="btn" data-k="act">E</button></div>
      </div>
    </main>`);
  app.appendChild(root);
  game.root = root;
  game.view = root.querySelector('.viewport');
  game.roomEl = root.querySelector('.room');
  game.fader = root.querySelector('.fader');

  const fit = () => {
    const s = Math.min(window.innerWidth / 1440, window.innerHeight / 900);
    game.view.style.transform = `scale(${s})`;
  };
  fit();
  window.addEventListener('resize', fit);

  root.querySelector('.minimap').addEventListener('click', () => toggleMap(true));

  // Touch buttons
  root.querySelectorAll('.touch button').forEach((b) => {
    const k = b.dataset.k;
    const down = (e) => {
      e.preventDefault();
      if (k === 'left' || k === 'right') game.keys.add(k);
      else if (k === 'jump') jump();
      else if (k === 'act') interact();
      else if (k === 'slash') slash();
    };
    const up = () => game.keys.delete(k);
    b.addEventListener('pointerdown', down);
    b.addEventListener('pointerup', up);
    b.addEventListener('pointerleave', up);
    b.addEventListener('pointercancel', up);
  });
}

/* ---------- room building ---------- */
function loadRoom(key, side) {
  const R = CONTENT.rooms[key];
  game.key = key;
  syncMusic();
  game.visited.add(key);
  localStorage.setItem('coc-visited', JSON.stringify([...game.visited]));
  history.replaceState(null, '', '#' + key);
  closePopup(true);
  game.target = null;
  game.seated = false;
  game.saved = false;
  game.jy = 0; game.vy = 0;
  game.slash = -1;
  game.x = side === 'right' ? EDGE_R - 26 : side === 'center' ? 180 : EDGE_L + 26;
  game.facing = side === 'right' ? -1 : 1;

  const torches = TORCHES[key].map((t, i) =>
    `<div class="torch" style="left:${t[0] * S - 70}px;top:${(t[1] - 5) * S - 70}px;animation-delay:-${(i * 0.23).toFixed(2)}s"></div>` +
    // embers: a few 1-px sparks drifting up from each flame
    [0, 1, 2, 3, 4].map((k) => {
      const dx = Math.round((hash(i * 7 + k, 11) - 0.5) * 6);
      const dur = (1.6 + hash(i * 7 + k, 12) * 1.4).toFixed(2);
      const del = (hash(i * 7 + k, 13) * 3).toFixed(2);
      const drift = Math.round((hash(i * 7 + k, 14) - 0.5) * 10) * S;
      return `<div class="ember${k % 3 === 0 ? ' hot' : ''}" style="left:${(t[0] + dx) * S}px;top:${(t[1] - 8) * S}px;--drift:${drift}px;animation-duration:${dur}s;animation-delay:-${del}s"></div>`;
    }).join('')).join('');
  let motes = '';
  for (let i = 0; i < 14; i++) motes += `<div class="mote" style="left:${Math.round(120 + hash(i, 1) * 1200)}px;top:${Math.round(300 + hash(i, 2) * 440)}px;animation-delay:-${(hash(i, 3) * 9).toFixed(2)}s"></div>`;
  const tapestries = (R.tapestries || []).map((t) => {
    const bg = t.tag === 'DONE' ? '#8FBF8A' : t.tag === 'ACTIVE' ? '#E8A45A' : '#6F8FC0';
    return `<div class="tapestry" style="left:${t.x * S + 26}px;top:${49 * S + 40}px;width:${52 * S - 52}px">
      <span class="px tag" style="background:${bg}">${esc(t.tag)}</span>
      <span class="px t">${esc(t.title)}</span><span class="px w">${esc(t.when)}</span></div>`;
  }).join('');
  const objects = R.objects.map((o, i) => {
    const has = !!o.sprite;
    return `<button type="button" class="hit" data-i="${i}" aria-label="${esc(o.verb + ' ' + o.label)}"
        style="left:${o.x_native * S - 60}px;top:${o.y_native * S - 20}px;width:120px;height:${has ? 110 : 140}px">
      ${has ? `<span class="relic-halo"></span><span class="relic"><img class="pix" src="${A('sprites/' + o.sprite + '.png')}" alt=""></span>` : ''}
      <span class="lbl px">${esc(o.label)}</span></button>`;
  }).join('');
  const exits = ['left', 'right'].filter((s) => R.exits[s]).map((s) =>
    `<button type="button" class="px exit ${s}" data-side="${s}">${s === 'left' ? '◄ ' : ''}${esc(R.exits[s])}${s === 'right' ? ' ►' : ''}</button>`).join('');

  game.roomEl.innerHTML = `
    <div class="art" role="img" aria-label="Pixel art: ${esc(R.title.toLowerCase())}" style="background-image:url(${A('rooms/' + key + '.png')})${key === 'chronicle' ? ';left:-1px' : ''}"></div>
    ${(CRACKS[key] || []).map(([x, y, sh, m]) => `<div class="crack" style="left:${x * S}px;top:${y * S}px;width:${CRACK_SHAPES[sh][0].length * S}px;height:${CRACK_SHAPES[sh].length * S}px${m ? ';transform:scaleX(-1)' : ''}">${pixelSVG(CRACK_SHAPES[sh], CRACK_PAL)}</div>`).join('')}
    ${key === 'gate' ? gateHtml() : ''}${torches}${motes}${tapestries}${objects}${exits}
    <div class="seated" hidden><img class="pix" src="${SPRITES.seated}" alt="The knight seated on the throne"></div>
    <div class="knight"><div class="shadow"></div><div class="body idle"><img class="pix" alt="The knight"></div></div>
    <div class="prompt" hidden><div><span class="px box"><span class="key">E</span><span class="txt"></span></span></div></div>`;

  game.knightEl = game.roomEl.querySelector('.knight');
  game.bodyEl = game.knightEl.querySelector('.body');
  game.imgEl = game.bodyEl.querySelector('img');
  game.seatEl = game.roomEl.querySelector('.seated');
  game.promptEl = game.roomEl.querySelector('.prompt');
  game.hitEls = [...game.roomEl.querySelectorAll('.hit')];
  game.lastSrc = null;
  game.nearIdx = -1;

  game.hitEls.forEach((b) => b.addEventListener('click', () => {
    const i = +b.dataset.i;
    const o = R.objects[i];
    walkTo(o.x_native, () => openPopup(i));
  }));
  game.roomEl.querySelectorAll('.exit').forEach((b) => b.addEventListener('click', () => {
    const s = b.dataset.side;
    walkTo(s === 'left' ? -50 : ROOM_W + 50, null);
  }));

  game.root.querySelector('.plaque .title').textContent = R.title;
  game.root.querySelector('.plaque .sub').textContent = R.section;
  game.root.querySelectorAll('.minimap .cell').forEach((c) => {
    c.classList.toggle('seen', game.visited.has(c.dataset.room));
    c.classList.toggle('here', c.dataset.room === key);
  });
  render();
}

// Gate Hall lever + portcullis (art: tools/lever_art.py). The whole portcullis drops from the arch slot; 22 rows stay visible when raised.
function gateHtml() {
  const c = game.gateClosed;
  return `<div class="portcullis${c ? ' closed' : ''}" style="left:${138 * S}px;top:${74 * S}px;width:${84 * S}px;height:${122 * S}px"><img class="pix" src="${A('sprites/portcullis.png')}" alt=""></div>
    <img class="pix lever" src="${A('sprites/lever_' + (c ? 'down' : 'up') + '.png')}" alt="" style="left:${90 * S}px;top:${150 * S}px;width:${17 * S}px;height:${26 * S}px">`;
}

const LEVER_X = 96;   // the lever's pivot (native px); its interact point sits to the right so the knight doesn't cover it

function toggleGate() {
  game.gateClosed = !game.gateClosed;
  localStorage.setItem('coc-gate', game.gateClosed ? 'closed' : 'open');
  game.roomEl.querySelector('.portcullis')?.classList.toggle('closed', game.gateClosed);
  const lever = game.roomEl.querySelector('.lever');
  if (lever) lever.src = A('sprites/lever_' + (game.gateClosed ? 'down' : 'up') + '.png');
}

function gateToast(msg) {
  game.roomEl.querySelector('.gate-toast')?.remove();
  const t = h(`<div class="px gate-toast">${esc(msg)}</div>`);
  game.roomEl.appendChild(t);
  setTimeout(() => t.remove(), 2400);
}

function travel(dest, side) {
  if (game.busy) return;
  if (dest === 'courtyard' && game.gateClosed && mode === 'game') {
    closePopup(true);
    history.replaceState(null, '', '#' + game.key);
    gateToast('THE GATE IS SEALED. STRIKE THE LEVER.');
    return;
  }
  if (dest === 'intro') { backToIntro(); return; }
  if (!CONTENT.rooms[dest] && dest !== 'courtyard') return;
  game.busy = true;
  toggleMap(false);
  game.keys.clear();
  game.fader.className = 'fader on';
  setTimeout(() => {
    if (dest === 'courtyard') enterArena();
    else { leaveArena(); loadRoom(dest, side); }
    game.fader.className = 'fader off';
    game.busy = false;
  }, reduced ? 0 : 300);
}

// Leaving through a door: arrive at the door that leads back where we came from.
function exitThrough(side) {
  const R = CONTENT.rooms[game.key];
  const dest = EXIT_TO[R.exits[side]];
  if (!dest) return;
  if (dest === 'intro' || dest === 'courtyard') { travel(dest); return; }
  const back = CONTENT.rooms[dest].exits;
  const from = Object.entries(EXIT_TO).filter(([, v]) => v === game.key).map(([k]) => k);
  let arrive = from.includes(back.left) ? 'left' : from.includes(back.right) ? 'right' : (side === 'left' ? 'right' : 'left');
  travel(dest, arrive);
}

/* ---------- the Courtyard Siege mini-game (src/arena.js) ---------- */
let arena = null;
function enterArena() {
  closePopup(true);
  game.inArena = true;
  game.key = 'courtyard';
  game.knightEl = null;
  game.view.classList.add('arena-on');
  history.replaceState(null, '', '#courtyard');
  arena.enter(game.roomEl);
  syncMusic();
}
function leaveArena() {
  if (!game.inArena) return;
  game.inArena = false;
  game.view.classList.remove('arena-on');
}

function walkTo(x, then) {
  if (game.popup) closePopup();
  game.target = { x, then };
}

/* ---------- music (src/music.js): one theme per area, crossfading as you move ---------- */
const music = createMusic();
const ROOM_MUSIC = { throne: 'court', gate: 'court' };                   // every other room: 'castle'
let musicOn = localStorage.getItem('coc-music') !== 'off';
let audioUnlocked = false;                                                  // browsers only allow sound after a click or key press
function musicWanted() {
  if (mode === 'intro') return 'title';
  if (game.inArena) return 'nightRide';
  return ROOM_MUSIC[game.key] || 'castle';
}
function syncMusic() {
  if (musicOn && audioUnlocked) music.play(musicWanted());
  else music.stop();
  const b = document.getElementById('music-toggle');
  if (b) { b.textContent = musicOn ? '♪ ON' : '♪ OFF'; b.setAttribute('aria-pressed', String(musicOn)); b.classList.toggle('off', !musicOn); }
}
function toggleMusic() {
  musicOn = !musicOn;
  localStorage.setItem('coc-music', musicOn ? 'on' : 'off');
  audioUnlocked = true;
  syncMusic();
}
function unlockAudio() {
  if (audioUnlocked) return;
  audioUnlocked = true;
  syncMusic();
}
for (const ev of ['pointerdown', 'keydown', 'touchstart']) window.addEventListener(ev, unlockAudio, { capture: true, passive: true });
document.addEventListener('visibilitychange', () => { if (document.hidden) music.suspend(); else if (musicOn) music.resume(); });
{
  const b = h(`<button type="button" id="music-toggle" class="px music-toggle" aria-label="Music" aria-pressed="true">♪ ON</button>`);
  b.addEventListener('click', (e) => { e.stopPropagation(); toggleMusic(); b.blur(); });
  document.body.appendChild(b);
}

/* ---------- input ---------- */
const typing = () => { const a = document.activeElement; return a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA'); };

window.addEventListener('keydown', (e) => {
  const typingField = /^(INPUT|TEXTAREA)$/.test(document.activeElement?.tagName || '');
  if ((e.key === 'n' || e.key === 'N') && !typingField && !(game.inArena && arena.typing()) && !e.metaKey && !e.ctrlKey) {
    toggleMusic(); return;
  }
  if (mode === 'intro') {
    if (['Enter', ' ', 'ArrowDown', 'PageDown'].includes(e.key) && document.activeElement?.id !== 'start') { e.preventDefault(); enterCastle(); }
    return;
  }
  if (game.inArena) {
    if (game.busy) return;
    if (arena.key(e)) { e.preventDefault(); return; }
  }
  if (e.key === 'Escape') {
    if (game.mapOpen) toggleMap(false);
    else if (game.popup) closePopup();
    return;
  }
  if (typing()) return;
  const k = e.key.toLowerCase();
  if (k === 'arrowleft' || k === 'a') { game.keys.add('left'); game.target = null; e.preventDefault(); }
  else if (k === 'arrowright' || k === 'd') { game.keys.add('right'); game.target = null; e.preventDefault(); }
  else if (k === ' ' || k === 'arrowup' || k === 'w') {
    if (e.key === ' ' && document.activeElement?.matches('button, a')) return;
    e.preventDefault(); jump();
  }
  else if (k === 'e') { e.preventDefault(); interact(); }
  else if (k === 'x') { e.preventDefault(); if (!e.repeat) slash(); }
  else if (k === 'm') { e.preventDefault(); toggleMap(!game.mapOpen); }
});
window.addEventListener('keyup', (e) => {
  const k = e.key.toLowerCase();
  if (k === 'arrowleft' || k === 'a') game.keys.delete('left');
  if (k === 'arrowright' || k === 'd') game.keys.delete('right');
});
window.addEventListener('blur', () => game.keys.clear());

function jump() {
  if (game.inArena) { arena.jump(); return; }
  if (game.popup || game.mapOpen || game.seated) return;
  if (game.jy === 0) game.vy = 150;
}

function slash() {
  if (game.inArena) { arena.slash(); return; }
  if (game.popup || game.mapOpen || game.seated || game.busy) return;
  if (game.slash >= 0) return;
  game.slash = 0;
  game.slashHit = false;
  game.target = null;
}

// On the strike frame: anything within reach in front of the knight reacts.
function slashStrike() {
  const objs = CONTENT.rooms[game.key].objects;
  objs.forEach((o, i) => {
    if (o.action === 'gate') {             // the lever only answers to the sword
      if (i !== game.nearIdx || (LEVER_X < game.x ? -1 : 1) !== game.facing) return;
      toggleGate();
      const spark = h(`<div class="spark" style="left:${(LEVER_X + 3) * S}px;top:${158 * S}px"></div>`);
      game.roomEl.appendChild(spark);
      setTimeout(() => spark.remove(), 400);
      return;
    }
    const d = (o.x_native - game.x) * game.facing;
    if (d < -6 || d > SLASH_REACH) return;
    const el = game.hitEls[i];
    el.classList.remove('struck');
    void el.offsetWidth;            // restart the shake animation
    el.classList.add('struck');
    const spark = h(`<div class="spark" style="left:${o.x_native * S}px;top:${(o.sprite ? o.y_native * S + 30 : Math.max(o.y_native * S, (FLOOR - 26) * S))}px"></div>`);
    game.roomEl.appendChild(spark);
    setTimeout(() => spark.remove(), 400);
  });
}

function interact() {
  if (game.inArena) { arena.confirm(); return; }
  if (game.mapOpen) return;
  if (game.popup) { closePopup(); return; }
  if (game.nearIdx >= 0 && CONTENT.rooms[game.key].objects[game.nearIdx].action !== 'gate') openPopup(game.nearIdx);
}

/* ---------- pop-up ---------- */
function linkHtml([text, href], i) {
  const cls = i === 0 ? 'btn' : 'btn btn-dark';
  if (href === '#courtyard' && game.gateClosed) return `<span class="${cls} btn-off" title="Strike the lever to open the gate">GATE SEALED</span>`;
  if (/^\[.*\]$/.test(href)) return `<span class="${cls} btn-off" title="Coming soon">${esc(text)}</span>`;
  if (href.startsWith('#')) return `<a class="${cls}" href="${esc(href)}" data-internal="${esc(href.slice(1))}">${esc(text)}</a>`;
  const ext = href.startsWith('http') || href.endsWith('.pdf') ? ' target="_blank" rel="noopener"' : '';
  return `<a class="${cls}" href="${esc(href)}"${ext}>${esc(text)}</a>`;
}

// The resume lives at person.links.resume (drop the PDF in public/resume.pdf). Shows the PDF inline if it exists.
async function loadResume(box) {
  const url = CONTENT.person.links.resume;
  let ok = false;
  try {
    const r = await fetch(url, { method: 'HEAD' });
    ok = r.ok && (r.headers.get('content-type') || '').includes('pdf');
  } catch { ok = false; }
  if (!box.isConnected) return;
  box.innerHTML = ok
    ? `<iframe class="resume-frame" src="${esc(url)}#view=FitH&toolbar=0&navpanes=0" title="Resume of ${esc(CONTENT.person.name)}"></iframe>
       <div class="links"><a class="btn" href="${esc(url)}" target="_blank" rel="noopener">OPEN FULL SCROLL</a><a class="btn btn-dark" href="${esc(url)}" download>DOWNLOAD</a></div>`
    : `<p>The scroll is still being inked. Check back soon.</p>`;
}

// Email helpers: a prefilled mailto link, plus a copy button for people without a mail app.
function mailtoLink(m = {}) {
  return `mailto:${CONTENT.person.links.email}?subject=${encodeURIComponent(m.subject || '')}&body=${encodeURIComponent(m.body || '')}`;
}
function copyBtn() { return `<button type="button" class="btn btn-dark copy-mail">COPY EMAIL</button>`; }

function openPopup(i) {
  const o = CONTENT.rooms[game.key].objects[i];
  if (o.action === 'gate') { game.facing = LEVER_X < game.x ? -1 : 1; slash(); return; }   // click/tap: walk over and swing
  const p = o.popup;
  closePopup(true);
  game.target = null;
  game.keys.clear();
  game.popupObj = i;
  // face the object
  if (Math.abs(o.x_native - game.x) > 2) game.facing = o.x_native > game.x ? 1 : -1;
  if (game.key === 'throne' && o.has_contact_form) game.seated = true;

  const form = o.has_contact_form ? (game.saved === 'sent'
    ? `<div class="saved" style="display:flex;flex-direction:column;gap:6px"><span class="px">RAVEN SENT</span><span style="font-size:22px">Your message has reached the throne. Expect a raven back soon.</span></div>`
    : game.saved === 'failed'
    ? `<div class="saved" style="display:flex;flex-direction:column;gap:6px"><span class="px" style="color:#E88A7A">THE RAVEN WAS LOST</span><span style="font-size:22px">The message couldn't be delivered. Send it from your own mail instead; it's filled in for you.</span>
        ${game.mailErr ? `<span style="font-size:18px;color:#A9B4D6">Relay said: ${esc(game.mailErr)}</span>` : ''}
        <div class="links"><a class="btn" href="${esc(mailtoLink(game.lastMail))}">EMAIL INSTEAD</a>${copyBtn()}</div></div>`
    : `<form novalidate>
        <div class="direct-mail"><span>Write directly to <b>${esc(CONTENT.person.links.email)}</b></span>${copyBtn()}</div>
        <label>NAME<input class="field" type="text" name="name" required autocomplete="name"></label>
        <label>EMAIL<input class="field" type="email" name="email" required autocomplete="email"></label>
        <label>MESSAGE<textarea class="field" name="msg" rows="2" required></textarea></label>
        <input type="text" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true" class="honey">
        <span class="err" style="font-size:20px;color:#E88A7A" hidden></span>
        <button type="submit" class="btn" style="align-self:flex-start">SEND RAVEN</button>
      </form>`) : '';

  const el = h(`
    <div class="frame popup${p.embed ? ' wide' : ''}" role="dialog" aria-modal="false" aria-labelledby="pop-title" style="${p.embed ? '' : `left:${o.x_native < 180 ? 760 : 140}px`}">
      <div class="head"><span class="px tag">${esc(p.tag)}</span>
        <button type="button" class="btn btn-dark close" aria-label="Close">ESC ✕</button></div>
      <div class="px ttl" id="pop-title">${esc(p.title)}</div>
      <div class="sub">${esc(p.sub)}</div>
      ${p.body.map((b) => `<p>${esc(b)}</p>`).join('')}
      ${p.bullets.length ? `<ul>${p.bullets.map((b) => `<li>${esc(b)}</li>`).join('')}</ul>` : ''}
      ${p.chips.length ? `<div class="chips">${p.chips.map((c) => `<span class="chip">${esc(c)}</span>`).join('')}</div>` : ''}
      ${form}
      ${p.embed === 'resume' ? `<div class="resume-view"><span class="px resume-wait">UNROLLING THE SCROLL...</span></div>` : ''}
      ${p.links.length ? `<div class="links">${p.links.map(linkHtml).join('')}</div>` : ''}
    </div>`);
  if (p.embed) {
    // documents render outside the scaled pixel-art stage so they stay sharp at the screen's real resolution
    const host = h(`<div class="doc-modal"></div>`);
    host.appendChild(el);
    host.addEventListener('click', (e) => { if (e.target === host) closePopup(); });
    document.body.appendChild(host);
    game.popup = host;
    el.querySelector('.close').focus({ preventScroll: true });
  } else {
    game.roomEl.appendChild(el);
    game.popup = el;
  }
  if (p.embed === 'resume') loadResume(el.querySelector('.resume-view'));

  el.querySelector('.close').addEventListener('click', () => closePopup());
  el.querySelectorAll('[data-internal]').forEach((a) => a.addEventListener('click', (e) => {
    e.preventDefault();
    const dest = a.dataset.internal;
    if (CONTENT.rooms[dest] || dest === 'courtyard') travel(dest, 'center');
  }));
  el.querySelectorAll('.copy-mail').forEach((b) => b.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(CONTENT.person.links.email); b.textContent = 'COPIED!'; }
    catch { b.textContent = CONTENT.person.links.email; }
    setTimeout(() => { b.textContent = 'COPY EMAIL'; }, 1800);
  }));
  const f = el.querySelector('form');
  if (f) f.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (f.dataset.busy) return;
    const d = Object.fromEntries(new FormData(f));
    const err = f.querySelector('.err');
    if (!d.name.trim() || !d.msg.trim() || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email)) {
      err.textContent = 'The scribe needs a name, a valid email and a message.';
      err.hidden = false;
      return;
    }
    const subject = `Audience request from ${d.name}`;
    const body = `${d.msg}\n\n${d.name}\n${d.email}`;
    game.lastMail = { subject, body };
    if (d._honey) { game.saved = 'sent'; openPopup(i); return; }        // a bot filled the hidden field: pretend it worked
    // deliver straight to the inbox through the form relay (content.json: person.contact_endpoint)
    const btn = f.querySelector('button[type=submit]');
    f.dataset.busy = '1'; btn.textContent = 'SENDING RAVEN...'; err.hidden = true;
    try {
      const r = await fetch(CONTENT.person.contact_endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ name: d.name, email: d.email, message: d.msg, _subject: subject, _replyto: d.email, _template: 'table', _captcha: 'false' }),
      });
      const j = await r.json().catch(() => ({}));
      game.saved = r.ok && String(j.success) !== 'false' ? 'sent' : 'failed';
      game.mailErr = game.saved === 'failed' ? (j.message || `The relay answered ${r.status}.`) : '';
    } catch (ex) { game.saved = 'failed'; game.mailErr = 'Could not reach the relay (network or blocker).'; }
    if (game.popupObj === i) openPopup(i);
  });
  // the siege button gets focus, so E then ENTER takes you straight out to fight
  (el.querySelector('[data-internal="courtyard"]') || el.querySelector('.close')).focus({ preventScroll: true });
  render();
}

function closePopup(silent) {
  if (!game.popup) return;
  game.popup.remove();
  game.popup = null;
  game.popupObj = -1;
  if (game.seated) { game.seated = false; }
  if (!silent) { game.root.focus({ preventScroll: true }); render(); }
}

/* ---------- map overlay ---------- */
function toggleMap(on) {
  if (on === game.mapOpen) return;
  game.mapOpen = on;
  game.keys.clear();
  const old = game.view.querySelector('.mapov');
  if (old) old.remove();
  if (!on) { game.root.focus({ preventScroll: true }); return; }
  const pct = Math.round((game.visited.size / ROOM_KEYS.length) * 100);
  const el = h(`
    <div class="mapov" role="dialog" aria-label="Castle map">
      <div class="frame panel">
        <div class="row"><h2 class="px">CASTLE MAP</h2><span class="px pct">EXPLORED ${pct}%</span>
          <button type="button" class="btn btn-dark close" style="min-height:36px;padding:0 10px;font-size:9px">ESC ✕</button></div>
        <div class="frame grid">
          ${CONTENT.map.map((m) => {
            const seen = game.visited.has(m.room), here = m.room === game.key;
            const cls = here ? 'here' : !seen ? 'unseen' : m.room === 'throne' ? 'throne' : '';
            return `<button type="button" class="map-room ${cls}" data-room="${m.room}" style="grid-column:${m.grid_column};grid-row:${m.grid_row}" aria-label="Travel to ${seen ? ROOM_NAMES[m.room] : 'unexplored room'}">
              <span>${seen ? ROOM_NAMES[m.room] : '???'}</span>
              ${here ? `<img class="you" src="${SPRITES.idleR}" alt="">` : ''}</button>`;
          }).join('')}
        </div>
        <div class="hint">Click a room to travel there. Unexplored rooms show as ???.</div>
      </div>
    </div>`);
  game.view.appendChild(el);
  el.addEventListener('click', (e) => { if (e.target === el) toggleMap(false); });
  el.querySelector('.close').addEventListener('click', () => toggleMap(false));
  el.querySelectorAll('.map-room').forEach((b) => b.addEventListener('click', () => {
    if (b.dataset.room === game.key) toggleMap(false);
    else travel(b.dataset.room, 'center');
  }));
  el.querySelector('.map-room.here')?.focus({ preventScroll: true });
}

/* ---------- loop ---------- */
function update(dt) {
  if (mode !== 'game' || game.busy) return;
  if (game.inArena) { arena.update(dt); return; }
  game.t += dt;
  const frozen = game.popup || game.mapOpen;
  if (game.slash >= 0) {
    game.slash += dt;
    if (!game.slashHit && game.slash >= SLASH_T[0]) { game.slashHit = true; slashStrike(); }
    if (game.slash >= SLASH_T[2]) game.slash = -1;
  }
  const rooted = game.slash >= 0 && game.jy === 0;   // planted feet while slashing on the ground
  let dir = 0;
  if (!frozen && !rooted) {
    if (game.keys.has('left')) dir -= 1;
    if (game.keys.has('right')) dir += 1;
    if (!dir && game.target) {
      const dx = game.target.x - game.x;
      if (Math.abs(dx) <= 1.5) {
        game.x = Math.max(EDGE_L, Math.min(EDGE_R, game.target.x));
        const then = game.target.then; game.target = null;
        if (then) then();
      } else dir = Math.sign(dx);
    }
  }
  game.walking = dir !== 0;
  if (dir) {
    game.facing = dir;
    game.x += dir * SPEED * dt;
    if (game.x < EDGE_L) { game.x = EDGE_L; if (CONTENT.rooms[game.key].exits.left) { exitThrough('left'); return; } }
    if (game.x > EDGE_R) { game.x = EDGE_R; if (CONTENT.rooms[game.key].exits.right) { exitThrough('right'); return; } }
  }
  if (game.vy || game.jy > 0) {
    game.jy += game.vy * dt;
    game.vy -= 600 * dt;
    if (game.jy <= 0) { game.jy = 0; game.vy = 0; }
  }

  // nearest interactable
  const objs = CONTENT.rooms[game.key].objects;
  let best = -1, bd = NEAR;
  objs.forEach((o, i) => { const d = Math.abs(o.x_native - game.x); if (d < bd) { bd = d; best = i; } });
  game.nearIdx = best;
}

function render() {
  if (mode === 'game' && game.inArena && !game.busy) { arena.render(); return; }
  if (mode !== 'game' || !game.knightEl) return;
  const nx = Math.round(game.x), ny = Math.round(game.jy);
  const R = game.facing > 0;
  let src;
  if (game.slash >= 0) {
    const f = game.slash < SLASH_T[0] ? 0 : game.slash < SLASH_T[1] ? 1 : 2;
    src = (R ? SPRITES.slashR : SPRITES.slashL)[f];
  } else if (game.walking || ny > 0) {
    const f = ny > 0 ? 0 : Math.floor(game.t * WALK_FPS) % 4;   // walk frames carry their own bob
    src = (R ? SPRITES.walkR : SPRITES.walkL)[f];
  } else {
    src = R ? SPRITES.idleR : SPRITES.idleL;
  }
  if (src !== game.lastSrc) {
    game.imgEl.src = src;
    game.imgEl.style.width = game.imgEl.style.height = HK * S + 'px';
    // centre the body column on the knight's x (64 = half the .knight box)
    game.bodyEl.style.left = 64 - ((R ? HK_CX : HK - 1 - HK_CX) + 0.5) * S + 'px';
    game.bodyEl.classList.toggle('idle', !(game.walking || ny > 0 || game.slash >= 0));
    game.lastSrc = src;
  }
  game.knightEl.style.transform = `translate(${nx * S - 64}px, ${(FLOOR - ny) * S - 160}px)`;
  game.knightEl.querySelector('.shadow').style.opacity = ny > 0 ? 0.25 : 1;

  game.knightEl.hidden = game.seated;
  game.seatEl.hidden = !game.seated;

  game.hitEls.forEach((b, i) => b.classList.toggle('near', i === game.nearIdx));
  const showPrompt = game.nearIdx >= 0 && !game.popup && !game.mapOpen && !game.target;
  game.promptEl.hidden = !showPrompt;
  if (showPrompt) {
    const o = CONTENT.rooms[game.key].objects[game.nearIdx];
    game.promptEl.style.left = o.x_native * S + 'px';
    game.promptEl.style.top = o.y_native * S - 64 + 'px';
    const txt = o.verb + ' ' + o.label;
    const key = o.action === 'gate' ? 'X' : 'E';
    const kEl = game.promptEl.querySelector('.key');
    if (kEl.textContent !== key) kEl.textContent = key;
    const t = game.promptEl.querySelector('.txt');
    if (t.textContent !== txt) t.textContent = txt;
  }
}

let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  update(dt);
  render();
  requestAnimationFrame(frame);
}

/* ---------- boot ---------- */
intro = buildIntro();
buildGame();
arena = createArena({
  keys: game.keys, S, FLOOR, SPRITES, HK, HK_CX, reduced,
  onExit: () => travel('gate', 'center'),   // back in through the gate
});
if (import.meta.env.DEV) window.__arena = arena.debug;
const start = location.hash.slice(1);
if (CONTENT.rooms[start]) { intro.hidden = true; enterCastle(start, 'center'); }
else if (start === 'courtyard') { intro.hidden = true; enterCastle('gate', 'left'); travel('courtyard'); }
window.addEventListener('hashchange', () => {
  const k = location.hash.slice(1);
  if ((!CONTENT.rooms[k] && k !== 'courtyard') || k === game.key) return;
  if (k === 'courtyard') { if (mode === 'intro') { intro.hidden = true; enterCastle('gate', 'left'); } travel('courtyard'); return; }
  if (mode === 'intro') { intro.hidden = true; enterCastle(k, 'center'); } else travel(k, 'center');
});
requestAnimationFrame(frame);
