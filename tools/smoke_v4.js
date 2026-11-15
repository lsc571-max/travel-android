// 앱 화면 검사: (1) 브라우저 모드(브리지 없음) (2) 안드로이드 모드(가짜 브리지)
const { JSDOM, VirtualConsole } = require('jsdom');
const fs = require('fs'), path = require('path');
const dir = process.argv[2], mode = process.argv[3] || 'web';
let html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
const nativeJs = fs.readFileSync(path.join(dir, 'native.js'), 'utf8');
html = html.replace('<script src="native.js"></script>', '<script>' + nativeJs + '</script>');
const errors = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => errors.push('jsdomError: ' + (e.detail?.stack || e.message)));
vc.on('error', e => errors.push('console.error: ' + (e?.stack || e)));
const fake = { sttModel: false, lsessions: [], lends: [], head: false, bg: [], pcm: [], ws: [], hasModel: false, llm: 'idle', chatFail: false, sessions: [], spoken: [], shared: [], saved: [], chats: [], online: true };
const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://app.travel.local/index.html', virtualConsole: vc,
  beforeParse(w) {
    w.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {} });
    w.scrollTo = () => {};
    w.Element.prototype.scrollIntoView = () => {};
    w.Element.prototype.scrollTo = () => {};
    Object.defineProperty(w.navigator, 'onLine', { get: () => fake.online, configurable: true });
    w.fetch = async (url) => {
      const u = String(url);
      if (u.includes('-tts')) { fake.tts = (fake.tts || 0) + 1; return { ok: true, status: 200, json: async () => ({ candidates: [{ content: { parts: [{ inlineData: { mimeType: 'audio/wav', data: 'UklGRgAAAAA=' } }] } }] }), clone() { return this; } }; }
      if (u.includes('mymemory')) return { ok: true, status: 200, json: async () => ({ responseStatus: 200, responseData: { translatedText: 'FREE-こんにちは' } }), clone() { return this; } };
      return { ok: false, status: 500, json: async () => ({}), clone() { return this; } };
    };
    w.URL.createObjectURL = () => 'blob:fake'; w.URL.revokeObjectURL = () => {};
    w.Audio = class { constructor(u) { this.src = u; fake.audio = (fake.audio || 0) + 1; } play() { setTimeout(() => { this.onplaying?.(); setTimeout(() => this.onended?.(), 5); }, 5); return Promise.resolve(); } pause() {} };
    w.AudioContext = class { constructor() { this.currentTime = 0; this.destination = {}; } createBuffer(c, n) { return { duration: n / 24000, getChannelData: () => new Float32Array(n) }; } resume() {} createBufferSource() { return { connect() {}, start() { fake.played = (fake.played || 0) + 1; } }; } close() {} };
    w.WebSocket = class { constructor(u) { this.url = u; this.sent = []; this.readyState = 0; fake.ws.push(this); setTimeout(() => { this.readyState = 1; this.onopen?.(); }, 2); } send(m) { const j = JSON.parse(m); this.sent.push(j); if (j.setup && !fake.noSetup) setTimeout(() => this.onmessage?.({ data: JSON.stringify({ setupComplete: {} }) }), 1); } close() { this.readyState = 3; } };
    w.AbortSignal.timeout = w.AbortSignal.timeout || (() => new w.AbortController().signal);
    w.addEventListener('error', e => errors.push('window error: ' + (e.error?.stack || e.message)));
    w.addEventListener('unhandledrejection', e => errors.push('unhandled: ' + (e.reason?.stack || e.reason)));
    if (mode === 'web') {
      w.SpeechSynthesisUtterance = function (t) { this.text = t; };
      w.speechSynthesis = { getVoices: () => [], cancel() {}, resume() {}, speaking: false, pending: false, paused: false,
        speak(u) { setTimeout(() => { u.onstart?.(); setTimeout(() => u.onend?.(), 5); }, 5); } };
      class SR { start() { w.__sr = this; setTimeout(() => { this.onstart?.(); this.onaudiostart?.(); }, 1); } stop() { setTimeout(() => this.onend?.(), 1); } abort() { setTimeout(() => this.onend?.(), 1); } }
      w.webkitSpeechRecognition = SR;
      return;
    }
    const nat = (fn, o) => setTimeout(() => w.__nat && w.__nat[fn](o), 1);
    const st = () => JSON.stringify({ engine: true, state: fake.llm, error: '', model: fake.hasModel ? (fake.sel || 'gemma4-e4b') : '', hasModel: fake.hasModel });
    const models = () => [{ id: 'gemma4-e4b', type: 'chat', name: 'Gemma 4 (4B) · 정확', note: '권장', approx: 5150e6, selected: fake.hasModel && fake.sel !== 'hymt2-q4', state: fake.dl ? 'downloading' : fake.hasModel ? 'ready' : 'none', done: fake.hasModel ? 5150e6 : 0, total: 5150e6 },
      { id: 'hymt2-q4', type: 'gguf', name: 'Hy-MT2 1.8B · 번역 전용', note: '빠름', approx: 1130e6, selected: fake.sel === 'hymt2-q4', state: fake.hy ? 'ready' : 'none', done: fake.hy ? 1130e6 : 0, total: 1130e6 },
      { id: 'whisper-turbo', kind: 'stt', type: 'whisper', name: 'Whisper turbo · 정확', note: '권장', approx: 1040e6, selected: fake.sttModel, state: fake.sttModel ? 'ready' : 'none', done: fake.sttModel ? 1040e6 : 0, total: 1040e6 }].map(m => ({ kind: 'mt', langs: '', custom: false, ...m }));
    w.AndroidBridge = {
      info: () => JSON.stringify({ version: '1.0', sdk: 34, stt: true, sttOffline: false, llmEngine: true }),
      sttStart(sid, lang, cont, off) { fake.sessions.push({ sid, lang, cont, off }); fake.sid = sid; nat('onStt', { sid, type: 'start' }); },
      sttStop(sid) { nat('onStt', { sid, type: 'end' }); },
      sttAbort(sid) { nat('onStt', { sid, type: 'end' }); },
      ttsVoices: () => JSON.stringify([{ name: 'ko-KR-a', lang: 'ko-KR', localService: true }, { name: 'ja-JP-a', lang: 'ja-JP', localService: true }]),
      ttsSpeak(id, text, lang, rate, voice, volume) { fake.spoken.push({ id, text, lang, rate, voice, volume }); nat('onTts', { id, type: 'start', charIndex: 0 }); setTimeout(() => w.__nat.onTts({ id, type: 'end', charIndex: 0 }), 8); },
      ttsCancel() {},
      llmState: st,
      llmEnsure() { if (fake.hasModel) { fake.llm = 'ready'; nat('onLlmState', JSON.parse(st())); } },
      llmStop() { fake.llm = 'idle'; nat('onLlmState', JSON.parse(st())); },
      llmChat(id, body) { const b = JSON.parse(body); fake.chats.push(b); if (fake.chatFail) nat('onLlm', { id, ok: false, error: '엔진 오류' }); else { const sys = b.messages[0].role === 'system' ? b.messages[0].content : '', inp = (b.messages.at(-1).content || '').replace(/^\[입력\] /, ''); nat('onLlm', { id, ok: true, text: /JSON/.test(sys) ? (fake.badJson ? '사출금형, 보압' : '```json\n' + JSON.stringify({ s: inp.replace(/어 |음 /g, ''), t: 'LOCAL-こんにちは' }) + '\n```') : 'LOCAL-こんにちは' }); } },
      models: () => JSON.stringify(models()),
      modelDownload(id) { if (id.startsWith('whisper')) { setTimeout(() => { fake.sttModel = true; w.__nat.onModel({ id, kind: 'stt', state: 'ready', done: 375e6, total: 375e6, msg: '' }); }, 30); return; } fake.dl = true; nat('onModel', { id, state: 'downloading', done: 100, total: 1130e6, msg: '' }); setTimeout(() => { fake.dl = false; fake.hasModel = true; w.__nat.onModel({ id, state: 'ready', done: 1130e6, total: 1130e6, msg: '' }); }, 30); },
      modelCancel() {}, modelDelete(id) { fake.hasModel = false; fake.llm = 'idle'; nat('onModel', { id, state: 'none', done: 0, total: 0, msg: '' }); }, modelSelect(id) { if (!id.startsWith('whisper')) fake.sel = id; this.llmEnsure(); },
      modelAdd: () => '',
      share(t, x) { fake.shared.push(x); }, copy() {}, paste: () => '붙여넣은 글',
      lsttInfo: () => JSON.stringify({ lib: true, usable: fake.sttModel, model: fake.sttModel ? 'whisper-turbo' : '', langs: '', running: false, busy: !!fake.sttBusy }),
      lsttStart(sid, lang, cont) { fake.lsessions.push({ sid, lang, cont }); fake.sid = sid; nat('onStt', { sid, type: 'start' }); },
      lsttEnd(sid, how) { fake.lends.push(how); if (fake.holdEnd && how === 'stop') { fake.heldSid = sid; return; } nat('onStt', { sid, type: 'end' }); },
      pcmStart(aec) { fake.pcm.push('start:' + aec); }, pcmStop() { fake.pcm.push('stop'); },
      headset: () => fake.head, setBackground(on) { fake.bg.push(on); }, setPlaying(on) { (fake.play = fake.play || []).push(on); },
      saveBegin: () => true, saveChunk: () => true, saveEnd: () => true, keepAwake() {}, openUrl() {}
    };
  }
});
const w = dom.window, d = w.document;
const ev = s => w.eval(s);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const step = async (name, fn) => { try { await fn(); await sleep(30); console.log('ok   ', name); } catch (e) { errors.push(name + ': ' + e.message); console.log('FAIL ', name, e.message); } };
const need = (c, m) => { if (!c) throw Error(m); };
const sttFinal = (text) => { w.__nat.onStt({ sid: fake.sid, type: 'partial', text: text.slice(0, 3) }); w.__nat.onStt({ sid: fake.sid, type: 'final', text }); };
(async () => {
  const P = t => w.__nat.onStt({ sid: fake.sid, type: 'partial', text: t });
  const F = (t, o = {}) => w.__nat.onStt({ sid: fake.sid, type: 'final', text: t, lang: 'en', db: -20, hz: 120, dur: 2, ...o });
  const modeTo = async m => { for (let i = 0; i < 3 && ev('state.mode') !== m; i++) { d.querySelector('.mode').click(); await sleep(20); } need(ev('state.mode') === m, 'mode ' + ev('state.mode')); };
  await step('home renders (A3)', () => { need(d.querySelector('.home'), 'no home'); need(d.querySelector('.home-corner').textContent.startsWith('A10'), 'version ' + d.querySelector('.home-corner').textContent); need(mode !== 'app' || !d.querySelector('.install-go'), 'install band shown'); });
  if (mode === 'app') {
    await step('before model: no engine yet, clear label', () => { need(ev('NAT.on') === true && typeof ev('SR') === 'function', 'polyfills'); need(ev('localReady()') === false && ev('engineChoices().join()') === 'free', 'choices ' + ev('engineChoices().join()')); need(/무료 번역기/.test(ev('engLabel()')), ev('engLabel()')); });
    await step('first-run offer → download both → auto link', async () => { await sleep(1000); const box = d.querySelector('.confirm-box'); need(box && /Gemma 4/.test(box.textContent) && /Whisper turbo/.test(box.textContent), 'offer dialog ' + box?.textContent.slice(0, 80)); [...box.querySelectorAll('button')].find(b => b.textContent === '지금 받기').click(); await sleep(800); need(fake.hasModel && fake.sttModel, 'downloaded'); need(ev('engine()') === 'local' && ev('localReady()'), 'engine'); need(ev('NAT.stt.usable()') === true, 'stt usable'); });
    await step('main screen: engine label, AI chips on one row, no fullscreen/offline banner', async () => { d.querySelector('.home').click(); await sleep(30); need(/폰 AI/.test(d.querySelector('.ai-state').textContent), d.querySelector('.ai-state').textContent); need(d.querySelectorAll('.ai-row .ai-chip').length === 2, 'chips'); fake.online = false; ev('render()'); need(!d.querySelector('.offline-banner'), 'banner'); fake.online = true; ev('render()'); });
    await step('conversation: text → phone AI, shows chars·seconds', async () => { await ev("consume('안녕하세요.','ko',{fromText:true})"); await sleep(120); need(ev('state.items[0].translation') === 'LOCAL-こんにちは' && ev('state.items[0].trMode') === 'local', JSON.stringify(ev('state.items[0]'))); need(/\d+자 · [\d.]+초/.test(d.querySelector('#transcript').textContent), 'metrics: ' + d.querySelector('#transcript').textContent.slice(0, 120)); });
    await step('glossary terms go into the phone AI prompt', async () => { ev("refs.unshift({id:777,gid:'base',kind:'용어',title:'시험',terms:['보압|고압 → '+active().code+': HOLDP'],text:'',sum:'',on:true,prio:false});saveRefs()"); await ev("consume('보압을 올려 주세요.','ko',{fromText:true})"); await sleep(120); const c = fake.chats.at(-1).messages.map(m => m.content).join('\n'); need(/보압→HOLDP/.test(c) && /\[입력\] 보압을 올려 주세요/.test(c), c.slice(-300)); });
    await step('conversation mic (ko, manual): local STT, interim shown, one row on stop', async () => { await sleep(900); const n = ev('state.items.length'); ev("pressTalk('ko')"); await sleep(40); need(ev('state.mic') && fake.lsessions.at(-1).lang === 'ko-KR' && fake.sessions.length === 0, 'local session'); P('화장실은'); await sleep(20); need(/화장실/.test(ev('state.interim')), 'interim'); F('화장실은 어디에 있나요', { lang: 'ko' }); await sleep(20); ev("pressTalk('ko')"); await sleep(500); need(ev('state.items.length') === n + 1 && ev('state.items.at(-1).original') === '화장실은 어디에 있나요', JSON.stringify(ev('state.items.at(-1).original'))); });
    await step('conversation mic (auto): language detected by the phone', async () => { await sleep(900); const n = ev('state.items.length'); ev("pressTalk('auto')"); await sleep(40); need(fake.lsessions.at(-1).lang === 'auto', JSON.stringify(fake.lsessions.at(-1))); F('Thank you very much', { lang: ev('active().code').split('-')[0] }); await sleep(700); need(ev('state.items.length') === n + 1 && ev('state.items.at(-1).source') === ev('active().code'), 'source ' + ev('state.items.at(-1).source')); ev("pressTalk('ko')"); await sleep(80); need(!ev('state.mic'), 'off'); });
    await step('follows speaker volume/speed/gender', async () => { ev("voicesG[active().code+'|m']='ja-JP-a'"); await sleep(900); const s0 = fake.spoken.length; ev("pressTalk('ko')"); await sleep(40); F('조용히 말합니다', { lang: 'ko', db: -30, dur: 2 }); await sleep(20); ev("pressTalk('ko')"); await sleep(700); ev("pressTalk('ko')"); await sleep(40); F('크게 빨리 말합니다 아주 크게', { lang: 'ko', db: -14, dur: 1 }); await sleep(20); ev("pressTalk('ko')"); await sleep(800); const sp = fake.spoken.slice(s0); need(sp.length >= 2, 'spoken ' + sp.length); const a = sp[0], b = sp.at(-1); need(b.volume > a.volume && b.rate > a.rate, 'vol ' + a.volume + '→' + b.volume + ' rate ' + a.rate + '→' + b.rate); need(b.voice === 'ja-JP-a', 'voice ' + b.voice); });
    await step('A4: phone AI cleans the heard Korean, then translates (one call), uses 자료·문장 서랍', async () => { ev("savedSents.push({o:'금형을 열어서 확인해 주세요',t:'SAVED-JA',s:'ko',tg:active().code,at:1});refs.unshift({id:778,gid:'base',kind:'자료',title:'사출 수업',terms:['이젝터 핀'],text:'',sum:'사출금형 수업 자료 요약',on:true,prio:false})"); const n = ev('state.items.length'); await ev("consume('어 이젝터 핀이 부러져서 음 금형을 열어서 확인해 봐야 합니다','ko',{fromMic:true,noMerge:true})"); await sleep(250); const e = JSON.parse(ev('JSON.stringify(state.items.at(-1))')), c = fake.chats.at(-1).messages.map(m => m.content).join('\n'); need(ev('state.items.length') === n + 1 && e.translation === 'LOCAL-こんにちは', 'translation ' + e.translation); need(e.original === '이젝터 핀이 부러져서 금형을 열어서 확인해 봐야 합니다', 'cleaned original: ' + e.original); need(fake.chats.at(-1).chat_template_kwargs?.enable_thinking === false, 'thinking must be off'); need(/\[배경\] 사출 수업: 사출금형 수업 자료 요약/.test(c) && /금형을 열어서 확인해 주세요 ⇒ SAVED-JA/.test(c) && /답하지 말고/.test(c), 'hints: ' + c.slice(-400)); });
    await step('A4: nonsense from the model is rejected (keeps what was said)', async () => { fake.badJson = true; await ev("consume('혹시 이 근처에 맛있는 식당 추천해 주실 수 있나요','ko',{fromMic:true,noMerge:true})"); await sleep(300); fake.badJson = false; const e = JSON.parse(ev('JSON.stringify(state.items.at(-1))')); need(e.original === '혹시 이 근처에 맛있는 식당 추천해 주실 수 있나요' && e.translation === 'LOCAL-こんにちは', JSON.stringify(e).slice(0, 200)); });
    await step('A4: conversation mode keeps listening with the screen off; 5-minute idle rule', async () => { await sleep(900); ev("pressTalk('ko')"); await sleep(40); need(ev('bgListen()') === true, 'bgListen in conversation'); Object.defineProperty(d, 'hidden', { get: () => true, configurable: true }); d.dispatchEvent(new w.Event('visibilitychange')); await sleep(30); need(ev('state.mic'), 'mic survived'); Object.defineProperty(d, 'hidden', { get: () => false, configurable: true }); d.dispatchEvent(new w.Event('visibilitychange')); ev("pressTalk('ko')"); await sleep(80); need(/5분 동안 말소리가 없어/.test(ev('activity.toString()')) && /300000/.test(ev('activity.toString()')), 'idle'); });
    await step('A5: reading aloud continues when the screen turns off (mic off)', async () => { need(!ev('state.mic'), 'mic should be off'); ev("speak('こんにちは。さようなら。','ja')"); await sleep(3); need(fake.play && fake.play.at(-1) === true, 'playing flag ' + JSON.stringify(fake.play)); Object.defineProperty(d, 'hidden', { get: () => true, configurable: true }); d.dispatchEvent(new w.Event('visibilitychange')); need(ev('outBusy') === true, 'speech was stopped by screen off'); Object.defineProperty(d, 'hidden', { get: () => false, configurable: true }); d.dispatchEvent(new w.Event('visibilitychange')); await sleep(1900); need(ev('outBusy') === false && fake.play.at(-1) === false, 'ended ' + JSON.stringify(fake.play)); });
    await step('A6: a short phrase written many times by the recognizer is collapsed to one', async () => { need(ev("collapseRepeats('안녕하세요, 안녕하세요, 안녕하세요, 안녕하세요, 안녕하세요.')") === '안녕하세요', ev("collapseRepeats('안녕하세요, 안녕하세요, 안녕하세요, 안녕하세요, 안녕하세요.')")); need(ev("collapseRepeats('네, 네. 알겠습니다')") === '네, 네. 알겠습니다', 'twice stays'); need(ev("collapseRepeats('감사합니다 정말 감사합니다 정말 감사합니다 정말 잘 부탁드립니다')") === '감사합니다 정말 잘 부탁드립니다', ev("collapseRepeats('감사합니다 정말 감사합니다 정말 감사합니다 정말 잘 부탁드립니다')")); await sleep(900); const n = ev('state.items.length'); ev("pressTalk('ko')"); await sleep(40); F('안녕하세요, 안녕하세요, 안녕하세요, 안녕하세요, 안녕하세요', { lang: 'ko' }); await sleep(20); ev("pressTalk('ko')"); await sleep(500); need(ev('state.items.length') === n + 1 && ev('state.items.at(-1).original') === '안녕하세요', ev('state.items.at(-1).original')); });
    await step('A10 listen mode: one button — 1분(지금 듣기) ↔ 나중에, no 실시간/수동 row', async () => { await modeTo('listen'); ev("store('listen_when','now');render()"); const cb = d.querySelector('.chunk-btn'); need(cb && /1분/.test(cb.textContent) && /지금 듣기/.test(cb.textContent), 'chunk button: ' + (cb && cb.textContent)); need(ev('listenChunk()') === 60 && ev('listenLater()') === false, 'one-minute chunks'); cb.click(); await sleep(10); need(/나중에/.test(d.querySelector('.chunk-btn').textContent) && ev('listenLater()') === true, 'later: ' + d.querySelector('.chunk-btn').textContent); d.querySelector('.chunk-btn').click(); await sleep(10); need(/1분/.test(d.querySelector('.chunk-btn').textContent) && ev('listenLater()') === false, 'back to now'); need(!d.querySelector('.listen-methods'), 'old row'); need(d.querySelectorAll('.ai-row .ai-chip').length === 2, 'chips'); });
    await step('listen + local STT: interim never added, every sentence exactly once (even if said twice)', async () => { await sleep(900); const n = ev('state.listening.length'); ev("pressTalk('foreign')"); await sleep(40); need(ev('state.mic') && fake.lsessions.at(-1).cont === true, 'listening'); P('Hello everyone nice to meet you'); await sleep(2600); P('Hello everyone nice to meet you I am a professor I teach'); await sleep(2600); need(ev('state.listening.length') === n, 'interim became a row'); F('Hello everyone nice to meet you I am a professor'); await sleep(100); P('I teach mold'); await sleep(2600); F('I teach mold design'); await sleep(100); F('I teach mold design'); await sleep(100); need(/Hello everyone/.test(ev('state.interim')), 'live text: ' + ev('state.interim')); ev("pressTalk('foreign')"); await sleep(1800); const rows = JSON.parse(ev('JSON.stringify(state.listening.slice(' + n + ').map(e=>e.original))')), all = rows.join(' | '); need(rows.length === 1, 'rows: ' + all); need((all.match(/Hello everyone/g) || []).length === 1, 'duplicate: ' + all); need((all.match(/I teach mold design/g) || []).length === 2, 'said twice must stay twice: ' + all); need(!/I teach mold(?! design)/.test(all), 'interim leaked: ' + all); });
    await step('listen: screen off keeps listening (local STT)', async () => { await sleep(900); const n = ev('state.listening.length'); ev("pressTalk('foreign')"); await sleep(40); need(ev('bgListen()') === true && fake.bg.at(-1) === true, 'bg ' + fake.bg.join()); Object.defineProperty(d, 'hidden', { get: () => true, configurable: true }); d.dispatchEvent(new w.Event('visibilitychange')); await sleep(30); need(ev('state.mic'), 'mic survived'); F('Where is the station'); await sleep(100); Object.defineProperty(d, 'hidden', { get: () => false, configurable: true }); d.dispatchEvent(new w.Event('visibilitychange')); ev("pressTalk('foreign')"); await sleep(1800); need(ev('state.listening.length') === n + 1 && /Where is the station/.test(ev('state.listening.at(-1).original')), 'row ' + ev('state.listening.length')); need(fake.bg.at(-1) === false, 'bg off'); });
    await step('A10: saved sound — each row knows where its sound is, 🎧 plays it', async () => {
      await sleep(900); const n = ev('state.listening.length'), T = Date.now() - 5000; ev("pressTalk('foreign')"); await sleep(40);
      F('Good morning everyone.', { f: 'L20261115-090000.pcm', a: 16000, b: 48000, t0: T, t1: T + 2000 }); await sleep(60);
      F('Today we talk about molds.', { f: 'L20261115-090000.pcm', a: 60000, b: 100000, t0: T + 3000, t1: T + 5500 }); await sleep(60);
      ev("pressTalk('foreign')"); await sleep(1800);
      const e = JSON.parse(ev('JSON.stringify(state.listening.at(-1))'));
      need(ev('state.listening.length') === n + 1 && /Good morning everyone\. Today we talk about molds\./.test(e.original), 'row: ' + JSON.stringify(e));
      need(e.au && e.au.f === 'L20261115-090000.pcm' && e.au.a === 16000 && e.au.b === 100000 && e.au.t0 === T && e.au.t1 === T + 5500 && e.heardAt === T + 5500, 'sound place: ' + JSON.stringify(e.au));
      const rb = [...d.querySelectorAll('.o-rec')].at(-1); need(rb, 'no 🎧 button'); rb.click();
      need(/\/rec\/L20261115-090000\.pcm\?a=11200&b=104800$/.test(ev('recAudio&&recAudio.src') || ''), 'plays: ' + ev('recAudio&&recAudio.src'));
      [...d.querySelectorAll('.o-rec')].at(-1).click(); need(ev('recAudio') === null, 'second press stops');
      [...d.querySelectorAll('.o-rec')].at(-1).click(); await sleep(60); need(ev('recAudio') === null && ev('recAudioEntry') === null, 'cleared when the sound ends');
    });
    await step('A10: chunks are cut by when the sound was heard (a late burst of sentences still becomes one-minute chunks)', async () => {
      await sleep(900); const n = ev('state.listening.length'), T = Date.now() - 200000, f = 'L20261115-091000.pcm'; ev("pressTalk('foreign')"); await sleep(40);
      F('First part of the talk.', { f, a: 0, b: 480000, t0: T, t1: T + 30000 }); await sleep(30);
      F('Second part of the talk.', { f, a: 480000, b: 990000, t0: T + 30500, t1: T + 62000 }); await sleep(600);   // 1분 넘음 + 문장 끝 → 끊음
      need(ev('state.listening.length') === n + 1, 'one-minute chunk not cut: ' + (ev('state.listening.length') - n));
      F('Third part.', { f, a: 990000, b: 1100000, t0: T + 63000, t1: T + 70000 }); await sleep(30);
      F('After a long pause.', { f, a: 1100000, b: 1200000, t0: T + 90000, t1: T + 95000 }); await sleep(100);   // 앞 말과 20초 떨어짐 → 앞 묶음을 먼저 끊음
      need(ev('state.listening.length') === n + 2 && /^Third part\.$/.test(ev('state.listening.at(-1).original')), 'quiet gap not cut: ' + ev('JSON.stringify(state.listening.slice(' + n + ').map(e=>e.original))'));
      ev("pressTalk('foreign')"); await sleep(1800);
      const rows = JSON.parse(ev('JSON.stringify(state.listening.slice(' + n + ').map(e=>[e.original,e.au&&e.au.a,e.au&&e.au.b]))'));
      need(rows.length === 3 && rows[0][0] === 'First part of the talk. Second part of the talk.' && rows[0][1] === 0 && rows[0][2] === 990000 && rows[2][0] === 'After a long pause.' && rows[2][1] === 1100000, JSON.stringify(rows));
    });
    await step('A10: stopping waits for sentences still being written down (no 5-second cut-off)', async () => {
      await sleep(900); const n = ev('state.listening.length'); ev("pressTalk('foreign')"); await sleep(40);
      F('The beginning of the last part.'); await sleep(60);
      fake.holdEnd = true; ev("pressTalk('foreign')"); await sleep(1300); need(!ev('state.mic') && fake.heldSid, 'stopping');
      await sleep(5600);                                  // 예전에는 5초 뒤 포기했음
      need(ev('state.listening.length') === n, 'gave up before the phone finished');
      need(/받아쓰기 처리 중/.test(d.querySelector('#drainStatus')?.textContent || ''), 'status: ' + (d.querySelector('#drainStatus')?.textContent || ''));
      w.__nat.onStt({ sid: fake.heldSid, type: 'final', text: 'And the very end of it.', lang: 'en', db: -20, hz: 120, dur: 2 }); await sleep(30);
      w.__nat.onStt({ sid: fake.heldSid, type: 'end' }); fake.holdEnd = false; fake.heldSid = 0; await sleep(400);
      need(ev('state.listening.length') === n + 1 && ev('state.listening.at(-1).original') === 'The beginning of the last part. And the very end of it.', 'tail lost: ' + ev('state.listening.at(-1).original'));
    });
    await step('A10: 나중에 듣기 prepares the translation silently; 지금 듣기 reads it', async () => {
      await sleep(900); ev("store('listen_when','later');render()"); const n = ev('state.listening.length'), s0 = fake.spoken.length; ev("pressTalk('foreign')"); await sleep(40);
      F('This is for later.'); await sleep(60); ev("pressTalk('foreign')"); await sleep(2200);
      const e = JSON.parse(ev('JSON.stringify(state.listening.at(-1))'));
      need(ev('state.listening.length') === n + 1 && e.later === true && e.translation && !/번역 중/.test(e.translation), 'row: ' + JSON.stringify(e));
      need(fake.spoken.length === s0, 'read aloud in later mode');
      ev("store('listen_when','now');render()"); ev("pressTalk('foreign')"); await sleep(40); F('This is for now.'); await sleep(60); ev("pressTalk('foreign')"); await sleep(2200);
      need(fake.spoken.length > s0 && !ev('state.listening.at(-1).later'), 'not read in now mode');
    });
    await step('A10: reads faster when the interpretation falls behind', async () => {
      const r = k => ev(`(()=>{const e={heardAt:Date.now()-${k}*1000};state.listening.push(e);const m=state.mic,md=state.mode;state.mic=true;state.mode='listen';const v=lagRate(e);state.mic=m;state.mode=md;state.listening.pop();return v})()`);
      need(r(60) === 1 && r(130) === 1.2 && r(200) === 1.35 && r(300) === 1.5, [r(60), r(130), r(200), r(300)].join());
      need(ev('lagRate({heardAt:Date.now()-300000})') === 1, 'only while listening');
    });
    await step('record mode screen opens (kept from V4)', async () => { await modeTo('record'); need(d.querySelector('.screen.record'), 'record screen'); await modeTo('conversation'); });
    await step('earphones keep the mic open while speaking', async () => { need(ev('earOn()') === false, 'no headset'); fake.head = true; await sleep(2100); need(ev('earOn()') === true, 'headset'); fake.head = false; await sleep(2100); });
    await step('settings: 번역 AI tab + V4 advanced items kept', async () => { ev('openSettings()'); const tabs = [...d.querySelectorAll('.set-tabs button')]; need(tabs.length === 4 && tabs[1].textContent === '번역 AI', tabs.map(b => b.textContent).join()); tabs[1].click(); await sleep(30); let t = d.querySelector('#app').textContent; need(/폰 안 AI \(끊김 없음\)/.test(t) && /Whisper turbo/.test(t) && /말한 사람 따라 하기/.test(t) && /AI 음성 · AI 통역사/.test(t) && /Gemma 4/.test(t) && /Hy-MT2/.test(t), 'ai sections'); need(/무료 번역기/.test(t), 'free translator chip'); [...d.querySelectorAll('button')].find(b => b.textContent === '시험 번역').click(); await sleep(80); need(/LOCAL-/.test(d.querySelector('.ai-result').textContent), 'test tr'); [...d.querySelectorAll('.set-tabs button')][3].click(); await sleep(30); t = d.querySelector('#app').textContent; need(/키 받으러 가기/.test(t) && /AI 사용량 기록/.test(t) && /무음 빼기/.test(t) && /받아쓰기 정리 기록/.test(t), 'adv items'); ev('closeLayer()'); });
    await step('free translator is back: per-sentence menu and engine button cycle', async () => { if (ev('state.page') !== 'main') d.querySelector('.home')?.click(); d.querySelector('.entry-engine').click(); const m = [...d.querySelectorAll('.entry-mode-menu button')].map(b => b.textContent).join(','); need(m === '폰AI,빠름,균형,정확,무료', m); ev('entryModeMenu?.()'); ev("store('ai_key','AIzaTEST');store('tr_engine','local');render()"); const seen = []; for (let i = 0; i < 5; i++) { d.querySelector('.ai-state').click(); seen.push(ev('currentEntryMode()')); } need(seen.join() === 'fast,balanced,accurate,free,local', seen.join()); ev("store('ai_key','');store('tr_engine','free');render()"); await ev("consume('무료로 번역','ko',{fromText:true})"); await sleep(150); need(ev('state.items.at(-1).translation') === 'FREE-こんにちは' && ev('state.items.at(-1).trMode') === 'free', ev('state.items.at(-1).translation')); ev("store('tr_engine','local');render()"); });
    await step('offline: still translates with phone AI', async () => { fake.online = false; const n = ev('state.items.length'); await ev("consume('물 좀 주세요.','ko',{fromText:true})"); await sleep(120); need(ev('state.items.length') === n + 1 && ev('state.items.at(-1).translation') === 'LOCAL-こんにちは', ev('state.items.at(-1).translation')); fake.online = true; });
    await step('phone AI failure → falls back to the free translator (no key)', async () => { fake.chatFail = true; await ev("consume('계산서 주세요.','ko',{fromText:true})"); await sleep(250); need(ev('state.items.at(-1).translation') === 'FREE-こんにちは' && ev('state.items.at(-1).trMode') === 'free', ev('state.items.at(-1).translation')); fake.chatFail = false; });
    await step('AI voice button → Gemini TTS; off → phone voice', async () => { ev("store('ai_key','');render()"); need(d.querySelectorAll('.ai-chip').length === 2 && !d.querySelector('.ai-chip.on'), 'chips'); ev('toggleAiVoice()'); need(ev("load('ai_voice_on')") !== '1', 'needs key'); ev("store('ai_key','AIzaTEST');toggleAiVoice()"); need(ev("load('ai_voice_on')") === '1', 'on'); const t0 = fake.tts || 0, s0 = fake.spoken.length; ev("speak('こんにちは','ja')"); await sleep(250); need((fake.tts || 0) === t0 + 1, 'tts calls ' + fake.tts); need(fake.audio >= 1, 'audio played'); need(fake.spoken.length === s0, 'phone voice not used'); ev('toggleAiVoice()'); ev("speak('こんにちは','ja')"); await sleep(100); need(fake.spoken.length === s0 + 1, 'phone voice again'); });
    const msg = (ws, sc) => ws.onmessage({ data: JSON.stringify({ serverContent: sc }) });
    const interpMode0 = ev('state.mode');
    await step('A9 interpreter (conversation): Gemini 3.8 Live, one speaker at a time, press again to translate', async () => {
      await modeTo('conversation'); ev("store('interp_conv','live');store('interp_shape_live','0')");
      const n0 = fake.ws.length, p0 = fake.played || 0; ev('startInterp()'); await sleep(30);
      need(ev('!!interp'), 'interp on'); need(fake.ws.length === n0 + 2, 'one connection per direction, got ' + (fake.ws.length - n0));
      const a = fake.ws[n0], b = fake.ws[n0 + 1], sa = a.sent[0].setup, sb = b.sent[0].setup;
      need(sa.model === 'models/gemini-3.8-live' && sa.generationConfig.responseModalities[0] === 'AUDIO' && !sa.generationConfig.translationConfig && sa.realtimeInputConfig.automaticActivityDetection.disabled === true && sa.inputAudioTranscription && sa.outputAudioTranscription, JSON.stringify(sa));
      need(/talks in Korean/.test(sa.systemInstruction.parts[0].text) && /interpreter/.test(sa.systemInstruction.parts[0].text) && /into natural spoken Korean/.test(sb.systemInstruction.parts[0].text), sa.systemInstruction.parts[0].text + ' | ' + sb.systemInstruction.parts[0].text);
      need(fake.pcm.at(-1) === 'start:true', 'pcm');
      w.__nat.onPcm('AAAA'); need(a.sent.length === 1 && b.sent.length === 1, 'no audio before a button is pressed');
      need(d.querySelectorAll('.talk').length === 2, 'no auto button while the interpreter is on');
      ev("pressTalk('ko')"); await sleep(5);
      need(a.sent[1].realtimeInput.activityStart && d.querySelector('.talk.k-ko').classList.contains('on'), 'turn start');
      w.__nat.onPcm('AAAA'); need(a.sent.length === 3 && a.sent[2].realtimeInput.audio.mimeType === 'audio/pcm;rate=16000' && b.sent.length === 1, 'audio only to the chosen direction');
      ev("pressTalk('ko')"); await sleep(5);
      need(a.sent[3].realtimeInput.activityEnd && !d.querySelector('.talk.on'), 'pressing again ends the turn');
      w.__nat.onPcm('AAAA'); need(a.sent.length === 4, 'no audio after the turn');
      const n = ev('state.items.length');
      msg(a, { inputTranscription: { text: '안녕하세요, 여러분 ' } }); msg(a, { inputTranscription: { text: '반갑습니다' } });
      msg(a, { outputTranscription: { text: 'こんにちは、' }, modelTurn: { parts: [{ inlineData: { data: 'AAAAAAAA' } }] } });
      msg(a, { outputTranscription: { text: '皆さん' }, turnComplete: true });
      await sleep(500);
      const e = JSON.parse(ev('JSON.stringify(state.items.at(-1))'));
      need(ev('state.items.length') === n + 1 && e.original === '안녕하세요, 여러분 반갑습니다' && e.translation === 'こんにちは、皆さん' && e.trMode === 'live' && e.source === 'ko', 'heard text added exactly once: ' + JSON.stringify(e));
      need((fake.played || 0) === p0 + 1 && d.querySelector('.ai-chip.live')?.textContent === '🎙 AI 통역사', 'audio/chip ' + d.querySelector('.ai-row').innerHTML.slice(0, 200));
      ev("pressTalk('foreign')"); await sleep(5); need(b.sent[1].realtimeInput.activityStart && d.querySelector('.talk.k-foreign').classList.contains('on'), 'other speaker');
      const ka = a.sent.length; ev("pressTalk('ko')"); await sleep(5); need(b.sent.at(-1).realtimeInput.activityEnd && a.sent.length === ka && !d.querySelector('.talk.on'), 'pressing the other language only ends this turn (its interpretation must be heard first)');
      msg(b, { inputTranscription: { text: 'ありがとう' } }); msg(b, { outputTranscription: { text: '감사합니다' }, modelTurn: { parts: [{ inlineData: { data: 'AAAAAAAA' } }] } }); await sleep(500);
      need((fake.played || 0) === p0 + 2, 'second interpretation played');
      ev("pressTalk('ko')"); await sleep(5); msg(b, { modelTurn: { parts: [{ inlineData: { data: 'AAAAAAAA' } }] } }); need((fake.played || 0) === p0 + 2, 'late sound of the previous turn is not played once someone starts talking'); ev("pressTalk('ko')"); await sleep(5);
      const e2 = JSON.parse(ev('JSON.stringify(state.items.at(-1))'));
      need(ev('state.items.length') === n + 2 && e2.original === 'ありがとう' && e2.translation === '감사합니다' && e2.target === 'ko', JSON.stringify(e2));
      ev('startInterp()'); await sleep(20); need(!ev('!!interp') && fake.pcm.at(-1) === 'stop', 'stopped');
      ev('startInterp()'); await sleep(30); fake.ws.at(-1).onclose({ code: 1008, reason: 'API key not valid' }); await sleep(20);
      need(!ev('!!interp') && /API key not valid/.test(d.querySelector('.ai-note')?.textContent || ''), 'reason shown: ' + d.querySelector('.ai-row').textContent);
    });
    await step('A9: other setup formats are tried, then the translate model if 3.8 Live cannot be used', async () => {
      ev("store('interp_shape','0');store('interp_shape_live','0')"); fake.noSetup = true; const n0 = fake.ws.length;
      ev('startInterp()'); await sleep(20);
      const s0 = fake.ws[n0].sent[0].setup; need(s0.generationConfig && s0.inputAudioTranscription && !s0.responseModalities, 'format 0: ' + JSON.stringify(s0));
      fake.ws[n0].onclose({ code: 1007, reason: 'Invalid JSON payload received. Unknown name' }); await sleep(20);
      const s1 = fake.ws.at(-1).sent[0].setup; need(ev('!!interp') && !s1.generationConfig && s1.responseModalities && s1.inputAudioTranscription, 'format 1: ' + JSON.stringify(s1));
      fake.ws.at(-1).onclose({ code: 1007, reason: 'Invalid JSON payload received.' }); await sleep(20);
      const s2 = fake.ws.at(-1).sent[0].setup; need(s2.generationConfig && !s2.inputAudioTranscription && s2.model === 'models/gemini-3.8-live', 'format 2: ' + JSON.stringify(s2));
      fake.ws.at(-1).onclose({ code: 1008, reason: 'models/gemini-3.8-live is not found' }); await sleep(20);
      const s3 = fake.ws.at(-1).sent[0].setup; need(ev('!!interp') && s3.model === 'models/gemini-3.5-live-translate-preview' && s3.generationConfig.translationConfig.targetLanguageCode && !s3.systemInstruction, 'translate fallback: ' + JSON.stringify(s3));
      fake.noSetup = false; ev('stopInterp()');
      need(ev("gemCfg('gemini-3.8-flash').thinkingConfig.thinkingLevel") === 'low' && ev("gemCfg('gemini-4-argon').thinkingConfig.thinkingLevel") === 'low' && ev("!gemCfg('gemini-3.5-flash-lite').thinkingConfig"), 'balanced model thinks low');
    });
    await step('A9 interpreter (listen): translate model, continuous, pick the direction, no chunk button', async () => {
      ev("store('interp_shape','0')"); await modeTo('listen'); ev("state.listenFrom='foreign'");
      const n0 = fake.ws.length, tgt = ev('liveCode(active().code)'); ev('startInterp()'); await sleep(30);
      need(ev('!!interp') && fake.ws.length === n0 + 1, 'one connection, got ' + (fake.ws.length - n0)); const a = fake.ws[n0], sa = a.sent[0].setup;
      need(sa.model === 'models/gemini-3.5-live-translate-preview' && sa.generationConfig.translationConfig.targetLanguageCode === 'ko' && sa.generationConfig.translationConfig.echoTargetLanguage === false && sa.inputAudioTranscription && !sa.systemInstruction && !sa.realtimeInputConfig, JSON.stringify(sa));
      need(!d.querySelector('.chunk-btn') && d.querySelector('.talk.k-foreign').classList.contains('on'), 'no chunk button, foreign button on');
      w.__nat.onPcm('AAAA'); need(a.sent.length === 2 && a.sent[1].realtimeInput.audio, 'streams right away');
      const n = ev('state.listening.length');
      msg(a, { inputTranscription: { text: '你好，' } }); msg(a, { inputTranscription: { text: '大家好' } });
      msg(a, { outputTranscription: { text: '안녕하세요, ' }, modelTurn: { parts: [{ inlineData: { data: 'AAAAAAAA' } }] } }); msg(a, { outputTranscription: { text: '여러분' }, turnComplete: true });
      msg(a, { inputTranscription: { text: '谢谢' } }); msg(a, { outputTranscription: { text: '감사합니다' } });
      await sleep(500);
      const r = JSON.parse(ev('JSON.stringify(state.listening.slice(-2))'));
      need(ev('state.listening.length') === n + 2 && r[0].original === '你好，大家好' && r[0].translation === '안녕하세요, 여러분' && r[1].original === '谢谢' && r[1].translation === '감사합니다' && r[0].target === 'ko', JSON.stringify(r));
      w.__nat.onPcm('AAAA'); need(a.sent.length === 2, 'speaker: no audio is sent while the interpretation is playing');
      ev('interp.next=0'); // 통역 소리가 다 나온 뒤
      ev("pressTalk('ko')"); await sleep(30);
      const b = fake.ws.at(-1); need(fake.ws.length === n0 + 2 && a.sent.at(-1).realtimeInput.audioStreamEnd === true && b.sent[0].setup.generationConfig.translationConfig.targetLanguageCode === tgt && d.querySelector('.talk.k-ko').classList.contains('on'), 'direction switched: ' + JSON.stringify(b.sent[0]));
      const ka = a.sent.length; w.__nat.onPcm('AAAA'); need(b.sent.at(-1).realtimeInput.audio && a.sent.length === ka, 'audio goes to the new direction only');
      b.onmessage({ data: JSON.stringify({ goAway: { timeLeft: '10s' } }) }); await sleep(30);
      const c = fake.ws.at(-1); need(c !== b && c.sent[0].setup.generationConfig.translationConfig.targetLanguageCode === tgt, 'new connection opened before the server drops the old one');
      w.__nat.onPcm('AAAA'); need(c.sent.at(-1).realtimeInput?.audio, 'audio moved to the new connection');
      c.onclose({ code: 1006, reason: '' }); await sleep(30);
      const c2 = fake.ws.at(-1); need(ev('!!interp') && c2 !== c && c2.sent[0].setup, 'reconnects by itself when the connection drops');
      ev("pressTalk('ko')"); await sleep(10); need(ev('!!interp') && !d.querySelector('.talk.on') && c2.sent.at(-1).realtimeInput.audioStreamEnd === true, 'same button again pauses');
      const k2 = c2.sent.length; w.__nat.onPcm('AAAA'); need(c2.sent.length === k2, 'no audio while paused');
      d.querySelector('.mode').click(); await sleep(20); need(!ev('!!interp'), 'changing the mode turns the interpreter off');
      ev("store('ai_key','')"); await modeTo(interpMode0);
    });
    await step('share goes to the phone share sheet', async () => { ev('shareAll()'); await sleep(10); d.querySelector('.share-pick button').click(); await sleep(30); need(fake.shared.length === 1 && /안녕하세요/.test(fake.shared[0]), 'shared'); });
    await step('delete model → free translator takes over', async () => { ev("NAT.llm.remove('gemma4-e4b')"); await sleep(80); need(ev('localReady()') === false && ev('engine()') === 'free' && /무료 번역기/.test(ev('engLabel()')), ev('engLabel()')); await ev("consume('테스트','ko',{fromText:true})"); await sleep(200); need(ev('state.items.at(-1).translation') === 'FREE-こんにちは', ev('state.items.at(-1).translation')); });
  }
  await step('common screens', async () => { if (ev("state.page") !== 'main') d.querySelector('.home')?.click(); ev("openDrawer('notes')"); ev('closeLayer()'); ev("openDrawer('refs')"); ev('closeLayer()'); ev('openPhrases()'); ev('openText()'); ev('openPhoto()'); ev('closeLayer()'); ev('openSettings()'); ev('closeLayer()'); ev('resetTranscripts();render()'); ev('goHome()'); });
  await sleep(300);
  console.log(errors.length ? '\nERRORS:\n' + errors.join('\n---\n') : '\nNO ERRORS');
  process.exit(errors.length ? 1 : 0);
})();
