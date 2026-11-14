# V4 웹앱(index.html) → 안드로이드 앱용 index.html
# 원칙: V4의 기능은 그대로 두고, 웹 전용만 빼고, 안드로이드 기능을 얹는다.
import sys, re, ast, os
src, out = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
s = open(src, encoding='utf-8').read()
def consts(path):
    t = ast.parse(open(os.path.join(here, path), encoding='utf-8').read())
    return [n.value for n in ast.walk(t) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
C1, C2 = consts('patch_native.py'), consts('patch_a2.py')
def blk(C, *markers):
    c = [x for x in C if all(m in x for m in markers)]
    c.sort(key=len)
    assert c, markers
    return c[0]
def rep(old, new, where=None):
    global s
    assert s.count(old) == 1, ('count', s.count(old), old[:80])
    s = s.replace(old, new)
def sub(text, old, new):
    assert text.count(old) == 1, ('sub count', text.count(old), old[:80])
    return text.replace(old, new)
def cut(a_marker, b_marker, new, include_b=True):
    global s
    assert s.count(a_marker) == 1, ('cut a', s.count(a_marker), a_marker[:60])
    a = s.index(a_marker); b = s.index(b_marker, a)
    if include_b: b += len(b_marker)
    s = s[:a] + new + s[b:]

# ───── 시작·버전 ─────
rep("<script>\n'use strict';", "<script src=\"native.js\"></script>\n<script>\n'use strict';")
n = len(s); s = re.sub(r"const APP_VERSION='[^']*';", "const APP_VERSION='A3 · Claude · 안드로이드 앱 (V4 기준) · 폰 AI·끊기지 않는 마이크·AI 통역사 · 2026.11.14';", s, count=1); assert len(s) != n
rep("if(load('defaults_v0')!=='1'){store('tr_engine','gemini');store('gem_tier','fast');store('defaults_v0','1')}",
    "if(load('defaults_v0')!=='1'){store('gem_tier','fast');store('defaults_v0','1')} // 앱: 기본 번역기는 폰 AI (없으면 Gemini)")

# ───── 뺀 것: 기본 용어 · 인터넷 없음 문구 · 웹 전용(설치·전체 화면·새 버전 당겨 받기·서비스 워커) ─────
cut("const SEED_GROUPS=[", "\n];\n", "const SEED_GROUPS=[]; // 앱: 기본 용어 없이 빈 상태로 시작 (용어는 사용자가 자기 휴대폰에 넣음)\n")
n = len(s); s = re.sub(r"\n  if\(!navigator\.onLine\)node\('div','offline-banner',[^\n]*\n", "\n", s); assert len(s) < n
rep("const isInstalled=()=>matchMedia(", "const isInstalled=()=>NAT.on||matchMedia(")
rep("async function forceUpdate(){\n", "async function forceUpdate(){\n  if(NAT.on)return; // 앱은 설치 파일을 덮어 설치해 업데이트\n")
rep("  {let y0=null,pulled=false;const pi=node('div','pull-ind'", "  if(!NAT.on){let y0=null,pulled=false;const pi=node('div','pull-ind'")
rep("if('serviceWorker'in navigator&&location.protocol==='https:'){", "if(!NAT.on&&'serviceWorker'in navigator&&location.protocol==='https:'){")
rep("const APP_URL='https://lsc571-max.github.io/travel/';", "const APK_URL='https://github.com/lsc571-max/travel-android/releases/latest/download/travel-interpreter.apk';\nconst APP_URL=NAT.on?APK_URL:'https://lsc571-max.github.io/travel/';")
rep("""  const text='여행 통역 앱 · 크롬으로 열고 "앱으로 설치하기"를 누르세요\\n'+APP_URL;""",
    """  const text=(NAT.on?'여행 통역 앱(안드로이드) · 아래 주소를 눌러 받아 설치하세요\\n':'여행 통역 앱 · 크롬으로 열고 "앱으로 설치하기"를 누르세요\\n')+APP_URL;""")
# 관리자 메뉴(버전 5번 누르기)는 유지 — 웹 올리기 대신 앱 설치 파일·저장소
rep("node('h4','','🔧 관리자 메뉴 (새 버전 올리기)',admin);", "node('h4','',NAT.on?'🔧 관리자 메뉴':'🔧 관리자 메뉴 (새 버전 올리기)',admin);")
a = s.index("  node('p','tiny','① 받은 zip을"); b = s.index("\n", a)
s = s[:a] + "  if(NAT.on)node('p','tiny','새 버전은 \"최신 설치 파일 받기\"로 받아 기존 앱 위에 그대로 설치하면 됩니다. 자료와 받아 둔 AI는 그대로 남습니다.',admin);else " + s[a+2:]
a = s.index("  const links=[['⬆ GitHub에 새 버전 올리기'"); b = s.index("\n", a)
s = s[:a] + "  const links=NAT.on?[['⬇ 최신 설치 파일 받기',APK_URL,true],['📂 앱 저장소 열기','https://github.com/lsc571-max/travel-android'],['🛠 만들기 기록','https://github.com/lsc571-max/travel-android/actions']]:" + s[a+len("  const links="):]

# ───── 번역기: 폰 AI(기본) · Gemini  (무료 번역기는 뺌) ─────
rep("function protectRev(text,src,force=false){if(!force&&engine()!=='free')return text;", "function protectRev(text,src,force=false){if(!force)return text;")
rep("model:engine()==='gemini'?gemModel():'free'}}", "model:engine()==='gemini'?gemModel():'local'}}")
rep("  if(engine()==='free'&&!(opt?._entryGemini&&geminiKey()))throw Object.assign(Error('Gemini 키·모드가 필요합니다'),{stop:true});",
    "  if(!geminiKey())throw Object.assign(Error('Gemini 키가 필요합니다'),{stop:true});")
rep("function warmGemini(){if(!aiReady()||!navigator.onLine||", "function warmGemini(){if(engine()!=='gemini'||!navigator.onLine||")
rep("function goMain(){setTimeout(warmGemini,0);", "function goMain(){setTimeout(warmGemini,0);if(localReady())NAT.llm.ensure();")
rep("""    if(!geminiKey()){notify('Gemini 키가 없어 무료 번역기를 사용합니다.');return}
    if(state.mic)stopMic();
    if(engine()==='free'){store('tr_engine','gemini');store('gem_tier','fast')}
    else {const i=GEM_TIERS.findIndex(x=>x[0]===gemTier());
      if(i===GEM_TIERS.length-1)store('tr_engine','free');else store('gem_tier',GEM_TIERS[i+1][0])}
    gemStop='';render();""",
"""    // 폰 AI → Gemini 빠름 → 균형 → 정확 → 폰 AI … (쓸 수 있는 것만)
    const modes=engineChoices();
    if(modes.length<2){notify(modes.length?(localReady()?'고급 탭에 Gemini 키를 넣으면 Gemini 번역기도 고를 수 있습니다.':'설정 → 번역 AI에서 폰 AI를 받으면 폰 AI 번역도 고를 수 있습니다.'):NO_ENGINE);return}
    if(state.mic)stopMic();
    setEngineMode(modes[(modes.indexOf(currentEntryMode())+1)%modes.length]);
    gemStop='';render();""")
rep("""      if(!geminiKey())store('tr_engine','free');
      else if(!had){store('tr_engine','gemini');store('gem_tier','fast')}""",
"""      if(!geminiKey()){if(load('tr_engine')==='gemini')store('tr_engine','local')}
      else if(!had&&!localReady()){store('tr_engine','gemini');store('gem_tier','fast')} // 폰 AI를 쓰는 중이면 기본 번역기는 그대로""")
rep("function provider(){return engine()==='gemini'?'gemini':null}", "function provider(){return geminiKey()?'gemini':null} // 폰 AI가 기본이어도 키가 있으면 사진·PDF·녹음·자료 정리는 Gemini로")
rep("async function aiPolish(area,code,onChange){\n  if(!aiReady()||!navigator.onLine)return;",
    "async function aiPolish(area,code,onChange){\n  if(engine()!=='gemini'||!navigator.onLine)return; // 자동 다듬기는 Gemini 번역기를 골랐을 때만 (크레딧 보호)")
rep("function engLabel(){if(engine()!=='gemini')return engineName();return 'Gemini '+GEM_TIERS.find(x=>x[0]===gemTier())[1]}",
    "function engLabel(){const e=engine();if(e==='local')return localReady()?'📱 폰 AI 번역':'번역기 없음 · 설정';return 'Gemini '+GEM_TIERS.find(x=>x[0]===gemTier())[1]}")
A1ENG = blk(C1, "function localPrompt(text,src,target){", "function localReady()")
local_fns = A1ENG[A1ENG.index("/* 폰 AI 번역 (Hy-MT2)"):]
rep("function engine(){const e=load('tr_engine','');if(e==='free')return'free';return geminiKey()?'gemini':'free'}\nconst engineName=()=>({free:'무료 번역기',gemini:'Gemini 번역기'})[engine()];",
r"""/* 번역기 두 가지: local = 폰 안 AI(무료·오프라인, 기본) · gemini.
   고른 번역기를 못 쓰는 상태면(모델 안 받음·키 없음) 쓸 수 있는 쪽으로 자동으로 넘어감 */
const NO_ENGINE='번역기가 준비되지 않았습니다. 설정 → 번역 AI에서 폰 AI를 받거나, 고급 탭에 Gemini 키를 넣어 주세요.';
function localReady(){return NAT.on&&NAT.llm.usable()}
function engine(){const e=load('tr_engine','');
  if(e==='gemini'&&geminiKey())return 'gemini';
  if(localReady())return 'local';
  return geminiKey()?'gemini':'local'}
const engineName=()=>({gemini:'Gemini 번역기',local:'폰 AI 번역'})[engine()];
function engineChoices(){const m=[];if(localReady())m.push('local');if(geminiKey())m.push('fast','balanced','accurate');return m}
function setEngineMode(m){if(m==='local')store('tr_engine','local');else{store('tr_engine','gemini');store('gem_tier',m)}if(m==='local'&&NAT.on)NAT.llm.ensure()}
""" + local_fns)
cut("async function translateAI(text,src,target,ctx){", "function cached(text,src,target){", r"""async function localChunks(text,src,target,onProgress){const out=[],parts=splitText(text,500);for(let i=0;i<parts.length;i++){out.push(await localTranslate(parts[i],src,target));if(parts.length>1)onProgress?.(out.join(' '),i+1,parts.length)}return out.join(' ')}
async function translateAI(text,src,target,ctx){ // Gemini로 번역 · 실패하면 폰 AI로
  try{return await geminiTranslate(text,src,target,ctx)}
  catch(err){if(!localReady())throw err;if(Date.now()-lastEngineWarn>60000){lastEngineWarn=Date.now();notify(`Gemini 번역 실패 → 폰 AI로 대신 번역합니다 (${err.message})`)}}
  return localChunks(text,src,target);
}
function cached(text,src,target){""")
cut("  if(!navigator.onLine)throw new Error('인터넷이 없습니다. 📚 여행 문구나 받아 둔 자주 쓰는 문장을 써 주세요');", "trPut('t',text,src,target,mode,res);return res;\n", r"""  let res=null;
  if(engine()==='local'){ // 폰 AI: 인터넷 없이 번역. 실패하면 키가 있을 때만 Gemini로
    if(!localReady())throw new Error(NO_ENGINE);
    try{res=await localChunks(text,src,target,onProgress)}
    catch(err){if(!geminiKey()||!navigator.onLine)throw Error('폰 AI 번역 실패 · '+err.message);if(Date.now()-lastEngineWarn>60000){lastEngineWarn=Date.now();notify('폰 AI 번역 실패 → Gemini로 대신 번역합니다 ('+err.message+')')}}
  }
  if(res==null){
    if(!navigator.onLine&&!localReady())throw new Error('인터넷이 없습니다. 📚 여행 문구나 받아 둔 자주 쓰는 문장을 써 주세요');
    const chunks=splitText(text,2500),out=[];
    for(let i=0;i<chunks.length;i++){out.push(await translateAI(chunks[i],src,target,i?'':ctx));if(chunks.length>1)onProgress?.(out.join(' '),i+1,chunks.length)}
    res=out.join(' ');
  }
  trPut('t',text,src,target,mode,res);return res;
""")
rep("const ENTRY_MODES=[['fast','빠름'],['balanced','균형'],['accurate','정확'],['free','무료']];\nconst currentEntryMode=()=>engine()==='gemini'?gemTier():'free';",
    "const ENTRY_MODES=[['local','폰AI'],['fast','빠름'],['balanced','균형'],['accurate','정확']];\nconst currentEntryMode=()=>engine()==='gemini'?gemTier():'local';")
rep("(m==='saved'?'저장':m==='manual'?'직접 수정':'방식')", "(m==='saved'?'저장':m==='manual'?'직접 수정':m==='live'?'AI 통역사':m==='free'?'무료':'방식')")
cut("  if(!navigator.onLine)throw Error('인터넷 연결을 확인해 주세요');\n  const reuse=!options.retranslate;", "return {s:entry.original,t,mode:'free'};\n}", r"""  const reuse=!options.retranslate; // 다시 번역을 눌렀을 때만 저장된 번역을 건너뜀
  const viaLocal=async()=>{
    const hit=reuse&&trGet('e',entry.original,entry.source,entry.target,'local');if(hit)return {...hit,mode:'local'};
    latencyMark(timing,'request');compareMark(timing,'',localPrompt(entry.original,entry.source,entry.target));const parts=[]; // "몇 자 · 몇 초" 표시용
    try{for(const part of splitText(entry.original,500)){if(signal.aborted)return null;parts.push(await localTranslate(part,entry.source,entry.target))}}finally{compareFinish(timing)}
    latencyMark(timing,'response');if(signal.aborted)return null;
    const t=parts.join(' ');trPut('e',entry.original,entry.source,entry.target,'local',{s:entry.original,t});return {s:entry.original,t,mode:'local'};
  };
  const viaGemini=async tier=>{ // undefined = 응답 실패
    const hit=reuse&&trGet('e',entry.original,entry.source,entry.target,tier);if(hit)return {...hit,mode:tier};
    let r;try{r=await geminiCleanTranslate(entry.original,entry.source,entry.target,entryContext(entry),timing,{tier,signal,merged:!!options.merged})}catch(e){if(signal.aborted)return null;r=null}
    if(signal.aborted)return null;
    if(r){trPut('e',entry.original,entry.source,entry.target,tier,{s:r.s,t:r.t});return {...r,mode:tier}}
  };
  if(mode==='local'){ // 폰 AI: 인터넷이 없어도 됨. 실패하면 키가 있을 때만 Gemini로
    if(localReady()){
      try{return await viaLocal()}
      catch(err){if(signal.aborted)return null;latencyMark(timing,'fallback');
        if(!geminiKey()||!navigator.onLine)throw Error('폰 AI 번역 실패 · '+err.message);
        notify('폰 AI 번역 실패 · Gemini로 이어서 번역합니다. ('+err.message+')')}
    }else if(!geminiKey())throw Error(NO_ENGINE);
    if(!navigator.onLine)throw Error('인터넷 연결을 확인해 주세요');
    const r=await viaGemini(gemTier());if(r===undefined)throw Error('Gemini 응답 실패');return r;
  }
  if(!geminiKey())throw Error('Gemini 키가 필요합니다');
  if(navigator.onLine){const r=await viaGemini(mode);if(r!==undefined)return r}
  latencyMark(timing,'fallback');
  if(!localReady())throw Error(navigator.onLine?entryModeName(mode)+' 응답 실패':'인터넷 연결을 확인해 주세요');
  notify(entryModeName(mode)+(navigator.onLine?' 응답 실패':' · 인터넷 없음')+' · 폰 AI로 이어서 번역합니다.');
  return viaLocal();
}""")
rep("  if(mode!=='free'&&!geminiKey()){notify('Gemini 키가 필요합니다.');return}",
    "  if(mode==='local'&&!localReady()){notify('폰 AI가 준비되지 않았습니다. 설정 → 번역 AI에서 받아 주세요.');return}\n  if(mode!=='local'&&!geminiKey()){notify('Gemini 키가 필요합니다.');return}")

# ───── 설정: "번역 AI" 탭 (모델 받기·음성 인식·따라 하기·AI 음성) ─────
rep("[['basic','기본'],['phrases','여행 문구'],['adv','고급']].forEach(", "[['basic','기본'],...(NAT.on?[['ai','번역 AI']]:[]),['phrases','여행 문구'],['adv','고급']].forEach(")
rep("  if(tab==='adv'){\n    sec=node('div','sec','',body);node('h4','','Gemini 키',sec);",
    "  if(tab==='ai'&&NAT.on)drawLocalAI(body);\n  if(tab==='adv'){\n    sec=node('div','sec','',body);node('h4','','Gemini 키',sec);")
B = blk(C1, "function drawLocalAI(body){", "function offerLocalAI(){")
B = sub(B, "  const st=NAT.llm.state,models=NAT.llm.models();", "  const st=NAT.llm.state,allModels=NAT.llm.models(),models=allModels.filter(m=>m.kind!=='stt'),sttModels=allModels.filter(m=>m.kind==='stt');")
B = sub(B, "  models.forEach(m=>{\n", "  const drawCards=(list,sec)=>list.forEach(m=>{\n")
B = sub(B, "  });\n  sec=node('div','sec','',body);node('h4','','다른 모델 직접 넣기',sec);", "  });\n  drawCards(models,sec);\n  sec=node('div','sec','',body);node('h4','','다른 모델 직접 넣기',sec);")
STT = blk(C2, "말한 사람 따라 하기", "drawCards(sttModels,sec)")
a = B.index("  sec=node('div','sec','',body);node('h4','','음성 인식',sec);"); b = B.index("  if(!NAT.info.sttOffline)ob.style.opacity=.5;\n}", a) + len("  if(!NAT.info.sttOffline)ob.style.opacity=.5;\n}")
B = B[:a] + STT + B[b:]
OFFER = blk(C2, "function offerLocalAI(){", "local_offer2")
a = B.index("function offerLocalAI(){"); b = B.index("\n}\n", a) + 3
B = B[:a] + OFFER + B[b:]
B = sub(B, blk(C2, "기본 번역기로 설정했습니다.", "NAT.llm.select(m.id);if(load('tr_engine')!=='local')store('tr_engine','local');") if False else B[B.index("    if(m.state==='ready'){ // 다 받으면"):B.index("    }else if(m.state==='error')")+len("    }")], blk(C2, "m.kind==='stt'", "store('stt_engine','local')"))
B = B.replace("function fmtMB(n)", "function fmtBig(n)").replace("fmtMB(", "fmtBig(").replace("'recording-card'", "'rec-item'")
B = sub(B, ",['gemini','Gemini'],['free','무료 번역기 (인터넷)']]", ",['gemini','Gemini']]")
B = sub(B, "const ok=k==='local'?localReady():k==='gemini'?geminiKey():true;", "const ok=k==='local'?localReady():geminiKey();")
B = sub(B, "(무료 번역기·Gemini는 쓸 수 있습니다)", "(Gemini 번역은 쓸 수 있습니다)")
B = sub(B, "g.classList.toggle('on',engine()!=='free')", "g.classList.toggle('on',engine()==='gemini')")
B = sub(B, "speak(code==='ko'?'이 목소리로 말할게요.':'Hello',code,{g,vol:1,rf:1})", "speakTone(code==='ko'?'이 목소리로 말할게요.':'Hello',code,{g,vol:1,rf:1})")
B = B.replace("fmtBig(m.total)).join", "fmtBig(m.total)).join")
rep("function drawSettings(body){", B)
rep("    else if(e.error==='network')notify('음성 인식 서버와 연결할 수 없습니다. 인터넷 연결을 확인해 주세요.');",
    "    else if(e.error==='network')notify('음성 인식 서버와 연결할 수 없습니다. 인터넷 연결을 확인해 주세요.');\n    else if(e.error==='language-not-supported'){state.mic=false;state.recognizer=null;render();notify('이 언어의 음성 인식을 휴대폰이 지원하지 않습니다. 설정 → 번역 AI → 음성 인식을 \"구글 기본\"으로 바꿔 보세요.')}")
rep("\nrender();\n", "\nrender();\nif(NAT.on){setTimeout(offerLocalAI,900);if(engine()==='local')NAT.llm.ensure()}\n")
rep("</style>", ".ai-result{margin-top:8px;padding:10px 12px;border-radius:10px;background:var(--surface);font-size:14px;line-height:1.5;white-space:pre-wrap}\n.ai-row{display:flex;gap:6px;justify-content:flex-end;padding:4px 12px 0;flex-wrap:nowrap}\n.ai-chip{border:1px solid var(--line);background:var(--bg);color:var(--muted);border-radius:14px;padding:4px 10px;font-size:12px;white-space:nowrap}\n.ai-chip.on{background:#7b4ed6;border-color:#7b4ed6;color:#fff;font-weight:700}\n</style>")

# ───── 소리: 말한 사람 따라 하기 · AI 음성 · AI 통역사 ─────
TONE = blk(C2, "function speakerTone(src){", "function voiceFor(code,tone){")
rep("function voiceFor(code){\n  const list=speechSynthesis.getVoices?.()||[];const want=state.voices[code];", TONE)
AI = blk(C2, "function startInterp(){", "async function geminiTTS(text,tone){")
AI = sub(AI, "method:'POST',_entryGemini:true,", "method:'POST',_entryGemini:true,_task:'AI 음성',")
AI = sub(AI, "    if(!ear&&it.ctx.currentTime<it.next+0.3)return;", "    if(!ear&&it.next>0&&it.ctx.currentTime<it.next+0.3)return;")
AI = sub(AI, "  const list=()=>listen?state.listening:state.items;", "  try{it.ctx.resume?.()}catch{}\n  const list=()=>listen?state.listening:state.items;")
AI += "function speakTone(text,code,tone){stopSpeech();const q=outReserve(code,null);q.force=true;q.tone=tone;outReady(q,text)} // 목소리 미리 듣기\n"
rep("let outInterrupt=null;\n", AI)
rep("function micYield(){if(state.recognizer&&isConv())pauseRecognizer()}",
    "const earOn=()=>NAT.on&&NAT.stt.headset(); // 이어폰을 끼면 통역 소리가 마이크로 다시 들어가지 않음\nfunction micYield(){if(state.recognizer&&isConv()&&!earOn())pauseRecognizer()}")
rep("parts=splitSentences(q.text),v=voiceFor(q.code);", "parts=splitSentences(q.text),tone=q.tone||(!q.force&&(q.field||'translation')==='translation'&&q.entry?.tone)||null,v=voiceFor(q.code,tone);")
AISAY = blk(C2, "const aiSay=async text=>{")
AISAY = sub(AISAY, "geminiTTS(text,q.tone)", "geminiTTS(text,tone)")
AISAY = sub(AISAY, "setReading(q.text,a.playbackRate);followReading()", "setReading(q.text);followReading()")
rep("  const say=(text,retried)=>{\n", AISAY)
rep("u.rate=state.rate;if(v)u.voice=v;", "u.rate=state.rate;if(v)u.voice=v;\n    if(tone&&toneOn()){u.rate=Math.min(2,u.rate*(tone.rf||1));u.volume=tone.vol||1}")
rep("  entry.timing=opt.timing||latencyStart();latencyMark(entry.timing,'consume');", "  if(opt.fromMic&&toneOn()){const tn=speakerTone(source);if(tn)entry.tone=tn}\n  entry.timing=opt.timing||latencyStart();latencyMark(entry.timing,'consume');")
rep("function pressTalk(k){\n", "function pressTalk(k){\n  if(interp)return notify('AI 통역사가 켜져 있습니다. 끄려면 \"AI 통역사\"를 다시 누르세요.');\n")
rep("  const tr2=node('div','talk-row','',s);", blk(C2, "const ar=node('div','ai-row','',s);"))

# ───── 마이크: 폰 안 음성 인식은 "확정 문장"만 올림 · 화면 꺼도 듣기 · 이어폰 ─────
rep("function resumeRecognizer(){if(isConv()&&(outBusy||state.speaking))return;if(state.mic&&!state.recognizer&&!state.modal&&!dict&&state.page==='main'&&!document.hidden)startRecognition()}",
    "function resumeRecognizer(){if(isConv()&&(outBusy||state.speaking)&&!earOn())return;if(state.mic&&!state.recognizer&&!state.modal&&!dict&&state.page==='main'&&(!document.hidden||bgListen()))startRecognition()}")
rep("  if(document.hidden){const wasMic=state.mic,t=state.mode==='listen'&&wasMic?manualTurn:null",
    "  if(document.hidden&&(bgListen()||interp))return; // 앱: 화면이 꺼져도 계속 듣고 통역\n  if(document.hidden){const wasMic=state.mic,t=state.mode==='listen'&&wasMic?manualTurn:null")
rep("function killAllMics(){stopRefCamera();", """/* 화면을 꺼도 계속 듣는 조건: 듣기 모드 + 폰 안 음성 인식 */
function bgListen(){return NAT.on&&state.mic&&state.page==='main'&&state.mode==='listen'&&NAT.stt.useLocal(state.listenFrom==='ko'?'ko-KR':active().locale)}
function killAllMics(){stopInterp();stopRefCamera();""")
rep("function updateMic(){\n", "function updateMic(){\n  if(NAT.on)NAT.stt.setBackground(bgListen()||!!interp);\n")
rep("  r.lang=foreign?active().locale:'ko-KR';const source=foreign?active().code:'ko';state.listenLang=source;updateMic();",
    "  const autoDet=!live&&state.recog==='auto'&&NAT.on&&NAT.stt.useLocal('ko-KR')&&NAT.stt.useLocal(active().locale); // 폰 안 음성 인식: 번갈아 듣지 않고 언어를 알아서 구분\n  r.lang=autoDet?'auto':foreign?active().locale:'ko-KR';let source=foreign?active().code:'ko';state.listenLang=source;updateMic();")
rep("""  function commit(){
    clearTimeout(gapTimer);if(!valid())return;
    let text=buffer.take();const drop=echo;echo=false;
    if(turn){
      if(!turn.finished&&!drop&&!isEmptyText(text))addTurnPart(turn,auDedupWords(text));""",
"""  function commit(direct){ // direct: 폰 안 음성 인식이 확정한 문장 하나 → 겹침 정리 없이 그대로 한 번만 넣음
    clearTimeout(gapTimer);if(!valid())return;
    const fromLocal=typeof direct==='string';
    let text=fromLocal?direct:buffer.take();const drop=echo;echo=false;
    if(turn){
      if(!turn.finished&&!drop&&!isEmptyText(text)){if(fromLocal)turn.parts.push(text);else addTurnPart(turn,auDedupWords(text))}""")
rep("    if(text===lastFinal.text&&now-lastFinal.at<5000)return;\n    lastFinal={text,at:now,source,micId};gotFin=true;state.sourceTurn++;",
    "    if(!fromLocal&&text===lastFinal.text&&now-lastFinal.at<5000)return;\n    if(autoDet&&r._lastLang){const fb=active().code.split('-')[0];if(/^ko/.test(r._lastLang))source='ko';else if(r._lastLang.startsWith(fb)||(fb==='zh'&&r._lastLang==='yue'))source=active().code;state.listenLang=source}\n    lastFinal={text,at:now,source,micId};gotFin=true;state.sourceTurn++;")
rep("""    echo=!live&&(state.speaking||Date.now()-speakEnd<600);
    const text=buffer.update(event.results);if(state.mic&&!r._draining)activity();
    const owns=!state.recognizer||state.recognizer===r;""",
"""    echo=!live&&(state.speaking||Date.now()-speakEnd<600)&&!earOn();
    const owns=!state.recognizer||state.recognizer===r;
    if(r._local){
      /* 폰 안 음성 인식: 문장이 끝나면 "확정"을 한 번 보내 줌 → 확정만 넣음.
         말하는 중의 중간 글자는 같은 소리를 여러 번 다시 읽은 것이라 화면에만 보여 줌 (넣으면 같은 말이 두 번 들어감). 마이크를 다시 켤 필요도 없음 */
      const last=event.results[event.results.length-1],t=String(last?.[0]?.transcript||'').trim();
      if(state.mic&&!r._draining)activity();
      if(last?.isFinal){
        if(t)commit(t);
        if(turn&&live&&t&&!turn.finished){ // 묶음을 끊을지 확인 (고른 시간·조용함)
          if(!turn.firstAt)turn.firstAt=performance.now();
          const tt=turn;clearTimeout(gapTimer);gapTimer=setTimeout(()=>{if(valid()&&state.recognizer===r)maybeCutListen(tt)},400);
          clearTimeout(listenQuietTimer);listenQuietTimer=setTimeout(()=>{if(valid())maybeCutListen(manualTurn,true)},listenQuiet());
        }
        return}
      if(turn){turn.live=echo?'':t;if(live&&t&&!turn.finished&&!turn.firstAt)turn.firstAt=performance.now();if(owns&&manualTurn===turn&&!turn.finished){state.interim=turnText(turn,' · ');updateLive()}return}
      if(owns){state.interim=echo?'':t;if(live&&t)state.listenPreview=t;updateLive()}
      return;
    }
    const text=buffer.update(event.results);if(state.mic&&!r._draining)activity();""")

# 여행 문구 받기·자주 쓰는 문장 미리 번역 (예전엔 무료 번역기) → 폰 AI로
rep("function cached(text,src,target){", """// 문장 하나를 미리 번역해 둘 때: 폰 AI로 (폰 AI가 없으면 Gemini)
async function translateOne(text,src,target){
  if(localReady())return localTranslate(text,src,target);
  if(geminiKey()&&navigator.onLine)return geminiTranslate(text,src,target,'');
  throw Error(NO_ENGINE);
}
function cached(text,src,target){""")
rep("async function precache(texts){\n  if(!navigator.onLine)return;", "async function precache(texts){\n  if(!navigator.onLine&&!localReady())return;")
rep("async function downloadPhrases(code,btn,done){\n  if(!navigator.onLine)return notify('인터넷이 될 때 받을 수 있습니다.');",
    "async function downloadPhrases(code,btn,done){\n  if(!localReady())return notify('여행 문구는 폰 AI로 번역해 받아 둡니다. 설정 → 번역 AI에서 폰 AI를 먼저 받아 주세요.'); // 수백 문장이라 Gemini 크레딧은 쓰지 않음")
# 남은 "무료 번역기" 안내 문구 정리
s = s.replace("(무료 번역기도 적용)", "(폰 AI 번역에도 적용)").replace("(무료 번역기도 사용)", "(폰 AI 번역에도 사용)")
open(out, 'w', encoding='utf-8').write(s)
print('ok', len(s))
left = [(i+1, l[:150]) for i, l in enumerate(s.split('\n')) if '무료' in l and ('notify' in l or "node('p'" in l)]
print(len(left),'lines mention 무료')
