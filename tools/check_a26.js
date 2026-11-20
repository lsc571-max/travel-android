// A26 재현 시험: 2026-11-20 검토에서 찾은 문제 8가지(+ 군말 언어 문제)가 고쳐졌는지 본다.
//   NODE_PATH=<jsdom 설치 폴더>/node_modules node tools/check_a26.js app/src/main/assets [저장소 폴더]
// 고치기 전 코드(A25)에서는 여기 시험들이 실패해야 한다 (2차 검증).
const { JSDOM, VirtualConsole } = require('jsdom');
const fs = require('fs'), path = require('path');
const dir = process.argv[2] || 'app/src/main/assets', repo = process.argv[3] || path.join(dir, '..', '..', '..', '..');
let html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
const nativeJs = fs.readFileSync(path.join(dir, 'native.js'), 'utf8');
html = html.replace('<script src="native.js"></script>', '<script>' + nativeJs + '</script>');
const errors = [], results = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => errors.push('jsdomError: ' + (e.detail?.stack || e.message)));
const fake = { spoken: [], chats: [], lsessions: [], online: true, gem: null, uploads: [], llmHold: false, llmDelay: 0, fast: false };
let realSetTimeout;
const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://app.travel.local/index.html', virtualConsole: vc,
  beforeParse(w) {
    realSetTimeout = w.setTimeout.bind(w);
    // 시계를 빠르게: fake.fast 이면 1분 넘는 타이머를 20ms로 (시간 제한 시험용)
    const st0 = w.setTimeout.bind(w); w.setTimeout = (f, ms, ...a) => st0(f, fake.fast && ms >= 30000 ? 20 : ms, ...a);
    w.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {} });
    w.scrollTo = () => {}; w.Element.prototype.scrollIntoView = () => {}; w.Element.prototype.scrollTo = () => {};
    try { w.localStorage.setItem('show_init', '1'); for (const k of ['photo', 'text', 'pron', 'retr', 'star', 'big', 'refs', 'engine', 'gemma', 'interp', 'aivoice', 'notes', 'rec']) w.localStorage.setItem('show_' + k, '1'); } catch (e) { }
    Object.defineProperty(w.navigator, 'onLine', { get: () => fake.online, configurable: true });
    try { const fi = require('fake-indexeddb'); w.indexedDB = fi.indexedDB; w.IDBKeyRange = fi.IDBKeyRange; } catch (e) { }
    const hang = opt => new Promise((_, rej) => { const s = opt && opt.signal; if (s) { if (s.aborted) rej(Object.assign(Error('aborted'), { name: 'AbortError' })); s.addEventListener('abort', () => rej(Object.assign(Error('aborted'), { name: 'AbortError' }))); } });
    w.fetch = async (url, opt) => {
      const u = String(url);
      if (u.includes('/upload/v1beta/files')) { fake.uploads.push('start'); if (fake.uploadHang === 'start') return hang(opt); return { ok: true, status: 200, headers: { get: k => k === 'x-goog-upload-url' ? 'https://upload.example/u1' : null }, json: async () => ({}) }; }
      if (u.startsWith('https://upload.example/')) { fake.uploads.push('body'); if (fake.uploadHang === 'body') return hang(opt); return { ok: true, status: 200, json: async () => ({ file: { name: 'files/x1', state: 'ACTIVE', uri: 'https://gem/files/x1' } }) }; }
      if (u.includes('/rec/')) { const big = fake.bigSound ? 15e6 : 160000; return { ok: true, status: 200, blob: async () => new w.Blob([new Uint8Array(big)], { type: 'audio/wav' }) }; }
      if (u.includes(':generateContent') && fake.gem) { const body = JSON.parse(opt.body); (fake.gemBodies = fake.gemBodies || []).push(body); if (fake.gemDelay) await new Promise(r => realSetTimeout(r, fake.gemDelay)); return { ok: true, status: 200, json: async () => ({ candidates: [{ content: { parts: [{ text: fake.gem(body) }] }, finishReason: 'STOP' }], usageMetadata: {} }), clone() { return this; } }; }
      return { ok: false, status: 500, json: async () => ({}), clone() { return this; } };
    };
    w.URL.createObjectURL = () => 'blob:fake'; w.URL.revokeObjectURL = () => {};
    w.Audio = class { play() { return Promise.resolve(); } pause() {} };
    w.AbortSignal.timeout = w.AbortSignal.timeout || (() => new w.AbortController().signal);
    w.addEventListener('error', e => errors.push('window error: ' + (e.error?.stack || e.message)));
    const nat = (fn, o) => realSetTimeout(() => w.__nat && w.__nat[fn](o), 1);
    const st = () => JSON.stringify({ engine: true, state: 'ready', error: '', model: 'gemma4-e4b', hasModel: true });
    w.AndroidBridge = {
      info: () => JSON.stringify({ version: '1.0', sdk: 34, stt: true, sttOffline: false, llmEngine: true }),
      sttStart(sid, lang) { fake.sid = sid; fake.google = true; nat('onStt', { sid, type: 'start' }); },
      sttStop(sid) { nat('onStt', { sid, type: 'end' }); }, sttAbort(sid) { nat('onStt', { sid, type: 'end' }); },
      ttsVoices: () => JSON.stringify([{ name: 'ko-KR-a', lang: 'ko-KR', localService: true }, { name: 'ja-JP-a', lang: 'ja-JP', localService: true }]),
      ttsInstall: () => true,
      ttsSpeak(id, text) { fake.spoken.push(text); nat('onTts', { id, type: 'start', charIndex: 0 }); realSetTimeout(() => w.__nat.onTts({ id, type: 'end', charIndex: 0 }), 15); },
      ttsCancel() {},
      llmState: st, llmEnsure() {}, llmStop() {},
      llmChat(id, body) {
        const b = JSON.parse(body); fake.chats.push(b); if (!fake.noStart) nat('onLlm', { id, started: true }); if (fake.llmHold) return;   // 답이 오지 않는 경우
        const sys = b.messages[0].role === 'system' ? b.messages[0].content : '', inp = (b.messages.at(-1).content || '').replace(/^\[입력\] /, '');
        const out = 'LOCAL-こんにちは' + fake.chats.length;
        realSetTimeout(() => w.__nat.onLlm({ id, ok: true, text: /JSON/.test(sys) ? '```json\n' + JSON.stringify({ s: inp, t: out }) + '\n```' : out }), fake.llmDelay || 1);
      },
      models: () => JSON.stringify([{ id: 'gemma4-e4b', kind: 'mt', type: 'chat', name: 'Gemma 4', selected: true, state: 'ready', done: 1, total: 1, langs: '' }, { id: 'whisper-turbo', kind: 'stt', type: 'whisper', name: 'Whisper', selected: true, state: 'ready', done: 1, total: 1, langs: '' }]),
      modelDownload() {}, modelCancel() {}, modelDelete() {}, modelSelect() {}, modelAdd: () => '',
      share() {}, copy() {}, paste: () => '',
      lsttInfo: () => JSON.stringify({ lib: true, usable: !fake.noLocalStt, model: 'whisper-turbo', langs: '', running: false, busy: false }),
      lsttStart(sid, lang, cont) { fake.lsessions.push({ sid, lang, cont }); fake.sid = sid; nat('onStt', { sid, type: 'start' }); },
      lsttStart2(sid, lang, cont) { fake.lsessions.push({ sid, lang, cont }); fake.sid = sid; nat('onStt', { sid, type: 'start' }); },
      lsttEnd(sid) { nat('onStt', { sid, type: 'end' }); },
      lsttFile() {}, setMic() {}, setCapture() {}, setKeepRec() {}, sendText: () => false, openApp: () => false,
      recFiles: () => JSON.stringify({ files: [], free: 52e9 }), recDelete: () => true, recKeep() {},
      pcmStart() {}, pcmStop() {}, headset: () => false, setBackground() {}, setPlaying() {},
      saveBegin: () => true, saveChunk: () => true, saveEnd: () => true, keepAwake() {}, openUrl() {}
    };
  }
});
const w = dom.window, d = w.document, ev = s => w.eval(s);
const sleep = ms => new Promise(r => realSetTimeout(r, ms));
const need = (c, m) => { if (!c) throw Error(m); };
const within = (p, ms, what) => Promise.race([p, new Promise((_, rej) => realSetTimeout(() => rej(Error(what + ': ' + ms + 'ms 안에 끝나지 않음 (시간 제한 없음)')), ms))]);
const step = async (name, fn) => { try { await fn(); console.log('ok   ', name); results.push([name, true]); } catch (e) { console.log('FAIL ', name, '—', e.message); results.push([name, false]); } };
const hide = on => { Object.defineProperty(d, 'hidden', { get: () => on, configurable: true }); Object.defineProperty(d, 'visibilityState', { get: () => on ? 'hidden' : 'visible', configurable: true }); d.dispatchEvent(new w.Event('visibilitychange')); };

(async () => {
  await sleep(300);
  d.querySelector('.home')?.click(); await sleep(50);
  ev("store('ai_key','');render()");   // Gemini 키 없음 → 대화 모드 번역은 폰 AI

  await step('1a. 화면이 꺼져도 진행 중인 번역은 끝까지 (마이크가 꺼져 있을 때)', async () => {
    fake.llmDelay = 300;
    const p = ev("consume('안녕하세요. 반갑습니다.','ko',{fromText:true})"); await sleep(60);
    const e = 'state.items.at(-1)';
    need(ev(e + '.correcting') === true, '번역이 시작되지 않음: ' + ev('JSON.stringify(' + e + ')'));
    hide(true); await sleep(20); hide(false);
    await p; await sleep(400);
    const t = ev(e + '.translation'), f = ev(e + '.failed');
    need(!f && /^LOCAL-/.test(t || ''), '번역이 취소됨: ' + JSON.stringify(t));
    fake.llmDelay = 0;
  });

  await step('1b. 화면이 꺼지면 마이크는 끄고(구글 인식), 진행 중인 번역은 계속', async () => {
    fake.noLocalStt = true; ev("NAT.stt.refresh()");
    fake.llmDelay = 300;
    const p = ev("consume('화장실은 어디에 있나요?','ko',{fromText:true})"); await sleep(40);
    ev("pressTalk('ko')"); await sleep(40);
    need(ev('state.mic') === true && ev('bgListen()') === false, '마이크가 켜지지 않음');
    hide(true); await sleep(20);
    need(ev('state.mic') === false, '화면이 꺼졌는데 마이크가 그대로');
    hide(false); await p; await sleep(400);
    const e = JSON.parse(ev("JSON.stringify(state.items.find(x=>x.original&&/화장실/.test(x.original)))"));
    need(e && !e.failed && /^LOCAL-/.test(e.translation || ''), '번역이 취소됨: ' + JSON.stringify(e && e.translation));
    fake.noLocalStt = false; ev("NAT.stt.refresh()"); fake.llmDelay = 0;
  });

  await step('2. 폰 AI 번역에 시간 제한 (답이 없으면 "시간 초과"로 실패, 1분 + 답 길이, 최대 4분)', async () => {
    fake.llmHold = true; fake.fast = true;
    let err = null;
    try { await within(ev("NAT.llm.chat({messages:[{role:'user',content:'x'}],max_tokens:50})"), 1500, '폰 AI 답 기다림'); } catch (e) { err = e; }
    fake.fast = false; fake.llmHold = false;
    need(err && /시간 초과/.test(err.message) && !/끝나지 않음/.test(err.message), '실패 이유: ' + (err && err.message));
    // 폰이 번역을 시작하지 못한 채 멈춰 있어도(엔진 준비·앞 요청 기다림) 끝내는 실패함
    fake.llmHold = true; fake.noStart = true; fake.fast = true; err = null;
    try { await within(ev("NAT.llm.chat({messages:[{role:'user',content:'x'}],max_tokens:50})"), 1500, '폰 AI 시작 기다림'); } catch (e) { err = e; }
    fake.fast = false; fake.llmHold = false; fake.noStart = false;
    need(err && /시간 초과/.test(err.message) && !/끝나지 않음/.test(err.message), '시작 못 함 실패 이유: ' + (err && err.message));
    need(ev("NAT.llm.waitMs({max_tokens:100})") === 70000 && ev("NAT.llm.waitMs({max_tokens:9000})") === 240000, '시간 계산: ' + ev("NAT.llm.waitMs({max_tokens:100})"));
  });

  await step('3. 큰 녹음을 Gemini에 올릴 때 시간 제한 (올리는 중 멈추면 그 줄만 "시간 초과")', async () => {
    ev("store('ai_key','AIzaTEST');render()");
    for (const where of ['start', 'body']) {
      fake.uploadHang = where; fake.fast = true; let err = null;
      try { await within(ev("gemUpload(new Blob([new Uint8Array(20)]),'audio/wav','x',()=>{})"), 1500, '올리기(' + where + ')'); } catch (e) { err = e; }
      fake.fast = false;
      need(err && /시간 초과/.test(err.message) && !/끝나지 않음/.test(err.message), where + ' 실패 이유: ' + (err && err.message));
    }
    // 듣기 모드 녹음 조각: 큰 소리를 올리다 멈추면 그 줄만 실패 이유가 남음
    fake.uploadHang = 'body'; fake.bigSound = true; fake.fast = true;
    ev("state.listening.push({original:'',translation:'',source:'en',target:'ko',piece:true,fromMic:true,au:{f:'L20261120-100000.pcm',a:0,b:16000*600,t0:1,t1:2},heardAt:2,createdAt:1})");
    let p; try { p = ev("scheduleEntry(state.listening.at(-1),'fast',{})"); await within(p, 2500, '녹음 조각 번역'); } catch (e) { fake.fast = false; throw e; }
    fake.fast = false; fake.uploadHang = null; fake.bigSound = false;
    const e = JSON.parse(ev('JSON.stringify(state.listening.at(-1))'));
    need(e.correcting === false && /시간 초과/.test(e.err || ''), '줄 상태: ' + JSON.stringify({ c: e.correcting, err: e.err, t: e.translation }));
    ev("dropRows([state.listening.at(-1)])");
  });

  await step('4. 배포용 설정 (디버그 끔 · 백업 끔 · 같은 서명 키)', async () => {
    const rd = p => fs.readFileSync(path.join(repo, p), 'utf8');
    const g = rd('app/build.gradle'), m = rd('app/src/main/AndroidManifest.xml'), y = rd('.github/workflows/build.yml'), j = rd('app/src/main/java/kr/pureun/travel/MainActivity.java');
    need(/release\s*\{[^}]*signingConfig signingConfigs\.debug[^}]*debuggable false/.test(g), 'build.gradle: release 설정 없음');
    need(/storeFile rootProject\.file\('keystore\/debug\.keystore'\)/.test(g), '서명 키가 바뀜');
    need(/android:allowBackup="false"/.test(m), 'allowBackup');
    need(/assembleRelease/.test(y) && /apk\/release\/app-release\.apk/.test(y) && !/assembleDebug/.test(y), 'workflow가 배포용을 만들지 않음');
    need(!/setWebContentsDebuggingEnabled\(true\)/.test(j), '화면 디버깅이 늘 켜짐');
  });

  await step('5. 말로 입력하기: 폰 안 음성 인식에서 앞 문장이 사라지지 않음', async () => {
    fake.noLocalStt = false; fake.llmDelay = 0; ev("NAT.stt.refresh();if(state.mic)stopMic()"); await sleep(20);
    const area = d.createElement('textarea'), btn = d.createElement('button'); d.body.append(area, btn);
    area.value = '처음 글.';
    w.__area = area; w.__btn = btn;
    ev("dictateTo(window.__area,'ko',window.__btn,null)"); await sleep(20);
    need(fake.lsessions.length, '폰 안 인식이 시작되지 않음: ' + JSON.stringify({ g: fake.google, info: ev('JSON.stringify(NAT.stt.info())'), loc: ev("NAT.stt.useLocal('ko-KR')"), eng: ev("load('stt_engine')") }));
    const F = t => w.__nat.onStt({ sid: fake.sid, type: 'final', text: t });
    w.__nat.onStt({ sid: fake.sid, type: 'partial', text: '첫 문장' }); F('첫 문장입니다.'); await sleep(5);
    w.__nat.onStt({ sid: fake.sid, type: 'partial', text: '두 번째' }); await sleep(5);
    need(/첫 문장입니다\. 두 번째/.test(area.value), '듣는 중: ' + area.value);
    F('두 번째 문장입니다.'); await sleep(5); F('세 번째.'); await sleep(5);
    const v = area.value; ev('stopDictation()');
    need(/^처음 글\. 첫 문장입니다\. 두 번째 문장입니다\. 세 번째\.$/.test(v), '받아 적힌 글: ' + v);
  });

  await step('6. 군말 빼기: 대문자 약어(ER·UM)와 다른 언어의 낱말(독일어 er·포르투갈어 um)은 그대로', async () => {
    const t = (s, l) => ev('stripFillers(' + JSON.stringify(s) + (l ? ',' + JSON.stringify(l) : '') + ')');
    need(/\bER\b/.test(t('Take him to the ER now.', 'en')), 'ER: ' + t('Take him to the ER now.', 'en'));
    need(/\bER\b/.test(t('Take him to the ER now.')), 'ER (언어 모름): ' + t('Take him to the ER now.'));
    need(/\bUM\b/.test(t('I studied at UM.', 'en')), 'UM: ' + t('I studied at UM.', 'en'));
    need(t('Er ist hier.', 'de') === 'Er ist hier.', '독일어: ' + t('Er ist hier.', 'de'));
    need(t('Eu tenho um carro.', 'pt') === 'Eu tenho um carro.', '포르투갈어: ' + t('Eu tenho um carro.', 'pt'));
    need(t('Um, I think, uh, we should go.', 'en') === 'I think, we should go.', '영어 군말은 뺌: ' + t('Um, I think, uh, we should go.', 'en'));
    need(ev("ruleClean('Er kommt um acht Uhr.','de')") === 'Er kommt um acht Uhr.', 'ruleClean 독일어: ' + ev("ruleClean('Er kommt um acht Uhr.','de')"));
    need(t('음 그러니까 어 내일 가요.', 'ko') === '그러니까 내일 가요.', '한국어 군말: ' + t('음 그러니까 어 내일 가요.', 'ko'));
  });

  await step('7. 다른 줄의 🔊를 눌러도 번역을 기다리던 새 문장은 번역이 끝나면 읽힘', async () => {
    ev("store('ai_key','');render()");
    await sleep(100); fake.spoken.length = 0; fake.llmDelay = 400;
    const p = ev("consume('오늘 회의는 세 시에 시작합니다.','ko',{fromText:true})"); await sleep(50);
    need(ev("outQ.some(q=>q.entry===state.items.at(-1)&&!q.ready)"), '새 문장이 읽을 차례에 없음');
    ev("speak('다른 줄 문장입니다.','ko')"); await sleep(30);
    await p; await sleep(600);
    fake.llmDelay = 0;
    need(fake.spoken.includes('다른 줄 문장입니다.'), '누른 줄을 읽지 않음: ' + JSON.stringify(fake.spoken));
    const tr = ev('state.items.at(-1).translation'); need(/^LOCAL-/.test(tr), '새 문장 번역: ' + tr);
    need(fake.spoken.some(x => x === tr), '새 문장이 읽히지 않음: ' + JSON.stringify(fake.spoken) + ' / ' + tr);
  });

  await step('8. "이 구간 다시 번역"을 해도 받아 둔 원문은 남음', async () => {
    ev("store('ai_key','AIzaTEST');render()");
    fake.gem = body => JSON.stringify({ t: '다시 번역한 문장입니다.' });
    ev("state.listening.push({original:'This is the original text.',translation:'처음 번역.',source:'en',target:'ko',piece:true,fromMic:true,trMode:'fast',top:1,au:{f:'L20261120-110000.pcm',a:0,b:80000,t0:1,t1:2},heardAt:2,createdAt:1,failed:false})");
    await within(ev("scheduleEntry(state.listening.at(-1),'fast',{retranslate:true})"), 3000, '다시 번역');
    const e = JSON.parse(ev('JSON.stringify(state.listening.at(-1))'));
    need(e.translation === '다시 번역한 문장입니다.', '번역: ' + e.translation + ' / ' + e.err);
    need(e.original === 'This is the original text.', '원문이 지워짐: ' + JSON.stringify(e.original));
    fake.gem = null;
  });

  await sleep(100);
  const bad = results.filter(r => !r[1]);
  console.log('\n' + (results.length - bad.length) + '/' + results.length + ' 통과' + (errors.length ? '\nERRORS:\n' + errors.join('\n') : ''));
  process.exit(bad.length || errors.length ? 1 : 0);
})();
