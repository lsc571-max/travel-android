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
    try { w.localStorage.setItem('show_init', '1'); for (const k of ['photo', 'text', 'pron', 'retr', 'star', 'big', 'refs', 'engine', 'gemma', 'interp', 'aivoice', 'notes', 'rec']) w.localStorage.setItem('show_' + k, '1'); } catch (e) { }   // 시험은 쓰던 휴대폰처럼 (기능이 모두 보이는 상태)
    w.Element.prototype.scrollIntoView = () => {};
    w.Element.prototype.scrollTo = () => {};
    Object.defineProperty(w.navigator, 'onLine', { get: () => fake.online, configurable: true });
    try { const fi = require('fake-indexeddb'); w.indexedDB = fi.indexedDB; w.IDBKeyRange = fi.IDBKeyRange; } catch (e) { }
    w.fetch = async (url, opt) => {
      const u = String(url);
      if (u.includes('frankfurter') || u.includes('er-api')) { (fake.fx = fake.fx || []).push(u); if (fake.fxFail || (fake.fxFirstFail && u.includes('frankfurter'))) return { ok: false, status: 500, json: async () => ({}) }; return { ok: true, status: 200, json: async () => ({ base: 'USD', rates: { KRW: 1473.4, JPY: 150 } }) }; }
      if (u.includes('gemini-3.5-flash-lite:generateContent') && opt && /OK라고만/.test(opt.body || '')) { fake.keyChecks = (fake.keyChecks || 0) + 1; return fake.keyBad ? { ok: false, status: 400, json: async () => ({ error: { message: 'API key not valid. Please pass a valid API key.' } }) } : { ok: true, status: 200, json: async () => ({ candidates: [{ content: { parts: [{ text: 'OK' }] } }] }) }; }
      if (u.startsWith('blob:')) return { ok: true, status: 200, blob: async () => new w.Blob([new Uint8Array(3000)], { type: 'audio/wav' }) };
      if (u.includes('/rec/')) { (fake.recFetch = fake.recFetch || []).push(u); if (fake.recGone) return { ok: false, status: 404, blob: async () => new w.Blob([]) }; return { ok: true, status: 200, blob: async () => new w.Blob([new Uint8Array(u.includes('raw=1') ? 6400 : 6444)], { type: u.includes('raw=1') ? 'application/octet-stream' : 'audio/wav' }) }; }
      if (u.includes(':generateContent') && !u.includes('-tts') && fake.gem) { const body = JSON.parse(opt.body); (fake.gemBodies = fake.gemBodies || []).push({ u, body }); if (fake.gemDelay) await new Promise(r => setTimeout(r, fake.gemDelay)); if (fake.gemStatus) return { ok: false, status: fake.gemStatus, json: async () => ({ error: { message: fake.gemError, code: fake.gemStatus } }), clone() { return this; } }; const r = fake.gem(body, u); if (!r) return { ok: false, status: 500, json: async () => ({}), clone() { return this; } }; return { ok: true, status: 200, json: async () => ({ candidates: [{ content: { parts: [{ text: JSON.stringify(r) }] } }], usageMetadata: { promptTokenCount: 2000, candidatesTokenCount: 700, thoughtsTokenCount: 100 } }), clone() { return this; } }; }
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
      ttsVoices: () => JSON.stringify(fake.voices || [{ name: 'ko-KR-a', lang: 'ko-KR', localService: true }, { name: 'ja-JP-a', lang: 'ja-JP', localService: true }]),
      ttsInstall() { fake.ttsInstalls = (fake.ttsInstalls || 0) + 1; return true; },
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
      share(t, x) { fake.shared.push(x); }, copy(x) { (fake.copied = fake.copied || []).push(x); }, paste: () => '붙여넣은 글',
      lsttInfo: () => JSON.stringify({ lib: true, usable: fake.sttModel, model: fake.sttModel ? 'whisper-turbo' : '', langs: '', running: false, busy: !!fake.sttBusy }),
      lsttStart(sid, lang, cont) { fake.lsessions.push({ sid, lang, cont }); fake.sid = sid; nat('onStt', { sid, type: 'start' }); },
      lsttStart2(sid, lang, cont, nodec) { fake.lsessions.push({ sid, lang, cont, nodec }); fake.sid = sid; nat('onStt', { sid, type: 'start' }); },
      lsttFile(id, f, a, b, lang) { (fake.files = fake.files || []).push({ f, a, b, lang }); setTimeout(() => nat('onSttFile', fake.fileFail ? { id, ok: false, error: '모델 없음' } : { id, ok: true, text: fake.fileText || 'whisper heard this' }), 5); },
      setMic(p) { (fake.mics = fake.mics || []).push(p); },
      setCapture(s) { (fake.caps = fake.caps || []).push(s); },
      setKeepRec(on) { (fake.keepRecs = fake.keepRecs || []).push(on); },
      sendText(pkg, text) { (fake.sent = fake.sent || []).push({ pkg, text }); return !!fake.appTakesText; },
      openApp(pkg) { (fake.opened = fake.opened || []).push(pkg); return !!fake.appInstalled; },
      sendAudio(id, pkg, f, a, b, text) { (fake.sentAudio = fake.sentAudio || []).push({ pkg, f, a, b, text }); setTimeout(() => nat('onSendAudio', { id, ok: true, how: 'app' }), 5); },
      sendAudios(id, pkg, list, text) { (fake.sentAudios = fake.sentAudios || []).push({ pkg, list: JSON.parse(list), text }); setTimeout(() => nat('onSendAudio', { id, ok: true, how: 'app' }), 5); },
      recFiles: () => JSON.stringify({ files: fake.heard || [], free: 52e9 }),
      recDelete(n) { (fake.dels = fake.dels || []).push(n); fake.heard = (fake.heard || []).map(x => n[0] === 'R' && 'R' + x.id + '.pcm' === n ? { ...x, r: 0 } : x).filter(x => !(n[0] === 'L' && 'L' + x.id + '.pcm' === n)); return true; },
      recKeep(name, on) { (fake.keeps = fake.keeps || []).push(name + ':' + on); },
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
  await step('home renders (A3)', () => { need(d.querySelector('.home'), 'no home'); need(d.querySelector('.home-corner').textContent.startsWith('A24'), 'version ' + d.querySelector('.home-corner').textContent); need(mode !== 'app' || !d.querySelector('.install-go'), 'install band shown'); });
  if (mode === 'app') {
    await step('before model: no engine yet, clear label', () => { need(ev('NAT.on') === true && typeof ev('SR') === 'function', 'polyfills'); need(ev('localReady()') === false && ev('engineChoices().join()') === '' && ev('engine()') === 'none', 'choices ' + ev('engineChoices().join()')); need(/번역기 없음/.test(ev('engLabel()')), ev('engLabel()')); });
    await step('first-run offer → download both → auto link', async () => { await sleep(1000); const box = d.querySelector('.confirm-box'); need(box && /Gemma 4/.test(box.textContent) && /Whisper turbo/.test(box.textContent), 'offer dialog ' + box?.textContent.slice(0, 80)); [...box.querySelectorAll('button')].find(b => b.textContent === '지금 받기').click(); await sleep(800); need(fake.hasModel && fake.sttModel, 'downloaded'); need(ev('engine()') === 'local' && ev('localReady()'), 'engine'); need(ev('NAT.stt.usable()') === true, 'stt usable'); });
    await step('main screen: engine label, AI chips on one row, no fullscreen/offline banner', async () => { d.querySelector('.home').click(); await sleep(30); need(/폰 AI/.test(d.querySelector('.ai-state').textContent), d.querySelector('.ai-state').textContent); need(d.querySelectorAll('.talk-row .ai-col .ai-chip').length === 2 && !d.querySelector('.ai-row'), 'AI chips next to the talk buttons'); need(d.querySelectorAll('.talk').length === 2 && !d.querySelector('.talk.k-auto'), 'no auto button'); need(!d.querySelector('.moon-btn'), 'no dim button'); fake.online = false; ev('render()'); need(!d.querySelector('.offline-banner'), 'banner'); fake.online = true; ev('render()'); });
    await step('conversation: text → phone AI, shows chars·seconds', async () => { await ev("consume('안녕하세요.','ko',{fromText:true})"); await sleep(120); need(ev('state.items[0].translation') === 'LOCAL-こんにちは' && ev('state.items[0].trMode') === 'local', JSON.stringify(ev('state.items[0]'))); need(/\d+자 · [\d.]+초/.test(d.querySelector('#transcript').textContent), 'metrics: ' + d.querySelector('#transcript').textContent.slice(0, 120)); });
    await step('glossary terms go into the phone AI prompt', async () => { ev("refs.unshift({id:777,gid:'base',kind:'용어',title:'시험',terms:['보압|고압 → '+active().code+': HOLDP'],text:'',sum:'',on:true,prio:false});saveRefs()"); await ev("consume('보압을 올려 주세요.','ko',{fromText:true})"); await sleep(120); const c = fake.chats.at(-1).messages.map(m => m.content).join('\n'); need(/보압→HOLDP/.test(c) && /\[입력\] 보압을 올려 주세요/.test(c), c.slice(-300)); });
    await step('conversation mic (ko, manual): local STT, interim shown, one row on stop', async () => { await sleep(900); const n = ev('state.items.length'); ev("pressTalk('ko')"); await sleep(40); need(ev('state.mic') && fake.lsessions.at(-1).lang === 'ko-KR' && fake.sessions.length === 0, 'local session'); P('화장실은'); await sleep(20); need(/화장실/.test(ev('state.interim')), 'interim'); F('화장실은 어디에 있나요', { lang: 'ko' }); await sleep(20); ev("pressTalk('ko')"); await sleep(500); need(ev('state.items.length') === n + 1 && ev('state.items.at(-1).original') === '화장실은 어디에 있나요', JSON.stringify(ev('state.items.at(-1).original'))); });
    await step('A11: no auto mode — a saved "auto" setting becomes 한국어', async () => { ev("state.recog='auto';render()"); need(ev('state.recog') === 'ko' && d.querySelectorAll('.talk').length === 2, 'recog ' + ev('state.recog')); });
    await step('follows speaker volume/speed/gender', async () => { ev("voicesG[active().code+'|m']='ja-JP-a'"); await sleep(900); const s0 = fake.spoken.length; ev("pressTalk('ko')"); await sleep(40); F('조용히 말합니다', { lang: 'ko', db: -30, dur: 2 }); await sleep(20); ev("pressTalk('ko')"); await sleep(700); ev("pressTalk('ko')"); await sleep(40); F('크게 빨리 말합니다 아주 크게', { lang: 'ko', db: -14, dur: 1 }); await sleep(20); ev("pressTalk('ko')"); await sleep(800); const sp = fake.spoken.slice(s0); need(sp.length >= 2, 'spoken ' + sp.length); const a = sp[0], b = sp.at(-1); need(b.volume > a.volume && b.rate > a.rate, 'vol ' + a.volume + '→' + b.volume + ' rate ' + a.rate + '→' + b.rate); need(b.voice === 'ja-JP-a', 'voice ' + b.voice); });
    await step('A4: phone AI cleans the heard Korean, then translates (one call), uses 자료·문장 서랍', async () => { ev("savedSents.push({o:'금형을 열어서 확인해 주세요',t:'SAVED-JA',s:'ko',tg:active().code,at:1});refs.unshift({id:778,gid:'base',kind:'자료',title:'사출 수업',terms:['이젝터 핀'],text:'',sum:'사출금형 수업 자료 요약',on:true,prio:false})"); const n = ev('state.items.length'); await ev("consume('어 이젝터 핀이 부러져서 음 금형을 열어서 확인해 봐야 합니다','ko',{fromMic:true,noMerge:true})"); await sleep(250); const e = JSON.parse(ev('JSON.stringify(state.items.at(-1))')), c = fake.chats.at(-1).messages.map(m => m.content).join('\n'); need(ev('state.items.length') === n + 1 && e.translation === 'LOCAL-こんにちは', 'translation ' + e.translation); need(e.original === '이젝터 핀이 부러져서 금형을 열어서 확인해 봐야 합니다', 'cleaned original: ' + e.original); need(fake.chats.at(-1).chat_template_kwargs?.enable_thinking === false, 'thinking must be off'); need(/\[배경\] 사출 수업: 사출금형 수업 자료 요약/.test(c) && /금형을 열어서 확인해 주세요 ⇒ SAVED-JA/.test(c) && /답하지 말고/.test(c), 'hints: ' + c.slice(-400)); });
    await step('A4: nonsense from the model is rejected (keeps what was said)', async () => { fake.badJson = true; await ev("consume('혹시 이 근처에 맛있는 식당 추천해 주실 수 있나요','ko',{fromMic:true,noMerge:true})"); await sleep(300); fake.badJson = false; const e = JSON.parse(ev('JSON.stringify(state.items.at(-1))')); need(e.original === '혹시 이 근처에 맛있는 식당 추천해 주실 수 있나요' && e.translation === 'LOCAL-こんにちは', JSON.stringify(e).slice(0, 200)); });
    await step('A4: conversation mode keeps listening with the screen off; 5-minute idle rule', async () => { await sleep(900); ev("pressTalk('ko')"); await sleep(40); need(ev('bgListen()') === true, 'bgListen in conversation'); Object.defineProperty(d, 'hidden', { get: () => true, configurable: true }); d.dispatchEvent(new w.Event('visibilitychange')); await sleep(30); need(ev('state.mic'), 'mic survived'); Object.defineProperty(d, 'hidden', { get: () => false, configurable: true }); d.dispatchEvent(new w.Event('visibilitychange')); ev("pressTalk('ko')"); await sleep(80); need(/5분 동안 말소리가 없어/.test(ev('activity.toString()')) && /300000/.test(ev('activity.toString()')), 'idle'); });
    await step('A5: reading aloud continues when the screen turns off (mic off)', async () => { need(!ev('state.mic'), 'mic should be off'); ev("speak('こんにちは。さようなら。','ja')"); await sleep(3); need(fake.play && fake.play.at(-1) === true, 'playing flag ' + JSON.stringify(fake.play)); Object.defineProperty(d, 'hidden', { get: () => true, configurable: true }); d.dispatchEvent(new w.Event('visibilitychange')); need(ev('outBusy') === true, 'speech was stopped by screen off'); Object.defineProperty(d, 'hidden', { get: () => false, configurable: true }); d.dispatchEvent(new w.Event('visibilitychange')); await sleep(1900); need(ev('outBusy') === false && fake.play.at(-1) === false, 'ended ' + JSON.stringify(fake.play)); });
    await step('A6: a short phrase written many times by the recognizer is collapsed to one', async () => { need(ev("collapseRepeats('안녕하세요, 안녕하세요, 안녕하세요, 안녕하세요, 안녕하세요.')") === '안녕하세요', ev("collapseRepeats('안녕하세요, 안녕하세요, 안녕하세요, 안녕하세요, 안녕하세요.')")); need(ev("collapseRepeats('네, 네. 알겠습니다')") === '네, 네. 알겠습니다', 'twice stays'); need(ev("collapseRepeats('감사합니다 정말 감사합니다 정말 감사합니다 정말 잘 부탁드립니다')") === '감사합니다 정말 잘 부탁드립니다', ev("collapseRepeats('감사합니다 정말 감사합니다 정말 감사합니다 정말 잘 부탁드립니다')")); await sleep(900); const n = ev('state.items.length'); ev("pressTalk('ko')"); await sleep(40); F('안녕하세요, 안녕하세요, 안녕하세요, 안녕하세요, 안녕하세요', { lang: 'ko' }); await sleep(20); ev("pressTalk('ko')"); await sleep(500); need(ev('state.items.length') === n + 1 && ev('state.items.at(-1).original') === '안녕하세요', ev('state.items.at(-1).original')); });
    await step('A15 listen mode: a 🌐 번역 button instead of the chunk-time switch', async () => { await modeTo('listen'); ev('render()'); const cb = d.querySelector('.chunk-btn'); need(cb && /번역/.test(cb.textContent) && !/1분|나중에/.test(cb.textContent), 'button: ' + (cb && cb.textContent)); need(ev('listenChunk()') === 870 && ev('listenChunkMax()') === 960 && ev('listenLater()') === false, 'pieces of about 15 minutes'); need(!d.querySelector('.listen-methods'), 'old row'); need(d.querySelectorAll('.talk-row .ai-col .ai-chip').length === 2, 'chips'); });
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
    await step('A10/A24: pieces are cut by the length of the stored sound — about 15 minutes, at a pause; a quiet gap no longer cuts', async () => {
      await sleep(900); const n = ev('state.listening.length'), T = Date.now() - 2000000, f = 'L20261115-091000.pcm'; ev("pressTalk('foreign')"); await sleep(40);
      F('First part of the talk.', { f, a: 0, b: 7200000, t0: T, t1: T + 450000 }); await sleep(30);
      F('Second part of the talk.', { f, a: 7200000, b: 13600000, t0: T + 450500, t1: T + 850000 }); await sleep(600);   // 14분 10초: 아직 끊지 않음
      need(ev('state.listening.length') === n, 'cut before 14 and a half minutes: ' + (ev('state.listening.length') - n));
      F('Still the second part.', { f, a: 13600000, b: 14000000, t0: T + 851000, t1: T + 876000 }); await sleep(600);   // 14분 35초 + 문장 끝 → 끊음
      need(ev('state.listening.length') === n + 1, 'the 15-minute piece was not cut: ' + (ev('state.listening.length') - n));
      F('Third part.', { f, a: 14000000, b: 14100000, t0: T + 877000, t1: T + 884000 }); await sleep(30);
      F('After a long pause.', { f, a: 14100000, b: 14200000, t0: T + 1000000, t1: T + 1005000 }); await sleep(100);   // 2분 떨어져 들림 → 끊지 않음
      need(ev('state.listening.length') === n + 1, 'a quiet gap must not cut the piece: ' + (ev('state.listening.length') - n));
      ev("pressTalk('foreign')"); await sleep(1800);
      const rows = JSON.parse(ev('JSON.stringify(state.listening.slice(' + n + ').map(e=>[e.original,e.au&&e.au.a,e.au&&e.au.b]))'));
      need(rows.length === 2 && rows[0][0] === 'First part of the talk. Second part of the talk. Still the second part.' && rows[0][1] === 0 && rows[0][2] === 14000000 && rows[1][0] === 'Third part. After a long pause.' && rows[1][1] === 14000000, JSON.stringify(rows));
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
    await step('A24: listen mode records pieces of about 15 minutes (a live row grows while recording); translating afterwards is by Gemini only; delete one row', async () => {
      await modeTo('listen'); ev("state.listening=state.listening.filter(x=>x.translation);store('ai_key','AIzaTEST');store('gem_tier','fast');render()"); await sleep(900);
      const n = ev('state.listening.length'), s0 = fake.spoken.length, c0 = (fake.chats || []).length, T = Date.now() - 2000000, f = 'L20261115-120000.pcm';
      need(ev('engine()') === 'gemini' && ev('currentEntryMode()') === 'fast', 'listen mode uses Gemini 빠름 by default: ' + ev('currentEntryMode()'));
      ev("pressTalk('foreign')"); await sleep(40); need(fake.lsessions.at(-1).nodec === true, 'listen mode always records only: ' + JSON.stringify(fake.lsessions.at(-1)));
      F('', { f, a: 0, b: 380000, t0: T, t1: T + 24000 }); await sleep(80);
      const last = () => [...d.querySelectorAll('.listen-row')].at(-1);
      need(ev('state.listening.length') === n + 1 && ev('state.listening.at(-1).growing') === true && /녹음하는 중/.test(last().textContent) && !last().querySelector('.del-ctrl') && !last().querySelector('.entry-engine'), 'a live row appears at the first sound, with no buttons while recording: ' + last().textContent.slice(0, 80));
      F('', { f, a: 390000, b: 13900000, t0: T + 25000, t1: T + 868000 }); await sleep(600);
      need(ev('state.listening.length') === n + 1 && ev('state.listening.at(-1).growing') === true && ev('state.listening.at(-1).au.b') === 13900000, 'the live row grows; no cut before 14 and a half minutes');
      F('', { f, a: 13912000, b: 14100000, t0: T + 869000, t1: T + 881000 }); await sleep(600);   // 14분 41초, 쉬는 곳 → 끊음
      need(ev('state.listening.length') === n + 1 && !ev('state.listening.at(-1).growing') && ev('state.listening.at(-1).au.b') === 14100000, 'cut at a pause near 15 minutes: ' + ev('JSON.stringify(state.listening.at(-1))').slice(0, 200));
      F('', { f, a: 14116000, b: 14400000, t0: T + 882000, t1: T + 900000 }); await sleep(30); ev("pressTalk('foreign')"); await sleep(1800);
      const rows = JSON.parse(ev('JSON.stringify(state.listening.slice(' + n + '))'));
      need(rows.length === 2 && rows.every(r => r.piece && !r.growing && r.translation === '' && r.original === '' && !r.correcting) && rows[0].au.a === 0 && rows[0].au.b === 14100000 && rows[1].au.a === 14100000 && rows[1].au.b === 14400000, 'two untranslated pieces, the second starts exactly where the first ended: ' + JSON.stringify(rows.map(r => r.au)));
      need(fake.spoken.length === s0 && (fake.chats || []).length === c0 && !(fake.files || []).some(x => x.f === f), 'nothing was transcribed, translated or read while listening');
      need(d.querySelectorAll('.piece-tag').length >= 2 && last().querySelector('.o-rec') && last().querySelector('.del-ctrl') && last().querySelector('.entry-engine') && !last().querySelector('.edit-ctrl') && last().querySelectorAll('.ctrls button').length === 3, 'an untranslated piece has 🎧 and only ○ · 방식 · 🗑');
      last().querySelector('.entry-engine').click(); const mm = [...d.querySelectorAll('.entry-mode-menu button')].map(b => b.textContent).join(','); ev('entryModeMenu?.()');
      need(mm === '빠름,균형,정확', 'no phone AI in listen mode: ' + mm);
      fake.online = false; ev('listenTranslate()'); await sleep(10); need(!d.querySelector('.confirm-box') && /인터넷이 연결되어 있지/.test(d.querySelector('.notice')?.textContent || '') && ev('engine()') === 'gemini', 'offline: told first, the phone AI does not take over in listen mode: ' + (d.querySelector('.notice')?.textContent || '')); fake.online = true;
      const TR = '오늘은 날씨가 좋습니다. '.repeat(90).trim(); fake.gem = () => ({ t: TR }); fake.gemBodies = []; fake.files = [];
      ev("state.listening.forEach(x=>x.sel=false);state.listening.at(-1).sel=true"); ev('listenTranslate()'); await sleep(10); need(/녹음 1개/.test(d.querySelector('.confirm-box')?.textContent || '') && /Gemini/.test(d.querySelector('.confirm-box').textContent), 'asks: ' + (d.querySelector('.confirm-box')?.textContent || ''));
      [...d.querySelectorAll('.confirm-box button')].find(b => b.textContent === '번역').click(); await sleep(600);
      need(ev('state.listening.at(-1).translation') === TR && ev('state.listening.at(-1).original') === '' && ev('state.listening.at(-1).trMode') === 'fast' && fake.gemBodies.length === 1 && JSON.stringify(fake.gemBodies[0].body.generationConfig.responseSchema.required) === '["t"]' && !ev('state.listening.at(-2).translation') && fake.files.length === 0 && (fake.chats || []).length === c0, 'the picked piece is translated by Gemini from the sound (translation only); the phone AI is not used: ' + ev('JSON.stringify(state.listening.at(-1))').slice(0, 160));
      need(fake.spoken.length > s0, 'read aloud after translating');
      ev("state.listening.forEach(x=>x.sel=false);render()"); const m = ev('state.listening.length'); [...d.querySelectorAll('.listen-row .del-ctrl')].at(-1).click(); await sleep(10);
      need(/이 줄을 지울까요/.test(d.querySelector('.confirm-box')?.textContent || ''), 'delete asks first'); [...d.querySelectorAll('.confirm-box button')].find(b => b.textContent === '삭제').click(); await sleep(20);
      need(ev('state.listening.length') === m - 1, 'one row deleted'); fake.gem = null; ev("store('ai_key','');render()");
    });
    await step('A10: reads faster when the interpretation falls behind', async () => {
      const r = k => ev(`(()=>{const e={heardAt:Date.now()-${k}*1000};state.listening.push(e);const m=state.mic,md=state.mode;state.mic=true;state.mode='listen';const v=lagRate(e);state.mic=m;state.mode=md;state.listening.pop();return v})()`);
      need(r(60) === 1 && r(130) === 1.2 && r(200) === 1.35 && r(300) === 1.5, [r(60), r(130), r(200), r(300)].join());
      need(ev('lagRate({heardAt:Date.now()-300000})') === 1, 'only while listening');
    });
    await step('A13: third mode is 모음 (collection) — text results go there in a different colour; recording moved to a side tab', async () => {
      await modeTo('conversation'); const n = ev('state.board.length'); ev('openText()'); await sleep(20);
      d.querySelector('textarea.editor').value = '영수증 주세요'; [...d.querySelectorAll('button')].find(b => b.textContent === '번역하기').click(); await sleep(300);
      need(ev('state.mode') === 'record' && /모음 모드/.test(d.querySelector('.mode').textContent) && d.querySelector('.screen.board'), 'switched to 모음: ' + ev('state.mode'));
      const e = JSON.parse(ev('JSON.stringify(state.board.at(-1))'));
      need(ev('state.board.length') === n + 1 && e.kind === 'text' && e.raw === '영수증 주세요' && e.translation && !e.failed, 'text row: ' + JSON.stringify(e));
      need(d.querySelector('.pair.k-text .src-tag')?.textContent === '⌨ 글' && d.querySelector('.talk-row.hide'), 'colour/tag: ' + (d.querySelector('.pair')?.className || ''));
      need(d.querySelectorAll('.side-tab2').length === 3 && d.querySelector('.side-tab2.st-rec'), 'three side tabs');
      ev("openDrawer('rec')"); await sleep(20); need(d.querySelector('.rec-drawer') && [...d.querySelectorAll('.rec-drawer button')].some(b => /녹음 시작/.test(b.textContent)), 'recording drawer');
      need(![...d.querySelectorAll('.rec-drawer button')].some(b => /받아쓰기|요약/.test(b.textContent)), 'transcribe/summary buttons removed'); ev('closeLayer()');
      ev("state.board.at(-1).sel=true;render()"); await sleep(10); need(/선택 1/.test(d.querySelector('.play-all').textContent), 'select works in 모음'); ev("state.board.forEach(x=>x.sel=false)");
      await modeTo('conversation');
    });
    await step('A13: a recording is translated from its sound into 모음 (Gemini hears it; language decided by listening); 방식 change hears it again', async () => {
      ev("store('ai_key','AIzaTEST');setEngineMode('fast');render()");
      ev("recList.unshift({id:'rec-test1',at:Date.now()-60000,dur:12,size:5000,mime:'audio/wav',status:'done'});recBlob=async()=>new Blob([new Uint8Array(6000)],{type:'audio/wav'})");
      fake.gem = (b, u) => ({ s: '내일 회의는 열 시입니다', t: '明日の会議は10時です', lang: 'ko' }); fake.gemBodies = [];
      ev("openDrawer('rec')"); await sleep(20); const tb = [...d.querySelectorAll('.rec-drawer button')].find(b => /번역/.test(b.textContent)); need(tb, 'no 번역 button'); tb.click(); await sleep(400);
      const e = JSON.parse(ev('JSON.stringify(state.board.at(-1))'));
      need(ev('state.mode') === 'record' && e.kind === 'rec' && e.recId === 'rec-test1' && e.original === '내일 회의는 열 시입니다' && e.translation === '明日の会議は10時です' && e.source === 'ko' && e.trMode === 'fast', 'rec row: ' + JSON.stringify(e));
      need(fake.gemBodies.length === 1 && fake.gemBodies[0].body.contents[0].parts.some(p => p.inline_data && p.inline_data.mime_type === 'audio/wav') && /lang/.test(JSON.stringify(fake.gemBodies[0].body.generationConfig.responseSchema)), 'recording sound sent');
      need(d.querySelector('.pair.k-rec .src-tag') && /🎙 녹음/.test(d.querySelector('.pair.k-rec .src-tag').textContent), 'rec colour/tag');
      fake.gem = (b, u) => /gemini-4-argon/.test(u) ? { s: '내일 회의는 오전 열 시입니다', t: '明日の会議は午前10時です', lang: 'ko' } : null; fake.gemBodies = [];
      await ev("retranslateEntry(state.board.at(-1),'accurate')"); await sleep(300);
      need(ev('state.board.at(-1).original') === '내일 회의는 오전 열 시입니다' && ev('state.board.at(-1).trMode') === 'accurate' && fake.gemBodies.length === 1, 'heard again with the accurate model: ' + ev('JSON.stringify(state.board.at(-1))'));
      fake.gem = null; ev("recList.shift()"); await modeTo('conversation');
    });
    await step('A13: after you stop talking the language button shows "통역하는 중…" until the interpretation comes', async () => {
      ev("setEngineMode('fast');render()"); fake.gem = () => ({ s: '감사합니다', t: 'ありがとうございます' }); fake.gemDelay = 500; await sleep(900); const n = ev('state.items.length');
      ev("pressTalk('ko')"); await sleep(40); need(d.querySelector('.talk.k-ko.on') && !d.querySelector('.talk.busy'), 'listening');
      F('', { f: 'L20261115-110000.pcm', a: 0, b: 30000, t0: Date.now() - 2500, t1: Date.now() - 500 }); await sleep(30);
      ev("pressTalk('ko')"); await sleep(200);
      const bz = d.querySelector('.talk.k-ko.busy'); need(bz && !bz.classList.contains('on') && /통역하는 중/.test(bz.querySelector('small').textContent) && !d.querySelector('.talk.k-foreign.busy'), 'busy mark: ' + d.querySelector('.talk.k-ko').className + ' ' + d.querySelector('.talk.k-ko small').textContent);
      await sleep(900); need(!d.querySelector('.talk.busy') && ev('state.items.length') === n + 1 && ev('state.items.at(-1).translation') === 'ありがとうございます', 'busy mark cleared when done: ' + ev('JSON.stringify(state.items.at(-1))'));
      fake.gemDelay = 0;
    });
    await step('A13: a sentence left over from the previous session becomes its own row (not mixed into the new one)', async () => {
      fake.gem = b => ({ s: '소리로 들은 말', t: '音で聞いた言葉' }); await sleep(900); const n = ev('state.items.length');
      ev("pressTalk('ko')"); await sleep(40);
      F('', { f: 'L20261115-111000.pcm', a: 0, b: 20000, t0: Date.now() - 9000, t1: Date.now() - 8000, old: true }); await sleep(300);
      need(ev('state.items.length') === n + 1 && ev('state.items.at(-1).au.b') === 20000, 'leftover row: ' + (ev('state.items.length') - n));
      F('', { f: 'L20261115-111000.pcm', a: 40000, b: 70000, t0: Date.now() - 2000, t1: Date.now() - 500 }); await sleep(30); ev("pressTalk('ko')"); await sleep(500);
      need(ev('state.items.length') === n + 2 && ev('state.items.at(-1).au.a') === 40000, 'new turn keeps only its own sound: ' + ev('JSON.stringify(state.items.at(-1).au)'));
    });
    await step('A13: a too-short answer is asked once more; if 방식 change still fails the old row is kept and the reason is shown', async () => {
      const long = '오늘은 금형 설계의 기본에 대해서 이야기하겠습니다. 먼저 사출 성형의 원리를 살펴보고 그다음에 냉각 회로를 설명하겠습니다.';
      ev("state.items.at(-1).original=" + JSON.stringify(long) + ";state.items.at(-1).translation='旧訳'");
      let calls = 0; fake.gem = (b, u) => { calls++; return { s: '오늘은 금형', t: '今日は金型' }; }; fake.gemBodies = [];
      await ev("retranslateEntry(state.items.at(-1),'balanced')"); await sleep(400);
      need(calls === 2 && /너무 짧았습니다/.test(JSON.stringify(fake.gemBodies[1].body.contents)), 'asked again: ' + calls);
      need(ev('state.items.at(-1).original') === long && ev('state.items.at(-1).translation') === '旧訳' && ev('state.items.at(-1).trMode') !== 'local', 'old row kept: ' + ev('JSON.stringify(state.items.at(-1))'));
      fake.gem = null;
    });
    await step('A13: pick a range with a long press, send only the picked rows; Gemini key check button', async () => {
      await modeTo('conversation'); ev("state.items.forEach(x=>x.sel=false);lastSel=null"); const m = ev('state.items.length'); need(m >= 4, 'need rows');
      ev("state.items[" + (m - 4) + "].sel=true;lastSel=state.items[" + (m - 4) + "];selRange(state.items[" + (m - 2) + "])"); await sleep(20);
      need(ev('state.items.filter(x=>x.sel).length') === 3 && /선택 3/.test(d.querySelector('.play-all').textContent), 'range: ' + ev('state.items.filter(x=>x.sel).length'));
      const s0 = fake.shared.length; ev('shareAll()'); await sleep(10); const b1 = [...d.querySelectorAll('.share-pick button')].map(b => b.textContent), hs = [...d.querySelectorAll('.share-h')].map(h => h.textContent);
      need(/고른 3줄/.test(d.querySelector('.share-box p').textContent) && /글자로 내보내기/.test(hs[0]) && /저장/.test(hs[1]) && b1.length === 8 && /^전체/.test(b1[0]) && b1[1] === '한국어만' && /^전체/.test(b1[3]) && /모두 풀기/.test(b1[6]) && b1[7] === '취소', 'one screen: 글자로 내보내기 / 저장, each 전체·한국어만·외국어만: ' + hs.join('|') + ' ' + b1.join());
      d.querySelector('.share-pick button').click(); await sleep(40);
      need(fake.shared.length === s0 + 1 && fake.shared.at(-1).split('\n\n').length === 3, 'only the picked rows shared: ' + (fake.shared.at(-1) || '').slice(0, 120));
      ev("state.items.forEach(x=>x.sel=false)");
      fake.keyBad = false; need(/키가 정상/.test(await ev("gemKeyCheck('AIzaTEST')")), 'key ok'); fake.keyBad = true; need(/키가 맞지 않습니다/.test(await ev("gemKeyCheck('AIzaBAD')")), 'key bad'); fake.keyBad = false;
      ev("openSettings();state.setTab='adv';state.adminOpen=false;render()"); await sleep(20); need(![...d.querySelectorAll('button')].some(b => /키 확인하기/.test(b.textContent)) || d.querySelector('.admin-box').hidden, 'the key is not on the ordinary settings screen');
      ev("state.adminOpen=true;state.adminTab='key';render()"); await sleep(20); need([...d.querySelectorAll('.admin-box button')].some(b => /키 확인하기/.test(b.textContent)) && /결제/.test(d.querySelector('.admin-box').textContent), 'key check button in the admin menu'); ev("state.adminOpen=false;closeLayer()");
    });
    await step('earphones keep the mic open while speaking', async () => { need(ev('earOn()') === false, 'no headset'); fake.head = true; await sleep(2100); need(ev('earOn()') === true, 'headset'); fake.head = false; await sleep(2100); });
    await step('A11 settings: 기본 · 번역 AI · 고급 (removed items are gone, microphone choice added)', async () => { ev('openSettings()'); let tabs = [...d.querySelector('.set-tabs').querySelectorAll('button')]; need(tabs.length === 4 && tabs[1].textContent === '번역 AI' && tabs[2].textContent === '보이기' && tabs[3].textContent === '고급', tabs.map(b => b.textContent).join()); let t = d.querySelector('#app').textContent; need(!/앱 주소 복사/.test(t), 'share-app button still there'); tabs[1].click(); await sleep(30); t = d.querySelector('#app').textContent; need(/Whisper turbo/.test(t) && /말한 사람 따라 하기/.test(t) && /AI 음성 · AI 통역사/.test(t) && /Gemma 4/.test(t) && /이어폰 마이크/.test(t), 'ai sections'); need(!/무료 번역기/.test(t) && !/구글 기본/.test(t) && !/다른 모델 직접 넣기/.test(t) && !/기본 번역기/.test(t), 'removed items still shown'); [...d.querySelectorAll('.chip')].find(b => /폰 마이크/.test(b.textContent)).click(); await sleep(20); need(fake.mics.at(-1) === 'phone' && ev("load('mic_src')") === 'phone', 'mic choice ' + fake.mics); [...d.querySelectorAll('.chip')].find(b => b.textContent === '자동').click(); await sleep(20); need(fake.mics.at(-1) === 'auto', 'mic back to auto'); [...d.querySelectorAll('button')].find(b => b.textContent === '시험 번역').click(); await sleep(80); need(/LOCAL-/.test(d.querySelector('.ai-result').textContent), 'test tr'); [...d.querySelectorAll('.set-tabs button')][3].click(); await sleep(30); t = d.querySelector('.modal-content').textContent; need(/무음 빼기/.test(t) && !/받아쓰기 정리 기록/.test(t), 'adv items'); need(d.querySelector('.admin-box').hidden, 'admin menu hidden until the version is tapped five times'); ev("state.adminOpen=true;state.adminTab='usage';render()"); await sleep(30); let at = [...d.querySelectorAll('.admin-box .set-tabs button')].map(b => b.textContent).join(); need(at === '사용량과 한도,깃허브 배포,키와 결제' && /이번 달 사용량/.test(d.querySelector('.admin-box').textContent) && /AI 사용량 기록/.test(d.querySelector('.admin-box').textContent), 'admin tabs: ' + at); ev("state.adminTab='key';render()"); await sleep(30); need(/키 받으러 가기/.test(d.querySelector('.admin-box').textContent), 'key tab'); ev("state.adminTab='deploy';render()"); await sleep(30); need(/최신 설치 파일 받기/.test(d.querySelector('.admin-box').textContent), 'deploy tab'); ev("state.adminOpen=false;state.adminTab='usage';closeLayer()"); });
    await step('A11: no free translator — per-sentence menu and engine button cycle', async () => { if (ev('state.page') !== 'main') d.querySelector('.home')?.click(); d.querySelector('.entry-engine').click(); const m = [...d.querySelectorAll('.entry-mode-menu button')].map(b => b.textContent).join(','); need(m === '빠름,균형,정확' || m === '폰AI', 'menu: ' + m); ev('entryModeMenu?.()'); ev("store('ai_key','AIzaTEST');store('gem_tier','fast');store('tr_engine','local');render()"); need(ev('engine()') === 'gemini' && ev('currentEntryMode()') === 'fast', 'Gemini 빠름 is the default even if the phone AI was chosen before: ' + ev('currentEntryMode()')); const seen = []; for (let i = 0; i < 4; i++) { d.querySelector('.ai-state').click(); seen.push(ev('currentEntryMode()')); } need(seen.join() === 'balanced,accurate,fast,balanced', 'the engine button goes round the Gemini steps only: ' + seen.join()); ev("store('gem_tier','fast')"); ev("store('ai_key','');store('tr_engine','free');render()"); need(ev('engine()') === 'local', 'an old "free" setting falls back to the phone AI: ' + ev('engine()')); ev("store('tr_engine','local');render()"); });
    await step('offline: still translates with phone AI', async () => { fake.online = false; const n = ev('state.items.length'); await ev("consume('물 좀 주세요.','ko',{fromText:true})"); await sleep(120); need(ev('state.items.length') === n + 1 && ev('state.items.at(-1).translation') === 'LOCAL-こんにちは', ev('state.items.at(-1).translation')); fake.online = true; });
    await step('A11: phone AI failure with no Gemini key → the row says it failed (no free translator)', async () => { fake.chatFail = true; await ev("consume('계산서 주세요.','ko',{fromText:true})"); await sleep(250); need(/번역 실패/.test(ev('state.items.at(-1).translation')) && ev('state.items.at(-1).failed') === true, ev('state.items.at(-1).translation')); fake.chatFail = false; });
    await step('AI voice button → Gemini TTS; off → phone voice', async () => { ev("store('ai_key','');render()"); need(d.querySelectorAll('.ai-chip').length === 2 && !d.querySelector('.ai-chip.on'), 'chips'); ev('toggleAiVoice()'); need(ev("load('ai_voice_on')") !== '1', 'needs key'); ev("store('ai_key','AIzaTEST');toggleAiVoice()"); need(ev("load('ai_voice_on')") === '1', 'on'); const t0 = fake.tts || 0, s0 = fake.spoken.length; ev("speak('こんにちは','ja')"); await sleep(250); need((fake.tts || 0) === t0 + 1, 'tts calls ' + fake.tts); need(fake.audio >= 1, 'audio played'); need(fake.spoken.length === s0, 'phone voice not used'); ev('toggleAiVoice()'); ev("speak('おはようございます','ja')"); await sleep(100); need(fake.spoken.length === s0 + 1, 'phone voice again (for a sentence that has no saved AI voice)'); });
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
      need((fake.played || 0) === p0 + 1 && d.querySelector('.ai-chip.live')?.textContent === '🎙 AI 통역사', 'audio/chip ' + d.querySelector('.talk-row').innerHTML.slice(0, 200));
      await sleep(80); need(ev("!!state.items.at(-1).vid&&voiceKeys.has('i:'+state.items.at(-1).vid)"), 'the interpreter voice is saved with the row: ' + ev('JSON.stringify(state.items.at(-1))'));
      ev("pressTalk('foreign')"); await sleep(5); need(b.sent[1].realtimeInput.activityStart && d.querySelector('.talk.k-foreign').classList.contains('on'), 'other speaker');
      const ka = a.sent.length; ev("pressTalk('ko')"); await sleep(5); need(b.sent.at(-1).realtimeInput.activityEnd && a.sent.length === ka && !d.querySelector('.talk.on'), 'pressing the other language only ends this turn (its interpretation must be heard first)');
      msg(b, { inputTranscription: { text: 'ありがとう' } }); msg(b, { outputTranscription: { text: '감사합니다' }, modelTurn: { parts: [{ inlineData: { data: 'AAAAAAAA' } }] } }); await sleep(500);
      need((fake.played || 0) === p0 + 2, 'second interpretation played');
      ev("pressTalk('ko')"); await sleep(5); msg(b, { modelTurn: { parts: [{ inlineData: { data: 'AAAAAAAA' } }] } }); need((fake.played || 0) === p0 + 2, 'late sound of the previous turn is not played once someone starts talking'); ev("pressTalk('ko')"); await sleep(5);
      const e2 = JSON.parse(ev('JSON.stringify(state.items.at(-1))'));
      need(ev('state.items.length') === n + 2 && e2.original === 'ありがとう' && e2.translation === '감사합니다' && e2.target === 'ko', JSON.stringify(e2));
      ev('startInterp()'); await sleep(20); need(!ev('!!interp') && fake.pcm.at(-1) === 'stop', 'stopped');
      need(ev("(aiUsage.t['AI 통역사 · 대화 (3.8 Live)']||{}).c>0"), 'interpreter time added to the usage record: ' + ev("JSON.stringify(aiUsage.t)"));
      ev('startInterp()'); await sleep(30); fake.ws.at(-1).onclose({ code: 1008, reason: 'API key not valid' }); await sleep(20);
      need(!ev('!!interp') && /API key not valid/.test(d.querySelector('.ai-note')?.textContent || ''), 'reason shown: ' + (d.querySelector('.ai-row')?.textContent || ''));
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
    const hasInline = b => (b.contents[0].parts || []).some(p => p.inline_data && p.inline_data.mime_type === 'audio/wav' && p.inline_data.data.length > 100);
    await step('A11: Gemini 번역기 — the phone does not write the words down; Gemini hears the saved sound and makes both the words and the translation', async () => {
      await modeTo('conversation'); ev("store('ai_key','AIzaTEST');setEngineMode('fast');render()"); need(ev('engine()') === 'gemini' && ev('hearByGemini()') === true, 'gemini engine');
      fake.gem = b => ({ s: '안녕하세요 여러분', t: 'みなさん、こんにちは' }); fake.gemBodies = []; fake.recFetch = [];
      await sleep(900); const n = ev('state.items.length'), T = Date.now() - 4000, f = 'L20261115-100000.pcm';
      ev("pressTalk('ko')"); await sleep(40); need(fake.lsessions.at(-1).nodec === true, 'phone asked to skip writing: ' + JSON.stringify(fake.lsessions.at(-1)));
      F('', { f, a: 32000, b: 80000, t0: T, t1: T + 3000 }); await sleep(30); need(/들음/.test(ev('state.interim')), 'shows that it is hearing: ' + ev('state.interim'));
      ev("pressTalk('ko')"); await sleep(700);
      const e = JSON.parse(ev('JSON.stringify(state.items.at(-1))'));
      need(ev('state.items.length') === n + 1 && e.original === '안녕하세요 여러분' && e.translation === 'みなさん、こんにちは' && e.trMode === 'fast' && e.sttBy === 'gemini' && e.au.a === 32000, 'row: ' + JSON.stringify(e));
      need(fake.gemBodies.length === 1 && /gemini-3\.5-flash-lite/.test(fake.gemBodies[0].u) && hasInline(fake.gemBodies[0].body) && /받아 적/.test(fake.gemBodies[0].body.systemInstruction.parts[0].text), 'sound sent to Gemini: ' + JSON.stringify(fake.gemBodies[0] || {}).slice(0, 300));
      need(/\/rec\/L20261115-100000\.pcm\?a=29600&b=82400$/.test(fake.recFetch[0]), 'sound range: ' + fake.recFetch[0]);
      need(!/\[앞\]/.test(JSON.stringify(fake.gemBodies[0].body)), 'the previous sentences must not be sent with the sound');
    });
    await step('A11: 방식을 바꾸면 글자가 아니라 저장된 소리를 다시 듣고, 한글과 번역을 둘 다 새로 만든다', async () => {
      fake.gem = (b, u) => /gemini-4-argon/.test(u) ? { s: '안녕하세요, 여러분. 반갑습니다', t: 'みなさん、こんにちは。はじめまして' } : null; fake.gemBodies = [];
      await ev("retranslateEntry(state.items.at(-1),'accurate')"); await sleep(300);
      const e = JSON.parse(ev('JSON.stringify(state.items.at(-1))'));
      need(e.original === '안녕하세요, 여러분. 반갑습니다' && e.translation === 'みなさん、こんにちは。はじめまして' && e.trMode === 'accurate', 'row: ' + JSON.stringify(e));
      need(fake.gemBodies.length === 1 && hasInline(fake.gemBodies[0].body) && fake.gemBodies[0].body.generationConfig.thinkingConfig.thinkingLevel === 'low', 'heard the sound again');
      fake.files = []; fake.fileText = '안녕하세요 여러분 반갑습니다'; await ev("retranslateEntry(state.items.at(-1),'local')"); await sleep(400);
      const e2 = JSON.parse(ev('JSON.stringify(state.items.at(-1))'));
      need(fake.files.length === 1 && fake.files[0].f === 'L20261115-100000.pcm' && e2.trMode === 'local' && e2.sttBy === 'phone' && /LOCAL-/.test(e2.translation), '폰 AI로 바꾸면 Whisper가 저장된 소리를 받아 적음: ' + JSON.stringify(e2) + ' ' + JSON.stringify(fake.files));
    });
    await step('A11: Gemini가 실패하면 저장된 소리를 Whisper로 받아 적어 폰 AI가 이어서 번역', async () => {
      fake.gem = () => null; fake.files = []; fake.fileText = '화장실이 어디에 있습니까'; await sleep(900); const n = ev('state.items.length'), T = Date.now() - 3000;
      ev("setEngineMode('balanced');render()"); ev("pressTalk('ko')"); await sleep(40); F('', { f: 'L20261115-100500.pcm', a: 0, b: 40000, t0: T, t1: T + 2500 }); await sleep(30); ev("pressTalk('ko')"); await sleep(900);
      const e = JSON.parse(ev('JSON.stringify(state.items.at(-1))'));
      need(ev('state.items.length') === n + 1 && fake.files.length === 1 && fake.files[0].f === 'L20261115-100500.pcm' && e.original && e.trMode === 'local' && /LOCAL-/.test(e.translation) && !e.failed, 'row: ' + JSON.stringify(e));
      fake.gem = null;
    });
    await step('A11: 폰 AI 번역기 — Whisper writes the words down as before (no change)', async () => {
      ev("store('ai_key','');render()"); await sleep(900); const n = ev('state.items.length'); need(ev('engine()') === 'local', 'no key → the phone AI takes over by itself (conversation mode): ' + ev('engine()'));
      ev("pressTalk('ko')"); await sleep(40); need(!fake.lsessions.at(-1).nodec && ev('hearByGemini()') === false, 'whisper mode: ' + JSON.stringify(fake.lsessions.at(-1)));
      F('물 한 잔 주세요', { lang: 'ko', f: 'L20261115-101000.pcm', a: 0, b: 30000, t0: Date.now() - 2000, t1: Date.now() - 500 }); await sleep(30); ev("pressTalk('ko')"); await sleep(700);
      const e = JSON.parse(ev('JSON.stringify(state.items.at(-1))'));
      need(ev('state.items.length') === n + 1 && e.sttBy === 'phone' && e.trMode === 'local' && e.au.f === 'L20261115-101000.pcm', 'row: ' + JSON.stringify(e));
    });
    await step('A16/A24: unbroken speech is not cut mid-way; a long gap is not pulled in; untranslated pieces can be saved and translated later', async () => {
      await modeTo('listen'); ev("state.listening=[];store('ai_key','AIzaTEST');render()"); await sleep(900);
      const T = Date.now() - 2000000, f = 'L20261115-130000.pcm';
      ev("pressTalk('foreign')"); await sleep(40);
      F('', { f, a: 0, b: 13900000, t0: T, t1: T + 868000 }); await sleep(30); F('', { f, a: 13900000, b: 14300000, t0: T + 868000, t1: T + 893000 }); await sleep(600);   // 14분 53초이지만 쉬지 않고 이어진 말(25초 구간)
      need(ev('state.listening.length') === 1 && ev('state.listening[0].growing') === true, 'not cut in the middle of unbroken speech: ' + ev('JSON.stringify(state.listening.map(x=>[x.growing,x.au.b]))'));
      F('', { f, a: 14300000, b: 14460000, t0: T + 893000, t1: T + 903000 }); await sleep(600);   // 쉬는 곳이 오면 끊음
      need(ev('state.listening.length') === 1 && !ev('state.listening[0].growing') && ev('state.listening[0].au.a') === 0 && ev('state.listening[0].au.b') === 14460000, 'cut at the next pause: ' + ev('JSON.stringify(state.listening)').slice(0, 200));
      F('', { f, a: 14600000, b: 14700000, t0: T + 913000, t1: T + 919000 }); await sleep(30); ev("pressTalk('foreign')"); await sleep(1800);
      need(ev('state.listening.length') === 2 && ev('state.listening[1].au.a') === 14600000, 'a gap longer than five seconds of stored sound is not pulled in: ' + ev('JSON.stringify(state.listening[1].au)'));
      // 아직 번역하지 않은 조각도 저장됨 → 모음 모드에서 열어 번역
      const n0 = ev('recList.length'); ev('shareAll()'); await sleep(10);
      need(/전체 2줄/.test(d.querySelector('.share-box')?.textContent || '') && /저장만/.test(d.querySelector('.share-note')?.textContent || ''), 'dialog: ' + (d.querySelector('.share-box')?.textContent || '').slice(0, 120));
      [...d.querySelectorAll('.share-pick button')][0].click(); await sleep(50);   // 글자로 내보내기 · 전체
      need(/번역이 아직 없습니다/.test(d.querySelector('.notice')?.textContent || '') && fake.shared.every(x => x !== ''), 'nothing to export as text yet: ' + (d.querySelector('.notice')?.textContent || ''));
      ev('shareAll()'); await sleep(10); [...d.querySelectorAll('.share-pick button')][3].click(); await sleep(200);   // 저장 · 전체
      need(ev('recList.length') === n0 + 1 && ev('recList[0].rows.length') === 2 && ev('recList[0].rows.every(r=>r.piece&&r.au&&!r.translation)'), 'untranslated pieces saved: ' + ev('JSON.stringify(recList[0])').slice(0, 300));
      ev('openSaved(recList[0])'); await sleep(60);
      const pr = [...d.querySelectorAll('.pair')].at(-1);
      need(ev('state.mode') === 'record' && pr && pr.querySelector('.piece-tag') && pr.querySelector('.o-rec') && pr.querySelector('.entry-engine') && pr.querySelector('.del-ctrl'), 'opened in 모음 with 🎧 · 방식 · 🗑: ' + (pr ? pr.textContent : ''));
      ev("store('ai_key','');render()"); fake.fileText = 'Opened later and translated.'; fake.files = []; ev("retranslateEntry(state.board.at(-1),'local')"); await sleep(600);   // 키가 없을 때(비상): 모음 모드에서는 폰 AI로
      need(ev('state.board.at(-1).original') === 'Opened later and translated.' && /LOCAL-/.test(ev('state.board.at(-1).translation')) && fake.files.length === 1 && fake.files[0].a === '14597600' && fake.files[0].b === '14702400', 'translated from the saved sound with a short margin: ' + JSON.stringify(fake.files) + ev('JSON.stringify(state.board.at(-1))').slice(0, 200));
      await ev('deleteSaved(recList[0])'); ev("state.board=[];state.listening=[];saveHistory()"); await modeTo('conversation');
    });
    await step('A17: listen mode can record the sound the phone itself plays (📱 폰 소리 · 🔇 무음)', async () => {
      await modeTo('listen'); ev("state.listening=[];setEngineMode('local');render()"); await sleep(900);
      const chips = () => [...d.querySelectorAll('.src-chip')], note = () => d.querySelector('.notice')?.textContent || '';
      need(chips().length === 3 && /마이크/.test(d.querySelector('.src-chip.on').textContent) && !d.querySelector('.src-note'), 'three choices, microphone by default: ' + chips().map(b => b.textContent).join());
      chips()[1].click(); await sleep(20);
      need(ev("load('listen_src')") === 'sys' && /폰 소리/.test(d.querySelector('.src-chip.on').textContent) && /시작/.test(d.querySelector('.src-note').textContent) && /폰에서 나오는 소리를 녹음합니다/.test(d.querySelector('#transcript').textContent), 'phone sound chosen, with a short guide: ' + d.querySelector('#transcript').textContent.slice(0, 80));
      fake.caps = []; ev("pressTalk('foreign')"); await sleep(40);
      need(fake.caps.at(-1) === 'sys' && fake.keepRecs.at(-1) === true && fake.lsessions.at(-1).nodec === true && ev('state.mic') === true, 'the phone is told to capture its own sound: ' + fake.caps.join());
      chips()[0].click(); await sleep(10); need(ev("load('listen_src')") === 'sys' && /멈춘 뒤/.test(note()), 'cannot switch while recording: ' + note());
      const T = Date.now() - 70000, f = 'L20261115-140000.pcm';
      F('', { f, a: 0, b: 320000, t0: T, t1: T + 20000 }); await sleep(30);
      w.__nat.onStt({ sid: fake.sid, type: 'error', text: 'capture-ended' }); w.__nat.onStt({ sid: fake.sid, type: 'end' }); await sleep(150);   // 알림줄에서 중지 · 화면 잠금
      need(ev('state.mic') === false && ev('state.listening.length') === 1 && ev('state.listening[0].sys') === true && ev('state.listening[0].au.b') === 320000 && /📱/.test(d.querySelector('.piece-tag').textContent) && /멈췄습니다/.test(note()), 'stopped from outside: what was recorded is kept: ' + ev('JSON.stringify(state.listening)').slice(0, 200) + ' ' + note());
      const s1 = fake.lsessions.length; await sleep(600); need(fake.lsessions.length === s1, 'does not start again by itself (it would ask for permission again)');
      ev("pressTalk('foreign')"); await sleep(40); w.__nat.onStt({ sid: fake.sid, type: 'error', text: 'capture-denied' }); w.__nat.onStt({ sid: fake.sid, type: 'end' }); await sleep(150);
      need(ev('state.mic') === false && ev('state.listening.length') === 1 && /허용하지 않아/.test(note()), 'permission refused: ' + note());
      chips()[2].click(); await sleep(20); need(/소리가 나지 않습니다/.test(d.querySelector('.src-note').textContent), 'silent note'); ev("pressTalk('foreign')"); await sleep(40);
      need(fake.caps.at(-1) === 'sysq', 'silent version: ' + fake.caps.join()); ev("pressTalk('foreign')"); await sleep(1800);
      await modeTo('conversation'); ev("pressTalk('ko')"); await sleep(40); need(fake.caps.at(-1) === 'mic' && fake.keepRecs.at(-1) === false, 'other modes always use the microphone, and their sound is not kept forever: ' + fake.caps.join()); ev("pressTalk('ko')"); await sleep(700);
      ev("store('listen_src','mic');state.listening=[];saveHistory()");
    });
    await step('A18: a failed translation shows why and a 다시 보내기 button; progress is shown while waiting', async () => {
      await modeTo('listen'); ev("state.listening=[];store('ai_key','AIzaTEST');setEngineMode('fast');render()"); await sleep(900);
      const T = Date.now() - 9000, f = 'L20261116-090000.pcm';
      ev("pressTalk('foreign')"); await sleep(40); F('', { f, a: 16000, b: 64000, t0: T, t1: T + 3000 }); await sleep(60); ev("pressTalk('foreign')"); await sleep(1800);
      need(ev('state.listening.length') === 1, 'one piece');
      // 사용 한도 초과
      fake.gem = () => null; fake.gemStatus = 429; fake.gemError = 'You exceeded your current quota, please check your plan and billing details.';
      ev('listenTranslate()'); await sleep(10); [...d.querySelectorAll('.confirm-box button')].find(b => b.textContent === '번역').click(); await sleep(400);
      const row = () => [...d.querySelectorAll('.listen-row')].at(-1), fn = () => row().querySelector('.fail-note');
      need(fn() && /사용 한도 초과/.test(fn().textContent) && /exceeded your current quota/.test(fn().textContent) && fn().querySelector('.fail-retry') && !ev('state.listening[0].correcting'), 'quota: reason stays on the row with the server text: ' + (fn() ? fn().textContent : row().textContent));
      const q0 = fake.gemBodies.length; fn().querySelector('.fail-retry').click(); await sleep(300);
      need(fake.gemBodies.length === q0 && /1분 뒤에 다시/.test(fn().textContent), 'after a quota error nothing is sent again for a minute: ' + (fake.gemBodies.length - q0) + ' ' + fn().textContent);
      ev("gemStop='';gemHalts=0");
      // 키 오류
      fake.gemStatus = 400; fake.gemError = 'API key not valid. Please pass a valid API key.'; fn().querySelector('.fail-retry').click(); await sleep(400);
      need(/API 키가 없거나 잘못됨/.test(fn().textContent), 'key: ' + fn().textContent);
      const g0 = fake.gemBodies.length; fn().querySelector('.fail-retry').click(); await sleep(300);
      need(fake.gemBodies.length === g0 && /API 키가 없거나 잘못됨/.test(fn().textContent), 'after a key error the same request is not sent again and again: ' + (fake.gemBodies.length - g0));
      ev("gemStop='';gemHalts=0");
      // 그 밖의 오류는 서버 글 그대로
      fake.gemStatus = 500; fake.gemError = 'Internal error encountered.'; fn().querySelector('.fail-retry').click(); await sleep(400);
      need(/Internal error encountered\./.test(fn().textContent) && !/한도|키|시간 초과/.test(fn().textContent), 'other: ' + fn().textContent);
      // 답이 늦는 동안: 무엇을 하는 중인지 보임 → 성공하면 이유가 사라짐
      fake.gemStatus = 0; fake.gemError = ''; fake.gemDelay = 500; fake.gem = () => ({ s: 'It works now.', t: '이제 됩니다.' });
      fn().querySelector('.fail-retry').click(); await sleep(150);
      need(/Gemini가 소리를 듣고 번역하는 중/.test(row().querySelector('.stage-live')?.textContent || '') && !fn(), 'progress while waiting: ' + row().textContent.slice(0, 120));
      await sleep(800); fake.gemDelay = 0;
      need(ev('state.listening[0].translation') === '이제 됩니다.' && !fn() && !ev('state.listening[0].err'), 'succeeded after resend: ' + ev('JSON.stringify(state.listening[0])').slice(0, 200));
      need(ev("whyFail(Error('폰 AI 번역 실패 · Read timed out'))").startsWith('시간 초과') && ev("whyFail(Error('Request payload size exceeds the limit: 20971520 bytes.'))").startsWith('파일이 너무 큼') && ev("whyFail(Error('인터넷 없음'))") === '인터넷 연결 안 됨 (인터넷 없음)', 'wording: ' + ev("whyFail(Error('인터넷 없음'))"));
      fake.gem = null; ev("store('ai_key','');setEngineMode('local');state.listening=[];saveHistory();render()"); await modeTo('conversation');
    });
    await step('A19: heard sound is kept (trimmed file + original); delete the original only, or rebuild rows from the original', async () => {
      await modeTo('listen'); ev("state.listening=[];store('ai_key','AIzaTEST');render()"); await sleep(300);
      fake.heard = [{ id: '20261116-090000', at: Date.now(), l: 3840000, r: 67200000, keep: false, live: false }]; fake.dels = [];
      ev("openDrawer('rec')"); await sleep(30);
      const hb = () => d.querySelector('.heard-box');
      need(hb() && /들은 소리 · 1번/.test(hb().textContent) && /저절로 지워지지 않습니다/.test(hb().textContent), 'summary in the recording tab: ' + (hb() ? hb().textContent.slice(0, 120) : 'none'));
      hb().querySelector('.rec-btns button').click(); await sleep(30);
      need(/걷어낸 파일 2:00/.test(hb().textContent) && /원본 35:00/.test(hb().textContent), 'lengths: ' + hb().textContent.slice(0, 260));
      const btn = t => [...hb().querySelectorAll('.heard-item button')].find(b => b.textContent.includes(t));
      btn('원본으로 다시 만들기').click(); await sleep(20); need(/15분씩 3줄/.test(d.querySelector('.confirm-box').textContent), 'asks: ' + d.querySelector('.confirm-box').textContent.slice(0, 80));
      [...d.querySelectorAll('.confirm-box button')].find(b => b.textContent === '만들기').click(); await sleep(60);
      const rows = JSON.parse(ev('JSON.stringify(state.listening)'));
      need(rows.length === 3 && rows.every(r => r.piece && r.rawCut && r.au.f === 'R20261116-090000.pcm') && rows[0].au.a === 0 && rows[1].au.a === 14400000 && rows[2].au.b === 33600000 && /원본/.test(d.querySelector('.piece-tag').textContent), 'rows from the original, 15 minutes each: ' + JSON.stringify(rows.map(r => r.au)).slice(0, 200));
      const QR = '조용한 부분까지 번역했습니다. '.repeat(70).trim(); fake.gem = () => ({ t: QR }); fake.recFetch = []; ev("retranslateEntry(state.listening[0],'fast')"); await sleep(500);
      need(/\/rec\/R20261116-090000\.pcm\?a=0&b=14402400$/.test(fake.recFetch[0] || '') && ev('state.listening[0].translation') === QR, 'translated by Gemini from the original file: ' + fake.recFetch[0]); fake.gem = null;
      ev("openDrawer('rec')"); await sleep(30); btn('원본만 지우기').click(); await sleep(20); [...d.querySelectorAll('.confirm-box button')].find(b => b.textContent === '삭제').click(); await sleep(40);
      need(fake.dels.join() === 'R20261116-090000.pcm' && /원본 없음/.test(hb().textContent) && !btn('원본만 지우기'), 'only the original is deleted: ' + fake.dels.join());
      btn('🗑 모두').click(); await sleep(20); [...d.querySelectorAll('.confirm-box button')].find(b => b.textContent === '삭제').click(); await sleep(40);
      need(fake.dels.includes('L20261116-090000.pcm') && !hb(), 'everything deleted only when asked: ' + fake.dels.join());
      fake.heard = []; ev("state.side=false;state.listening=[];store('ai_key','');saveHistory();render()"); await modeTo('conversation');
    });
    await step('A20/A24: short joined recordings go to Gemini together (up to 15 minutes), translation only; per row: translate again, show the original', async () => {
      await modeTo('listen'); ev("store('ai_key','AIzaTEST');store('rec_topic','금형 강의');store('gem_tier','fast');render()"); await sleep(300);
      const T = Date.now() - 2000000, mk = "(a,b)=>({original:'',translation:'',source:'en',target:'ko',failed:false,correcting:false,fromMic:true,micId:1,createdAt:Date.now(),piece:true,au:{f:'L20261116-100000.pcm',a,b,t0:" + T + "+a/16,t1:" + T + "+b/16},heardAt:" + T + "+b/16})";
      ev("{const mk=" + mk + ";state.listening=[mk(0,3840000),mk(3840000,7680000),mk(7680000,22080000)];saveHistory();render()}");   // 4분 · 4분 · 15분
      const TR = '금형 강의 번역문입니다. '.repeat(90).trim(), OR = 'This is the original talk. '.repeat(60).trim();
      fake.gem = b => b.generationConfig.responseSchema.required[0] === 's' ? { s: OR } : { t: TR }; fake.gemBodies = [];
      ev('listenTranslate()'); await sleep(10); const ct = d.querySelector('.confirm-box').textContent;
      need(/녹음 3개/.test(ct) && /15분까지 묶어 2번/.test(ct) && /번역문만/.test(ct), 'asks: ' + ct);
      [...d.querySelectorAll('.confirm-box button')].find(b => b.textContent === '번역').click(); await sleep(700);
      const rows = JSON.parse(ev('JSON.stringify(state.listening)'));
      need(rows.length === 2 && rows[0].bundle === 2 && rows[0].au.a === 0 && rows[0].au.b === 7680000 && rows[0].parts.length === 2 && !rows[1].bundle && rows.every(r => r.translation === TR && r.original === '' && r.trMode === 'fast'), 'two requests: the two short pieces together, the 15-minute piece alone: ' + JSON.stringify(rows.map(r => [r.bundle, r.au.a, r.au.b, r.translation.slice(0, 20)])));
      const b0 = fake.gemBodies[0].body, sys = b0.systemInstruction.parts[0].text;
      need(fake.gemBodies.length === 2 && JSON.stringify(b0.generationConfig.responseSchema.required) === '["t"]' && !b0.generationConfig.responseSchema.properties.s && /녹음의 종류: 금형 강의/.test(sys) && /번역문만 출력/.test(sys), 'translation only, with the kind of recording: ' + fake.gemBodies.length + ' ' + sys.slice(0, 80));
      need(/묶음 2개/.test(d.querySelector('.piece-tag').textContent) && /8:00/.test(d.querySelector('.piece-tag').textContent), 'bundle tag: ' + d.querySelector('.piece-tag').textContent);
      const acts = () => [...d.querySelector('.listen-row').querySelectorAll('.piece-acts button')];
      need(acts().length === 2 && /다시 번역/.test(acts()[0].textContent) && /영어 원문 보기/.test(acts()[1].textContent), 'two buttons per row: ' + acts().map(b => b.textContent).join());
      acts()[1].click(); await sleep(400);
      need(fake.gemBodies.length === 3 && JSON.stringify(fake.gemBodies[2].body.generationConfig.responseSchema.required) === '["s"]' && ev('state.listening[0].original') === OR && ev('state.listening[0].translation') === TR && ev('state.listening[1].original') === '' && acts().length === 1, 'the original is fetched only for that row, only when asked: ' + fake.gemBodies.length + ' ' + ev('JSON.stringify(state.listening.map(x=>x.original.slice(0,20)))'));
      acts()[0].click(); await sleep(400);
      need(fake.gemBodies.length === 4 && /a=-?\d+&b=7682400/.test(fake.recFetch.at(-1)), 'translate again sends only that row: ' + fake.recFetch.at(-1));
      ev("openSettings();state.setTab='ai';render()"); await sleep(30); need(!/한 번에 보내는 묶음 크기/.test(d.querySelector('.modal-content').textContent) && /녹음의 종류/.test(d.querySelector('.modal-content').textContent), 'the bundle-size choice is gone; the kind of recording stays'); ev('closeLayer()');
      fake.gem = null; ev("store('ai_key','');store('rec_topic','');state.listening=[];saveHistory();render()"); await modeTo('conversation');
    });
    await step('A21/A24: send-to-interpreter (Gemini · Claude); listen mode has three buttons — interpreter, send the picked recordings, send all recordings (several files in order)', async () => {
      await modeTo('conversation'); ev("store('show_sendto','0');store('show_gemapp','0');render()"); await sleep(50);
      need(!d.querySelector('.send-row') && !d.querySelector('.send-grid'), 'hidden until switched on');
      ev("store('show_sendto','1');render()"); await sleep(50);
      const sb = () => [...d.querySelectorAll('.send-row button')];
      need(sb().length === 2 && /Gemini로 보내기/.test(sb()[0].textContent) && /Claude로 보내기/.test(sb()[1].textContent), 'two buttons in conversation mode: ' + sb().map(b => b.textContent).join());
      fake.sent = []; fake.opened = []; fake.copied = []; fake.appTakesText = true; sb()[0].click(); await sleep(30);
      const lang = ev('active().name');
      need(fake.sent.length === 1 && fake.sent[0].pkg === 'com.google.android.apps.bard' && fake.sent[0].text.startsWith('너는 한국어와 ' + lang + ' 통역사다.') && fake.sent[0].text.includes(lang + '가 들리면 한국어로') && /"통역 끝"이라고 하면 멈춰라\.$/.test(fake.sent[0].text) && fake.copied.length === 0, 'prompt handed to the Gemini app with the chosen language: ' + JSON.stringify(fake.sent[0]).slice(0, 160));
      fake.appTakesText = false; fake.appInstalled = true; sb()[1].click(); await sleep(30);
      need(fake.sent.at(-1).pkg === 'com.anthropic.claude' && fake.copied.length === 1 && fake.copied[0] === fake.sent.at(-1).text && fake.opened.at(-1) === 'com.anthropic.claude' && /붙여넣어/.test(d.querySelector('.notice').textContent), 'cannot hand over → copied, app opened, told to paste: ' + d.querySelector('.notice').textContent);
      fake.appInstalled = false; sb()[1].click(); await sleep(30); need(/설치되어 있지 않습니다/.test(d.querySelector('.notice').textContent), 'not installed: ' + d.querySelector('.notice').textContent);
      // 듣기 모드: 버튼 세 개
      await modeTo('listen'); ev("store('show_gemapp','1');store('rec_topic','금형 강의');render()"); await sleep(30);
      const gb = () => [...d.querySelectorAll('.send-grid .send-btn')], gt = () => gb().map(b => b.textContent.replace(/\s+/g, ' ').trim());
      need(gb().length === 3 && /Gemini\s*듣기 통역사/.test(gt()[0]) && /선택한 녹음\s*Gemini로 보내기/.test(gt()[1]) && /전체 녹음\s*Gemini로 보내기/.test(gt()[2]) && !/앱으로 듣기/.test(d.querySelector('#app').textContent), 'three buttons, no "앱으로 듣기" label: ' + gt().join(' | '));
      fake.appTakesText = true; ev("state.listenFrom='foreign'"); gb()[0].click(); await sleep(30);
      need(fake.sent.at(-1).text.startsWith('지금부터 들리는 ' + lang + '를 한국어로만 바로 말해라.'), 'interpreter prompt: ' + fake.sent.at(-1).text.slice(0, 60));
      const T = Date.now() - 3000000, mk = "(a,b)=>({original:'',translation:'',source:'en',target:'ko',failed:false,correcting:false,fromMic:true,micId:1,createdAt:Date.now(),piece:true,au:{f:'L20261116-110000.pcm',a,b,t0:" + T + "+a/16,t1:" + T + "+b/16},heardAt:" + T + "+b/16})";
      ev("{const mk=" + mk + ";state.listening=[mk(0,14400000),mk(14400000,28800000),mk(28800000,43200000)];saveHistory();render()}"); await sleep(30);
      fake.sentAudios = []; fake.copied = []; gb()[1].click(); await sleep(30); need(fake.sentAudios.length === 0 && /○로 골라/.test(d.querySelector('.notice').textContent), 'nothing picked: ' + d.querySelector('.notice').textContent);
      ev("state.listening[0].sel=true;state.listening[2].sel=true;render()"); gb()[1].click(); await sleep(80);
      let sa = fake.sentAudios[0];
      need(sa && sa.pkg === 'com.google.android.apps.bard' && JSON.stringify(sa.list) === JSON.stringify([['L20261116-110000.pcm', 0, 14402400], ['L20261116-110000.pcm', 28797600, 43202400]]) && /음성 파일 1, 2을 번호 순서대로 차례로/.test(sa.text) && /1 → 2/.test(sa.text) && /영어/.test(sa.text) && /한국어로 번역/.test(sa.text) && /\[음성 파일 1\]/.test(sa.text) && /녹음의 종류: 금형 강의/.test(sa.text) && fake.copied[0] === sa.text, 'the two picked files go in order with the instruction: ' + JSON.stringify(sa).slice(0, 260));
      need(ev('!!state.listening[0].sentApp&&!state.listening[1].sentApp&&!!state.listening[2].sentApp'), 'sent rows are marked');
      gb()[2].click(); await sleep(80); sa = fake.sentAudios[1];
      need(sa && sa.list.length === 3 && /음성 파일 1, 2, 3을 번호 순서대로 차례로/.test(sa.text) && /1 → 2 → 3/.test(sa.text), 'all three files: ' + JSON.stringify(sa && sa.list));
      const ab = [...d.querySelectorAll('.piece-acts button')].find(b => /Gemini로 보내기/.test(b.textContent)); need(ab, 'the per-row button stays');
      fake.sentAudio = []; ab.click(); await sleep(80); need(fake.sentAudio.length === 1 && fake.sentAudio[0].f === 'L20261116-110000.pcm', 'one row alone: ' + JSON.stringify(fake.sentAudio[0]));
      ev("{const mk=" + mk + ";state.listening=Array.from({length:12},(_,i)=>mk(i*1600000,(i+1)*1600000));render()}"); gb()[2].click(); await sleep(80); sa = fake.sentAudios.at(-1);
      need(sa.list.length === 10 && /나머지 2개/.test(d.querySelector('.notice').textContent), 'ten files at a time: ' + sa.list.length + ' ' + d.querySelector('.notice').textContent);
      gb()[2].click(); await sleep(80); need(fake.sentAudios.at(-1).list.length === 2 && fake.sentAudios.at(-1).list[0][1] === 10 * 1600000 - 2400, 'the next press sends the rest: ' + JSON.stringify(fake.sentAudios.at(-1).list));
      ev("store('show_sendto','0');store('show_gemapp','0');store('rec_topic','');state.listening=[];saveHistory();render()"); await modeTo('conversation');
    });
    await step('A22: the phone voice with the best quality is used; a one-time offer to get a high-quality voice when there is none', async () => {
      await modeTo('conversation'); const code = ev('active().code'), loc = ev('localeOf(active().code)');
      fake.voices = [{ name: 'ko-low', lang: 'ko-KR', localService: true, q: 300 }, { name: 'ko-high', lang: 'ko-KR', localService: true, q: 400 }, { name: 'ko-net', lang: 'ko-KR', localService: false, q: 500 }, { name: 'fg-low', lang: loc, localService: true, q: 300 }];
      w.__nat.onVoices(); ev("state.voices={};localStorage.removeItem('hq_asked_ko');localStorage.removeItem('hq_asked_'+active().code);for(const k in hqSeen)delete hqSeen[k]"); await sleep(20);
      need(ev("voiceFor('ko').name") === 'ko-high' && ev("voiceHq('ko')") === true && ev('voiceHq(active().code)') === false, 'installed high-quality voice first: ' + ev("voiceFor('ko').name"));
      ev('render()'); await sleep(1800);
      const cb = d.querySelector('.confirm-box'); need(cb && /고품질 음성이 이 휴대폰에 없습니다/.test(cb.textContent) && cb.textContent.includes(ev('active().name')), 'offer for the language without one: ' + (cb ? cb.textContent : 'none'));
      fake.ttsInstalls = 0; [...cb.querySelectorAll('button')].find(b => /고품질 음성 받기/.test(b.textContent)).click(); await sleep(30);
      need(fake.ttsInstalls === 1, 'opens the phone voice-data screen');
      ev('render()'); await sleep(1800); need(!d.querySelector('.confirm-box'), 'asked only once per language');
      ev("state.setTab='basic';openSettings()"); await sleep(50); const lines = [...d.querySelectorAll('.hq-line')].map(x => x.textContent);
      need(lines.length === 2 && /✅/.test(lines[0]) && /⚠/.test(lines[1]) && [...d.querySelectorAll('.modal button')].some(b => b.textContent === '고품질 음성 받기'), 'settings show the state per language: ' + lines.join(' | '));
      need(ev("load('ai_voice_on')") !== '1', 'AI voice stays off unless switched on');
      ev('state.modal=null;render()'); fake.voices = null; w.__nat.onVoices(); await sleep(20);
    });
    await step('A23: only what is switched on in settings is on the screen; monthly usage with a limit in the admin menu', async () => {
      await modeTo('conversation'); ev("store('ai_key','AIzaTEST');render()"); if (!ev('state.items.length')) { await ev("consume('안녕하세요.','ko',{fromText:true})"); await sleep(300); } ev('render()'); await sleep(50);
      const has = sel => !!d.querySelector(sel), txt = () => d.querySelector('#app').textContent;
      need(/글로 통역/.test(txt()) && /사진 통역/.test(txt()) && d.querySelector('.ai-state').style.display !== 'none' && d.querySelectorAll('.ai-chip').length === 2 && d.querySelectorAll('.side-tab2').length === 3 && has('.entry-engine') && has('.ctrl.star'), 'everything visible on a phone that was already in use');
      // 설정 → 보이기 탭에서 끔
      ev("state.setTab='show';openSettings()"); await sleep(40);
      const sw = name => [...d.querySelectorAll('.sw-row')].find(r => r.textContent.includes(name)).querySelector('.sw');
      need(d.querySelectorAll('.sw-row').length === 14 && ![...d.querySelectorAll('.sw-row')].some(r => /폰 AI/.test(r.textContent)) && sw('사진 통역').textContent === '보임' && sw('통역사로 보내기').textContent === '숨김', 'switch list: ' + d.querySelectorAll('.sw-row').length);
      for (const n of ['사진 통역', '글로 통역', '발음 보기', '다시 번역', '별표 저장', '크게 보기', '단어장', '번역기 고르기', 'AI 통역사', 'AI 음성', '자주 쓰는 문장', '녹음 탭']) { sw(n).click(); await sleep(15); }
      need(sw('사진 통역').textContent === '숨김', 'switched off'); ev('closeLayer()'); await sleep(40);
      need(!/글로 통역/.test(txt()) && !/사진 통역/.test(txt()) && d.querySelector('.ai-state').style.display === 'none' && d.querySelectorAll('.ai-chip').length === 0 && d.querySelectorAll('.side-tab2').length === 0 && !has('.entry-engine') && !has('.ctrl.star') && !has('.edit-ctrl ~ .nothing'), 'buttons are gone from the screen: ' + [...d.querySelectorAll('.bar button,.talk-row button,.ctrls button')].map(b => b.textContent.trim()).join('|').slice(0, 200));
      need(has('.talk') && has('.mode') && /기록 삭제/.test(txt()), 'language buttons, mode, delete stay');
      d.querySelector('.bubble.ko, .bubble').click(); await sleep(30); need(ev('state.modal') == null, 'tapping a bubble no longer opens the large view');
      d.querySelector('.mode').click(); await sleep(30); need(ev('state.mode') === 'listen', 'to listen'); d.querySelector('.mode').click(); await sleep(30); need(ev('state.mode') === 'conversation', 'the collection mode is skipped when text · photo · recording are all hidden: ' + ev('state.mode'));
      need(ev('aiVoiceOn()') === false, 'AI voice is not used when hidden');
      ev("FEATS.forEach(([k])=>store('show_'+k,FEATS_NEW.includes(k)?'0':'1'));render()"); await sleep(30);
      // 처음 설치 = 모두 꺼짐 / 쓰던 휴대폰 = 쓰던 기능은 켜짐
      const init = ev("(used=>{const ls={};const get=k=>ls[k]??null;if(used)ls.travel_settings='{}';for(const [k] of FEATS)if(get('show_'+k)==null)ls['show_'+k]=used&&!FEATS_NEW.includes(k)?'1':'0';return Object.values(ls).filter(v=>v==='1').length})");
      need(init(false) === 0 && init(true) === 12, 'first install: all off; a phone already in use: the 12 existing features stay on: ' + init(false) + ',' + init(true));
      // 이번 달 사용량과 한도 (관리자 메뉴)
      const keepU = ev('JSON.stringify(aiUsage)'); d.querySelector('.notice')?.remove();
      ev("aiUsage={since:Date.now(),t:{},m:{}};store('usd_krw','1400');store('usd_krw_at',String(Date.now()));store('usage_limit_krw','50');store('usage_warn_day','')");
      ev("usageLive('AI 통역사 · 통역 전용',120,60,'tr')"); await sleep(20);
      const mo = JSON.parse(ev('JSON.stringify(usageMonth())')); need(mo.n === 1 && Math.abs(mo.sec - 120) < 0.01 && mo.c > 0, 'this month: ' + JSON.stringify(mo));
      need(/한도/.test(d.querySelector('.notice')?.textContent || '') && /%/.test(d.querySelector('.notice').textContent), 'warned once when the estimate passes 80% of the limit: ' + (d.querySelector('.notice')?.textContent || ''));
      d.querySelector('.notice').remove(); ev("usageLive('AI 통역사 · 통역 전용',60,60,'tr')"); await sleep(20); need(!d.querySelector('.notice'), 'not warned again the same day');
      ev("openSettings();state.adminOpen=true;state.adminTab='usage';render()"); await sleep(40); const at = d.querySelector('.admin-box').textContent;
      need(/이번 달 사용량/.test(at) && /어림값/.test(at) && /Gemini에 보낸 요청2번/.test(at) && /보낸 소리 길이3\.0분/.test(at) && /한도의 \d+%/.test(at) && [...d.querySelectorAll('.admin-box a')].some(a => /aistudio\.google\.com\/usage/.test(a.href)), 'month section: ' + at.slice(0, 200));
      ev("store('usage_limit_krw','0');state.adminOpen=false;closeLayer();store('ai_key','');render()"); ev('aiUsage=' + keepU);
    });
    await step('A24: Gemini 빠름 is the default everywhere; the phone AI takes over by itself only in an emergency (offline · no key · no credit), in conversation mode only', async () => {
      await modeTo('conversation'); ev("store('ai_key','AIzaTEST');store('gem_tier','fast');store('tr_engine','local');gemStop='';render()"); await sleep(50);
      const label = () => d.querySelector('.ai-state').textContent, menu = () => { [...d.querySelectorAll('.entry-engine')].at(-1).click(); const m = [...d.querySelectorAll('.entry-mode-menu button')].map(b => b.textContent).join(','); ev('entryModeMenu?.()'); return m; };
      if (!ev('state.items.length')) { fake.gem = () => ({ s: '안녕하세요.', t: 'こんにちは。' }); await ev("consume('안녕하세요.','ko',{fromText:true})"); await sleep(300); fake.gem = null; }
      ev("delete state.items.at(-1).top;state.items.at(-1).trMode='local';render()");
      need(ev('engine()') === 'gemini' && ev('currentEntryMode()') === 'fast' && /Gemini/.test(label()) && /빠름/.test(label()) && ev('engineChoices().join()') === 'fast,balanced,accurate' && menu() === '빠름,균형,정확', 'normal: Gemini 빠름, the phone AI is not offered: ' + label() + ' / ' + ev('engineChoices().join()'));
      // 인터넷이 끊김
      fake.online = false; w.dispatchEvent(new w.Event('offline')); await sleep(30);
      need(ev('engine()') === 'local' && /폰 AI \(비상용\)/.test(label()) && ev('engineChoices().join()') === 'local' && menu() === '폰AI', 'offline: only the phone AI is shown: ' + label() + ' / ' + menu());
      d.querySelector('.ai-state').click(); await sleep(20); need(ev('engine()') === 'local' && /인터넷이 끊겼습니다/.test(d.querySelector('.notice').textContent), 'tapping the engine button explains why: ' + d.querySelector('.notice').textContent);
      const c0 = fake.chats.length, n = ev('state.items.length'); await ev("consume('비상일 때 쓰는 새 문장입니다.','ko',{fromText:true})"); await sleep(200);
      need(ev('state.items.length') === n + 1 && ev('state.items.at(-1).trMode') === 'local' && fake.chats.length > c0, 'translated by the phone AI while offline: ' + ev('JSON.stringify(state.items.at(-1))').slice(0, 120));
      fake.online = true; w.dispatchEvent(new w.Event('online')); await sleep(30);
      need(ev('engine()') === 'gemini' && /Gemini/.test(label()), 'back to Gemini by itself when the internet returns: ' + label());
      // 크레딧 · 지출 한도
      ev("gemHalts=1;gemHalt('Gemini 지출 한도에 닿았습니다.');render()"); await sleep(20);
      need(ev('engine()') === 'local' && /폰 AI \(비상용\)/.test(label()) && /지출 한도/.test(ev('engineWhy()')), 'no credit: the phone AI takes over: ' + label());
      ev("gemStop='';gemHalts=0;store('ai_key','');render()"); await sleep(20);
      need(ev('engine()') === 'local' && /키가 없습니다/.test(ev('engineWhy()')), 'no key: the phone AI takes over');
      // 듣기 모드에는 적용하지 않음
      await modeTo('listen'); await sleep(30);
      need(ev('engine()') === 'none' && /번역기 없음/.test(d.querySelector('.chunk-btn').textContent), 'listen mode never uses the phone AI (no key → no translator): ' + d.querySelector('.chunk-btn').textContent);
      ev("store('ai_key','AIzaTEST');render()"); fake.online = false; ev('render()'); await sleep(20);
      need(ev('engine()') === 'gemini' && /빠름/.test(d.querySelector('.chunk-btn').textContent), 'listen mode stays on Gemini even when offline: ' + d.querySelector('.chunk-btn').textContent);
      fake.online = true; need(/5분 동안 말소리가 없어/.test(ev('activity.toString()')) && /stopMic\(true\)/.test(ev('activity.toString()')), 'listening stops by itself after five minutes without sound (keeps what was recorded)');
      ev("store('ai_key','');render()"); await modeTo('conversation');
      ev("openSettings();state.setTab='ai';render()"); await sleep(30); need(/폰 AI 번역은 비상용입니다/.test(d.querySelector('.modal-content').textContent) && /Gemma 4/.test(d.querySelector('.modal-content').textContent), 'the phone AI items stay in settings'); ev('closeLayer()');
    });
    await step('A14: 저장 keeps the rows with their sound; open them later from the recording tab', async () => {
      await modeTo('listen'); ev("store('ai_key','AIzaTEST');render()"); fake.gem = () => ({ t: '이 강연을 저장해 주세요.' });
      await sleep(900); const T = Date.now() - 9000, f = 'L20261115-102000.pcm';
      ev("pressTalk('foreign')"); await sleep(40); F('', { f, a: 16000, b: 64000, t0: T, t1: T + 3000 }); await sleep(60); ev("pressTalk('foreign')"); await sleep(1800);
      ev('listenTranslate()'); await sleep(10); [...d.querySelectorAll('.confirm-box button')].find(b => b.textContent === '번역').click(); await sleep(700); fake.gem = null;
      need(![...d.querySelectorAll('.top-left .home-btn')].some(b => /저장/.test(b.textContent)), 'the separate 저장 button is gone');
      const n0 = ev('recList.length'); fake.keeps = []; ev("state.listening.forEach(x=>x.sel=false);state.listening.at(-1).sel=true"); ev('shareAll()'); await sleep(10);
      [...d.querySelectorAll('.share-pick button')][3].click(); await sleep(200);     // 저장 · 전체
      need(ev('recList.length') === n0 + 1, 'not saved');
      const m = JSON.parse(ev('JSON.stringify(recList[0])'));
      need(m.saved && m.side === 'all' && m.rows.length === 1 && m.rows[0].translation === '이 강연을 저장해 주세요.' && m.rows[0].au.f === f && m.rows[0].au.a === 16000, 'saved bundle: ' + JSON.stringify(m).slice(0, 300));
      need(fake.keeps.join() === f + ':true', 'original sound file kept past five days: ' + fake.keeps.join());
      ev("openDrawer('rec')"); await sleep(20); const sb = d.querySelector('.rec-drawer .saved-item'); need(sb && /저장한 기록/.test(sb.textContent) && /1줄/.test(sb.textContent), 'listed in the recording tab'); 
      [...sb.querySelectorAll('button')].find(x => /열기/.test(x.textContent)).click(); await sleep(60);
      need(ev('state.mode') === 'record' && ev('state.board.at(-1).savedId') === m.id && ev('state.board.at(-1).translation') === '이 강연을 저장해 주세요.' && ev('state.board.at(-1).au.a') === 16000, 'opened in 모음: ' + ev('JSON.stringify(state.board.at(-1))').slice(0, 200));
      await ev("deleteSaved(recList[0])"); need(ev('recList.length') === n0 && fake.keeps.at(-1) === f + ':false', 'deleted; sound file may be cleaned again: ' + fake.keeps.join());
      await modeTo('listen');
      ev("state.listening.forEach(x=>x.sel=false)"); await modeTo('conversation'); ev("store('ai_key','');setEngineMode('local');render()");
    });
    await step('A12: AI usage shows the estimated cost in won, per task and in total, with the price rises by date', async () => {
      const near = (a, b) => Math.abs(a - b) < 1e-9;
      need(ev("gemPrice('gemini-3.5-flash-lite').join()") === '0.3,2.5', 'flash-lite');
      need(ev("gemPrice('gemini-4-argon',new Date(2026,10,20).getTime()).join()") === '2,10' && ev("gemPrice('gemini-4-argon',new Date(2026,11,1).getTime()).join()") === '4,20', 'argon rises on Dec 1');
      need(ev("gemPrice('gemini-3.8-flash',new Date(2026,11,31).getTime()).join()") === '0.75,3.75' && ev("gemPrice('gemini-3.8-flash',new Date(2027,0,1).getTime()).join()") === '1.5,7.5', '3.8 flash rises on Jan 1');
      need(ev("gemPrice('gemini-3.8-flash-lite-tts',new Date(2026,11,31).getTime()).join()") === '0.5,6' && ev("gemPrice('gemini-3.8-flash-lite-tts',new Date(2027,0,1).getTime()).join()") === '1,12' && ev("gemPrice('gemini-3.1-flash-tts-preview').join()") === '1,20', 'tts');
      const hear = JSON.parse(ev("JSON.stringify(aiUsage.t['소리 듣고 번역']||null)")); need(hear && hear.n >= 2 && hear.c > 0, 'sound task recorded with a cost: ' + JSON.stringify(hear));
      ev("aiUsage={since:Date.now(),t:{}};usageLive('AI 통역사 · 통역 전용',60,60,'tr');usageLive('AI 통역사 · 대화 (3.8 Live)',60,60,'live')");
      need(near(ev("aiUsage.t['AI 통역사 · 통역 전용'].c"), 0.0368) && near(ev("aiUsage.t['AI 통역사 · 대화 (3.8 Live)'].c"), 0.023), 'live per-minute prices');
      ev("store('usd_krw','1400');store('usd_krw_at',String(Date.now()));openSettings();state.adminOpen=true;state.adminTab='usage';render()"); await sleep(30); const t = d.querySelector('#app').textContent;
      need(/지금까지 쓴 금액 \(추정\)약 84원/.test(t) && /약 52원/.test(t) && /약 32원/.test(t), 'won shown: ' + (t.match(/지금까지 쓴 금액.{0,40}/) || [''])[0]);
      ev("store('usd_krw','1500');render()"); need(/약 90원/.test(d.querySelector('#app').textContent), 'exchange rate applied'); ev("closeLayer()");
      fake.fx = []; fake.fxFail = true; await ev("store('usd_krw_at','0');fxRefresh(true)"); need(ev('usdRate()') === 1500 && fake.fx.length === 2, 'keeps the last value when the rate cannot be fetched: ' + ev('usdRate()'));
      fake.fxFail = false; fake.fxFirstFail = true; fake.fx = []; await ev("fxRefresh(true)"); need(ev('usdRate()') === 1473 && ev("load('usd_krw_auto')") === '1' && fake.fx.length === 2, 'second source used: ' + ev('usdRate()'));
      fake.fxFirstFail = false; fake.fx = []; await ev("fxRefresh()"); need(fake.fx.length === 0, 'asks only once a day');
      ev("openSettings();state.adminOpen=true;state.adminTab='usage';render()"); await sleep(30); need(/1달러 = 1,473원/.test(d.querySelector('#app').textContent) && /자동으로 가져옴/.test(d.querySelector('#app').textContent) && [...d.querySelectorAll('input')].filter(i => i.type === 'number').length === 1, 'rate shown as one line, no input box for it (the only number box is the monthly limit)'); ev("store('usd_krw','1400');state.adminOpen=false;closeLayer()");
    });
    await step('A14: the step only goes up — a row made with 정확 cannot be changed to a lower step', async () => {
      await modeTo('conversation'); ev("store('ai_key','AIzaTEST');render()");
      ev("state.items.at(-1).trMode='accurate';state.items.at(-1).top=3;render()"); [...d.querySelectorAll('.entry-engine')].at(-1).click();
      let m = [...d.querySelectorAll('.entry-mode-menu button')].map(b => b.textContent).join(','); need(m === '정확', 'top row menu: ' + m); ev('entryModeMenu?.()');
      ev("state.items.at(-1).trMode='fast';state.items.at(-1).top=1;render()"); [...d.querySelectorAll('.entry-engine')].at(-1).click();
      m = [...d.querySelectorAll('.entry-mode-menu button')].map(b => b.textContent).join(','); need(m === '빠름,균형,정확', 'fast row menu: ' + m); ev('entryModeMenu?.()');
      ev("delete state.items.at(-1).top;state.items.at(-1).trMode='local';render()"); [...d.querySelectorAll('.entry-engine')].at(-1).click();
      m = [...d.querySelectorAll('.entry-mode-menu button')].map(b => b.textContent).join(','); need(m === '빠름,균형,정확', 'a phone AI row can go up to the Gemini steps (the phone AI itself is not offered while Gemini works): ' + m); ev('entryModeMenu?.()');
    });
    await step('A14: delete only the picked rows (asks twice)', async () => {
      const n = ev('state.items.length'); need(n >= 3, 'rows'); ev("state.items.forEach(x=>x.sel=false);state.items[0].sel=true;state.items[1].sel=true;render()");
      const keep = ev('state.items[2].original'); d.querySelector('.wipe').click(); await sleep(10);
      const b1 = [...d.querySelectorAll('.share-pick button')].map(b => b.textContent); need(b1[0] === '고른 2줄만 삭제' && b1[1] === '전체 삭제' && b1[2] === '취소', 'asks: ' + b1.join());
      d.querySelector('.share-pick button').click(); await sleep(10); need(/고른 2줄을 지울까요/.test(d.querySelector('.confirm-box')?.textContent || ''), 'second question: ' + (d.querySelector('.confirm-box')?.textContent || ''));
      [...d.querySelectorAll('.confirm-box button')].find(b => b.textContent === '삭제').click(); await sleep(20);
      need(ev('state.items.length') === n - 2 && ev('state.items[0].original') === keep, 'picked rows deleted: ' + ev('state.items.length'));
    });
    await step('A14: one photo = one row; AI voice is saved and replayed without internet; the model in use is marked', async () => {
      const es = JSON.parse(ev("JSON.stringify(photoEntries({id:7,at:1,fg:'ja',blocks:[{lang:'ja',o:'山田太郎',tr:{ko:'야마다 타로'}},{lang:'ja',o:'営業部長',tr:{ko:'영업부장'}},{lang:'ko',o:'서울',tr:{ja:'ソウル'}}]}))"));
      need(es.length === 1 && es[0].original === '山田太郎\n営業部長\n서울' && es[0].translation === '야마다 타로\n영업부장\nソウル' && es[0].source === 'ja' && es[0].target === 'ko' && es[0].photoBlock === 'all' && es[0].kind === 'photo', 'photo row: ' + JSON.stringify(es));
      ev("store('ai_key','AIzaTEST');store('ai_voice_on','1');render()"); const t0 = fake.tts || 0; ev("speak('ありがとうございます。','ja')"); await sleep(400);
      need((fake.tts || 0) === t0 + 1 && ev("!!aiSavedKey('ありがとうございます。',null)"), 'AI voice stored after the first reading: ' + ev('[...voiceKeys].length'));
      ev("store('ai_voice_on','0');aiTtsCache.clear()"); fake.online = false; const a0 = fake.audio || 0, s0 = fake.spoken.length; ev("speak('ありがとうございます。','ja')"); await sleep(300);
      need((fake.tts || 0) === t0 + 1 && (fake.audio || 0) === a0 + 1 && fake.spoken.length === s0, 'offline and AI voice off: the saved AI voice is used (no new request, no phone voice)'); fake.online = true;
      ev("openSettings();state.setTab='ai';render()"); await sleep(30); need(d.querySelector('.rec-item.in-use .use-badge') && /사용 중/.test(d.querySelector('.use-badge').textContent), 'model in use is marked'); ev('closeLayer()');
      ev("openDrawer('rec')"); await sleep(20); need(d.querySelector('.rec-two .rec-tr') && /번역/.test(d.querySelector('.rec-two .rec-tr').textContent), 'big 번역 button next to 녹음 시작'); ev('closeLayer()');
      ev("store('ai_key','');setEngineMode('local');render()");
    });
    await step('A15: deleting rows keeps the AI voice that a saved record still uses', async () => {
      await modeTo('conversation');
      ev("state.items.push({original:'고맙습니다',translation:'助かりました。',source:'ko',target:'ja',failed:false,trMode:'fast'})");
      const key = ev("ttsKey('助かりました。','')"); await ev("voicePut(" + JSON.stringify(key) + ",new Blob([new Uint8Array(2000)]))"); need(ev("voiceKeys.has(" + JSON.stringify(key) + ")"), 'clip stored');
      ev("recList.unshift({id:'save-t',at:Date.now(),saved:true,side:'all',status:'done',rows:[{original:'고맙습니다',translation:'助かりました。',source:'ko',target:'ja'}]})");
      ev("dropRows([state.items.at(-1)])"); await sleep(60); need(ev("voiceKeys.has(" + JSON.stringify(key) + ")"), 'the saved record still needs this voice, so it must stay');
      ev("state.items.push({original:'고맙습니다',translation:'助かりました。',source:'ko',target:'ja',failed:false,trMode:'fast'});recList.shift()");
      ev("dropRows([state.items.at(-1)])"); await sleep(60); need(!ev("voiceKeys.has(" + JSON.stringify(key) + ")"), 'nobody uses it any more, so it is removed');
    });
    await step('share goes to the phone share sheet', async () => { await modeTo('conversation'); ev("state.items.forEach(x=>x.sel=false)"); const s0 = fake.shared.length; ev('shareAll()'); await sleep(10); d.querySelector('.share-pick button').click(); await sleep(30); need(fake.shared.length === s0 + 1 && /안녕하세요/.test(fake.shared.at(-1)), 'shared'); });
    await step('A11: delete the model with no key → no translator, the row says so', async () => { ev("NAT.llm.remove('gemma4-e4b')"); await sleep(80); need(ev('localReady()') === false && ev('engine()') === 'none' && /번역기 없음/.test(ev('engLabel()')), ev('engLabel()')); await ev("consume('테스트','ko',{fromText:true})"); await sleep(200); need(/번역 실패/.test(ev('state.items.at(-1).translation')) && /번역기가 준비되지 않았습니다/.test(ev('state.items.at(-1).translation')), ev('state.items.at(-1).translation')); });
  }
  await step('common screens', async () => { if (ev("state.page") !== 'main') d.querySelector('.home')?.click(); ev("openDrawer('notes')"); ev('closeLayer()'); ev("openDrawer('refs')"); ev('closeLayer()'); ev('openPhrases()'); ev('openText()'); ev('openPhoto()'); ev('closeLayer()'); ev('openSettings()'); ev('closeLayer()'); ev('resetTranscripts();render()'); ev('goHome()'); });
  await sleep(300);
  console.log(errors.length ? '\nERRORS:\n' + errors.join('\n---\n') : '\nNO ERRORS');
  process.exit(errors.length ? 1 : 0);
})();
