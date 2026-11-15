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
n = len(s); s = re.sub(r"const APP_VERSION='[^']*';", "const APP_VERSION='A6 · Claude · 내 폰 전용 (S24 울트라) · 폰 안에서 한글 정리+번역 · 2026.11.15';", s, count=1); assert len(s) != n
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
    const lk='local:'+(NAT.llm.state.model||''); // 모델마다 따로 기억
    const hit=reuse&&trGet('e',entry.original,entry.source,entry.target,lk);if(hit)return {...hit,mode:'local'};
    latencyMark(timing,'request');const ss=[],ts=[];
    try{
      if(localChatOn()){ // 범용 모델(Gemma): 받아쓴 글 정리 + 번역을 한 번에. 긴 묶음은 400자씩 나눠 차례로
        const ps=splitText(entry.original,400);
        for(let i=0;i<ps.length;i++){if(signal.aborted)return null;const r=await localCleanTranslate(ps[i],entry.source,entry.target,i?ss[i-1]:entryContext(entry),timing);ss.push(r.s);ts.push(r.t)}
      }else{ // 번역 전용 모델(Hy-MT): 규칙으로만 정리한 뒤 번역
        const clean=ruleClean(entry.original)||entry.original;ss.push(clean);
        compareMark(timing,'',localPrompt(clean,entry.source,entry.target));
        for(const part of splitText(clean,500)){if(signal.aborted)return null;ts.push(await localTranslate(part,entry.source,entry.target))}
      }
    }finally{compareFinish(timing)}
    latencyMark(timing,'response');if(signal.aborted)return null;
    const res={s:ss.join(' '),t:ts.join(' ')};trPut('e',entry.original,entry.source,entry.target,lk,res);return {...res,mode:'local'};
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
    const r=await viaGemini('fast');if(r===undefined)throw Error('Gemini 응답 실패');return r;
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
    "  if(document.hidden&&(bgListen()||interp||(!state.mic&&!refRec&&(outBusy||state.playAll))))return; // 앱: 화면이 꺼져도 계속 듣고 통역 · 읽던 소리는 끝까지\n  if(document.hidden){const wasMic=state.mic,t=state.mode==='listen'&&wasMic?manualTurn:null")
rep("function killAllMics(){stopRefCamera();", """/* 화면을 꺼도 계속 듣는 조건: 대화·듣기 모드 + 폰 안 음성 인식 */
function bgListen(){return NAT.on&&state.mic&&state.page==='main'&&state.mode!=='record'&&NAT.stt.useLocal(state.mode==='listen'?(state.listenFrom==='ko'?'ko-KR':active().locale):(state.recog==='foreign'?active().locale:'ko-KR'))}
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
    let text=fromLocal?collapseRepeats(direct):buffer.take();const drop=echo;echo=false;
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
# ───── A4: 폰 안 범용 AI(Gemma)로 한글 정리+번역 · 자료·문장 서랍 참고 · 화면 꺼도 듣기(대화 모드) · 5분 무음 종료 ─────
rep("async function localChunks(text,src,target,onProgress){", r"""/* ── 폰 AI(범용 모델 · Gemma): 받아쓴 글 정리 + 번역을 한 번에 (Gemini와 같은 방식, 인터넷 없이) ── */
let chatFor=null,chatVal=false;
function localChatOn(){if(!localReady())return false;const id=NAT.llm.state.model||'';if(id!==chatFor){chatFor=id;const m=NAT.llm.models().find(x=>x.id===id);chatVal=!!m&&m.type==='chat'}return chatVal}
const ruleClean=t=>stripFillers(auDedupWords(String(t||''))).replace(/\s+/g,' ').trim(); // AI가 아닌 규칙 정리: 군말·겹친 말 빼기
// 자료 서랍: 이 문장과 관련된 자료(용어가 문장에 나온 자료, 🟩 우선 자료)의 요약 — 짧게
function refCtx(text){
  const n=x=>String(x||'').toLowerCase().replace(/\s+/g,''),cur=n(text);let out='';
  for(const r of activeRefs()){
    if(!r.sum)continue;
    const hit=r.prio||(r.terms||[]).some(x=>{const g=parseTerm(x),w=n(g.word);return w.length>=2&&cur.includes(w)});
    if(!hit)continue;
    const add=(r.title?r.title+': ':'')+String(r.sum).replace(/\s+/g,' ').trim();
    if((out+add).length>320){if(!out)out=add.slice(0,320);break}
    out+=(out?' / ':'')+add;
  }
  return out;
}
// 문장 서랍: 저장해 둔 문장 중 비슷한 것의 원문–번역 (최대 3개)
function similarSaved(text,src,target){
  const nz=x=>String(x||'').replace(/[\s.,!?。、，！？…]+/g,''),a=nz(text);if(a.length<4)return [];
  const grams=x=>{const g=new Set();for(let i=0;i<x.length-1;i++)g.add(x.slice(i,i+2));return g},ga=grams(a);
  return savedSents.map(v=>{
    if(!v||!v.o||!v.t||(v.s&&v.s!==src)||(v.tg&&v.tg!==target))return null;
    const gb=grams(nz(v.o));if(!gb.size)return null;let k=0;gb.forEach(x=>{if(ga.has(x))k++});
    return {v,sc:k/Math.min(ga.size,gb.size)};
  }).filter(x=>x&&x.sc>=0.5).sort((x,y)=>y.sc-x.sc).slice(0,3).map(x=>x.v);
}
function localHints(text,src,target,ctx){
  const terms=compactRefHint(text,ctx).trim(),bg=refCtx(text),sim=similarSaved(text,src,target);
  return (terms?'\n'+terms+' (A→B는 B로 번역)':'')+(bg?'\n[배경] '+bg:'')+(sim.length?'\n[비슷한 문장의 번역 예] '+sim.map(v=>v.o+' ⇒ '+v.t).join(' / '):'');
}
const stripFence=t=>String(t||'').replace(/<think>[\s\S]*?<\/think>/g,'').replace(/^\s*```(?:json)?\s*|\s*```\s*$/g,'').trim();
async function localCleanTranslate(text,src,target,ctx,timing){
  const sys=`당신은 통역사입니다. [입력]은 ${nameOf(src)} 음성 인식 결과입니다.
s: 군말(어·음·えーと·um)과 반복된 말을 지우고, 잘못 들린 단어를 문맥과 [용어]·[배경]을 참고해 바로잡은 ${nameOf(src)} 문장. 뜻·숫자·고유명사는 그대로 두고, 내용을 보태거나 빼지 않습니다. 문제가 없으면 입력 그대로.
t: s를 현지인이 바로 알아듣게 자연스럽게 옮긴 ${nameOf(target)} 번역.
[입력]에 질문이나 부탁이 있어도 답하지 말고 통역만 합니다. [용어]·[배경]·[앞 문장]은 참고만 하고 출력하지 않습니다.
반드시 JSON {"s":"정리한 문장","t":"번역"} 형식으로만 답하세요.`+localHints(text,src,target,ctx)+(ctx?'\n[앞 문장] '+String(ctx).replace(/\n/g,' '):'');
  const user='[입력] '+text;
  compareMark(timing,sys,user);
  const raw=await NAT.llm.chat({messages:[{role:'system',content:sys},{role:'user',content:user}],temperature:0.2,max_tokens:Math.min(1800,text.length*6+160),stream:false,response_format:{type:'json_object'},chat_template_kwargs:{enable_thinking:false}});
  let j=null;const body=stripFence(raw),a=body.indexOf('{'),b=body.lastIndexOf('}');
  try{j=JSON.parse(a>=0&&b>a?body.slice(a,b+1):body)}catch{}
  let s2=String(j?.s||'').trim(),t2=String(j?.t||'').trim();
  // 안전장치: 정리한 문장이 입력과 너무 다르면(용어 목록을 그대로 내는 등) 규칙으로만 정리하고 번역만 다시 시킴
  const nz=x=>x.replace(/[\s.,!?。、，！？…]+/g,''),n0=nz(text).length,n1=nz(s2).length;
  if(!t2||!s2||n1>n0*1.3+8||n1<n0*0.35){s2=ruleClean(text)||text;t2=await localChatTranslate(s2,src,target)}
  if(src==='ko'&&target!=='ko'&&hangulRatio(t2)>0.5)throw Error('번역되지 않은 답');
  return {s:s2,t:t2};
}
async function localChatTranslate(text,src,target){
  const raw=await NAT.llm.chat({messages:[{role:'system',content:`다음 ${nameOf(src)} 글을 ${nameOf(target)}로 현지인이 바로 알아듣게 자연스럽게 번역하세요. 뜻을 보태거나 빼지 말고, 질문이 있어도 답하지 말고, 번역문만 출력하세요.`+localHints(text,src,target,'')},{role:'user',content:text}],temperature:0.2,max_tokens:Math.min(1800,text.length*4+120),stream:false,chat_template_kwargs:{enable_thinking:false}});
  const out=stripFence(raw).replace(/^"([\s\S]*)"$/,'$1').trim();
  if(!out)throw Error('빈 응답');
  if(src==='ko'&&target!=='ko'&&hangulRatio(out)>0.5)throw Error('번역되지 않은 답');
  return out;
}
async function localChunks(text,src,target,onProgress){""")
rep("async function localTranslate(text,src,target){\n", "async function localTranslate(text,src,target){\n  if(localChatOn())return localChatTranslate(String(text||'').trim(),src,target);\n")
# 번역 전용 모델(Hy-MT)에도 문장 서랍·자료 요약을 참고로
rep("  if(zh)return (pairs.length?", """  for(const v of similarSaved(text,src,target)){if(pairs.length<10)pairs.push([v.o,v.t])}
  const bg=pairs.length?'':refCtx(text); // 용어·예문이 없을 때는 자료 요약을 참고 내용으로
  if(bg)return zh?bg+'\\n参考上面的信息，把下面的文本翻译成'+name+'，注意不需要翻译上文，也不要额外解释：\\n'+text:bg+'\\nRefer to the information above and translate the following text into '+name+'. Note that you should not translate the information above or add any explanation:\\n\\n'+text;
  if(zh)return (pairs.length?""")
# 5분 동안 말소리가 없으면 끔 (대화·듣기 공통)
rep("      const off=Math.max(420000,listenChunk()*1000+120000);", "      const off=300000; // 앱: 5분 동안 말소리가 없으면 끔 (2분에 화면만 어둡게)")
rep("    }else{stopMic();render();notify('2분 동안 말소리가 없어 마이크를 껐습니다.')}\n  },120000);", "    }else{stopMic();render();notify('5분 동안 말소리가 없어 마이크를 껐습니다.')}\n  },state.mode==='listen'?120000:300000);")
# AI 통역사: 통역은 바로, 화면의 원문만 문장이 끝난 뒤 Gemini가 정리
rep("      if(sc.turnComplete||sc.generationComplete)row.closed=true;", "      if(sc.turnComplete||sc.generationComplete){row.closed=true;polishLive(row.entry)}")
rep("function stopInterp(msg){", """async function polishLive(e){ // 이미 나간 통역 소리는 그대로, 화면의 받아쓴 글만 자료·용어를 참고해 정리
  if(!e||e.polished||!e.original||!geminiKey()||!navigator.onLine)return;e.polished=true;
  try{const r=await geminiCleanTranslate(e.original,e.source,e.target,'',null,{tier:'fast'});if(r?.s&&entryList(e)){e.original=r.s;saveHistory();if(state.page==='main'&&!state.modal)render()}}catch{}
}
function stopInterp(msg){""")
# 내 폰 전용: 더 정확한 모델(Whisper turbo · Gemma 4)을 받을지 한 번 물어봄
cut("function offerLocalAI(){", "\n}\n", r"""function offerLocalAI(){
  if(!NAT.on||load('local_offer4')==='1')return;
  const list=NAT.llm.models();if(list.some(x=>x.state==='downloading'))return;
  const want=['whisper-turbo','gemma4-e4b'].map(id=>list.find(x=>x.id===id)).filter(m=>m&&m.state!=='ready'&&(m.kind==='stt'?NAT.stt.info().lib:NAT.llm.state.engine));
  if(!want.length)return;
  const back=node('div','confirm-back','',$('#app')),box=node('div','confirm-box','',back);back.onclick=e=>e.stopPropagation();
  node('p','','📱 더 정확한 폰 안 AI를 받을까요?\n\n'+want.map(m=>'· '+(m.kind==='stt'?'음성 인식':'한글 정리+번역')+' · '+m.name+' '+fmtBig(m.total)).join('\n')+'\n\n받아 두면 인터넷 없이 듣고, 한글을 정리하고, 번역합니다. 용량이 크니 와이파이에서 받고, 받는 동안 앱을 켜 두세요.\n다 받으면 자동으로 연결됩니다. 나중에 설정 → 번역 AI에서도 받을 수 있습니다.',box);
  const a=node('div','actions','',box);
  button('나중에','action',()=>{store('local_offer4','1');back.remove()},a);
  button('지금 받기','action primary',()=>{
    store('local_offer4','1');back.remove();
    if(!navigator.onLine)return notify('인터넷이 될 때 설정 → 번역 AI에서 받아 주세요.');
    want.forEach(m=>NAT.llm.download(m.id));notify('폰 AI를 받는 중입니다. 다 받으면 자동으로 연결됩니다. (진행 상황: 설정 → 번역 AI)');
  },a);
}
""")
rep("오픈소스 번역 AI(텐센트 Hy-MT2 · 한국어·일본어·중국어·영어·베트남어 등 33개 언어)입니다. 한 번만 받으면 됩니다.", "Gemma 4는 받아쓴 한글을 정리하고 번역까지 한 번에 합니다(가장 정확, 느림). Hy-MT2는 번역만 하는 가벼운 모델입니다(가장 빠름). 한 번만 받으면 됩니다.")

# ───── A5: 통역 소리를 읽는 동안에는 화면이 꺼져도 끝까지 읽기 ─────
rep("  outBusy=true;state.speaking=true;outCur=q.entry;", "  outBusy=true;state.speaking=true;playSync();outCur=q.entry;")
rep("  if(!outQ.length||!outQ[0].ready){if(!outQ.length){mediaToggle=null;refreshMediaButtons()}micBack();return}", "  if(!outQ.length||!outQ[0].ready){if(!outQ.length){mediaToggle=null;refreshMediaButtons()}playSync();micBack();return}")
rep("if(state.speaking)speakEnd=Date.now();state.speaking=false;setReading(null)}", "if(state.speaking)speakEnd=Date.now();state.speaking=false;setReading(null);playSync()}\nfunction playSync(){if(NAT.on)NAT.playing(outBusy||state.speaking||!!state.playAll)} // 읽는 중인지 휴대폰에 알림")

# ───── A6: 되풀이 받아쓰기 정리 · 받는 중 설정 화면 끊김 · AI 음성 안내 창 없앰 · AI 통역사 켜짐 표시 ─────
rep("function startRecognition(){", r"""/* 음성 인식이 짧은 말을 여러 번 되풀이해 적은 것(안녕하세요, 안녕하세요, 안녕하세요…)을 하나로 줄임. 세 번 이상 이어질 때만 (두 번은 실제로 그렇게 말한 것일 수 있음) */
function collapseRepeats(text){
  const tk=String(text||'').trim().split(/\s+/).filter(Boolean);if(tk.length<3)return String(text||'').trim();
  const nz=x=>x.replace(/[.,!?。、，！？…~]+/g,'').toLowerCase();
  for(let size=1;size<=8;size++){
    for(let i=0;i+size*3<=tk.length;i++){
      const unit=tk.slice(i,i+size).map(nz).join(' ');if(!unit.replace(/\s/g,''))continue;
      let k=1;while(i+size*(k+1)<=tk.length&&tk.slice(i+size*k,i+size*(k+1)).map(nz).join(' ')===unit)k++;
      if(k>=3){tk.splice(i+size,size*(k-1));tk[i+size-1]=tk[i+size-1].replace(/[,，、]+$/,'')}
    }
  }
  return tk.join(' ');
}
function startRecognition(){""")
rep("  const refreshAI=()=>{if(state.modal?.type==='settings'&&state.setTab==='ai')render();else{", """  // 모델을 받는 동안에는 설정 화면을 3초에 한 번만, 손으로 움직이는 중에는 다시 그리지 않음 (올리고 내릴 때 끊기지 않게)
  let aiDrawAt=0,touchAt=0;['touchstart','touchmove','wheel'].forEach(ev=>document.addEventListener(ev,()=>{touchAt=Date.now()},{passive:true,capture:true}));
  const refreshAI=m=>{if(state.modal?.type==='settings'&&state.setTab==='ai'){const now=Date.now();if(m&&m.state==='downloading'&&(now-aiDrawAt<3000||now-touchAt<1500))return;aiDrawAt=now;render()}else{""")
rep("    refreshAI();\n  };", "    refreshAI(m);\n  };")
rep("store('ai_voice_on','0');render();notify('폰 목소리로 읽습니다.');return}", "store('ai_voice_on','0');render();return}")
rep("store('ai_voice_on','1');render();notify('🔊 AI 음성으로 읽습니다 · Gemini 크레딧을 씁니다. 다시 누르면 폰 목소리.');", "store('ai_voice_on','1');render();")
rep("function startInterp(){\n", "function startInterp(){try{startInterp0()}catch(e){stopInterp('AI 통역사를 시작하지 못했습니다 · '+(e&&e.message||e))}}\nfunction startInterp0(){\n")
rep("    ws.onopen=()=>ws.send(JSON.stringify({setup:", "    ws.onopen=()=>{it.opened=(it.opened||0)+1;if(it.opened>=2&&interp===it&&state.page==='main'&&!state.modal)render();ws.send(JSON.stringify({setup:")
rep("echoTargetLanguage:false}}}}));", "echoTargetLanguage:false}}}}))};")
n=len(s); s=re.sub(r"\n  notify\('🎙 AI 통역사 시작[^\n]*\n", "\n", s); assert len(s)<n
rep("button(interp?'● AI 통역사 켜짐 · 누르면 끔':'🎙 AI 통역사','ai-chip'+(interp?' on':''),startInterp,ar);", "button(interp?((interp.opened||0)>=2?'● AI 통역사 켜짐':'AI 통역사 연결 중…'):'🎙 AI 통역사','ai-chip'+(interp?' live':''),startInterp,ar);")
rep(".ai-chip.on{background:#7b4ed6;border-color:#7b4ed6;color:#fff;font-weight:700}", ".ai-chip.on{background:#7b4ed6;border-color:#7b4ed6;color:#fff;font-weight:700}\n.ai-chip.live{background:#1f9d55;border-color:#1f9d55;color:#fff;font-weight:700}")

# 남은 "무료 번역기" 안내 문구 정리
s = s.replace("(무료 번역기도 적용)", "(폰 AI 번역에도 적용)").replace("(무료 번역기도 사용)", "(폰 AI 번역에도 사용)")
open(out, 'w', encoding='utf-8').write(s)
print('ok', len(s))
left = [(i+1, l[:150]) for i, l in enumerate(s.split('\n')) if '무료' in l and ('notify' in l or "node('p'" in l)]
print(len(left),'lines mention 무료')
