// Knight for Hire: original medieval-style music, synthesised live with the Web Audio API.
// No audio files: each instrument is built from oscillators, filters and noise, and every
// tune is written below as plain note text (e.g. "A4:2 G4:.5 F4:.5", where the number is beats).

const SEMI = { C: -9, 'C#': -8, Db: -8, D: -7, 'D#': -6, Eb: -6, E: -5, F: -4, 'F#': -3, Gb: -3, G: -2, 'G#': -1, Ab: -1, A: 0, 'A#': 1, Bb: 1, B: 2 };
const freq = (n) => { const m = /^([A-G][#b]?)(-?\d)$/.exec(n); return 440 * 2 ** ((SEMI[m[1]] + (m[2] - 4) * 12) / 12); };

// "A4:2 G4:.5 r:1 | C5" -> [[note|null, beats], ...]; a bare note uses the default length
function parse(text, def = 1) {
  return text.split(/\s+/).filter((t) => t && t !== '|').map((t) => {
    const [n, d] = t.split(':');
    return [n === 'r' ? null : n.split('+'), d ? +d : def];             // "C4+E4+G4" is a chord
  });
}
// broken-chord accompaniment: each chord is played as a repeating pattern of its tones
function arp(chords, pattern, step) {
  return chords.map((c) => pattern.map((i) => `${c[i]}:${step}`).join(' ')).join(' ');
}

/* ------------------------------------------------------------------ instruments */
function noiseBuffer(ctx) {
  const b = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate), d = b.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  return b;
}
function env(g, t, a, peak, decay, end = 0.0001) {
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(peak, t + a);
  g.gain.exponentialRampToValueAtTime(end, t + a + decay);
}
const INST = {
  // plucked lute: bright saw + triangle, a filter that closes fast like a plucked string
  lute(ctx, out, t, f, dur, v) {
    const g = ctx.createGain(), lp = ctx.createBiquadFilter();
    lp.type = 'lowpass'; lp.Q.value = 2;
    lp.frequency.setValueAtTime(Math.min(9000, f * 9), t); lp.frequency.exponentialRampToValueAtTime(f * 1.4, t + 0.35);
    for (const [type, mul, lvl] of [['sawtooth', 1, 0.5], ['triangle', 2, 0.25]]) {
      const o = ctx.createOscillator(), og = ctx.createGain(); o.type = type; o.frequency.value = f * mul; og.gain.value = lvl;
      o.connect(og).connect(lp); o.start(t); o.stop(t + 2.2);
    }
    env(g, t, 0.004, v, Math.min(1.8, 0.5 + dur));
    lp.connect(g).connect(out);
  },
  // harp: rounder and longer ringing than the lute
  harp(ctx, out, t, f, dur, v) {
    const g = ctx.createGain();
    for (const [type, mul, lvl] of [['triangle', 1, 0.7], ['sine', 2, 0.3]]) {
      const o = ctx.createOscillator(), og = ctx.createGain(); o.type = type; o.frequency.value = f * mul; og.gain.value = lvl;
      o.connect(og).connect(g); o.start(t); o.stop(t + 3.2);
    }
    env(g, t, 0.006, v, 2.8);
    g.connect(out);
  },
  // recorder: breathy sine with a gentle delayed vibrato
  recorder(ctx, out, t, f, dur, v) {
    const g = ctx.createGain(), o = ctx.createOscillator(), o2 = ctx.createOscillator(), o2g = ctx.createGain();
    const lfo = ctx.createOscillator(), lg = ctx.createGain();
    o.type = 'sine'; o.frequency.value = f; o2.type = 'triangle'; o2.frequency.value = f; o2g.gain.value = 0.18;
    lfo.frequency.value = 5.2; lg.gain.setValueAtTime(0, t); lg.gain.linearRampToValueAtTime(f * 0.006, t + 0.35);
    lfo.connect(lg); lg.connect(o.frequency); lg.connect(o2.frequency);
    o.connect(g); o2.connect(o2g).connect(g);
    const len = Math.max(0.12, dur - 0.04);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v, t + 0.06);
    g.gain.setValueAtTime(v, t + len); g.gain.exponentialRampToValueAtTime(0.0001, t + len + 0.12);
    for (const x of [o, o2, lfo]) { x.start(t); x.stop(t + len + 0.2); }
    g.connect(out);
  },
  // shawm: a reedy, nasal double-reed lead for battle
  shawm(ctx, out, t, f, dur, v) {
    const g = ctx.createGain(), bp = ctx.createBiquadFilter(), o = ctx.createOscillator(), o2 = ctx.createOscillator();
    bp.type = 'bandpass'; bp.frequency.value = Math.min(4000, f * 2.2); bp.Q.value = 0.9;
    o.type = 'square'; o.frequency.value = f; o2.type = 'sawtooth'; o2.frequency.value = f * 1.003;
    o.connect(bp); o2.connect(bp); bp.connect(g);
    const len = Math.max(0.1, dur - 0.03);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v, t + 0.02);
    g.gain.setValueAtTime(v * 0.85, t + len); g.gain.exponentialRampToValueAtTime(0.0001, t + len + 0.08);
    for (const x of [o, o2]) { x.start(t); x.stop(t + len + 0.12); }
    g.connect(out);
  },
  // bass: soft triangle with a sine sub, short so it can pulse
  bass(ctx, out, t, f, dur, v) {
    const g = ctx.createGain();
    for (const [type, mul, lvl] of [['triangle', 1, 0.8], ['sine', 0.5, 0.5]]) {
      const o = ctx.createOscillator(), og = ctx.createGain(); o.type = type; o.frequency.value = f * mul; og.gain.value = lvl;
      o.connect(og).connect(g); o.start(t); o.stop(t + dur + 0.3);
    }
    env(g, t, 0.01, v, Math.max(0.15, dur * 0.9));
    g.connect(out);
  },
  // frame drum: a pitched thump plus a skin slap
  drum(ctx, out, t, f, dur, v, noise) {
    const g = ctx.createGain(), o = ctx.createOscillator();
    o.type = 'sine'; o.frequency.setValueAtTime(150, t); o.frequency.exponentialRampToValueAtTime(55, t + 0.18);
    env(g, t, 0.003, v, 0.28); o.connect(g).connect(out); o.start(t); o.stop(t + 0.4);
    const n = ctx.createBufferSource(), ng = ctx.createGain(), bp = ctx.createBiquadFilter();
    n.buffer = noise; bp.type = 'bandpass'; bp.frequency.value = 420; bp.Q.value = 0.8;
    env(ng, t, 0.002, v * 0.35, 0.12); n.connect(bp).connect(ng).connect(out); n.start(t); n.stop(t + 0.2);
  },
  snare(ctx, out, t, f, dur, v, noise) {
    const n = ctx.createBufferSource(), ng = ctx.createGain(), hp = ctx.createBiquadFilter();
    n.buffer = noise; hp.type = 'highpass'; hp.frequency.value = 1400;
    env(ng, t, 0.002, v, 0.14); n.connect(hp).connect(ng).connect(out); n.start(t); n.stop(t + 0.2);
  },
  // bowed string section: detuned saws, slow swell, gentle vibrato (pads and long notes)
  strings(ctx, out, t, f, dur, v) {
    const g = ctx.createGain(), lp = ctx.createBiquadFilter(), lfo = ctx.createOscillator(), lg = ctx.createGain();
    lp.type = 'lowpass'; lp.frequency.value = Math.min(5000, f * 5); lp.Q.value = 0.5;
    lfo.frequency.value = 5; lg.gain.value = f * 0.004; lfo.connect(lg);
    const len = Math.max(0.2, dur);
    for (const det of [-7, 0, 7]) {
      const o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = f; o.detune.value = det;
      lg.connect(o.frequency); o.connect(lp); o.start(t); o.stop(t + len + 0.7);
    }
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v, t + Math.min(0.35, len * 0.4));
    g.gain.setValueAtTime(v, t + len); g.gain.exponentialRampToValueAtTime(0.0001, t + len + 0.6);
    lfo.start(t); lfo.stop(t + len + 0.7);
    lp.connect(g).connect(out);
  },
  // solo fiddle: bright bowed lead with expressive delayed vibrato
  fiddle(ctx, out, t, f, dur, v) {
    const g = ctx.createGain(), bp = ctx.createBiquadFilter(), lp = ctx.createBiquadFilter(), lfo = ctx.createOscillator(), lg = ctx.createGain();
    bp.type = 'peaking'; bp.frequency.value = 2800; bp.gain.value = 5;
    lp.type = 'lowpass'; lp.frequency.value = Math.min(7000, f * 6);
    lfo.frequency.value = 5.6; lg.gain.setValueAtTime(0, t); lg.gain.linearRampToValueAtTime(f * 0.009, t + Math.min(0.3, dur * 0.6)); lfo.connect(lg);
    const len = Math.max(0.08, dur - 0.02);
    for (const det of [-3, 3]) {
      const o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = f; o.detune.value = det;
      lg.connect(o.frequency); o.connect(lp); o.start(t); o.stop(t + len + 0.25);
    }
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v, t + Math.min(0.06, len * 0.3));
    g.gain.setValueAtTime(v * 0.9, t + len); g.gain.exponentialRampToValueAtTime(0.0001, t + len + 0.18);
    lfo.start(t); lfo.stop(t + len + 0.25);
    lp.connect(bp).connect(g).connect(out);
  },
  // harpsichord: bright, metallic pluck that dies quickly
  harpsichord(ctx, out, t, f, dur, v) {
    const g = ctx.createGain(), lp = ctx.createBiquadFilter();
    lp.type = 'lowpass'; lp.frequency.setValueAtTime(Math.min(12000, f * 14), t); lp.frequency.exponentialRampToValueAtTime(f * 3, t + 0.5);
    for (const [type, mul, lvl] of [['sawtooth', 1, 0.4], ['square', 2, 0.18], ['sawtooth', 1.003, 0.3]]) {
      const o = ctx.createOscillator(), og = ctx.createGain(); o.type = type; o.frequency.value = f * mul; og.gain.value = lvl;
      o.connect(og).connect(lp); o.start(t); o.stop(t + 1.3);
    }
    env(g, t, 0.002, v, 0.9);
    lp.connect(g).connect(out);
  },
  // pipe organ: stacked sine partials, steady and churchy
  organ(ctx, out, t, f, dur, v) {
    const g = ctx.createGain(), len = Math.max(0.2, dur);
    for (const [mul, lvl] of [[1, 0.6], [2, 0.3], [3, 0.12], [0.5, 0.25]]) {
      const o = ctx.createOscillator(), og = ctx.createGain(); o.type = 'sine'; o.frequency.value = f * mul; og.gain.value = lvl;
      o.connect(og).connect(g); o.start(t); o.stop(t + len + 0.5);
    }
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v, t + 0.08);
    g.gain.setValueAtTime(v, t + len); g.gain.exponentialRampToValueAtTime(0.0001, t + len + 0.35);
    g.connect(out);
  },
  // war horn: brassy swell, the filter opens as the note blooms
  horn(ctx, out, t, f, dur, v) {
    const g = ctx.createGain(), lp = ctx.createBiquadFilter(), lfo = ctx.createOscillator(), lg = ctx.createGain();
    const len = Math.max(0.1, dur - 0.03);
    lp.type = 'lowpass'; lp.Q.value = 1.2;
    lp.frequency.setValueAtTime(f * 1.4, t); lp.frequency.exponentialRampToValueAtTime(Math.min(6000, f * 4.5), t + 0.14);
    lp.frequency.setTargetAtTime(f * 3, t + 0.2, 0.3);
    lfo.frequency.value = 4.8; lg.gain.setValueAtTime(0, t); lg.gain.linearRampToValueAtTime(f * 0.004, t + 0.4); lfo.connect(lg);
    for (const [type, det, lvl] of [['sawtooth', -5, 0.6], ['sawtooth', 5, 0.6], ['square', 0, 0.25]]) {
      const o = ctx.createOscillator(), og = ctx.createGain(); o.type = type; o.frequency.value = f; o.detune.value = det; og.gain.value = lvl;
      lg.connect(o.frequency); o.connect(og).connect(lp); o.start(t); o.stop(t + len + 0.3);
    }
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v, t + 0.05);
    g.gain.setValueAtTime(v * 0.85, t + len); g.gain.exponentialRampToValueAtTime(0.0001, t + len + 0.22);
    lfo.start(t); lfo.stop(t + len + 0.3);
    lp.connect(g).connect(out);
  },
  // choir: detuned voices through "ah" vowel formants, slow to swell
  choir(ctx, out, t, f, dur, v) {
    const g = ctx.createGain(), sum = ctx.createGain(), len = Math.max(0.3, dur);
    for (const [fq, q, lvl] of [[750, 7, 1], [1150, 9, 0.6], [2600, 10, 0.25]]) {
      const bp = ctx.createBiquadFilter(), bg = ctx.createGain(); bp.type = 'bandpass'; bp.frequency.value = fq; bp.Q.value = q; bg.gain.value = lvl;
      sum.connect(bp).connect(bg).connect(g);
    }
    for (const det of [-9, -3, 4, 10]) {
      const o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = f; o.detune.value = det;
      o.connect(sum); o.start(t); o.stop(t + len + 1);
    }
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v * 3, t + Math.min(0.6, len * 0.5));
    g.gain.setValueAtTime(v * 3, t + len); g.gain.exponentialRampToValueAtTime(0.0001, t + len + 0.8);
    g.connect(out);
  },
  shaker(ctx, out, t, f, dur, v, noise) {
    const n = ctx.createBufferSource(), ng = ctx.createGain(), hp = ctx.createBiquadFilter();
    n.buffer = noise; hp.type = 'highpass'; hp.frequency.value = 6500;
    env(ng, t, 0.003, v, 0.045); n.connect(hp).connect(ng).connect(out); n.start(t); n.stop(t + 0.08);
  },
};

/* ------------------------------------------------------------------ the tunes (all original compositions) */
const ch = (...notes) => notes;                                    // a chord: low to high
const pad = (chords, beats) => chords.map((c) => `${c.join('+')}:${beats}`).join(' ');
const bar = (n, s) => Array(n).fill(s).join(' ');

// LANDING: slow and wistful, a harp ostinato under a lonely fiddle (mood after "Enter Pharloom")
const T1 = [ch('D3', 'A3', 'D4', 'F4'), ch('Bb2', 'F3', 'Bb3', 'D4'), ch('F2', 'C3', 'F3', 'A3'), ch('C3', 'G3', 'C4', 'E4'),
            ch('D3', 'A3', 'D4', 'F4'), ch('Bb2', 'F3', 'Bb3', 'D4'), ch('G2', 'D3', 'G3', 'Bb3'), ch('A2', 'E3', 'A3', 'C#4')];
// CASTLE: a stately court with harpsichord, organ and a walking bass (mood after "High Halls")
const T2 = [ch('G2', 'D3', 'G3', 'Bb3'), ch('D2', 'A2', 'D3', 'F#3'), ch('Eb2', 'Bb2', 'Eb3', 'G3'), ch('Bb1', 'F2', 'Bb2', 'D3'),
            ch('C2', 'G2', 'C3', 'Eb3'), ch('G2', 'D3', 'G3', 'Bb3'), ch('D2', 'A2', 'D3', 'F#3'), ch('G2', 'D3', 'G3', 'Bb3')];
// battle option chords
const B1 = [['D3', 'F3', 'A3'], ['D3', 'F3', 'A3'], ['Bb2', 'D3', 'F3'], ['C3', 'E3', 'G3'], ['D3', 'F3', 'A3'], ['D3', 'F3', 'A3'], ['Bb2', 'D3', 'F3'], ['A2', 'C#3', 'E3']];
const B2 = [ch('E2', 'E3', 'G3', 'B3'), ch('F2', 'F3', 'A3', 'C4'), ch('E2', 'E3', 'G3', 'B3'), ch('D2', 'D3', 'F#3', 'A3'),
            ch('C2', 'C3', 'E3', 'G3'), ch('D2', 'D3', 'F3', 'A3'), ch('F2', 'F3', 'A3', 'C4'), ch('E2', 'E3', 'G#3', 'B3')];
const B4 = [ch('C4', 'Eb4', 'G4'), ch('Ab3', 'C4', 'Eb4'), ch('F3', 'Ab3', 'C4'), ch('G3', 'B3', 'D4'),
            ch('C4', 'Eb4', 'G4'), ch('Ab3', 'C4', 'Eb4'), ch('Db4', 'F4', 'Ab4'), ch('G3', 'B3', 'D4')];
// option E: D minor with a dark flat-second (Eb) and the harmonic-minor C#
const B5 = [ch('D2', 'D3', 'F3', 'A3'), ch('Eb2', 'Eb3', 'G3', 'Bb3'), ch('D2', 'D3', 'F3', 'A3'), ch('C2', 'C3', 'E3', 'G3'),
            ch('Bb1', 'Bb2', 'D3', 'F3'), ch('G1', 'G2', 'Bb2', 'D3'), ch('Eb2', 'Eb3', 'G3', 'Bb3'), ch('A1', 'A2', 'C#3', 'E3')];
// CASTLE (roaming the palace): moonlit and airy, harp arpeggios under long recorder notes
const M = { Am: ch('A2', 'E3', 'A3', 'C4'), F: ch('F2', 'C3', 'F3', 'A3'), C: ch('C3', 'G3', 'C4', 'E4'), G: ch('G2', 'D3', 'G3', 'B3'), E: ch('E2', 'B2', 'E3', 'G#3') };

export const TRACKS = {
  title: {
    title: 'Beneath the Silver Moon', mood: 'Landing page · wistful, airy · D minor · slow 4/4',
    bpm: 70, drone: ['D2', 'A2'],
    parts: [
      { inst: 'harp', vol: 0.13, seq: arp(T1, [0, 2, 3, 1, 3, 2, 3, 1], 0.5) },
      { inst: 'strings', vol: 0.05, seq: pad(T1.map((c) => c.slice(1)), 4) },
      { inst: 'fiddle', vol: 0.085, seq: `r:2 A4 D5 | F5:3 E5:.5 D5:.5 | C5:2 A4:2 | G4:3 r:1 |
        A4 D5 E5 F5 | G5:2 F5 D5 | Bb4:1.5 C5:.5 D5:2 | C#5:3 r:1` },
    ],
  },
  castle: {
    title: 'Moon over the Battlements', mood: 'Inside the castle · quiet, airy · A minor · slow',
    bpm: 62, drone: ['A1', 'E2'],
    parts: [
      { inst: 'harp', vol: 0.11, seq: arp([M.Am, M.F, M.C, M.G, M.Am, M.F, M.C, M.E], [0, 1, 2, 3, 2, 1, 2, 3], 0.5) },
      { inst: 'recorder', vol: 0.13, seq: 'E5:4 C5:4 G4:2 E4:2 D4:4 A4:2 C5:2 A4:4 G4:2 E5:2 D5:2 B4:2' },
    ],
  },
  court: {
    title: 'The Gilded Court', mood: 'Spare · stately, regal · G minor · 4/4',
    bpm: 92, drone: null,
    parts: [
      { inst: 'harpsichord', vol: 0.09, seq: arp(T2, [0, 2, 3, 2, 1, 2, 3, 2], 0.5) },
      { inst: 'organ', vol: 0.05, seq: pad(T2.map((c) => c.slice(1)), 4) },
      { inst: 'bass', vol: 0.22, seq: `G2 A2 Bb2 D3 | D2 F#2 A2 D3 | Eb2 G2 Bb2 G2 | Bb1 D2 F2 Bb2 |
        C2 Eb2 G2 C3 | G2 Bb2 D3 Bb2 | D2 A2 F#2 A2 | G2 D2 G2:2` },
      { inst: 'fiddle', vol: 0.08, seq: `D5 G5 F#5:.5 G5:.5 A5 | F#5:1.5 E5:.5 D5:2 | Eb5 G5 Bb5 G5 | F5:2 D5:2 |
        Eb5 D5:.5 C5:.5 G5 Eb5 | D5 Bb4 G4 Bb4 | A4 C5 F#5 A5 | G5:3 r:1` },
      { inst: 'drum', vol: 0.32, seq: bar(8, 'X:1 r:3') },
    ],
  },
  // ---- battle options
  warDrums: {
    title: 'War Drums of the Keep', mood: 'Battle A · epic war march · D minor · driving 4/4',
    bpm: 132, drone: null,
    parts: [
      { inst: 'strings', vol: 0.07, seq: B1.map(([r, a, b]) => `${r}:.5 ${r}:.5 ${a}:.5 ${r}:.5 ${b}:.5 ${r}:.5 ${a}:.5 ${r}:.5`).join(' ') },
      { inst: 'horn', vol: 0.085, seq: `D4:1.5 A4:.5 A4:2 | G4 F4 E4 F4 | D4:1.5 F4:.5 Bb4:2 | A4 G4 E4:2 |
        D5:1.5 A4:.5 F4 A4 | G4 A4 Bb4 A4 | F4 G4 D4:2 | E4 C#4 A3:2` },
      { inst: 'choir', vol: 0.05, seq: pad(B1.map(([r, a, b]) => [r.replace('3', '4').replace('2', '3'), a.replace('3', '4').replace('2', '3'), b.replace('3', '4').replace('2', '3')]), 4) },
      { inst: 'bass', vol: 0.32, seq: B1.map(([r]) => `${r.replace('3', '2')}:1 r:.5 ${r.replace('3', '2')}:.5 ${r.replace('3', '2')}:1 r:1`).join(' ') },
      { inst: 'drum', vol: 0.62, seq: bar(8, 'X:1 r:.5 X:.5 X:1 r:.5 X:.5') },
      { inst: 'snare', vol: 0.15, seq: bar(8, 'r:1 X:1 r:1 X:.5 X:.5') },
    ],
  },
  gallop: {
    title: 'The Crimson Gallop', mood: 'Battle B · fierce Celtic reel · E Phrygian · fast 6/8',
    bpm: 168, drone: ['E2'],
    parts: [
      { inst: 'fiddle', vol: 0.1, seq: `E5:.5 G5:.5 B5:.5 G5:.5 E5:.5 B4:.5 | F5:.5 A5:.5 C6:.5 A5:.5 F5:.5 C5:.5 | E5:.5 G5:.5 B5:.5 A5:.5 G5:.5 F5:.5 | D5:.5 F#5:.5 A5:.5 F#5:.5 D5:.5 A4:.5 |
        C5:.5 E5:.5 G5:.5 E5:.5 C5:.5 G4:.5 | D5:.5 F5:.5 A5:.5 F5:.5 D5:.5 A4:.5 | F5:.5 A5:.5 C6:.5 B5:.5 A5:.5 G5:.5 | G#5:1 F5:.5 E5:1.5` },
      { inst: 'lute', vol: 0.1, seq: B2.map((c) => `${c.slice(1).join('+')}:1.5 ${c.slice(1).join('+')}:1.5`).join(' ') },
      { inst: 'bass', vol: 0.34, seq: B2.map((c) => `${c[0]}:1.5 ${c[0]}:1.5`).join(' ') },
      { inst: 'drum', vol: 0.58, seq: bar(8, 'X:1 r:.5 X:.5 X:.5 X:.5') },
      { inst: 'shaker', vol: 0.07, seq: bar(48, 'X:.5') },
    ],
  },
  siege: {
    title: 'Siege at the Gate', mood: 'Battle C · reedy and relentless · E minor · fast 4/4',
    bpm: 138, drone: null,
    parts: [
      { inst: 'shawm', vol: 0.16, seq: `E5 B4:.5 E5:.5 G5 F#5 | E5:1.5 D5:.5 C5 B4 | A4 D5 F#5 A5 | G5 F#5 D#5:2 |
        E5:.5 E5:.5 G5 B5 A5 | G5 E5 C5:2 | D5 F#5 A5 F#5 | B4 D#5 F#5:2` },
      { inst: 'bass', vol: 0.44, seq: ['E2', 'C2', 'D2', 'B1', 'E2', 'C2', 'D2', 'B1'].map((n) => bar(8, `${n}:.5`)).join(' ') },
      { inst: 'drum', vol: 0.78, seq: bar(8, 'X:1 r:1 X:1 r:1') },
      { inst: 'snare', vol: 0.26, seq: bar(8, 'r:1 X:1 r:1 X:1') },
      { inst: 'shaker', vol: 0.08, seq: bar(64, 'X:.5') },
      { inst: 'lute', vol: 0.13, seq: arp([ch('E3', 'B3', 'E4', 'G4'), ch('C3', 'G3', 'C4', 'E4'), ch('D3', 'A3', 'D4', 'F#4'), ch('B2', 'F#3', 'B3', 'D#4')].flatMap((c) => [c, c]), [0, 1, 2, 3], 1) },
    ],
  },
  nightRide: {
    title: 'The Night Ride', mood: 'Battle E · dark and ominous · D minor · fast 6/8',
    bpm: 168, drone: ['D2'],
    parts: [
      // galloping low strings: the engine of the piece
      { inst: 'strings', vol: 0.075, seq: B5.map((c) => `${c[1]}:.5 ${c[1]}:.5 ${c[3]}:.5 ${c[1]}:.5 ${c[2]}:.5 ${c[3]}:.5`).join(' ') },
      // a grim war horn in dotted 6/8 rhythms
      { inst: 'horn', vol: 0.09, seq: `D4:1 F4:.5 A4:1.5 | G4:1 Eb4:.5 Bb3:1.5 | A4:1 D5:.5 C#5:1.5 | C5:1 G4:.5 E4:1.5 |
        D5:1 F5:.5 D5:1 Bb4:.5 | G4:1.5 Bb4:1.5 | Eb5:1 D5:.5 Bb4:1.5 | C#5:1.5 A4:1.5` },
      // second time round a fiddle joins with dark running eighths (16-bar loop)
      { inst: 'fiddle', vol: 0.075, seq: `r:24 | D5:.5 E5:.5 F5:.5 A5:.5 F5:.5 E5:.5 | Eb5:.5 G5:.5 Bb5:.5 G5:.5 Eb5:.5 D5:.5 | D5:.5 F5:.5 A5:.5 D6:.5 C#6:.5 A5:.5 | C6:.5 G5:.5 E5:.5 G5:.5 E5:.5 C5:.5 |
        Bb5:.5 F5:.5 D5:.5 F5:.5 Bb5:.5 D6:.5 | G5:.5 Bb5:.5 D6:.5 Bb5:.5 G5:.5 D5:.5 | Eb5:.5 G5:.5 Bb5:.5 Eb6:.5 D6:.5 Bb5:.5 | C#6:1 A5:.5 E5:.5 C#5:.5 A4:.5` },
      { inst: 'choir', vol: 0.05, seq: pad(B5.map((c) => c.slice(1).map((n) => n.replace(/\d/, (d) => String(+d + 1)))), 3) },
      { inst: 'bass', vol: 0.36, seq: B5.map((c) => `${c[0]}:1.5 ${c[0]}:1.5`).join(' ') },
      { inst: 'drum', vol: 0.66, seq: bar(8, 'X:1 r:.5 X:.5 X:.5 X:.5') },
      { inst: 'snare', vol: 0.1, seq: bar(8, 'r:1.5 X:1.5') },
    ],
  },
  wyrm: {
    title: 'The Wyrm Ascendant', mood: 'Battle D · dark and ominous · C minor · heavy 4/4',
    bpm: 100, drone: ['C2', 'G2'],
    parts: [
      { inst: 'choir', vol: 0.055, seq: pad(B4, 4) },
      { inst: 'organ', vol: 0.045, seq: pad(B4.map((c) => c.map((n) => n.replace('4', '3'))), 4) },
      { inst: 'horn', vol: 0.09, seq: `C4:2 Eb4 G4 | Ab4:3 G4 | F4 Ab4 C5:2 | B4:2 D5 B4 |
        C5:1.5 Bb4:.5 G4:2 | Ab4 C5 Eb5:2 | Db5:1.5 C5:.5 Ab4:2 | G4:2 D4 B3` },
      { inst: 'strings', vol: 0.06, seq: B4.map((c) => bar(8, `${c[0].replace(/\d/, '2')}:.5`)).join(' ') },
      { inst: 'drum', vol: 0.66, seq: bar(8, 'X:1 r:1 X:.5 X:.5 r:1') },
    ],
  },
};

/* ------------------------------------------------------------------ the player */
export function createMusic() {
  let ctx = null, master, dry, wet, noise, timer = null, current = null, droneNodes = [], volume = 0.6;
  const state = { parts: [] };

  function init() {
    if (ctx) return;
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    master = ctx.createGain(); master.gain.value = 0;
    const comp = ctx.createDynamicsCompressor(); comp.threshold.value = -14; comp.ratio.value = 3;
    dry = ctx.createGain(); dry.gain.value = 0.85;
    wet = ctx.createGain(); wet.gain.value = 0.32;
    // stone-hall reverb: a decaying burst of stereo noise as the impulse response
    const ir = ctx.createBuffer(2, ctx.sampleRate * 2.6, ctx.sampleRate);
    for (let ch = 0; ch < 2; ch++) { const d = ir.getChannelData(ch); for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length) ** 2.6; }
    const verb = ctx.createConvolver(); verb.buffer = ir;
    const bus = ctx.createGain();
    bus.connect(dry).connect(comp); bus.connect(verb).connect(wet).connect(comp);
    comp.connect(master).connect(ctx.destination);
    state.bus = bus;
    noise = noiseBuffer(ctx);
  }

  function startDrone(notes, t) {
    stopDrone(t);
    if (!notes) return;
    for (const n of notes) {
      const lp = ctx.createBiquadFilter(), g = ctx.createGain();
      lp.type = 'lowpass'; lp.frequency.value = 380;
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.035, t + 2.5);
      for (const det of [-4, 4]) {
        const o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = freq(n); o.detune.value = det;
        o.connect(lp); o.start(t); droneNodes.push(o);
      }
      lp.connect(g).connect(state.bus); droneNodes.push(g);
    }
  }
  function stopDrone(t) {
    for (const n of droneNodes) {
      if (n instanceof GainNode) { n.gain.cancelScheduledValues(t); n.gain.setTargetAtTime(0.0001, t, 0.4); }
      else n.stop(t + 2);
    }
    droneNodes = [];
  }

  function tick() {
    const ahead = ctx.currentTime + 0.2, spb = 60 / current.bpm;
    for (const p of state.parts) {
      while (p.next < ahead) {
        const [notes, beats] = p.seq[p.i];
        if (notes) for (const n of notes) INST[p.inst](ctx, state.bus, p.next, n === 'X' ? 0 : freq(n), beats * spb, p.vol, noise);
        p.next += beats * spb;
        p.i = (p.i + 1) % p.seq.length;
      }
    }
  }

  // Switching tracks crossfades: the old tune fades out, then the new one fades in from its first bar.
  function play(name) {
    init();
    if (ctx.state === 'suspended') ctx.resume();
    if (current === TRACKS[name] && timer) return;
    const now = ctx.currentTime, switching = !!timer;
    const t = now + (switching ? 0.9 : 0.1);
    master.gain.cancelScheduledValues(now);
    if (switching) {
      master.gain.setTargetAtTime(0.0001, now, 0.22);                    // fade the old tune out
      state.parts = [];                                                   // and stop scheduling its notes
      stopDrone(now);
    }
    current = TRACKS[name];
    state.parts = current.parts.map((p) => ({ inst: p.inst, vol: p.vol, seq: parse(p.seq), i: 0, next: t + 0.05 }));
    startDrone(current.drone, t);
    master.gain.setTargetAtTime(volume, t, 0.5);                          // then bring the new one up
    if (!timer) timer = setInterval(tick, 25);
  }

  /* ---------------- sound effects: one-shots on their own bus (not affected by music fades) ---------------- */
  let fx = null; const lastFx = {};
  function fxBus() {
    if (fx) return fx;
    // a firm limiter: several hits, roars and fireballs at once shouldn't distort
    const comp = ctx.createDynamicsCompressor(); comp.threshold.value = -18; comp.ratio.value = 12; comp.knee.value = 6; comp.attack.value = 0.002; comp.release.value = 0.15;
    fx = ctx.createGain(); fx.gain.value = 0.5;
    const verb = ctx.createConvolver(), wetG = ctx.createGain(); wetG.gain.value = 0.18;
    const ir = ctx.createBuffer(2, ctx.sampleRate * 1.2, ctx.sampleRate);
    for (let c = 0; c < 2; c++) { const d = ir.getChannelData(c); for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length) ** 3; }
    verb.buffer = ir;
    fx.connect(comp); fx.connect(verb).connect(wetG).connect(comp);
    comp.connect(ctx.destination);
    return fx;
  }
  const nz = (t, dur, type, f0, f1, q, peak, out) => {             // a filtered noise burst with a sweeping filter
    const n = ctx.createBufferSource(), flt = ctx.createBiquadFilter(), g = ctx.createGain();
    n.buffer = noise; flt.type = type; flt.Q.value = q;
    flt.frequency.setValueAtTime(f0, t); flt.frequency.exponentialRampToValueAtTime(f1, t + dur);
    env(g, t, Math.min(0.02, dur * 0.2), peak, dur);
    n.connect(flt).connect(g).connect(out); n.start(t); n.stop(t + dur + 0.05);
  };
  const tone = (t, dur, type, f0, f1, peak, out, a = 0.004) => {    // a pitched blip with a pitch slide
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type; o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f1, t + dur);
    env(g, t, a, peak, dur);
    o.connect(g).connect(out); o.start(t); o.stop(t + dur + 0.05);
  };
  // a beast's roar: detuned low saws, growling tremolo, a sweeping filter and breath noise
  const roar = (t, dur, f0, f1, peak, out) => {
    const g = ctx.createGain(), lp = ctx.createBiquadFilter(), trem = ctx.createOscillator(), tg = ctx.createGain();
    lp.type = 'lowpass'; lp.frequency.setValueAtTime(500, t); lp.frequency.exponentialRampToValueAtTime(1600, t + dur * 0.3); lp.frequency.exponentialRampToValueAtTime(350, t + dur);
    trem.frequency.value = 26; tg.gain.value = peak * 0.45; trem.connect(tg).connect(g.gain);   // growl scales with the roar
    for (const [mul, det] of [[1, -12], [1, 12], [1.5, 0], [0.5, 0]]) {
      const o = ctx.createOscillator(); o.type = 'sawtooth'; o.detune.value = det;
      o.frequency.setValueAtTime(f0 * mul, t); o.frequency.exponentialRampToValueAtTime(f1 * mul, t + dur);
      o.connect(lp); o.start(t); o.stop(t + dur + 0.1);
    }
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(peak, t + 0.18);
    g.gain.setValueAtTime(peak, t + dur * 0.6); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    trem.start(t); trem.stop(t + dur + 0.1);
    lp.connect(g).connect(out);
    nz(t, dur * 0.9, 'lowpass', 900, 250, 0.7, peak * 0.5, out);
  };
  // a noise swoosh with a gentle fade-in (no hard click at the start)
  const swoosh = (t, dur, type, f0, f1, q, peak, att, out) => {
    const n = ctx.createBufferSource(), flt = ctx.createBiquadFilter(), g = ctx.createGain();
    n.buffer = noise; flt.type = type; flt.Q.value = q;
    flt.frequency.setValueAtTime(f0, t); flt.frequency.exponentialRampToValueAtTime(f1, t + dur);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(peak, t + att); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    n.connect(flt).connect(g).connect(out); n.start(t); n.stop(t + dur + 0.05);
  };
  const jit = () => 0.9 + Math.random() * 0.2;                     // small pitch variation per swing
  const FX = {
    slash: (t, o) => { const v = jit(); swoosh(t, 0.2, 'lowpass', 320 * v, 950 * v, 0.9, 0.9, 0.06, o); },   // a soft air whoosh, easy on the ears when spammed
    chime: (t, o) => {                                              // a soft magical sparkle: a quick rising arpeggio of bell tones
      const roots = [1318.5, 1396.9, 1568, 1174.7], r = roots[Math.floor(Math.random() * roots.length)];
      [1, 1.26, 1.498, 2].forEach((m, i) => {
        tone(t + i * 0.045, 0.55, 'sine', r * m, r * m * 1.002, 0.09 - i * 0.012, o, 0.004);
        tone(t + i * 0.045, 0.3, 'triangle', r * m * 2, r * m * 2, 0.018, o, 0.004);   // a glassy overtone
      });
      nz(t, 0.35, 'highpass', 7000, 9000, 0.7, 0.05, o);            // faint shimmer
    },
    step: (t, o) => {                                               // an armoured boot on stone: a soft thud plus a little chainmail jingle
      const v = 0.9 + Math.random() * 0.2;
      tone(t, 0.06, 'sine', 120 * v, 60, 0.14, o, 0.003);
      nz(t, 0.045, 'lowpass', 1100 * v, 300, 0.8, 0.13, o);
      nz(t + 0.01, 0.05, 'bandpass', 6500 * v, 5000, 4.0, 0.04, o);
    },
    hit: (t, o) => { tone(t, 0.13, 'sine', 170, 55, 0.9, o); nz(t, 0.09, 'lowpass', 2200, 500, 0.8, 0.6, o); },
    hitDragon: (t, o) => { tone(t, 0.11, 'sine', 210, 70, 0.7, o); nz(t, 0.08, 'lowpass', 2600, 700, 0.8, 0.5, o); tone(t + 0.02, 0.14, 'sawtooth', 1100, 520, 0.12, o); },
    ogreDie: (t, o) => { tone(t, 0.42, 'sawtooth', 150, 60, 0.28, o, 0.03); tone(t, 0.42, 'square', 75, 40, 0.18, o, 0.03); tone(t + 0.3, 0.3, 'sine', 120, 40, 0.8, o); nz(t + 0.3, 0.25, 'lowpass', 900, 150, 0.7, 0.4, o); },
    dragonDie: (t, o) => { tone(t, 0.45, 'sawtooth', 1500, 380, 0.4, o, 0.01); tone(t, 0.45, 'square', 1510, 390, 0.2, o, 0.01); nz(t + 0.05, 0.4, 'bandpass', 1800, 400, 1.2, 0.9, o); },
    clang: (t, o) => {
      for (const [r, lvl, d] of [[1, 0.35, 0.7], [2.76, 0.22, 0.5], [5.4, 0.14, 0.35], [8.93, 0.08, 0.25]]) tone(t, d, 'sine', 640 * r, 640 * r * 0.995, lvl, o, 0.002);
      nz(t, 0.04, 'highpass', 5000, 3000, 0.7, 0.4, o);
    },
    fireball: (t, o) => { nz(t, 0.34, 'lowpass', 300, 2600, 0.9, 0.8, o); nz(t + 0.04, 0.25, 'bandpass', 1400, 600, 1.5, 0.4, o); tone(t, 0.3, 'sine', 90, 50, 0.4, o, 0.03); },
    flame: (t, o) => { nz(t, 0.55, 'bandpass', 500, 1400, 0.8, 2.0, o); nz(t, 0.5, 'lowpass', 300, 120, 0.7, 1.4, o); },
    sizzle: (t, o) => { nz(t, 0.22, 'highpass', 2500, 6000, 0.8, 0.35, o); tone(t, 0.08, 'triangle', 1200, 900, 0.1, o); },
    hurt: (t, o) => { nz(t, 0.16, 'lowpass', 1600, 300, 0.8, 0.7, o); tone(t, 0.16, 'square', 240, 110, 0.18, o); tone(t, 0.18, 'sine', 120, 50, 0.8, o); },
    roar: (t, o) => roar(t, 1.7, 95, 62, 0.22, o),
    wyrmHurt: (t, o) => { roar(t, 0.55, 140, 95, 0.26, o); tone(t, 0.15, 'sine', 140, 50, 0.5, o); },
    dive: (t, o) => { nz(t, 0.34, 'bandpass', 350, 2200, 1.0, 3.2, o); },
    slam: (t, o) => { tone(t, 0.75, 'sine', 95, 26, 1.0, o); nz(t, 0.9, 'lowpass', 600, 60, 0.7, 0.8, o); nz(t, 0.12, 'highpass', 2000, 800, 0.7, 0.3, o); },
    wyrmDie: (t, o) => { roar(t, 2.4, 120, 38, 0.24, o); tone(t + 2.1, 1.0, 'sine', 80, 22, 0.8, o); nz(t + 2.1, 1.1, 'lowpass', 500, 50, 0.7, 0.6, o); },
  };
  function sfx(name) {
    init();
    if (ctx.state === 'suspended') ctx.resume();
    const t = ctx.currentTime;
    if (lastFx[name] && t - lastFx[name] < 0.07) return;               // a burst of the same sound plays once
    lastFx[name] = t;
    if (FX[name]) FX[name](t + 0.005, fxBus());
  }

  // pause/resume the whole engine (e.g. when the tab is hidden)
  function suspend() { if (ctx && ctx.state === 'running') ctx.suspend(); }
  function resume() { if (ctx && ctx.state === 'suspended' && timer) ctx.resume(); }

  function stop() {
    if (!ctx || !timer) return;
    clearInterval(timer); timer = null;
    master.gain.cancelScheduledValues(ctx.currentTime);
    master.gain.setTargetAtTime(0.0001, ctx.currentTime, 0.25);
    stopDrone(ctx.currentTime);
    current = null;
  }

  function setVolume(v) { volume = v; if (ctx && timer) master.gain.setTargetAtTime(v, ctx.currentTime, 0.1); }

  return { play, stop, setVolume, suspend, resume, sfx, get playing() { return !!timer; }, get track() { return current; } };
}
