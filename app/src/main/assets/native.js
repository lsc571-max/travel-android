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
    return;
  }
  try { NAT.info = JSON.parse(B.info()) } catch (e) { }
  const N = window.__nat = {};
  const def = (obj, key, value) => { try { Object.defineProperty(obj, key, { value, configurable: true, writable: true }) } catch (e) { try { obj[key] = value } catch (e2) { } } };

  /* ── 1) 음성 인식: 웹의 SpeechRecognition 모양 그대로 ── */
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
      let off = false; try { off = localStorage.getItem('stt_offline') === '1' } catch (e) { }
      B.sttStart(this._sid, this.lang, !!this.continuous, off);
    }
    stop() { if (this._sid) B.sttStop(this._sid) }
    abort() { if (this._sid) B.sttAbort(this._sid) }
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
        if (m.text) {
          r._finals.push(m.text);
          r._fire('result', { type: 'result', results: r._results(), resultIndex: r._finals.length - 1 });
          // 이어 듣기가 너무 길어지면(문장 6개) 한 번 끊고 새로 시작하게 함 → 화면 쪽 목록이 끝없이 길어지지 않게
          if (r.continuous && r._finals.length >= 6 && r._sid) B.sttAbort(r._sid);
        }
        break;
      case 'error': r._fire('error', { type: 'error', error: m.text || 'unknown' }); break;
      case 'end': sessions.delete(m.sid); r._sid = 0; r._fire('end'); break;
    }
  };
  if (NAT.info.stt) { window.SpeechRecognition = NativeSR; window.webkitSpeechRecognition = NativeSR; }

  /* ── 2) 목소리: 웹의 speechSynthesis 모양 그대로 ── */
  let uidSeq = 0, voices = [];
  const utt = new Map();
  const loadVoices = () => {
    try { voices = JSON.parse(B.ttsVoices()).map(v => ({ name: v.name, lang: v.lang, localService: !!v.localService, default: false, voiceURI: v.name })) } catch (e) { voices = [] }
  };
  class Utter {
    constructor(text) { this.text = String(text == null ? '' : text); this.lang = ''; this.rate = 1; this.pitch = 1; this.volume = 1; this.voice = null; this.onstart = this.onend = this.onerror = this.onboundary = null }
  }
  const synth = {
    speaking: false, pending: false, paused: false, onvoiceschanged: null,
    getVoices() { return voices },
    speak(u) { const id = ++uidSeq; utt.set(id, u); this.pending = true; B.ttsSpeak(id, u.text, u.lang || '', Number(u.rate) || 1, (u.voice && u.voice.name) || '') },
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
  N.onModel = m => { refresh(); if (NAT.onmodel) NAT.onmodel(m) };
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
