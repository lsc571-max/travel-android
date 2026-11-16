/* 안드로이드 앱 연결.
   화면(index.html)이 쓰는 브라우저 기능(음성 인식·목소리·공유·파일 저장)을 휴대폰 기능으로 바꿔 끼우고,
   폰 안 번역 AI(NAT.llm)를 쓸 수 있게 한다.
   브라우저에서 그냥 열면(AndroidBridge 없음) 아무것도 바꾸지 않는다. */
(function () {
  'use strict';
  const B = window.AndroidBridge;
  const NAT = window.NAT = { on: !!B, info: {}, onchange: null, onmodel: null, toast: null };
  if (!B) {
    NAT.llm = { state: { engine: false, state: 'idle', error: '', model: '', hasModel: false }, usable: () => false, models: () => [] };
    NAT.stt = { tone: null, info: () => ({}), refresh: () => ({}), usable: () => false, useLocal: () => false, headset: () => false, setBackground() { }, busy: () => false, speaking: () => false, setMic() { }, setCapture() { }, setKeepRec() { }, canCapture: () => false, files: () => ({ files: [], free: 0 }), remove: () => false, transcribe: () => Promise.reject(new Error('앱에서만 됩니다')), transcribePcm: () => Promise.reject(new Error('앱에서만 됩니다')), keep() { } };
    NAT.playing = () => { };
    NAT.ttsInstall = () => false;
    NAT.app = { sendText: () => false, open: () => false, copy: () => false, sendAudio: () => Promise.reject(new Error('앱에서만 됩니다')) };
    return;
  }
  try { NAT.info = JSON.parse(B.info()) } catch (e) { }
  const N = window.__nat = {};
  const def = (obj, key, value) => { try { Object.defineProperty(obj, key, { value, configurable: true, writable: true }) } catch (e) { try { obj[key] = value } catch (e2) { } } };

  /* ── 1) 음성 인식: 웹의 SpeechRecognition 모양 그대로 ──
     두 가지 엔진: 폰 안 AI(끊기지 않는 마이크, lstt*) · 휴대폰의 구글 음성 인식(stt*) */
  let sttInfo = {}, headAt = 0, headVal = false, bgVal = null, fileSeq = 0;
  const fileReqs = new Map();
  N.onSttFile = m => { const p = fileReqs.get(m.id); if (!p) return; fileReqs.delete(m.id); if (m.ok) p.res(m.text || ''); else p.rej(new Error(m.error || '받아 적지 못했습니다')) };
  const refreshStt = () => { try { sttInfo = JSON.parse(B.lsttInfo()) } catch (e) { sttInfo = {} } };
  refreshStt();
  const pref = k => { try { return localStorage.getItem(k) || '' } catch (e) { return '' } };
  NAT.stt = {
    tone: null,                                   // 방금 말한 사람의 목소리 {db, hz, dur, chars, at}
    info() { return sttInfo },
    refresh() { refreshStt(); return sttInfo },
    usable() { return !!sttInfo.usable },
    /** 이 언어를 폰 안 AI로 들을 수 있는지 (설정에서 구글을 골랐거나 모델이 그 언어를 못 하면 false) */
    useLocal(lang) {
      if (pref('stt_engine') === 'google' || !sttInfo.usable) return false;
      if (!sttInfo.langs) return true;
      const c = String(lang || '').toLowerCase().split('-')[0];
      return sttInfo.langs.split(',').includes(c === 'fil' ? 'tl' : c);
    },
    /** 마이크 고르기: 'auto' · 'phone'(폰 마이크) · 'ear'(이어폰 마이크) */
    setMic(pref) { try { B.setMic(String(pref || 'auto')) } catch (e) { } },
    /** 듣는 소리 고르기: 'mic'(마이크) · 'sys'(폰에서 나오는 소리) · 'sysq'(폰 소리, 스피커·이어폰으로는 소리 없이). 다음에 듣기를 시작할 때 적용 */
    setCapture(src) { try { if (B.setCapture) B.setCapture(String(src || 'mic')) } catch (e) { } },
    /** 듣기 모드의 녹음인지 알림: true = 걷어낸 파일 + 원본을 저절로 지우지 않고 보관 / false = 대화 모드(5일) */
    setKeepRec(on) { try { if (B.setKeepRec) B.setKeepRec(!!on) } catch (e) { } },
    /** 폰에서 나오는 소리를 녹음할 수 있는 앱인지 */
    canCapture() { return typeof B.setCapture === 'function' && !!sttInfo.usable },
    /** 저장해 둔 소리(au = {f 파일, a~b 표본})를 폰 안 AI(Whisper)로 받아 적음 → 글 */
    transcribe(au, lang) {
      return new Promise((res, rej) => {
        const id = ++fileSeq; fileReqs.set(id, { res, rej });
        setTimeout(() => { if (fileReqs.delete(id)) rej(new Error('시간 초과 · 폰이 받아 적는 데 너무 오래 걸립니다')) }, 120000 + Math.max(0, au.b - au.a) / 16000 * 3000);   // 2분 + 소리 길이의 3배 넘게 답이 없으면 그만 기다림 (다음 줄이 막히지 않게)
        try { B.lsttFile(id, String(au.f), String(Math.max(0, au.a - 2400)), String(au.b + 2400), String(lang || '')) } catch (e) { fileReqs.delete(id); rej(e) }   // 앞뒤 0.15초 여유 (이웃 조각의 말이 들어가지 않게)
      });
    },
    /** 화면이 가진 소리(16kHz Int16Array — 녹음 등)를 폰 안 AI(Whisper)로 받아 적음 → 글 */
    async transcribePcm(pcm, lang, id) {
      const name = 'T-' + String(id || Date.now()).replace(/[^A-Za-z0-9._-]/g, '') + '.pcm', u8 = new Uint8Array(pcm.buffer, pcm.byteOffset, pcm.byteLength), STEP = 3 * 131072;
      for (let p = 0; p < u8.length; p += STEP) {
        let bin = ''; const part = u8.subarray(p, Math.min(u8.length, p + STEP));
        for (let i = 0; i < part.length; i += 0x8000) bin += String.fromCharCode.apply(null, part.subarray(i, i + 0x8000));
        if (!B.recWrite(name, btoa(bin), p === 0)) throw new Error('소리를 폰에 넘기지 못했습니다');
        await new Promise(r => setTimeout(r));
      }
      return new Promise((res, rej) => {
        const rid = ++fileSeq; fileReqs.set(rid, { res, rej });
        setTimeout(() => { if (fileReqs.delete(rid)) rej(new Error('시간 초과 · 폰이 받아 적는 데 너무 오래 걸립니다')) }, 120000 + pcm.length / 16000 * 3000);
        try { B.lsttFile(rid, name, '0', '0', String(lang || '')) } catch (e) { fileReqs.delete(rid); rej(e) }
      });
    },
    /** 듣기 모드에서 들은 소리 파일 목록: {files: [{id, at, l(걷어낸 파일 크기), r(원본 크기), keep, live}], free(남은 공간)} */
    files() { try { return B.recFiles ? JSON.parse(B.recFiles()) : { files: [], free: 0 } } catch (e) { return { files: [], free: 0 } } },
    /** 들은 소리 파일 하나 지우기 ('L…pcm' 걷어낸 파일 · 'R…pcm' 원본) */
    remove(name) { try { return !!(B.recDelete && B.recDelete(String(name))) } catch (e) { return false } },
    /** 저장한 기록이 쓰는 소리 파일 표시 (지울 때 알려 주기 위함) */
    keep(name, on) { try { B.recKeep(String(name), on !== false) } catch (e) { } },
    /** 아직 받아 적지 못한 소리가 폰 안에 남아 있는지 */
    busy() { refreshStt(); return !!sttInfo.busy },
    /** 지금 말소리가 이어지는 중인지 */
    speaking() { refreshStt(); return !!sttInfo.speaking },
    headset() { const now = Date.now(); if (now - headAt > 2000) { headAt = now; try { headVal = !!B.headset() } catch (e) { headVal = false } } return headVal },
    setBackground(on) { on = !!on; if (on !== bgVal) { bgVal = on; B.setBackground(on) } }
  };
  /* 통역 소리를 읽는 동안 알려 줌 → 화면이 꺼져도 끝까지 읽음. 끝났다는 신호는 1.5초 뒤에 (문장 사이에 껐다 켜지 않게) */
  let playVal = false, playT = null;
  NAT.playing = on => {
    clearTimeout(playT);
    if (on) { if (!playVal) { playVal = true; try { B.setPlaying(true) } catch (e) { } } }
    else if (playVal) playT = setTimeout(() => { playVal = false; try { B.setPlaying(false) } catch (e) { } }, 1500);
  };
  /* 폰의 음성 데이터 설치 화면 열기 (고품질 음성 받기) */
  NAT.ttsInstall = () => { try { return !!(B.ttsInstall && B.ttsInstall()) } catch (e) { return false } };
  /* 다른 앱(제미나이 · Claude)으로 넘기기: 글(지시문) · 소리 파일. pkg = 앱 이름표(패키지) */
  let sendSeq = 0;
  const sendReqs = new Map();
  N.onSendAudio = m => { const p = sendReqs.get(m.id); if (!p) return; sendReqs.delete(m.id); if (m.ok) p.res({ how: m.how }); else p.rej(new Error(m.error || '보내지 못했습니다')) };
  NAT.app = {
    /** 글을 그 앱에 바로 넘김. 넘겼으면 true */
    sendText(pkg, text) { try { return !!(B.sendText && B.sendText(String(pkg), String(text))) } catch (e) { return false } },
    /** 그 앱을 엶. 설치되어 있지 않으면 false */
    open(pkg) { try { return !!(B.openApp && B.openApp(String(pkg))) } catch (e) { return false } },
    copy(text) { try { B.copy(String(text)); return true } catch (e) { return false } },
    /** 저장된 소리의 한 구간(au = {f, a, b})을 파일로 만들어 그 앱에 넘김 → {how: 'app' | 'menu'} */
    sendAudio(pkg, au, text) {
      return new Promise((res, rej) => {
        if (!B.sendAudio) return rej(new Error('이 앱 버전에서는 안 됩니다'));
        const id = ++sendSeq; sendReqs.set(id, { res, rej });
        try { B.sendAudio(id, String(pkg), String(au.f), String(Math.max(0, au.a - 2400)), String(au.b + 2400), String(text)) } catch (e) { sendReqs.delete(id); rej(e) }
      });
    }
  };
  let sidSeq = 0;
  const sessions = new Map();
  class NativeSR {
    constructor() {
      this.lang = 'ko-KR'; this.continuous = false; this.interimResults = true; this.maxAlternatives = 1;
      this.onresult = this.onerror = this.onend = this.onstart = this.onaudiostart = this.onspeechstart = this.onspeechend = null;
      this._sid = 0; this._finals = []; this._interim = '';
    }
    start() {
      if (this._sid) throw new Error('이미 듣는 중입니다');
      this._sid = ++sidSeq; this._finals = []; this._interim = '';
      sessions.set(this._sid, this);
      this._lastLang = '';
      this._local = this.lang === 'auto' ? NAT.stt.usable() && pref('stt_engine') !== 'google' : NAT.stt.useLocal(this.lang);
      // noDecode: 폰은 받아 적지 않고 말소리 구간(저장된 소리의 자리)만 알려 줌 — Gemini가 그 소리를 직접 들을 때
      if (this._local) { if (this.noDecode && B.lsttStart2) B.lsttStart2(this._sid, this.lang, !!this.continuous, true); else B.lsttStart(this._sid, this.lang, !!this.continuous) }
      else B.sttStart(this._sid, this.lang === 'auto' ? 'ko-KR' : this.lang, !!this.continuous, pref('stt_offline') === '1');
    }
    stop() { if (this._sid) { if (this._local) B.lsttEnd(this._sid, 'stop'); else B.sttStop(this._sid) } }
    abort() { if (this._sid) { if (this._local) B.lsttEnd(this._sid, 'abort'); else B.sttAbort(this._sid) } }
    _results() {
      const list = this._finals.map(t => { const r = [{ transcript: t, confidence: 1 }]; r.isFinal = true; return r });
      if (this._interim) { const r = [{ transcript: this._interim, confidence: 0 }]; r.isFinal = false; list.push(r) }
      return list;
    }
    _fire(name, ev) { const f = this['on' + name]; if (typeof f === 'function') { try { f.call(this, ev || { type: name }) } catch (e) { console.error(e) } } }
  }
  N.onStt = m => {
    const r = sessions.get(m.sid); if (!r) return;
    switch (m.type) {
      case 'start': r._fire('start'); r._fire('audiostart'); break;
      case 'speechstart': r._fire('speechstart'); break;
      case 'speechend': r._fire('speechend'); break;
      case 'partial':
        r._interim = m.text || '';
        r._fire('result', { type: 'result', results: r._results(), resultIndex: r._finals.length });
        break;
      case 'final':
        r._interim = '';
        if (m.text || (m.f && r._local)) {          // 글 없이 소리 자리만 오는 경우도 넘김 (받아 적지 않는 방식)
          m.text = m.text || '';
          if (m.lang) r._lastLang = m.lang;
          if (m.dur) NAT.stt.tone = { db: m.db, hz: m.hz, dur: m.dur, chars: m.text.replace(/\s/g, '').length, at: Date.now() };
          // 이 문장의 소리가 저장된 자리(f 파일의 a~b 표본)와 들린 시각(t0~t1 ms)
          r._lastMeta = m.f ? { f: m.f, a: m.a, b: m.b, t0: m.t0, t1: m.t1, old: !!m.old } : null;   // old = 앞 세션에서 받아 적다 남은 말
          if (r._local) r._finals = [m.text];      // 폰 안 인식: 확정 문장을 하나씩만 넘김 (목록이 길어지지 않으므로 세션을 다시 열 필요가 없음 → 그 사이에 문장이 빠질 일이 없음)
          else r._finals.push(m.text);
          r._fire('result', { type: 'result', results: r._results(), resultIndex: r._finals.length - 1 });
          // 구글 인식: 이어 듣기가 너무 길어지면(문장 6개) 화면 쪽 세션만 새로 시작 → 목록이 끝없이 길어지지 않게
          if (!r._local && r.continuous && r._finals.length >= 6 && r._sid) B.sttAbort(r._sid);
        }
        break;
      case 'error': r._fire('error', { type: 'error', error: m.text || 'unknown' }); break;
      case 'end': sessions.delete(m.sid); r._sid = 0; r._fire('end'); break;
    }
  };
  if (NAT.info.stt || sttInfo.lib) { window.SpeechRecognition = NativeSR; window.webkitSpeechRecognition = NativeSR; }

  /* ── 2) 목소리: 웹의 speechSynthesis 모양 그대로 ── */
  let uidSeq = 0, voices = [];
  const utt = new Map();
  const loadVoices = () => {
    try { voices = JSON.parse(B.ttsVoices()).map(v => ({ name: v.name, lang: v.lang, localService: !!v.localService, quality: v.q || 0, default: false, voiceURI: v.name })) } catch (e) { voices = [] }
  };
  class Utter {
    constructor(text) { this.text = String(text == null ? '' : text); this.lang = ''; this.rate = 1; this.pitch = 1; this.volume = 1; this.voice = null; this.onstart = this.onend = this.onerror = this.onboundary = null }
  }
  const synth = {
    speaking: false, pending: false, paused: false, onvoiceschanged: null,
    getVoices() { return voices },
    speak(u) { const id = ++uidSeq; utt.set(id, u); this.pending = true; B.ttsSpeak(id, u.text, u.lang || '', Number(u.rate) || 1, (u.voice && u.voice.name) || '', Number(u.volume) > 0 ? Number(u.volume) : 1) },
    cancel() { utt.clear(); this.speaking = false; this.pending = false; B.ttsCancel() },
    pause() { }, resume() { }
  };
  N.onTts = m => {
    const u = utt.get(m.id); if (!u) return;
    if (m.type === 'start') { synth.speaking = true; synth.pending = utt.size > 1; if (u.onstart) u.onstart({ type: 'start', utterance: u }) }
    else if (m.type === 'boundary') { if (u.onboundary) u.onboundary({ type: 'boundary', charIndex: m.charIndex, name: 'word' }) }
    else {
      utt.delete(m.id); synth.speaking = false; synth.pending = utt.size > 0;
      const f = m.type === 'error' ? u.onerror : u.onend;
      if (f) f({ type: m.type, utterance: u, error: m.type === 'error' ? 'synthesis-failed' : undefined });
    }
  };
  N.onVoices = () => { loadVoices(); if (synth.onvoiceschanged) synth.onvoiceschanged() };
  loadVoices();
  def(window, 'speechSynthesis', synth);
  window.SpeechSynthesisUtterance = Utter;

  /* ── 3) 폰 안 번역 AI ── */
  let reqSeq = 0, llmState = { engine: false, state: 'idle', error: '', model: '', hasModel: false };
  const reqs = new Map();
  const refresh = () => { try { llmState = JSON.parse(B.llmState()) } catch (e) { } };
  refresh();
  N.onLlm = m => { const p = reqs.get(m.id); if (!p) return; reqs.delete(m.id); if (m.ok) p.res(m.text); else p.rej(new Error(m.error || '폰 AI 오류')) };
  N.onLlmState = s => { llmState = s; if (NAT.onchange) NAT.onchange() };
  N.onModel = m => { refresh(); refreshStt(); if (NAT.onmodel) NAT.onmodel(m) };
  NAT.llm = {
    get state() { return llmState },
    /** 엔진이 앱에 들어 있고 모델 파일도 받아 둔 상태 */
    usable() { return !!(llmState.engine && llmState.hasModel) },
    ensure() { B.llmEnsure() },
    stop() { B.llmStop() },
    chat(body) { return new Promise((res, rej) => { const id = ++reqSeq; reqs.set(id, { res, rej }); B.llmChat(id, JSON.stringify(body)) }) },
    models() { try { return JSON.parse(B.models()) } catch (e) { return [] } },
    download(id) { B.modelDownload(id) },
    cancel(id) { B.modelCancel(id) },
    remove(id) { B.modelDelete(id) },
    select(id) { B.modelSelect(id) },
    add(name, url) { return B.modelAdd(name, url) }
  };

  /* ── 3-1) AI 통역사용 마이크 소리(16kHz PCM, 0.1초 조각, base64) ── */
  NAT.pcm = {
    cb: null, onend: null,
    start(cb, echoCancel) { this.cb = cb; B.pcmStart(!!echoCancel) },
    stop() { this.cb = null; B.pcmStop() }
  };
  N.onPcm = b64 => { if (NAT.pcm.cb) NAT.pcm.cb(b64) };
  N.onPcmEnd = e => { const f = NAT.pcm.onend; if (f) f(e) };

  /* ── 4) 공유·복사·화면 꺼짐 방지·파일 저장 ── */
  def(navigator, 'share', async d => {
    d = d || {};
    const text = [d.text, d.url && !(d.text || '').includes(d.url) ? d.url : ''].filter(Boolean).join('\n');
    B.share(d.title || '여행 통역', text);
  });
  def(navigator, 'clipboard', { writeText: async t => { B.copy(String(t)) }, readText: async () => B.paste() });
  def(navigator, 'wakeLock', {
    request: async () => {
      B.keepAwake(true);
      const s = { released: false, release: async () => { s.released = true; B.keepAwake(false) }, addEventListener() { }, removeEventListener() { } };
      return s;
    }
  });
  async function saveHref(href, name) {
    try {
      const blob = await (await fetch(href)).blob();
      if (!B.saveBegin(name, blob.type || '')) throw new Error('begin');
      const CH = 384 * 1024;
      for (let o = 0; o < blob.size; o += CH) {
        const buf = new Uint8Array(await blob.slice(o, o + CH).arrayBuffer());
        let s = '';
        for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
        if (!B.saveChunk(btoa(s))) throw new Error('chunk');
      }
      if (!B.saveEnd()) throw new Error('end');
      if (NAT.toast) NAT.toast('"' + name + '" 파일을 내려받기(Download) 폴더에 저장했습니다.');
    } catch (e) { if (NAT.toast) NAT.toast('파일을 저장하지 못했습니다.') }
  }
  const origClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () {
    if (this.hasAttribute('download') && /^(blob:|data:)/.test(this.href)) { saveHref(this.href, this.getAttribute('download') || 'file'); return }
    return origClick.call(this);
  };
})();
