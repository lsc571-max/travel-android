import sys, re
d = sys.argv[1]
# ───────── native.js ─────────
p = d + '/native.js'; s = open(p, encoding='utf-8').read()
def rep(old, new):
    global s
    assert s.count(old) == 1, ('count', s.count(old), old[:70])
    s = s.replace(old, new)
rep("""  /* ── 1) 음성 인식: 웹의 SpeechRecognition 모양 그대로 ── */
  let sidSeq = 0;""", """  /* ── 1) 음성 인식: 웹의 SpeechRecognition 모양 그대로 ──
     두 가지 엔진: 폰 안 AI(끊기지 않는 마이크, lstt*) · 휴대폰의 구글 음성 인식(stt*) */
  let sttInfo = {}, headAt = 0, headVal = false, bgVal = null;
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
    headset() { const now = Date.now(); if (now - headAt > 2000) { headAt = now; try { headVal = !!B.headset() } catch (e) { headVal = false } } return headVal },
    setBackground(on) { on = !!on; if (on !== bgVal) { bgVal = on; B.setBackground(on) } }
  };
  let sidSeq = 0;""")
rep("""      let off = false; try { off = localStorage.getItem('stt_offline') === '1' } catch (e) { }
      B.sttStart(this._sid, this.lang, !!this.continuous, off);
    }
    stop() { if (this._sid) B.sttStop(this._sid) }
    abort() { if (this._sid) B.sttAbort(this._sid) }""",
"""      this._lastLang = '';
      this._local = this.lang === 'auto' ? NAT.stt.usable() && pref('stt_engine') !== 'google' : NAT.stt.useLocal(this.lang);
      if (this._local) B.lsttStart(this._sid, this.lang, !!this.continuous);
      else B.sttStart(this._sid, this.lang === 'auto' ? 'ko-KR' : this.lang, !!this.continuous, pref('stt_offline') === '1');
    }
    stop() { if (this._sid) { if (this._local) B.lsttEnd(this._sid, 'stop'); else B.sttStop(this._sid) } }
    abort() { if (this._sid) { if (this._local) B.lsttEnd(this._sid, 'abort'); else B.sttAbort(this._sid) } }""")
rep("""        if (m.text) {
          r._finals.push(m.text);
          r._fire('result', { type: 'result', results: r._results(), resultIndex: r._finals.length - 1 });
          // 이어 듣기가 너무 길어지면(문장 6개) 한 번 끊고 새로 시작하게 함 → 화면 쪽 목록이 끝없이 길어지지 않게
          if (r.continuous && r._finals.length >= 6 && r._sid) B.sttAbort(r._sid);
        }""",
"""        if (m.text) {
          if (m.lang) r._lastLang = m.lang;
          if (m.dur) NAT.stt.tone = { db: m.db, hz: m.hz, dur: m.dur, chars: m.text.replace(/\\s/g, '').length, at: Date.now() };
          r._finals.push(m.text);
          r._fire('result', { type: 'result', results: r._results(), resultIndex: r._finals.length - 1 });
          // 화면이 꺼져 있으면 타이머가 느려지므로, 문장이 오면 바로 넘김
          if (r._local && document.hidden && typeof r._flush === 'function') { try { r._flush() } catch (e) { } }
          // 이어 듣기가 너무 길어지면(문장 6개) 화면 쪽 세션만 새로 시작 → 목록이 끝없이 길어지지 않게 (폰 안 AI는 마이크를 끄지 않음)
          if (r.continuous && r._finals.length >= 6 && r._sid) { if (r._local) B.lsttEnd(r._sid, 'detach'); else B.sttAbort(r._sid) }
        }""")
rep("  if (NAT.info.stt) { window.SpeechRecognition = NativeSR; window.webkitSpeechRecognition = NativeSR; }",
    "  if (NAT.info.stt || sttInfo.lib) { window.SpeechRecognition = NativeSR; window.webkitSpeechRecognition = NativeSR; }")
rep("B.ttsSpeak(id, u.text, u.lang || '', Number(u.rate) || 1, (u.voice && u.voice.name) || '')",
    "B.ttsSpeak(id, u.text, u.lang || '', Number(u.rate) || 1, (u.voice && u.voice.name) || '', Number(u.volume) > 0 ? Number(u.volume) : 1)")
rep("  N.onModel = m => { refresh(); if (NAT.onmodel) NAT.onmodel(m) };",
    "  N.onModel = m => { refresh(); refreshStt(); if (NAT.onmodel) NAT.onmodel(m) };")
rep("  /* ── 4) 공유·복사·화면 꺼짐 방지·파일 저장 ── */",
"""  /* ── 3-1) AI 통역사용 마이크 소리(16kHz PCM, 0.1초 조각, base64) ── */
  NAT.pcm = {
    cb: null, onend: null,
    start(cb, echoCancel) { this.cb = cb; B.pcmStart(!!echoCancel) },
    stop() { this.cb = null; B.pcmStop() }
  };
  N.onPcm = b64 => { if (NAT.pcm.cb) NAT.pcm.cb(b64) };
  N.onPcmEnd = e => { const f = NAT.pcm.onend; if (f) f(e) };

  /* ── 4) 공유·복사·화면 꺼짐 방지·파일 저장 ── */""")
rep("""    NAT.llm = { state: { engine: false, state: 'idle', error: '', model: '', hasModel: false }, usable: () => false, models: () => [] };""",
"""    NAT.llm = { state: { engine: false, state: 'idle', error: '', model: '', hasModel: false }, usable: () => false, models: () => [] };
    NAT.stt = { tone: null, info: () => ({}), refresh: () => ({}), usable: () => false, useLocal: () => false, headset: () => false, setBackground() { } };""")
open(p, 'w', encoding='utf-8').write(s)

# ───────── index.html ─────────
p = d + '/index.html'; s = open(p, encoding='utf-8').read()
rep("const APP_VERSION='A1 · Claude · 안드로이드 앱 · 폰 AI 번역 · 2026.11.14';",
    "const APP_VERSION='A2 · Claude · 안드로이드 앱 · 끊기지 않는 마이크·AI 음성·AI 통역사 · 2026.11.14';")
# (a) 인터넷 없음 문구 삭제
n0 = len(s); s = re.sub(r"\n  if\(!navigator\.onLine\)node\('div','offline-banner',[^\n]*\n", "\n", s); assert len(s) < n0
# (b) 듣기 모드 조작줄 한 줄
rep("    node('small','',state.listenManual?'다시 누르면 구간 번역 · 녹음은 계속':'계속 듣고 자동으로 번역',controls);",
    "    {const hint=node('small',listenRaw?'raw-status':'',listenRaw?'● 녹음 중':rawStarting?'마이크 연결 중…':state.listenManual?'다시 누르면 번역':'자동 번역',controls);if(listenRaw)hint.id='rawRecordStatus'}")
rep("""    if(listenRaw){const label=node('small','raw-status','● 원음 녹음 중',controls);label.id='rawRecordStatus'}
    else if(rawStarting)node('small','','마이크 연결 중…',controls);
""", "")
rep("if(n)n.textContent='● 원음 녹음 중 · '+", "if(n)n.textContent='● 녹음 '+")
rep(".listen-methods{display:flex;gap:8px;align-items:center;padding:4px 14px;flex-wrap:wrap}",
    ".listen-methods{display:flex;gap:6px;align-items:center;padding:4px 12px;flex-wrap:nowrap}")
rep(".listen-method{border:0;border-radius:9px;padding:7px 13px;background:var(--surface);color:var(--muted)}",
    ".listen-method{border:0;border-radius:9px;padding:7px 10px;background:var(--surface);color:var(--muted);white-space:nowrap;flex-shrink:0;font-size:14px}")
rep(".listen-methods small{font-size:11px;color:var(--muted)}",
    ".listen-methods small{font-size:11px;color:var(--muted);flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n.ai-row{display:flex;gap:6px;justify-content:flex-end;padding:2px 12px 0}\n.ai-chip{border:1px solid var(--line);background:var(--bg);color:var(--muted);border-radius:14px;padding:4px 10px;font-size:12px;white-space:nowrap}\n.ai-chip.on{background:#7b4ed6;border-color:#7b4ed6;color:#fff;font-weight:700}")
# (c) 기본 용어를 프로그램에서 뺌 → 빈 상태로 시작
a = s.index("const SEED_GROUPS=["); b = s.index("\n];\n", a) + 4
s = s[:a] + s[b:]
a = s.index("if(!Array.isArray(refGroups)){"); b = s.index("\n  saveRefs();\n}", a) + len("\n  saveRefs();\n}")
s = s[:a] + "if(!Array.isArray(refGroups)){ // 처음 설치: 빈 상태. 용어·자료는 사용자가 자기 휴대폰에 직접 넣음\n  refGroups=[{id:'base',name:'기본 자료',color:'#eef1f5',on:true,base:true}];\n  saveRefs();\n}" + s[b:]
assert 'SEED_GROUPS' not in s
# (d) 이어폰: 통역 소리가 나는 동안에도 계속 듣기
rep("function micYield(){const r=state.recognizer;if(!r||!isConv())return;pauseRecognizer()}",
    "const earOn=()=>NAT.on&&NAT.stt.headset(); // 이어폰을 끼면 통역 소리가 마이크로 다시 들어가지 않음\nfunction micYield(){const r=state.recognizer;if(!r||!isConv()||earOn())return;pauseRecognizer()}")
rep("function resumeRecognizer(){if(isConv()&&(outBusy||state.speaking))return;", "function resumeRecognizer(){if(isConv()&&(outBusy||state.speaking)&&!earOn())return;")
rep("&&state.page==='main'&&!document.hidden)startRecognition()}", "&&state.page==='main'&&(!document.hidden||bgListen()))startRecognition()}")
rep("    echo=!live&&(state.speaking||Date.now()-speakEnd<600);", "    echo=!live&&(state.speaking||Date.now()-speakEnd<600)&&!earOn();")
# (e) 듣기 모드: 화면을 꺼도 계속 통역 (폰 안 음성 인식일 때)
rep("  if(document.hidden){const wasMic=state.mic;resetTranscripts(false);",
    "  if(document.hidden&&(bgListen()||interp))return; // 화면이 꺼져도 계속 듣고 통역\n  if(document.hidden){const wasMic=state.mic;resetTranscripts(false);")
rep("function killAllMics(){stopRefCamera();", """/* 화면을 꺼도 계속 듣는 조건: 듣기 모드(실시간) + 폰 안 음성 인식 */
function bgListen(){return NAT.on&&state.mic&&state.page==='main'&&state.mode==='listen'&&!state.listenManual&&NAT.stt.useLocal(state.listenFrom==='ko'?'ko-KR':active().locale)}
function killAllMics(){stopInterp();stopRefCamera();""")
rep("function updateMic(){\n", "function updateMic(){\n  if(NAT.on)NAT.stt.setBackground(bgListen()||!!interp);\n")
# (f) 말한 사람 목소리 따라 하기: 남녀·크기·속도
rep("function voiceFor(code,tone){\n  const list=speechSynthesis.getVoices?.()||[];const want=state.voices[code];",
"""/* 말한 사람 따라 하기 (폰 안 음성 인식일 때): 남녀 목소리 · 크기 · 속도 */
let voicesG=loadJSON('voices_g',{}); // {'ja|m':'목소리 이름','ja|f':…}
const toneOn=()=>NAT.on&&load('tone_follow','1')!=='0';
const toneBase={db:null,cps:{}};
function speakerTone(src){
  const t=NAT.stt.tone;if(!t||Date.now()-t.at>15000)return null;
  const out={g:t.hz>0?(t.hz<165?'m':'f'):'',vol:1,rf:1};
  if(toneBase.db==null)toneBase.db=t.db;
  const dv=Math.max(-8,Math.min(6,t.db-toneBase.db));toneBase.db=toneBase.db*0.8+t.db*0.2;
  out.vol=Math.max(0.5,Math.min(1,0.85*Math.pow(10,dv/20)));       // 평소 크기 = 0.85, 크게 말하면 1까지
  const cps=t.dur>0.8?t.chars/t.dur:0;
  if(cps){const b=toneBase.cps[src]||(toneBase.cps[src]=cps);out.rf=Math.max(0.85,Math.min(1.25,cps/b));toneBase.cps[src]=b*0.8+cps*0.2}
  return out;
}
function voiceFor(code,tone){
  const list=speechSynthesis.getVoices?.()||[];const want=state.voices[code];
  if(tone&&tone.g&&toneOn()){const n=voicesG[code+'|'+tone.g];if(n){const gv=list.find(v=>v.name===n);if(gv)return gv}}""")
rep("u.rate=q.fixed?(state.mode==='listen'?Math.min(1.5,state.rate):state.rate):outRate(q.text.length);if(v)u.voice=v;",
    "u.rate=q.fixed?(state.mode==='listen'?Math.min(1.5,state.rate):state.rate):outRate(q.text.length);if(v)u.voice=v;\n    if(q.tone&&!q.fixed&&toneOn()){u.rate=Math.min(2,u.rate*(q.tone.rf||1));u.volume=q.tone.vol||1}")
rep("  const entry={original:text,translation:'번역 중…',source,target,", "  if(opt.fromMic&&toneOn()){const tn=speakerTone(source);if(tn)opt={...opt,tone:tn}}\n  const entry={original:text,translation:'번역 중…',source,target,")
# (g) AI 음성: say() 앞에서 가로챔
rep("  const say=(text,retried)=>{\n", """  // AI 음성(Gemini): 켜져 있으면 폰 목소리 대신 AI가 읽음. 실패하면 그 문장은 폰 목소리로
  const aiSay=async text=>{
    let done=false;const end=()=>{if(done||finished||gen!==outGen)return;done=true;next()};
    try{
      const url=await geminiTTS(text,q.tone);
      if(gen!==outGen||finished||q.cancelled){return}
      const a=new Audio(url);curAudio=a;a.playbackRate=Math.max(0.8,Math.min(1.6,state.rate/1.15));
      a.onplaying=()=>{if(q.entry)q.entry.spokenAt=Date.now();setReading(q.text,a.playbackRate);followReading()};
      a.onended=()=>{if(curAudio===a)curAudio=null;end()};
      a.onerror=()=>{if(curAudio===a)curAudio=null;if(done||finished||gen!==outGen)return;done=true;q._noAi=true;say(text)};
      await a.play();
    }catch(e){
      if(gen!==outGen||finished||done)return;done=true;q._noAi=true;
      if(Date.now()-aiVoiceWarn>30000){aiVoiceWarn=Date.now();notify('AI 음성 실패 → 폰 목소리로 읽습니다 ('+(e.message||e)+')')}
      say(text);
    }
  };
  const say=(text,retried)=>{
    if(aiVoiceOn()&&!q._noAi&&!retried&&gen===outGen&&!finished){aiSay(text);return}
""")
rep("let outInterrupt=null;\n", r"""let outInterrupt=null;
/* ── AI 음성 (Gemini TTS) ── 버튼으로 켜고 끔. 크레딧을 씀 */
let aiVoiceWarn=0;
const aiVoiceOn=()=>load('ai_voice_on')==='1'&&geminiKey()&&navigator.onLine;
const AI_VOICES=[['Kore','Kore · 여성 · 또렷함'],['Aoede','Aoede · 여성 · 산뜻함'],['Leda','Leda · 여성 · 젊음'],['Zephyr','Zephyr · 여성 · 밝음'],['Orus','Orus · 남성 · 또렷함'],['Puck','Puck · 남성 · 경쾌함'],['Charon','Charon · 남성 · 차분함'],['Fenrir','Fenrir · 남성 · 활기참']];
function b64Bytes(b64){const bin=atob(b64),u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);return u}
function pcmWavUrl(bytes,rate){ // 머리표 없는 PCM을 WAV로 감쌈
  const h=new DataView(new ArrayBuffer(44)),w=(o,t)=>{for(let i=0;i<t.length;i++)h.setUint8(o+i,t.charCodeAt(i))};
  w(0,'RIFF');h.setUint32(4,36+bytes.length,true);w(8,'WAVE');w(12,'fmt ');h.setUint32(16,16,true);h.setUint16(20,1,true);h.setUint16(22,1,true);
  h.setUint32(24,rate,true);h.setUint32(28,rate*2,true);h.setUint16(32,2,true);h.setUint16(34,16,true);w(36,'data');h.setUint32(40,bytes.length,true);
  return URL.createObjectURL(new Blob([h.buffer,bytes],{type:'audio/wav'}));
}
async function geminiTTS(text,tone){
  const voice=tone&&tone.g&&toneOn()?(tone.g==='m'?load('ai_voice_m','Orus'):load('ai_voice_f','Kore')):load('ai_voice','Kore');
  const key=encodeURIComponent(load('ai_key').trim());let err;
  // 새 모델 형식 먼저, 안 되면 예전 형식
  const tries=[['gemini-3.8-flash-lite-tts',{voiceConfig:{voice}}],['gemini-3.1-flash-tts-preview',{voiceConfig:{prebuiltVoiceConfig:{voiceName:voice}}}]];
  for(const [model,speechConfig] of tries){
    try{
      const res=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${key}`,{method:'POST',_entryGemini:true,headers:{'content-type':'application/json'},
        body:JSON.stringify({contents:[{role:'user',parts:[{text}]}],generationConfig:{responseModalities:['AUDIO'],speechConfig}}),signal:AbortSignal.timeout(20000)});
      const j=await res.json().catch(()=>({}));if(!res.ok)throw Error(j.error?.message||('Gemini 오류 '+res.status));
      const part=(j.candidates?.[0]?.content?.parts||[]).find(x=>x.inlineData?.data);if(!part)throw Error('소리 없음');
      const mime=String(part.inlineData.mimeType||'').toLowerCase(),bytes=b64Bytes(part.inlineData.data);
      if(mime.includes('wav')||(bytes[0]===0x52&&bytes[1]===0x49&&bytes[2]===0x46&&bytes[3]===0x46))return URL.createObjectURL(new Blob([bytes],{type:'audio/wav'}));
      return pcmWavUrl(bytes,+(mime.match(/rate=(\d+)/)?.[1]||24000));
    }catch(e){err=e;if(e.stop||gemStop)break}
  }
  throw err||Error('AI 음성 실패');
}
function toggleAiVoice(){
  if(load('ai_voice_on')==='1'){store('ai_voice_on','0');render();notify('폰 목소리로 읽습니다.');return}
  if(!geminiKey())return notify('AI 음성은 Gemini 키가 필요합니다. 설정 → 고급에서 키를 넣어 주세요.');
  store('ai_voice_on','1');render();notify('🔊 AI 음성으로 읽습니다 · Gemini 크레딧을 씁니다. 다시 누르면 폰 목소리.');
}
/* ── AI 통역사 (Gemini Live Translate) ──
   마이크 소리를 그대로 Gemini에 흘려보내면 통역된 소리가 바로 돌아옴. 질문에 답하지 않고 통역만 함.
   한국어→외국어, 외국어→한국어 두 방향을 동시에 열어 둠. 이어폰이 없으면 통역 소리가 나는 동안 마이크를 잠깐 쉼(메아리 방지). */
let interp=null;
const liveCode=c=>({'zh-CN':'zh-Hans','zh-TW':'zh-Hant',tl:'fil'})[c]||c;
function stopInterp(msg){
  const it=interp;if(!it)return;interp=null;
  try{NAT.pcm.onend=null;NAT.pcm.stop()}catch{}
  it.socks.forEach(ws=>{try{ws.onclose=null;ws.onerror=null;ws.close()}catch{}});
  try{it.ctx.close()}catch{}
  clearTimeout(it.timer);releaseWake();
  if(msg)notify(msg);
  if(state.page==='main')render();
}
function startInterp(){
  if(interp)return stopInterp('AI 통역사를 껐습니다.');
  if(!NAT.on)return notify('AI 통역사는 안드로이드 앱에서만 됩니다.');
  if(!geminiKey())return notify('AI 통역사는 Gemini 키가 필요합니다. 설정 → 고급에서 키를 넣어 주세요.');
  if(!navigator.onLine)return notify('AI 통역사는 인터넷이 필요합니다.');
  if(state.mic)stopMic(isManualInput());stopSpeech();
  const fg=active().code,ear=NAT.stt.headset(),listen=state.mode==='listen';
  const it=interp={socks:[],ctx:new (window.AudioContext||window.webkitAudioContext)({sampleRate:24000}),next:0,timer:null,rows:{},fails:0};
  const list=()=>listen?state.listening:state.items;
  const paint=()=>{if(it.timer)return;it.timer=setTimeout(()=>{it.timer=null;if(interp===it&&state.page==='main'&&!state.modal){render();scrollEnd()}},400)};
  const play=b64=>{
    if(state.speech===3)return;
    const u=b64Bytes(b64),n=u.length>>1,dv=new DataView(u.buffer),buf=it.ctx.createBuffer(1,n,24000),ch=buf.getChannelData(0);
    for(let i=0;i<n;i++)ch[i]=dv.getInt16(i*2,true)/32768;
    const src=it.ctx.createBufferSource();src.buffer=buf;src.connect(it.ctx.destination);
    const at=Math.max(it.ctx.currentTime+0.03,it.next);src.start(at);it.next=at+buf.duration;
  };
  const open=target=>{
    const source=target==='ko'?fg:'ko',row={entry:null,inBuf:'',at:0};it.rows[target]=row;
    const ws=new WebSocket('wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key='+encodeURIComponent(load('ai_key').trim()));
    ws.onopen=()=>ws.send(JSON.stringify({setup:{model:'models/gemini-3.5-live-translate-preview',generationConfig:{responseModalities:['AUDIO'],inputAudioTranscription:{},outputAudioTranscription:{},translationConfig:{targetLanguageCode:liveCode(target),echoTargetLanguage:false}}}}));
    ws.onmessage=async ev=>{
      if(interp!==it)return;let m;
      try{m=JSON.parse(typeof ev.data==='string'?ev.data:await ev.data.text())}catch{return}
      const sc=m.serverContent;if(!sc)return;
      const now=Date.now();
      if(sc.inputTranscription?.text){if(now-row.at>6000)row.inBuf='';row.inBuf+=sc.inputTranscription.text;row.at=now;if(row.entry&&now-row.entry.createdAt<60000&&!row.closed){row.entry.original=(row.entry.original+sc.inputTranscription.text).trimStart();paint()}}
      const outText=sc.outputTranscription?.text;
      if(outText){
        // 2.5초 넘게 쉬었다가 다시 나오면 새 줄
        if(!row.entry||row.closed||now-row.outAt>2500){row.entry={original:row.inBuf.trim(),translation:'',source,target,failed:false,trMode:'live',createdAt:now};row.closed=false;row.inBuf='';list().push(row.entry)}
        else if(row.inBuf){row.entry.original=(row.entry.original+row.inBuf).trim();row.inBuf=''}
        row.entry.translation+=outText;row.outAt=now;paint();
      }
      for(const part of sc.modelTurn?.parts||[])if(part.inlineData?.data)play(part.inlineData.data);
      if(sc.turnComplete||sc.generationComplete)row.closed=true;
    };
    const fail=()=>{if(interp!==it)return;if(++it.fails>=1)stopInterp('AI 통역사 연결이 끊겼습니다. 다시 눌러 주세요. (키·크레딧·인터넷 확인)')};
    ws.onerror=fail;ws.onclose=fail;
    it.socks.push(ws);
  };
  open(fg);open('ko');
  NAT.pcm.onend=e=>{if(interp===it)stopInterp(e?'마이크를 열 수 없습니다.':'')};
  NAT.pcm.start(b64=>{
    if(interp!==it)return;
    if(!ear&&it.ctx.currentTime<it.next+0.3)return; // 스피커로 통역 소리가 나는 동안은 보내지 않음
    const msg=JSON.stringify({realtimeInput:{audio:{data:b64,mimeType:'audio/pcm;rate=16000'}}});
    it.socks.forEach(ws=>{if(ws.readyState===1)ws.send(msg)});
  },!ear);
  keepAwake();render();
  notify('🎙 AI 통역사 시작 · 말하면 바로 통역합니다 · Gemini 크레딧을 씁니다'+(ear?'':' · 이어폰을 끼면 더 자연스럽습니다'));
}
""")
# 통역사가 켜져 있으면 말하기 버튼은 쉬게
rep("function pressTalk(k){\n", "function pressTalk(k){\n  if(interp)return notify('AI 통역사가 켜져 있습니다. 끄려면 \"AI 통역사\"를 다시 누르세요.');\n")
# AI 버튼 줄 (말하기 버튼 위)
rep("  const tr2=node('div','talk-row','',s);", """  if(NAT.on){ // AI 통역사 · AI 음성 (Gemini 키가 있을 때 쓸 수 있음)
    const ar=node('div','ai-row','',s);
    button(interp?'● AI 통역사 켜짐 · 누르면 끔':'🎙 AI 통역사','ai-chip'+(interp?' on':''),startInterp,ar);
    button(load('ai_voice_on')==='1'?'🔊 AI 음성 켜짐':'🔊 AI 음성','ai-chip'+(load('ai_voice_on')==='1'?' on':''),toggleAiVoice,ar);
  }
  const tr2=node('div','talk-row','',s);""")
# (j) 자동 버튼: 폰 안 음성 인식이면 말한 언어를 알아서 구분
rep("  r.lang=foreign?active().locale:'ko-KR';const source=foreign?active().code:'ko';state.listenLang=source;updateMic();",
    "  const autoDet=!live&&state.recog==='auto'&&NAT.on&&NAT.stt.useLocal('ko-KR')&&NAT.stt.useLocal(active().locale); // 폰 안 음성 인식: 번갈아 듣지 않고 언어를 알아서 구분\n  r.lang=autoDet?'auto':foreign?active().locale:'ko-KR';let source=foreign?active().code:'ko';state.listenLang=source;updateMic();")
rep("    lastFinal={text,at:now,source,micId};gotFin=true;state.sourceTurn++;",
    "    if(autoDet&&r._lastLang){const fb=active().code.split('-')[0];if(/^ko/.test(r._lastLang))source='ko';else if(r._lastLang.startsWith(fb)||(fb==='zh'&&r._lastLang==='yue'))source=active().code;state.listenLang=source}\n    lastFinal={text,at:now,source,micId};gotFin=true;state.sourceTurn++;")
# (i) 설정: 모델 목록을 번역/음성 인식으로 나눔
rep("  const st=NAT.llm.state,models=NAT.llm.models();", "  const st=NAT.llm.state,allModels=NAT.llm.models(),models=allModels.filter(m=>m.kind!=='stt'),sttModels=allModels.filter(m=>m.kind==='stt');")
rep("  models.forEach(m=>{\n", "  const drawCards=(list,sec)=>list.forEach(m=>{\n")
rep("  });\n  sec=node('div','sec','',body);node('h4','','다른 모델 직접 넣기',sec);", "  });\n  drawCards(models,sec);\n  sec=node('div','sec','',body);node('h4','','다른 모델 직접 넣기',sec);")
a = s.index("  sec=node('div','sec','',body);node('h4','','음성 인식',sec);"); b = s.index("  if(!NAT.info.sttOffline)ob.style.opacity=.5;\n}", a) + len("  if(!NAT.info.sttOffline)ob.style.opacity=.5;\n}")
s = s[:a] + r"""  sec=node('div','sec','',body);node('h4','','음성 인식 (마이크)',sec);
  node('p','tiny','"폰 안 AI"는 마이크를 끄지 않고 계속 듣습니다(띡 소리·끊김 없음, 인터넷 불필요). 아래에서 음성 인식 모델을 받아야 쓸 수 있습니다. 모델이 못 하는 언어는 자동으로 구글 음성 인식을 씁니다.',sec);
  const si=NAT.stt.refresh(),eng=load('stt_engine')==='google'?(load('stt_offline')==='1'?'goff':'google'):(si.usable?'local':'google'),sr=node('div','chips','',sec);
  const lb=button('📱 폰 안 AI (끊김 없음)','chip'+(eng==='local'?' on':''),()=>{if(!si.lib)return notify('이 설치 파일에는 음성 인식 엔진이 들어 있지 않습니다.');if(!si.usable)return notify('먼저 아래에서 음성 인식 모델을 받아 주세요.');if(state.mic)stopMic();store('stt_engine','local');render()},sr);
  if(!si.usable)lb.style.opacity=.5;
  button('구글 기본','chip'+(eng==='google'?' on':''),()=>{if(state.mic)stopMic();store('stt_engine','google');store('stt_offline','0');render()},sr);
  const ob=button('구글 오프라인','chip'+(eng==='goff'?' on':''),()=>{if(!NAT.info.sttOffline)return notify('이 휴대폰은 구글 오프라인 음성 인식을 지원하지 않습니다.');if(state.mic)stopMic();store('stt_engine','google');store('stt_offline','1');render()},sr);
  if(!NAT.info.sttOffline)ob.style.opacity=.5;
  drawCards(sttModels,sec);
  sec=node('div','sec','',body);node('h4','','말한 사람 따라 하기',sec);
  node('p','tiny','폰 안 AI로 들을 때, 말한 사람의 목소리에 맞춰 통역 소리를 냅니다. 크게 말하면 크게, 빨리 말하면 빨리 읽고, 아래에서 남성·여성 목소리를 정해 두면 말한 사람에 맞춰 고릅니다.',sec);
  const tf=toneOn();
  button((tf?'☑':'☐')+' 크기·속도·남녀 따라 하기','action'+(tf?' primary':''),()=>{store('tone_follow',tf?'0':'1');render()},sec);
  if(tf){
    const vs=speechSynthesis.getVoices?.()||[];
    [['ko','한국어'],[active().code,active().name]].forEach(([code,name])=>{
      const pre=localeOf(code).slice(0,2).toLowerCase(),lst=vs.filter(v=>v.lang.toLowerCase().replace('_','-').startsWith(pre));
      [['m','남성이 말했을 때'],['f','여성이 말했을 때']].forEach(([g,label])=>{
        node('label','field',name+' 목소리 · '+label,sec);
        const sel=node('select','text-field','',sec);const o0=node('option','','기본 목소리 그대로',sel);o0.value='';
        lst.forEach(v=>{const o=node('option','',v.name+(v.localService?'':' · 온라인'),sel);o.value=v.name});
        sel.value=voicesG[code+'|'+g]||'';
        sel.onchange=()=>{if(sel.value)voicesG[code+'|'+g]=sel.value;else delete voicesG[code+'|'+g];store('voices_g',JSON.stringify(voicesG));if(sel.value)speak(code==='ko'?'이 목소리로 말할게요.':'Hello',code,{g,vol:1,rf:1})};
      });
    });
  }
  sec=node('div','sec','',body);node('h4','','AI 음성 · AI 통역사 (Gemini)',sec);
  node('p','tiny','번역 화면의 "AI 음성"을 켜면 Gemini가 자연스러운 목소리로 읽고, "AI 통역사"를 켜면 Gemini가 실시간으로 듣고 바로 통역합니다(질문에 답하지 않고 통역만). 둘 다 Gemini 키와 인터넷이 필요하고 크레딧을 씁니다.'+(geminiKey()?'':' 지금은 키가 없습니다 — 고급 탭에서 넣어 주세요.'),sec);
  [['ai_voice','AI 음성 목소리 (기본)','Kore'],['ai_voice_m','남성이 말했을 때','Orus'],['ai_voice_f','여성이 말했을 때','Kore']].forEach(([k,label,dv])=>{
    node('label','field',label,sec);const sel=node('select','text-field','',sec);
    AI_VOICES.forEach(([v,t])=>{const o=node('option','',t,sel);o.value=v});sel.value=load(k,dv);sel.onchange=()=>store(k,sel.value);
  });
}""" + s[b:]
# (k) 처음 안내: 번역 AI + 음성 인식 AI를 함께
a = s.index("function offerLocalAI(){"); b = s.index("\n}\n", a) + 3
s = s[:a] + r"""function offerLocalAI(){
  if(!NAT.on||load('local_offer2')==='1')return;
  const list=NAT.llm.models();if(list.some(x=>x.state==='downloading'))return;
  const want=[];
  if(NAT.llm.state.engine&&!list.some(x=>x.kind==='mt'&&x.state==='ready')){const m=list.find(x=>x.kind==='mt');if(m)want.push(m)}
  if(NAT.stt.info().lib&&!list.some(x=>x.kind==='stt'&&x.state==='ready')){const m=list.find(x=>x.kind==='stt');if(m)want.push(m)}
  if(!want.length)return;
  const back=node('div','confirm-back','',$('#app')),box=node('div','confirm-box','',back);back.onclick=e=>e.stopPropagation();
  node('p','','📱 폰 안 AI를 받을까요?\n\n'+want.map(m=>'· '+(m.kind==='mt'?'번역 AI':'음성 인식 AI(끊기지 않는 마이크)')+' '+fmtMB(m.total)).join('\n')+'\n\n무료이고, 받아 두면 인터넷 없이도 듣고 번역합니다. 와이파이 권장.\n받는 동안에도 앱을 쓸 수 있고, 나중에 설정 → 번역 AI에서도 받을 수 있습니다.',box);
  const a=node('div','actions','',box);
  button('나중에','action',()=>{store('local_offer2','1');back.remove()},a);
  button('지금 받기','action primary',()=>{
    store('local_offer2','1');back.remove();
    if(!navigator.onLine)return notify('인터넷이 될 때 설정 → 번역 AI에서 받아 주세요.');
    want.forEach(m=>NAT.llm.download(m.id));notify('폰 AI를 받는 중입니다. 다 받으면 자동으로 연결됩니다. (진행 상황: 설정 → 번역 AI)');
  },a);
}
""" + s[b:]
rep("""    if(m.state==='ready'){ // 다 받으면 자동으로 연결: 그 모델을 고르고 폰 AI를 기본 번역기로
      NAT.llm.select(m.id);if(load('tr_engine')!=='local')store('tr_engine','local');
      notify('📱 폰 AI 번역 준비 완료 · 기본 번역기로 설정했습니다.');
    }""", """    if(m.state==='ready'&&m.kind==='stt'){ // 음성 인식 모델: 다 받으면 끊기지 않는 마이크로 자동 연결
      NAT.llm.select(m.id);store('stt_engine','local');setTimeout(()=>NAT.stt.refresh(),600);
      notify('🎙 폰 안 음성 인식 준비 완료 · 이제 마이크가 끊기지 않습니다.');
    }else if(m.state==='ready'){ // 번역 모델: 다 받으면 그 모델을 고르고 폰 AI를 기본 번역기로
      NAT.llm.select(m.id);if(load('tr_engine')!=='local')store('tr_engine','local');
      notify('📱 폰 AI 번역 준비 완료 · 기본 번역기로 설정했습니다.');
    }""")
open(p, 'w', encoding='utf-8').write(s)
print('patched ok')
