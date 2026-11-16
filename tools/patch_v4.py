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
n = len(s); s = re.sub(r"const APP_VERSION='[^']*';", "const APP_VERSION='A20 · Claude · 내 폰 전용 (S24 울트라) · 소리 저장 · 폰 소리 녹음 · 폰 AI / Gemini가 소리 직접 듣기 · 2026.11.15';", s, count=1); assert len(s) != n
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
rep("model:engine()==='gemini'?gemModel():'free'}}", "model:engine()==='gemini'?gemModel():'local'}}")
rep("  if(engine()==='free'&&!(opt?._entryGemini&&geminiKey()))throw Object.assign(Error('Gemini 키·모드가 필요합니다'),{stop:true});",
    "  if((engine()==='free'||!geminiKey())&&!(opt?._entryGemini&&geminiKey()))throw Object.assign(Error('Gemini 키·모드가 필요합니다'),{stop:true});")
rep("function warmGemini(){if(!aiReady()||!navigator.onLine||", "function warmGemini(){if(engine()!=='gemini'||!navigator.onLine||")
rep("function goMain(){setTimeout(warmGemini,0);", "function goMain(){setTimeout(warmGemini,0);if(localReady())NAT.llm.ensure();")
rep("""    if(!geminiKey()){notify('Gemini 키가 없어 무료 번역기를 사용합니다.');return}
    if(state.mic)stopMic();
    if(engine()==='free'){store('tr_engine','gemini');store('gem_tier','fast')}
    else {const i=GEM_TIERS.findIndex(x=>x[0]===gemTier());
      if(i===GEM_TIERS.length-1)store('tr_engine','free');else store('gem_tier',GEM_TIERS[i+1][0])}
    gemStop='';render();""",
"""    // 폰 AI → Gemini 빠름 → 균형 → 정확 → 무료 → 폰 AI … (쓸 수 있는 것만)
    const modes=engineChoices();
    if(modes.length<2){notify(modes.length?(localReady()?'고급 탭에 Gemini 키를 넣으면 Gemini 번역기도 고를 수 있습니다.':'설정 → 번역 AI에서 폰 AI를 받으면 폰 AI 번역도 고를 수 있습니다.'):NO_ENGINE);return}
    if(state.mic)stopMic();
    setEngineMode(modes[(modes.indexOf(currentEntryMode())+1)%modes.length]);
    gemStop='';render();""")
rep("""      if(!geminiKey())store('tr_engine','free');
      else if(!had){store('tr_engine','gemini');store('gem_tier','fast')}""",
"""      if(!geminiKey()){if(load('tr_engine')==='gemini')store('tr_engine','local')}
      else if(!had&&!localReady()){store('tr_engine','gemini');store('gem_tier','fast')} // 폰 AI를 쓰는 중이면 기본 번역기는 그대로""")
rep("function provider(){return engine()==='gemini'?'gemini':null}", "function provider(){return geminiKey()&&engine()!=='free'?'gemini':null} // 폰 AI가 기본이어도 키가 있으면 사진·PDF·녹음·자료 정리는 Gemini로")
rep("async function aiPolish(area,code,onChange){\n  if(!aiReady()||!navigator.onLine)return;",
    "async function aiPolish(area,code,onChange){\n  if(engine()!=='gemini'||!navigator.onLine)return; // 자동 다듬기는 Gemini 번역기를 골랐을 때만 (크레딧 보호)")
rep("function engLabel(){if(engine()!=='gemini')return engineName();return 'Gemini '+GEM_TIERS.find(x=>x[0]===gemTier())[1]}",
    "function engLabel(){const e=engine();if(e==='local')return '📱 폰 AI 번역';if(e==='free')return '무료 번역기';return 'Gemini '+GEM_TIERS.find(x=>x[0]===gemTier())[1]}")
A1ENG = blk(C1, "function localPrompt(text,src,target){", "function localReady()")
local_fns = A1ENG[A1ENG.index("/* 폰 AI 번역 (Hy-MT2)"):]
rep("function engine(){const e=load('tr_engine','');if(e==='free')return'free';return geminiKey()?'gemini':'free'}\nconst engineName=()=>({free:'무료 번역기',gemini:'Gemini 번역기'})[engine()];",
r"""/* 번역기 세 가지: local = 폰 안 AI(무료·오프라인, 기본) · gemini · free = 무료 번역기(인터넷 필요).
   고른 번역기를 못 쓰는 상태면(모델 안 받음·키 없음) 쓸 수 있는 쪽으로 자동으로 넘어감 */
const NO_ENGINE='번역기가 준비되지 않았습니다. 설정 → 번역 AI에서 폰 AI를 받거나, 고급 탭에 Gemini 키를 넣어 주세요.';
function localReady(){return NAT.on&&NAT.llm.usable()}
function engine(){const e=load('tr_engine','');
  if(e==='free')return 'free';
  if(e==='gemini'&&geminiKey())return 'gemini';
  if(localReady())return 'local';
  return geminiKey()?'gemini':'free'} // 폰 AI도 키도 없으면 무료 번역기(인터넷)
const engineName=()=>({gemini:'Gemini 번역기',local:'폰 AI 번역',free:'무료 번역기'})[engine()];
function engineChoices(){const m=[];if(localReady())m.push('local');if(geminiKey())m.push('fast','balanced','accurate');m.push('free');return m}
function setEngineMode(m){if(m==='local'||m==='free')store('tr_engine',m);else{store('tr_engine','gemini');store('gem_tier',m)}if(m==='local'&&NAT.on)NAT.llm.ensure()}
""" + local_fns)
cut("async function translateAI(text,src,target,ctx){", "function cached(text,src,target){", r"""async function localChunks(text,src,target,onProgress){const out=[],parts=splitText(text,500);for(let i=0;i<parts.length;i++){out.push(await localTranslate(parts[i],src,target));if(parts.length>1)onProgress?.(out.join(' '),i+1,parts.length)}return out.join(' ')}
async function translateAI(text,src,target,ctx){ // Gemini로 번역 · 실패하면 폰 AI로
  try{return await geminiTranslate(text,src,target,ctx)}
  catch(err){if(!localReady())throw err;if(Date.now()-lastEngineWarn>60000){lastEngineWarn=Date.now();notify(`Gemini 번역 실패 → 폰 AI로 대신 번역합니다 (${err.message})`)}}
  return localChunks(text,src,target);
}
async function freeOne(text,src,target){ // 무료 번역기 (MyMemory · 인터넷 필요)
  text=stripFillers(text);
  const qs=new URLSearchParams({q:text,langpair:`${src}|${target}`});
  const res=await fetch('https://api.mymemory.translated.net/get?'+qs,{signal:AbortSignal.timeout(15000)});
  if(!res.ok)throw Error('번역 서버 오류 '+res.status);
  const p=await res.json();
  if(Number(p.responseStatus)!==200)throw Error(p.responseDetails||'번역 실패');
  const out=decodeEntities(p.responseData?.translatedText);
  if(!out)throw Error('번역 결과 없음');
  return out;
}
function cached(text,src,target){""")
cut("  if(!navigator.onLine)throw new Error('인터넷이 없습니다. 📚 여행 문구나 받아 둔 자주 쓰는 문장을 써 주세요');", "trPut('t',text,src,target,mode,res);return res;\n", r"""  let res=null;const eng=engine(),warn=m=>{if(Date.now()-lastEngineWarn>60000){lastEngineWarn=Date.now();notify(m)}};
  if(eng==='local'&&localReady()){ // 폰 AI: 인터넷 없이 번역
    try{res=await localChunks(text,src,target,onProgress)}
    catch(err){if(!navigator.onLine)throw Error('폰 AI 번역 실패 · '+err.message);warn('폰 AI 번역 실패 → '+(geminiKey()?'Gemini':'무료 번역기')+'로 대신 번역합니다 ('+err.message+')')}
  }
  if(res==null&&!navigator.onLine){
    if(!localReady())throw new Error('인터넷이 없습니다. 📚 여행 문구나 받아 둔 자주 쓰는 문장을 써 주세요');
    res=await localChunks(text,src,target,onProgress); // 인터넷이 없으면 폰 AI로
  }
  if(res==null&&eng!=='free'&&geminiKey()){
    try{const chunks=splitText(text,2500),out=[];
      for(let i=0;i<chunks.length;i++){out.push(await translateAI(chunks[i],src,target,i?'':ctx));if(chunks.length>1)onProgress?.(out.join(' '),i+1,chunks.length)}
      res=out.join(' ')}
    catch(err){warn('Gemini 번역 실패 → 무료 번역기로 대신 번역합니다 ('+err.message+')')}
  }
  if(res==null){ // 무료 번역기 (380자씩)
    const chunks=splitText(text,380),out=[];
    for(let i=0;i<chunks.length;i++){out.push(await freeOne(chunks[i],src,target));if(chunks.length>1)onProgress?.(out.join(' '),i+1,chunks.length)}
    res=out.join(' ');
  }
  trPut('t',text,src,target,mode,res);return res;
""")
rep("const ENTRY_MODES=[['fast','빠름'],['balanced','균형'],['accurate','정확'],['free','무료']];\nconst currentEntryMode=()=>engine()==='gemini'?gemTier():'free';",
    "const ENTRY_MODES=[['local','폰AI'],['fast','빠름'],['balanced','균형'],['accurate','정확'],['free','무료']];\nconst currentEntryMode=()=>{const e=engine();return e==='gemini'?gemTier():e};")
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
  const viaFree=async()=>{
    const hit=reuse&&trGet('e',entry.original,entry.source,entry.target,'free');if(hit)return {...hit,mode:'free'};
    const input=entry.source==='ko'?protectWords(entry.original,entry.target):protectRev(entry.original,entry.source,true),parts=[];
    latencyMark(timing,'fallbackRequest');
    for(const part of splitText(input)){if(signal.aborted)return null;parts.push(await freeOne(part,entry.source,entry.target))}
    latencyMark(timing,'fallbackResponse');const t=parts.join(' ');trPut('e',entry.original,entry.source,entry.target,'free',{s:entry.original,t});return {s:entry.original,t,mode:'free'};
  };
  /* 순서: 고른 번역기 → 실패하면 다른 번역기. 폰 AI 실패 → (키 있으면) Gemini 빠름 → 무료 / Gemini 실패 → 폰 AI → 무료 / 인터넷 없음 → 폰 AI */
  if(mode==='free'){
    if(navigator.onLine)return viaFree();
    if(localReady()){notify('인터넷이 없어 폰 AI로 번역합니다.');return viaLocal()}
    throw Error('인터넷 연결을 확인해 주세요');
  }
  if(mode==='local'){
    if(localReady()){
      try{return await viaLocal()}
      catch(err){if(signal.aborted)return null;latencyMark(timing,'fallback');
        if(!navigator.onLine)throw Error('폰 AI 번역 실패 · '+err.message);
        notify('폰 AI 번역 실패 · '+(geminiKey()?'Gemini 빠름':'무료 번역기')+'으로 이어서 번역합니다. ('+err.message+')')}
    }else if(!navigator.onLine)throw Error(NO_ENGINE);
    if(geminiKey()){const r=await viaGemini('fast');if(r!==undefined)return r}
    return viaFree();
  }
  if(geminiKey()&&navigator.onLine){const r=await viaGemini(mode);if(r!==undefined)return r}
  latencyMark(timing,'fallback');
  if(localReady()){notify(entryModeName(mode)+(navigator.onLine?' 응답 실패':' · 인터넷 없음')+' · 폰 AI로 이어서 번역합니다.');return viaLocal()}
  if(!navigator.onLine)throw Error('인터넷 연결을 확인해 주세요');
  notify(entryModeName(mode)+' 응답 실패 · 무료 번역기로 이어서 번역합니다.');return viaFree();
}""")
rep("  if(mode!=='free'&&!geminiKey()){notify('Gemini 키가 필요합니다.');return}",
    "  if(mode==='local'&&!localReady()){notify('폰 AI가 준비되지 않았습니다. 설정 → 번역 AI에서 받아 주세요.');return}\n  if(mode!=='local'&&mode!=='free'&&!geminiKey()){notify('Gemini 키가 필요합니다.');return}")

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
  if(navigator.onLine)return freeOne(text,src,target); // 여행 문구 받기 등: 인터넷이 되면 무료 번역기 (빠름)
  if(localReady())return localTranslate(text,src,target);
  throw Error(NO_ENGINE);
}
function cached(text,src,target){""")
rep("async function precache(texts){\n  if(!navigator.onLine)return;", "async function precache(texts){\n  if(!navigator.onLine&&!localReady())return;")
rep("async function downloadPhrases(code,btn,done){\n  if(!navigator.onLine)return notify('인터넷이 될 때 받을 수 있습니다.');",
    "async function downloadPhrases(code,btn,done){\n  if(!navigator.onLine&&!localReady())return notify('인터넷이 될 때 받을 수 있습니다.');")
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

# ───── A7: AI 통역사 — 버튼 크기 고정(색으로만 표시) · 준비 확인 뒤 소리 전송 · 꺼진 이유 표시 ─────
rep("button(interp?((interp.opened||0)>=2?'● AI 통역사 켜짐':'AI 통역사 연결 중…'):'🎙 AI 통역사','ai-chip'+(interp?' live':''),startInterp,ar);",
    "if(interpNote)node('small','ai-note',interpNote,ar); // 꺼진 이유 (다시 켤 때까지 보임)\n    button('🎙 AI 통역사','ai-chip'+(interp?((interp.opened||0)>=2?' live':' wait'):''),startInterp,ar);")
rep("button(load('ai_voice_on')==='1'?'🔊 AI 음성 켜짐':'🔊 AI 음성','ai-chip'+(load('ai_voice_on')==='1'?' on':''),toggleAiVoice,ar);",
    "button('🔊 AI 음성','ai-chip'+(load('ai_voice_on')==='1'?' on':''),toggleAiVoice,ar);")
rep(".ai-chip.live{background:#1f9d55;border-color:#1f9d55;color:#fff;font-weight:700}",
    ".ai-chip.live{background:#1f9d55;border-color:#1f9d55;color:#fff}\n.ai-chip.wait{border-color:#1f9d55;color:#1f9d55;animation:aiwait .7s ease-in-out infinite alternate}\n@keyframes aiwait{from{opacity:.4}to{opacity:1}}\n.ai-chip,.ai-chip.on,.ai-chip.live,.ai-chip.wait{font-weight:600;min-width:96px;text-align:center;line-height:1.3;flex-shrink:0}\n.ai-note{flex:1;min-width:0;align-self:center;font-size:11px;color:#c0392b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}")
rep("let interp=null;\n", "let interp=null,interpNote='';\n")
rep("  const it=interp;if(!it)return;interp=null;\n", "  const it=interp;if(!it)return;interp=null;interpNote=msg&&!/껐습니다/.test(msg)?msg:'';\n")
rep("function startInterp0(){\n", "function startInterp0(){\n  interpNote='';\n")
rep("    ws.onopen=()=>{it.opened=(it.opened||0)+1;if(it.opened>=2&&interp===it&&state.page==='main'&&!state.modal)render();ws.send(JSON.stringify({setup:", "    ws.onopen=()=>{ws.send(JSON.stringify({setup:")
rep("      const sc=m.serverContent;if(!sc)return;", "      if(m.setupComplete!==undefined&&!ws.ready){ws.ready=true;it.opened=(it.opened||0)+1;if(interp===it&&state.page==='main'&&!state.modal)render();return} // 준비 완료 → 이때부터 소리를 보냄\n      const sc=m.serverContent;if(!sc)return;")
rep("    const fail=()=>{if(interp!==it)return;if(++it.fails>=1)stopInterp('AI 통역사 연결이 끊겼습니다. 다시 눌러 주세요. (키·크레딧·인터넷 확인)')};\n    ws.onerror=fail;ws.onclose=fail;",
    "    ws.onerror=()=>{};ws.onclose=ev=>{if(interp!==it)return;const why=String(ev&&ev.reason||'').slice(0,90)||(ev&&ev.code?'코드 '+ev.code:'');stopInterp('AI 통역사 연결이 끊겼습니다'+(why?' · '+why:'')+' (키·크레딧·인터넷 확인)')};")
rep("  NAT.pcm.onend=e=>{if(interp===it)stopInterp(e?'마이크를 열 수 없습니다.':'')};\n  NAT.pcm.start(b64=>{",
    "  NAT.pcm.onend=e=>{if(interp!==it)return;if(!e&&!it.pcmRetry){it.pcmRetry=1;setTimeout(()=>{if(interp===it)startPcm()},400);return} // 마이크 전달이 멈추면 한 번 다시 엶\n    stopInterp(e?'AI 통역사: 마이크를 열 수 없습니다 ('+e+')':'AI 통역사: 마이크 전달이 멈췄습니다')};\n  const startPcm=()=>NAT.pcm.start(b64=>{")
rep("    it.socks.forEach(ws=>{if(ws.readyState===1)ws.send(msg)});\n  },!ear);", "    it.socks.forEach(ws=>{if(ws.readyState===1&&ws.ready)ws.send(msg)});\n  },!ear);\n  startPcm();")

# ───── A8: AI 통역사 설정 형식 자동 맞춤·이유 전체 보기 · AI 음성 미리 만들기(문장 사이 쉼 줄임) ─────
cut("    ws.onopen=()=>{ws.send(JSON.stringify({setup:{model:", "echoTargetLanguage:false}}}}))};", "    ws.onopen=()=>{ws.send(JSON.stringify({setup:interpSetup(it.shape,liveCode(target))}))};")
rep("      if(m.setupComplete!==undefined&&!ws.ready){ws.ready=true;", "      if(ws.old)return;\n      if(m.setupComplete!==undefined&&!ws.ready){ws.ready=true;store('interp_shape',String(it.shape));")
rep("    ws.onerror=()=>{};ws.onclose=ev=>{if(interp!==it)return;const why=String(ev&&ev.reason||'').slice(0,90)||(ev&&ev.code?'코드 '+ev.code:'');stopInterp(", """    ws.onerror=()=>{};ws.onclose=ev=>{if(interp!==it||ws.old)return;const why=String(ev&&ev.reason||'').slice(0,400)||(ev&&ev.code?'코드 '+ev.code:'');
      if(!it.opened&&it.shape<2&&!/key|quota|permission|billing|exceed/i.test(why)){ // 서버가 설정 형식을 받아 주지 않으면 다른 형식으로 다시 연결 (받아쓴 글 요청 위치 → 글 없이 소리만)
        it.shape++;it.socks.forEach(x=>{x.old=true;try{x.close()}catch{}});it.socks=[];open(fg);open('ko');return}
      store('interp_shape','0');stopInterp(""")
rep("  const it=interp={socks:[],", "  const it=interp={shape:Math.min(2,+load('interp_shape','0')||0),socks:[],")
rep("function stopInterp(msg){", """/* AI 통역사 연결 설정. 받아쓴 글(화면 표시용)을 요청하는 자리가 문서마다 달라 세 가지를 차례로 시도: 0 = setup 바로 아래 · 1 = generationConfig 안 · 2 = 글 없이 통역 소리만 */
function interpSetup(shape,code){
  const g={responseModalities:['AUDIO'],translationConfig:{targetLanguageCode:code,echoTargetLanguage:false}},st={model:'models/gemini-3.5-live-translate-preview',generationConfig:g};
  if(shape===0){st.inputAudioTranscription={};st.outputAudioTranscription={}}
  else if(shape===1){g.inputAudioTranscription={};g.outputAudioTranscription={}}
  return st;
}
function stopInterp(msg){""")
rep("if(interpNote)node('small','ai-note',interpNote,ar); // 꺼진 이유 (다시 켤 때까지 보임)", "if(interpNote)node('small','ai-note',interpNote,ar).onclick=()=>askConfirm(interpNote,'복사',()=>{try{navigator.clipboard.writeText(interpNote);notify('복사했습니다.')}catch{}}); // 꺼진 이유 (누르면 전체 보기·복사)")
# AI 음성: 지금 문장을 읽는 동안 다음 문장들의 소리를 미리 만들어 둠
rep("      const url=await geminiTTS(text,tone);", "      const url=await aiTts(text,tone);")
rep("async function geminiTTS(text,tone){", """const aiTtsCache=new Map(); // 문장 → 만들어 둔(만드는 중인) 소리
function aiTts(text,tone){
  const k=(tone&&tone.g||'')+'|'+text;let p=aiTtsCache.get(k);
  if(!p){p=geminiTTS(text,tone);p.catch(()=>aiTtsCache.delete(k));aiTtsCache.set(k,p);if(aiTtsCache.size>40)aiTtsCache.delete(aiTtsCache.keys().next().value)}
  return p;
}
async function geminiTTS(text,tone){""")
rep("  outBusy=true;state.speaking=true;playSync();outCur=q.entry;", "  if(aiVoiceOn()){parts.slice(0,6).forEach(x=>{aiTts(x,tone).catch(()=>{})});const nx=outQ[0];if(nx&&nx.ready&&nx.text)splitSentences(nx.text).slice(0,2).forEach(x=>{aiTts(x,nx.tone||null).catch(()=>{})})} // 미리 만들기: 이 글의 문장들 + 다음 글의 첫 문장\n  outBusy=true;state.speaking=true;playSync();outCur=q.entry;")

# ───── A9: AI 통역사 새 방식 (기존 번역기와 분리) · 균형 모델 생각 수준 낮춤 ─────
# 듣기 모드 = 통역 전용 모델(끊김 없이, 방향 고르기) · 대화 모드 = Gemini 3.8 Live(말하고 버튼을 다시 누르면 통역)
# 연결은 방향마다 하나, 소리는 고른 방향에만 · 받아쓴 글은 한 번만 붙임 · Gemini 재정리(polishLive) 없음
# 설정 형식은 공식 문서(Live API WebSockets 참조·Live Translate 안내, 2026-11-15 확인) 기준
cut("/* ── AI 통역사 (Gemini Live Translate) ──", "  startPcm();\n  keepAwake();render();\n}\n", r"""/* ── AI 통역사 (A9) ──
   번역기·폰 음성 인식·글 정리와 섞지 않고, 듣기·통역·말하기를 모두 Gemini 음성 모델에 맡김.
   · 듣기 모드: 통역 전용 모델(Live Translate)이 끊김 없이 통역. 외국어 버튼 = 외국어→한국어, 한국어 버튼 = 한국어→외국어. 같은 버튼을 다시 누르면 멈춤
   · 대화 모드: 한 번에 한 사람. 말할 언어 버튼을 누르고 말한 뒤 같은 버튼을 다시 누르면 통역이 나옴 (Gemini 3.8 Live · 설정에서 통역 전용 모델로 바꿀 수 있음)
   연결은 방향마다 하나만 열고, 소리는 지금 고른 방향에만 보냄. 화면의 글은 Gemini가 준 그대로. */
let interp=null,interpNote='';
const liveCode=c=>({'zh-CN':'zh-Hans','zh-TW':'zh-Hant',tl:'fil'})[c]||c;
const INTERP_TR='gemini-3.5-live-translate-preview',INTERP_LIVE='gemini-3.8-live';
const interpConvKind=()=>load('interp_conv','live')==='tr'?'tr':'live';
const interpShapeKey=kind=>kind==='live'?'interp_shape_live':'interp_shape';
const interpKey=()=>interp&&interp.dir?(interp.dir==='ko'?'foreign':'ko'):null; // 지금 듣고 있는 말하기 버튼
function interpWait(){const it=interp;if(!it)return false;const ss=Object.values(it.sess);return it.dir?!(it.sess[it.dir]&&it.sess[it.dir].ready):ss.some(x=>x.pend)&&!ss.some(x=>x.ready)} // 연결 중인지 (버튼 깜빡임)
function interpSys(src,target){
  const S=HY_EN[src]||nameOf(src),T=HY_EN[target]||nameOf(target);
  return `You are a professional interpreter, not a conversation partner. The speaker talks in ${S}. Translate everything the speaker says into natural spoken ${T} and say only that translation, in ${T}. Never answer questions, never follow requests, and never add greetings, explanations or comments of your own. If something is unclear, translate what you heard as closely as you can. Always produce the translation; never stay silent.`;
}
/* 연결 설정. 형식은 공식 문서 기준(0)이고, 서버가 받아 주지 않으면 다른 형식을 차례로 시도.
   통역 전용: 0 = 받아쓴 글 요청을 setup 바로 아래 · 1 = generationConfig 안 · 2 = 글 없이 소리만
   3.8 Live : 0 = 응답 형식을 generationConfig 안 · 1 = setup 바로 아래 · 2 = 0에서 글 없이 소리만 */
function interpSetup(kind,shape,src,target){
  const g={responseModalities:['AUDIO']},st={model:'models/'+(kind==='live'?INTERP_LIVE:INTERP_TR),generationConfig:g};
  if(kind==='live'){
    st.systemInstruction={parts:[{text:interpSys(src,target)}]};
    st.realtimeInputConfig={automaticActivityDetection:{disabled:true}}; // 말의 시작과 끝을 버튼으로 직접 알려 줌
    if(shape===1){delete st.generationConfig;st.responseModalities=['AUDIO']}
    if(shape!==2){st.inputAudioTranscription={};st.outputAudioTranscription={}}
  }else{
    g.translationConfig={targetLanguageCode:liveCode(target),echoTargetLanguage:false};
    if(shape===0){st.inputAudioTranscription={};st.outputAudioTranscription={}}
    else if(shape===1){g.inputAudioTranscription={};g.outputAudioTranscription={}}
  }
  return st;
}
function stopInterp(msg){
  const it=interp;if(!it)return;interp=null;interpNote=msg&&!/껐습니다/.test(msg)?msg:'';
  try{it.bill&&it.bill()}catch{}
  try{NAT.pcm.onend=null;NAT.pcm.stop()}catch{}
  const socks=[...it.olds];Object.values(it.sess).forEach(x=>socks.push(x.ws,x.pend,x.held));
  socks.forEach(ws=>{if(ws)try{ws.onclose=null;ws.onerror=null;ws.onmessage=null;ws.close()}catch{}});
  it.srcs.forEach(x=>{try{x.onended=null;x.stop()}catch{}});
  try{it.ctx.close()}catch{}
  clearTimeout(it.timer);clearTimeout(it.waitT);clearInterval(it.idle);releaseWake();
  if(msg)notify(msg);
  if(state.page==='main')render();
}
function startInterp(){try{startInterp0()}catch(e){stopInterp('AI 통역사를 시작하지 못했습니다 · '+(e&&e.message||e))}}
function startInterp0(){
  interpNote='';
  if(interp)return stopInterp('AI 통역사를 껐습니다.');
  if(!NAT.on)return notify('AI 통역사는 안드로이드 앱에서만 됩니다.');
  if(!geminiKey())return notify('AI 통역사는 Gemini 키가 필요합니다. 설정 → 고급에서 키를 넣어 주세요.');
  if(!navigator.onLine)return notify('AI 통역사는 인터넷이 필요합니다.');
  if(state.mic)stopMic(isManualInput());stopSpeech();
  const fg=active().code,ear=NAT.stt.headset(),listen=state.mode==='listen';
  const it=interp={listen,kind:listen?'tr':interpConvKind(),sess:{},olds:[],dir:null,pending:false,ctx:new (window.AudioContext||window.webkitAudioContext)({sampleRate:24000}),next:0,srcs:[],timer:null,waitT:null,idle:null,lastAct:Date.now(),inSec:0,outSec:0};
  try{it.ctx.resume?.()}catch{}
  it.bill=()=>{if(it.inSec<0.05&&it.outSec<0.05)return;usageLive(it.kind==='live'?'AI 통역사 · 대화 (3.8 Live)':'AI 통역사 · 통역 전용',it.inSec,it.outSec,it.kind);it.inSec=0;it.outSec=0}; // 쓴 시간을 사용량 기록에 더함
  const url='wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key='+encodeURIComponent(load('ai_key').trim());
  const alive=()=>interp===it,touch=()=>{it.lastAct=Date.now()};
  const list=()=>listen?state.listening:state.items;
  const paint=()=>{if(it.timer)return;it.timer=setTimeout(()=>{it.timer=null;if(alive()&&state.page==='main'&&!state.modal){render();scrollEnd()}},400)};
  const keyTrouble=why=>/key|quota|permission|billing|exceed/i.test(why);
  const play=b64=>{
    if(state.speech===3)return;
    const u=b64Bytes(b64),n=u.length>>1,dv=new DataView(u.buffer),buf=it.ctx.createBuffer(1,n,24000),ch=buf.getChannelData(0);
    for(let i=0;i<n;i++)ch[i]=dv.getInt16(i*2,true)/32768;
    const src=it.ctx.createBufferSource();src.buffer=buf;src.connect(it.ctx.destination);
    const at=Math.max(it.ctx.currentTime+0.03,it.next);src.start(at);it.next=at+buf.duration;
    it.srcs.push(src);src.onended=()=>{const i=it.srcs.indexOf(src);if(i>=0)it.srcs.splice(i,1)};
  };
  const hush=()=>{it.srcs.splice(0).forEach(x=>{try{x.onended=null;x.stop()}catch{}});it.next=0}; // 나오던 통역 소리를 멈춤
  const newRow=()=>({entry:null,closed:true,outAt:0});
  const session=target=>it.sess[target]||(it.sess[target]={target,source:target==='ko'?fg:'ko',kind:it.kind,shape:Math.min(2,+load(interpShapeKey(it.kind),'0')||0),ws:null,pend:null,held:null,ready:false,everUp:false,turn:false,q:[],row:newRow(),fails:0});
  /* 화면의 글: Gemini가 보내 준 받아쓴 글·통역 글을 그대로, 한 번씩만 붙임.
     대화 모드는 말 한 번이 한 줄. 듣기 모드는 통역이 쉬었다 다시 나오거나 길어지면 문장 끝에서 새 줄 */
  const onContent=(s,sc)=>{
    const row=s.row,now=Date.now(),inT=sc.inputTranscription&&sc.inputTranscription.text,outT=sc.outputTranscription&&sc.outputTranscription.text;
    const open=()=>{row.entry={original:'',translation:'',source:s.source,target:s.target,failed:false,trMode:'live',createdAt:now};row.closed=false;row.outAt=0;list().push(row.entry)};
    if(inT){touch();const e=row.entry;
      if(!e||row.closed||(listen&&e.translation&&row.outAt&&now-row.outAt>1500))open(); // 통역이 끝나고 쉰 뒤의 말은 새 줄
      row.entry.original=(row.entry.original+inT).trimStart();paint()}
    if(outT){touch();const e=row.entry;
      if(!e||row.closed||(listen&&((row.outAt&&now-row.outAt>2500)||(e.translation.length>=220&&/[.?!。？！…]["'”’)]*\s*$/.test(e.translation)))))open();
      row.entry.translation+=outT;row.outAt=now;paint()}
    let sound=false;for(const part of (sc.modelTurn&&sc.modelTurn.parts)||[])if(part.inlineData&&part.inlineData.data){sound=true;it.outSec+=part.inlineData.data.length*0.75/48000;if(listen||s.outOn)play(part.inlineData.data)} // 대화 모드: 새로 말하기 시작하면 앞 통역의 남은 소리는 내지 않음
    if(sound)touch();
    if((outT||sound)&&it.pending){it.pending=false;clearTimeout(it.waitT);paint()}
    if(sc.interrupted)hush();
    if(listen&&(sc.turnComplete||sc.generationComplete))row.closed=true;
  };
  const swap=(s,ws)=>{ // 새 연결로 바꿈. 예전 연결은 남은 통역이 다 나올 때까지 잠깐 둠
    const old=s.ws;s.ws=ws;s.pend=null;s.ready=true;s.everUp=true;store(interpShapeKey(s.kind),String(s.shape));
    if(old&&old!==ws&&old.readyState<2){old.retired=true;it.olds.push(old);setTimeout(()=>{try{old.close()}catch{}},listen?5000:15000)}
    s.q.splice(0).forEach(m=>{try{ws.send(m)}catch{}});
    if(alive()&&state.page==='main'&&!state.modal)render();
  };
  const connect=s=>{
    if(s.pend)return;
    const ws=new WebSocket(url);s.pend=ws;ws.at=Date.now();ws.kind=s.kind;
    ws.onopen=()=>{try{ws.send(JSON.stringify({setup:interpSetup(s.kind,s.shape,s.source,s.target)}))}catch{}};
    ws.onmessage=async ev=>{
      if(!alive())return;let m;
      try{m=JSON.parse(typeof ev.data==='string'?ev.data:await ev.data.text())}catch{return}
      if(m.setupComplete!==undefined){ // 준비 완료 → 이때부터 소리를 보냄
        if(ws.up||s.pend!==ws)return;ws.up=true;
        if(s.turn&&s.ready&&s.ws&&s.ws.readyState===1){s.pend=null;s.held=ws}else swap(s,ws); // 말하는 도중이면 그 말이 끝난 뒤에 바꿈
        return}
      if(m.goAway&&s.ws===ws&&!ws.going){ws.going=true;connect(s)} // 서버가 곧 끊는다고 알림(연결은 10분쯤마다 끊김) → 새 연결을 미리 열어 끊김 없이 넘어감
      if(m.serverContent)onContent(s,m.serverContent);
    };
    ws.onerror=()=>{};
    ws.onclose=ev=>{
      if(!alive()||ws.retired)return;
      const why=String(ev&&ev.reason||'').slice(0,400)||(ev&&ev.code?'코드 '+ev.code:''),tail=(why?' · '+why:'')+' (키·크레딧·인터넷 확인)';
      if(s.held===ws){s.held=null;return}
      if(s.pend===ws)s.pend=null;
      if(keyTrouble(why))return stopInterp('AI 통역사 연결이 끊겼습니다'+tail);
      if(!ws.up){ // 준비되기 전에 닫힘
        if(s.ws&&s.ws!==ws&&s.ready)return; // 미리 열어 두려던 새 연결만 실패 → 쓰던 연결은 그대로
        if(ws.kind!==s.kind){connect(s);return}
        if(!s.everUp&&navigator.onLine){
          if(s.shape<2){s.shape++;connect(s);return} // 서버가 설정 형식을 받아 주지 않으면 다른 형식으로 다시 연결
          if(s.kind==='live'){ // Gemini 3.8 Live를 쓸 수 없으면 통역 전용 모델로 이어감
            if(!it.fellBack){it.fellBack=true;notify('Gemini 3.8 Live에 연결하지 못해 통역 전용 모델로 통역합니다.'+(why?' ('+why.slice(0,120)+')':''))}
            it.kind='tr';
            Object.values(it.sess).forEach(x=>{if(x.kind!=='live'||x.everUp)return;x.kind='tr';x.shape=Math.min(2,+load(interpShapeKey('tr'),'0')||0);
              const hadEnd=x.q.some(m=>m.includes('"activityEnd"'));x.q=x.q.filter(m=>!m.includes('"activityStart"')&&!m.includes('"activityEnd"'));if(hadEnd)x.q.push(JSON.stringify({realtimeInput:{audioStreamEnd:true}}))});
            connect(s);return}
          store(interpShapeKey(s.kind),'0');return stopInterp('AI 통역사 연결이 끊겼습니다'+tail)}
        if(++s.fails>3)return stopInterp('AI 통역사에 연결하지 못했습니다'+tail);
        setTimeout(()=>{if(alive()&&!s.ws&&!s.pend)connect(s)},1000);return}
      if(s.ws!==ws)return;
      // 쓰던 연결이 끊김 → 다시 연결
      s.ready=false;s.ws=null;
      const lived=Date.now()-ws.at,using=it.dir===s.target;
      if(lived>30000)s.fails=0;
      if(!using&&lived<=30000){if(alive()&&state.page==='main'&&!state.modal)render();return} // 쓰지 않는 연결이 금방 끊기면 그대로 두고, 다음에 버튼을 누를 때 다시 연결
      if(using&&++s.fails>3)return stopInterp('AI 통역사 연결이 자꾸 끊깁니다'+tail);
      if(!listen&&s.turn&&s.kind==='live'){s.turn=false;s.q=[];if(it.dir===s.target)it.dir=null;notify('연결이 바뀌어 방금 말이 끊겼습니다. 버튼을 누르고 다시 말해 주세요.');render()}
      connect(s);
    };
  };
  const send=(s,o)=>{
    const m=JSON.stringify(o);
    if(s.ready&&s.ws&&s.ws.readyState===1){try{s.ws.send(m)}catch{}return}
    s.q.push(m);if(s.q.length>900)s.q.splice(1,s.q.length-900); // 연결을 기다리는 동안은 모아 두었다가 준비되면 보냄
    if(!s.ws&&!s.pend)connect(s);
  };
  const startDir=target=>{
    const s=session(target);it.dir=target;touch();
    if(!listen){hush();Object.values(it.sess).forEach(x=>{x.outOn=false});s.turn=true;s.row=newRow();it.pending=false;clearTimeout(it.waitT);if(s.kind==='live')send(s,{realtimeInput:{activityStart:{}}})}
    if(!s.ws&&!s.pend)connect(s);
  };
  const endDir=()=>{
    const s=it.sess[it.dir];it.dir=null;if(!s)return;
    if(!listen&&s.kind==='live')send(s,{realtimeInput:{activityEnd:{}}}); // 말이 끝났다고 알림 → 통역 시작
    else send(s,{realtimeInput:{audioStreamEnd:true}});
    if(listen)return;
    s.turn=false;s.outOn=true;if(s.held){const w=s.held;s.held=null;swap(s,w)}
    it.pending=true;clearTimeout(it.waitT);
    it.waitT=setTimeout(()=>{if(!alive()||!it.pending)return;it.pending=false;notify('통역이 나오지 않았습니다. 버튼을 누르고 다시 한 번 말해 주세요.');render()},15000);
  };
  it.talk=k=>{ // 말하기 버튼 (한국어 · 외국어)
    if((state.mode==='listen')!==listen||active().code!==fg){ // 모드나 언어가 바뀌었으면 새로 연결
      stopInterp();if(state.mode==='listen')state.listenFrom=k==='ko'?'ko':'foreign';startInterp();if(interp&&!interp.listen)interp.talk(k);return}
    if(k!=='ko'&&k!=='foreign')return;
    const target=k==='ko'?fg:'ko';touch();
    if(it.dir===target){endDir();render();return} // 같은 버튼 → 듣기 모드: 멈춤 · 대화 모드: 통역
    if(it.dir){endDir();if(!listen){render();return}} // 대화 모드: 다른 언어 버튼을 누르면 지금 말을 통역만 함 (통역을 들은 뒤 그 버튼을 다시 눌러 말하기)
    if(listen){state.listenFrom=k;persist()}
    startDir(target);render();
  };
  NAT.pcm.onend=e=>{if(!alive())return;if(!e&&!it.pcmRetry){it.pcmRetry=1;setTimeout(()=>{if(alive())startPcm()},400);return} // 마이크 전달이 멈추면 한 번 다시 엶
    stopInterp(e?'AI 통역사: 마이크를 열 수 없습니다 ('+e+')':'AI 통역사: 마이크 전달이 멈췄습니다')};
  const startPcm=()=>NAT.pcm.start(b64=>{
    if(!alive()||!it.dir)return; // 고른 방향이 없으면 소리를 보내지 않음
    if(listen&&!ear&&it.next>0&&it.ctx.currentTime<it.next+0.3)return; // 듣기 모드·스피커: 통역 소리가 나는 동안은 보내지 않음 (메아리 방지)
    send(session(it.dir),{realtimeInput:{audio:{data:b64,mimeType:'audio/pcm;rate=16000'}}});it.inSec+=0.1;
  },!ear);
  startPcm();
  it.idle=setInterval(()=>{if(!alive())return;it.bill();if(Date.now()-it.lastAct>300000)stopInterp('5분 동안 말소리가 없어 AI 통역사를 껐습니다.')},15000);
  if(listen)startDir(state.listenFrom==='ko'?fg:'ko'); // 듣기 모드: 켜면 바로 통역 시작
  else{connect(session(fg));connect(session('ko'))} // 대화 모드: 두 방향을 미리 연결만 해 둠 (소리는 버튼을 누른 쪽에만 보냄)
  keepAwake();render();
}
""")
# 화면: AI 통역사가 켜져 있으면 말하기 버튼이 통역사를 움직임 · 자동 버튼과 묶음 시간은 숨김
rep("button('🎙 AI 통역사','ai-chip'+(interp?((interp.opened||0)>=2?' live':' wait'):''),startInterp,ar);",
    "button('🎙 AI 통역사','ai-chip'+(interp?(interpWait()?' wait':' live'):''),startInterp,ar);")
rep("  if(interp)return notify('AI 통역사가 켜져 있습니다. 끄려면 \"AI 통역사\"를 다시 누르세요.');\n", "  if(interp)return interp.talk(k); // AI 통역사가 켜져 있으면 말하기 버튼은 통역사에게\n")
rep("  const keys=listen?['ko','foreign']:['ko','foreign','auto'];", "  const keys=listen||interp?['ko','foreign']:['ko','foreign','auto']; // AI 통역사는 말할 언어를 직접 고름 (자동 없음)")
rep("  if(listen){const cb=button('','chunk-btn',nextListenChunk,tr2);", "  if(listen&&!interp){const cb=button('','chunk-btn',nextListenChunk,tr2);")
rep("    const on=state.mic&&b.dataset.k===cur;\n", "    const on=interp?interpKey()===b.dataset.k:state.mic&&b.dataset.k===cur;\n")
rep("sm.textContent=!on?(state.mode==='listen'?'눌러서 듣기':'눌러서 말하기'):", "sm.textContent=interp?(on?(state.mode==='listen'?'통역 중 · 누르면 멈춤':'말씀하세요 · 다시 누르면 통역'):state.mode==='listen'?'눌러서 듣기':'눌러서 말하기'):!on?(state.mode==='listen'?'눌러서 듣기':'눌러서 말하기'):")
rep("  if(m)m.textContent=!state.mic?'':", "  if(m)m.textContent=interp?(interpKey()?'AI 통역사 · '+(interpKey()==='ko'?'한국어':active().name)+' 듣는 중':interp.pending?'AI 통역사 · 통역하는 중…':'AI 통역사 켜짐'):!state.mic?'':")
rep("resetTranscripts(false);state.dim=false;recOpen=null;state.mode={conversation:'listen',listen:'record',record:'conversation'}[state.mode];", "stopInterp();resetTranscripts(false);state.dim=false;recOpen=null;state.mode={conversation:'listen',listen:'record',record:'conversation'}[state.mode];")
rep("  if(!state.items.length&&!state.interim)hint(parent,'아래 한국어·외국어 버튼을 누르고 말씀하세요.", "  if(interp&&!state.items.length)hint(parent,'🎙 AI 통역사가 켜져 있습니다.\\n말할 언어 버튼을 누르고 말한 뒤,\\n같은 버튼을 다시 누르면 통역이 나옵니다.');\n  else if(!state.items.length&&!state.interim)hint(parent,'아래 한국어·외국어 버튼을 누르고 말씀하세요.")
rep("  if(!state.listening.length&&!state.interim)hint(parent,'아래 언어 버튼을 누르면 계속 들으면서", "  if(interp&&!state.listening.length)hint(parent,'🎙 AI 통역사가 켜져 있습니다.\\n'+active().name+' 버튼: '+active().name+' → 한국어\\n한국어 버튼: 한국어 → '+active().name+'\\n끊김 없이 계속 통역하고,\\n같은 버튼을 다시 누르면 멈춥니다.');\n  else if(!state.listening.length&&!state.interim)hint(parent,'아래 언어 버튼을 누르면 계속 들으면서")
# 설정: 대화 모드에서 쓸 AI 통역사 모델 고르기
rep("\"AI 통역사\"를 켜면 Gemini가 실시간으로 듣고 바로 통역합니다(질문에 답하지 않고 통역만).", "\"AI 통역사\"를 켜면 듣기·통역·말하기를 모두 Gemini가 합니다(질문에 답하지 않고 통역만). 듣기 모드는 끊김 없이 계속 통역하고, 대화 모드는 말할 언어 버튼을 누르고 말한 뒤 같은 버튼을 다시 누르면 통역합니다.")
rep("    AI_VOICES.forEach(([v,t])=>{const o=node('option','',t,sel);o.value=v});sel.value=load(k,dv);sel.onchange=()=>store(k,sel.value);\n  });\n",
    "    AI_VOICES.forEach(([v,t])=>{const o=node('option','',t,sel);o.value=v});sel.value=load(k,dv);sel.onchange=()=>store(k,sel.value);\n  });\n"
    "  {node('label','field','AI 통역사 · 대화 모드에서 쓸 모델',sec);const sel=node('select','text-field','',sec);\n"
    "    [['live','Gemini 3.8 Live · 말을 마치고 버튼을 누르면 통역 (기본)'],['tr','통역 전용 모델 · 말하는 동안 바로 통역']].forEach(([v,t])=>{const o=node('option','',t,sel);o.value=v});\n"
    "    sel.value=interpConvKind();sel.onchange=()=>{store('interp_conv',sel.value);if(interp&&!interp.listen)stopInterp('AI 통역사를 껐습니다.')};\n"
    "    node('p','tiny','듣기 모드는 항상 통역 전용 모델을 씁니다. 대화 모드에서 통역 대신 대답을 하거나 말을 빼먹으면 \"통역 전용 모델\"로 바꿔 보세요.',sec)}\n")
# 균형(gemini-3.8-flash): 생각을 끌 수 없고 기본이 "중간"이라 느리고 비쌈 → 정확(argon)처럼 "낮음"으로 (공식 문서: low·medium·high만 지원)
rep("if(/argon/.test(m))c.thinkingConfig={thinkingLevel:'low'};return c}", "if(/argon|gemini-3\\.8-flash$/.test(m))c.thinkingConfig={thinkingLevel:'low'};return c}")

# ───── A10: 듣기 모드 1단계 — 들은 소리 저장(긴 무음만 빼고, 5일) · 묶음 1분 하나 · 지금 듣기 ↔ 나중에 듣기 · 멈춰도 끝까지 받아 적기 · 밀리면 빨리 읽기 · 원본 소리 듣기 ─────
# 폰 쪽(AudioStore·SttCore·LocalStt·Heavy): 받아 적기와 번역을 차례로, 밀린 소리는 버리지 않음, 문장마다 저장 자리(f·a·b)와 들린 시각(t0·t1)을 넘겨 줌
rep("const LISTEN_CHUNKS=[20,40,60,300,600];\nfunction listenChunk(){const v=+load('listen_chunk','60');return LISTEN_CHUNKS.includes(v)?v:60}",
    "const LISTEN_CHUNKS=[60]; // 앱: 묶음은 1분 하나 (짧은 말은 15초 조용하면 바로 번역)\nfunction listenChunk(){return 60}\nconst listenLater=()=>load('listen_when','now')==='later'; // 나중에 듣기: 듣는 동안은 읽지 않고 받아 적고 번역만 해 둠")
rep("function nextListenChunk(){const i=LISTEN_CHUNKS.indexOf(listenChunk());store('listen_chunk',String(LISTEN_CHUNKS[(i+1)%LISTEN_CHUNKS.length]));",
    "function nextListenChunk(){store('listen_when',listenLater()?'now':'later');notify(listenLater()?'📼 나중에 듣기 · 듣는 동안은 읽지 않고 받아 적고 번역만 해 둡니다. 끝난 뒤 위의 \"전체\"로 들으세요.':'⏱ 지금 듣기 · 1분쯤 모아 번역해서 바로 읽어 줍니다.');")
rep("cb.innerHTML=`<span>⏱ ${chunkLabel(listenChunk())}</span><small>묶음</small>`;cb.title='몇 초씩 모아 번역할지 (누를 때마다 바뀜)'}",
    "cb.innerHTML=listenLater()?'<span>📼 나중에</span><small>끝나고 듣기</small>':'<span>⏱ 1분</span><small>지금 듣기</small>';cb.title='지금 듣기(1분씩 모아 바로 읽기) ↔ 나중에 듣기(끝난 뒤 듣기)'}")
rep("'쯤 모이면 문장이 끝나는 곳에서 끊어\\n한 번에 번역해 읽어 줍니다.\\n같은 버튼을 다시 누르면 남은 말까지 번역하고 끝납니다.\\n⏱ 버튼으로 묶음 시간을 바꿀 수 있어요.'",
    "'쯤 모이면 문장이 끝나는 곳에서 끊어\\n한 번에 번역해 '+(listenLater()?'둡니다 (지금은 읽지 않음).\\n끝난 뒤 위의 \"전체\"를 누르면 차례로 읽어 줍니다.':'읽어 줍니다.')+'\\n같은 버튼을 다시 누르면 남은 말까지 번역하고 끝납니다.\\n옆 버튼으로 지금 듣기 ↔ 나중에 듣기를 바꿉니다.'")
rep("  const sec=(performance.now()-turn.firstAt)/1000;\n  if(quiet||sec>=listenChunkMax()",
    "  const sec=turn.au?(turn.au.t1-turn.au.t0)/1000:(performance.now()-turn.firstAt)/1000; // 폰 안 인식: 소리가 들린 시각으로 잼 (받아 적기가 밀려도 묶음 길이가 흔들리지 않게)\n  if(quiet||sec>=listenChunkMax()")
rep("""      if(last?.isFinal){
        if(t)commit(t);
        if(turn&&live&&t&&!turn.finished){ // 묶음을 끊을지 확인 (고른 시간·조용함)
          if(!turn.firstAt)turn.firstAt=performance.now();
          const tt=turn;clearTimeout(gapTimer);gapTimer=setTimeout(()=>{if(valid()&&state.recognizer===r)maybeCutListen(tt)},400);
          clearTimeout(listenQuietTimer);listenQuietTimer=setTimeout(()=>{if(valid())maybeCutListen(manualTurn,true)},listenQuiet());
        }
        return}""",
"""      if(last?.isFinal){
        const au=r._lastMeta||null; // 이 문장의 소리가 저장된 자리와 들린 시각
        if(t&&au&&turn&&live&&!turn.finished&&turn.au&&turn.parts.length&&au.t0-turn.au.t1>=listenQuiet()&&state.recognizer===r)r._cut(); // 앞 말과 15초 넘게 떨어져 들린 말 → 앞 묶음을 먼저 끊음
        if(t)commit(t,au);
        if(t&&au&&turn&&!turn.finished)turnAudio(turn,au);
        if(turn&&live&&t&&!turn.finished){ // 묶음을 끊을지 확인 (1분·조용함)
          if(!turn.firstAt)turn.firstAt=performance.now();
          const tt=turn;clearTimeout(gapTimer);gapTimer=setTimeout(()=>{if(valid()&&state.recognizer===r)maybeCutListen(tt)},400);
          clearTimeout(listenQuietTimer);listenQuietTimer=setTimeout(function quiet(){if(!valid())return;if(NAT.on&&NAT.stt.busy()){listenQuietTimer=setTimeout(quiet,2000);return}maybeCutListen(manualTurn,true)},listenQuiet()); // 받아 적을 소리가 남아 있으면 조용한 것이 아님
        }
        return}""")
rep("  function commit(direct){ // direct:", "  function commit(direct,au){ // direct:")
rep("    consume(text,source,{toListen:live,fromMic:true,micId,timing});", "    consume(text,source,{toListen:live,fromMic:true,micId,timing,au:fromLocal?au:null});")
rep("function finishManualTurn(turn){", """// 이 묶음의 소리가 저장된 자리(파일 f의 a~b)와 들린 시각(t0~t1)을 모음
function turnAudio(turn,au){
  if(!turn.au||turn.au.f!==au.f)turn.au={f:au.f,a:au.a,b:au.b,t0:au.t0,t1:au.t1};
  else{turn.au.a=Math.min(turn.au.a,au.a);turn.au.b=Math.max(turn.au.b,au.b);turn.au.t1=Math.max(turn.au.t1,au.t1)}
}
function finishManualTurn(turn){""")
rep("consume(text,turn.source,{toListen:turn.toListen,fromMic:true,noMerge:true,micId:turn.micId,timing});", "consume(text,turn.source,{toListen:turn.toListen,fromMic:true,noMerge:true,micId:turn.micId,timing,au:turn.au});")
rep("  entry.timing=opt.timing||latencyStart();latencyMark(entry.timing,'consume');\n  list.push(entry);",
    "  if(opt.au){entry.au=opt.au;entry.heardAt=opt.au.t1} // 저장된 원본 소리의 자리 · 들린 시각\n  if(toListen&&opt.fromMic&&listenLater())entry.later=true; // 나중에 듣기: 지금은 읽지 않음\n  entry.timing=opt.timing||latencyStart();latencyMark(entry.timing,'consume');\n  list.push(entry);")
rep("  slot.ready=false;slot.text=null;work.slot=slot;", "  slot.ready=false;slot.text=null;work.slot=slot;slot.silent=!!entry.later&&!options.retranslate;")
rep("while(outQ.length&&outQ[0].ready&&(!outQ[0].text||(state.speech===3&&!outQ[0].force))){", "while(outQ.length&&outQ[0].ready&&(!outQ[0].text||outQ[0].silent||(state.speech===3&&!outQ[0].force))){")
rep("r._draining=false;srAll.delete(r);finishManualTurn(turn);updateDrainStatus()},5000);", "r._draining=false;srAll.delete(r);finishManualTurn(turn);updateDrainStatus()},r._local?1800000:5000); // 폰 안 인식: 밀린 소리를 끝까지 받아 적을 때까지 기다림 (다 되면 폰이 알려 줌)")
rep("    if(r._draining){commit();r._draining=false;finishManualTurn(turn);updateDrainStatus();return}", "    if(r._draining){commit();r._draining=false;finishManualTurn(turn);updateDrainStatus();laterReady();return}")
rep("function stopMic(submitManual=false){", """function laterReady(){ // 나중에 듣기: 남은 번역까지 끝나면 알림
  if(!listenLater()||state.mode!=='listen')return;
  listenTextChain.then(()=>{if(state.mic||state.mode!=='listen')return;const n=state.listening.filter(x=>x.later&&x.translation&&!x.failed&&!x.correcting).length;if(n)notify('📼 통역 '+n+'개가 준비됐습니다. 위의 "전체"를 누르면 차례로 읽어 줍니다.')});
}
function stopMic(submitManual=false){""")
# 밀리면 빨리 읽기
rep("function pumpOut(){\n", """/* 듣기 모드: 통역이 실제 말보다 많이 늦어지면(밀림) 읽는 속도를 올려 따라잡음 */
let lagSec=0;
function lagRate(entry){
  lagSec=0;if(!entry||!entry.heardAt||!state.mic||state.mode!=='listen'||!state.listening.includes(entry))return 1;
  lagSec=Math.max(0,(Date.now()-entry.heardAt)/1000);
  return lagSec>240?1.5:lagSec>170?1.35:lagSec>110?1.2:1;
}
function pumpOut(){
""")
rep("  const q=outQ.shift(),gen=outGen,parts=splitSentences(q.text),", "  const q=outQ.shift(),gen=outGen,lagF=lagRate(q.entry),parts=splitSentences(q.text),")
rep("    if(tone&&toneOn()){u.rate=Math.min(2,u.rate*(tone.rf||1));u.volume=tone.vol||1}", "    if(tone&&toneOn()){u.rate=Math.min(2,u.rate*(tone.rf||1));u.volume=tone.vol||1}\n    if(lagF>1)u.rate=Math.min(2,u.rate*lagF); // 밀렸으면 빨리 읽음")
rep("a.playbackRate=Math.max(0.8,Math.min(1.6,state.rate/1.15));", "a.playbackRate=Math.max(0.8,Math.min(1.9,state.rate/1.15*lagF));")
rep("nameOf(state.listenLang)+' 듣는 중';", "nameOf(state.listenLang)+' 듣는 중'+(state.mode==='listen'&&state.speaking&&lagSec>110?' · '+Math.round(lagSec/60)+'분 밀림 · 빨리 읽는 중':'');")
# 저장된 원본 소리 듣기 (🎧)
rep("textActions(ot,()=>x.original,x.source);sayBtn(original,x,'original',14,'o-say');", "textActions(ot,()=>x.original,x.source);sayBtn(original,x,'original',14,'o-say');recBtn(original,x);")
rep("  if(original)sayBtn(b,item,'original',14,'o-say');", "  if(original){sayBtn(b,item,'original',14,'o-say');recBtn(b,item)}")
rep("function sayBtn(parent,item,field,size,cls){", """/* 저장된 원본 소리 듣기 (폰 안 인식으로 들은 말 · 긴 무음만 빼고 5일 보관) */
let recAudio=null,recAudioEntry=null;
function recBtn(parent,item){
  if(!NAT.on||!item.au||!item.au.f)return null;
  const on=recAudioEntry===item;
  return iconButton(on?'■':'🎧','o-say o-rec',on?'원본 소리 멈춤':'원본 소리 듣기',ev=>{ev.stopPropagation();playRec(item)},parent);
}
function playRec(item){
  const same=recAudioEntry===item;
  if(recAudio){try{recAudio.pause()}catch{}recAudio=null;recAudioEntry=null}
  if(same){render();return}
  stopSpeech();
  const a=new Audio('/rec/'+encodeURIComponent(item.au.f)+'?a='+Math.max(0,item.au.a-4800)+'&b='+(item.au.b+4800)); // 앞뒤 0.3초 여유
  recAudio=a;recAudioEntry=item;
  const end=()=>{if(recAudio===a){recAudio=null;recAudioEntry=null;if(state.page==='main'&&!state.modal)render()}};
  a.onended=end;a.onerror=()=>{end();notify('저장된 소리를 찾을 수 없습니다. (소리는 5일 뒤 지워집니다)')};
  try{const p=a.play();if(p&&p.catch)p.catch(()=>{})}catch{}
  render();
}
function sayBtn(parent,item,field,size,cls){""")

# ───── A11: 내 폰 전용 정리 + Gemini가 저장된 소리를 직접 듣기 + 나중에 듣기 완성·저장 + 마이크 고르기 ─────
# 뺀 것(사용자 결정): 무료 번역기 · 여행 문구 기능 · 대화 모드 자동 버튼 · 화면 어둡게 · 구글 음성 인식 선택 · 다른 모델 직접 넣기 · 기본 번역기 칸 · 앱 주소 보내기 · 받아쓰기 정리 기록
# 번역기: 폰 AI = Whisper가 받아 적고 Gemma가 정리+번역 / Gemini(빠름·균형·정확) = 저장된 소리를 Gemini가 직접 듣고 받아 적기+번역. 방식을 바꿀 때도 소리부터 다시

# (1) 무료 번역기 빼기
rep("  if(e==='free')return 'free';\n  if(e==='gemini'&&geminiKey())return 'gemini';\n  if(localReady())return 'local';\n  return geminiKey()?'gemini':'free'} // 폰 AI도 키도 없으면 무료 번역기(인터넷)",
    "  if(e==='gemini'&&geminiKey())return 'gemini';\n  if(localReady())return 'local';\n  return geminiKey()?'gemini':'none'} // 폰 AI도 키도 없으면 번역기 없음")
rep("local:'폰 AI 번역',free:'무료 번역기'})[engine()];", "local:'폰 AI 번역',none:'번역기 없음'})[engine()];")
rep("if(geminiKey())m.push('fast','balanced','accurate');m.push('free');return m}", "if(geminiKey())m.push('fast','balanced','accurate');return m}")
rep("if(e==='free')return '무료 번역기';return 'Gemini '", "if(e==='none')return '번역기 없음';return 'Gemini '")
rep("['accurate','정확'],['free','무료']];", "['accurate','정확']];")
rep("warn('폰 AI 번역 실패 → '+(geminiKey()?'Gemini':'무료 번역기')+'로 대신 번역합니다 ('+err.message+')')", "if(!geminiKey())throw Error('폰 AI 번역 실패 · '+err.message);warn('폰 AI 번역 실패 → Gemini로 대신 번역합니다 ('+err.message+')')")
rep("    catch(err){warn('Gemini 번역 실패 → 무료 번역기로 대신 번역합니다 ('+err.message+')')}", "    catch(err){throw Error('Gemini 번역 실패 · '+err.message)}")
rep("""  if(res==null){ // 무료 번역기 (380자씩)
    const chunks=splitText(text,380),out=[];
    for(let i=0;i<chunks.length;i++){out.push(await freeOne(chunks[i],src,target));if(chunks.length>1)onProgress?.(out.join(' '),i+1,chunks.length)}
    res=out.join(' ');
  }
""", "  if(res==null)throw Error(NO_ENGINE);\n")
rep("  if(navigator.onLine)return freeOne(text,src,target); // 여행 문구 받기 등: 인터넷이 되면 무료 번역기 (빠름)\n  if(localReady())return localTranslate(text,src,target);\n  throw Error(NO_ENGINE);",
    "  if(localReady())return localTranslate(text,src,target);\n  if(geminiKey()&&navigator.onLine)return geminiTranslate(text,src,target,'');\n  throw Error(NO_ENGINE);")
cut("  let sec=node('div','sec','',body);node('h4','','기본 번역기',sec);", "    if(!ok)b.style.opacity=.5;\n  });\n", "  let sec; // (기본 번역기 고르기는 번역 화면 아래 버튼으로)\n")

# (2) 한 줄 통역: 폰 AI는 받아 적은 글로, Gemini는 저장된 소리로
cut("async function translateEntryText(entry,mode,timing,signal,options){", "  notify(entryModeName(mode)+' 응답 실패 · 무료 번역기로 이어서 번역합니다.');return viaFree();\n}", r"""/* 한 줄 통역. 고른 번역기에 따라
   · 폰 AI: 폰이 받아 적은 글(Whisper) → Gemma가 정리+번역
   · Gemini(빠름·균형·정확): 저장된 원본 소리를 Gemini가 직접 듣고 → 받아 적은 글 + 번역 (소리가 없는 줄은 글로)
   방식을 바꿔 다시 할 때도 소리가 있으면 소리부터 다시 듣는다. 실패하면 다른 쪽으로 넘어간다 (Gemini ↔ 폰 AI) */
async function translateEntryText(entry,mode,timing,signal,options){
  if(!options.retranslate&&entry.original){const saved=cached(entry.original,entry.source,entry.target);if(saved)return {s:entry.original,t:saved,mode:'saved'}}
  if(!['local','fast','balanced','accurate'].includes(mode))mode=currentEntryMode();
  const reuse=!options.retranslate,au=NAT.on&&entry.au&&entry.au.f?entry.au:null; // au = 저장된 원본 소리의 자리
  // 폰 AI가 번역할 글. 폰이 받아 적은 글이 없으면(소리만 있는 줄 · Gemini가 만든 줄을 폰 AI로 다시 할 때) 저장된 소리를 Whisper로 받아 적음
  const heardText=async()=>{
    if(!au||(entry.original&&(entry.sttBy==='phone'||!options.retranslate)))return entry.original;
    let t='';try{t=await NAT.stt.transcribe(au,localeOf(entry.source))}catch(e){if(entry.original)return entry.original;throw e}
    if(signal.aborted)return null;
    if(isEmptyText(t)){if(entry.original)return entry.original;throw Error('말소리를 알아듣지 못했습니다')}
    entry.sttBy='phone';return entry.source==='ko'?fixHeard(t):t;
  };
  const viaLocal=async()=>{
    const base=await heardText();if(base==null||signal.aborted)return null;
    if(isEmptyText(base))throw Error('받아 적은 글이 없습니다');
    const lk='local:'+(NAT.llm.state.model||''),fromSound=base!==entry.original; // 모델마다 따로 기억
    const hit=reuse&&trGet('e',base,entry.source,entry.target,lk);if(hit)return {...hit,mode:'local',fromSound};
    latencyMark(timing,'request');const ss=[],ts=[];
    try{
      if(localChatOn()){ // 범용 모델(Gemma): 받아쓴 글 정리 + 번역을 한 번에. 긴 묶음은 400자씩 나눠 차례로
        const ps=splitText(base,400);
        for(let i=0;i<ps.length;i++){if(signal.aborted)return null;const r=await localCleanTranslate(ps[i],entry.source,entry.target,i?ss[i-1]:entryContext(entry),timing);ss.push(r.s);ts.push(r.t)}
      }else{ // 번역 전용 모델: 규칙으로만 정리한 뒤 번역
        const clean=ruleClean(base)||base;ss.push(clean);
        compareMark(timing,'',localPrompt(clean,entry.source,entry.target));
        for(const part of splitText(clean,500)){if(signal.aborted)return null;ts.push(await localTranslate(part,entry.source,entry.target))}
      }
    }finally{compareFinish(timing)}
    latencyMark(timing,'response');if(signal.aborted)return null;
    const res={s:ss.join(' '),t:ts.join(' ')};trPut('e',base,entry.source,entry.target,lk,res);return {...res,mode:'local',fromSound};
  };
  const viaGeminiText=async tier=>{ // 소리가 없는 줄(글로 넣은 말 등). undefined = 응답 실패
    if(isEmptyText(entry.original))return undefined;
    const hit=reuse&&trGet('e',entry.original,entry.source,entry.target,tier);if(hit)return {...hit,mode:tier};
    let r;try{r=await geminiCleanTranslate(entry.original,entry.source,entry.target,entryContext(entry),timing,{tier,signal,merged:!!options.merged})}catch(e){if(signal.aborted)return null;r=null}
    if(signal.aborted)return null;
    if(r){trPut('e',entry.original,entry.source,entry.target,tier,{s:r.s,t:r.t});return {...r,mode:tier}}
  };
  const viaGeminiSound=async tier=>{ // 저장된 소리를 Gemini가 직접 들음. undefined = 응답 실패
    const key=au.f+':'+au.a+':'+au.b,hit=reuse&&trGet('h',key,entry.source,entry.target,tier);if(hit){entry.sttBy='gemini';return {...hit,mode:tier,fromSound:true}}
    let r;try{r=await gemHearTranslate(au,entry.source,entry.target,'',timing,{tier,signal,prevLen:options.retranslate?String(entry.original||'').replace(/\s/g,'').length:0})}catch(e){if(signal.aborted)return null;if(e.gone&&entry.original)return viaGeminiText(tier);r=null} // 소리가 이미 지워졌으면(5일) 남아 있는 글로
    if(signal.aborted)return null;
    if(r){trPut('h',key,entry.source,entry.target,tier,{s:r.s,t:r.t});entry.sttBy='gemini';return {...r,mode:tier,fromSound:true}}
  };
  const viaGemini=tier=>au?viaGeminiSound(tier):viaGeminiText(tier),canGem=()=>geminiKey()&&navigator.onLine;
  if(mode==='local'){
    if(localReady()){
      try{return await viaLocal()}
      catch(err){if(signal.aborted)return null;latencyMark(timing,'fallback');
        if(!canGem())throw Error('폰 AI 번역 실패 · '+err.message);
        notify('폰 AI 번역 실패 · Gemini 빠름으로 이어서 번역합니다. ('+err.message+')')}
    }else if(!canGem())throw Error(NO_ENGINE);
    const r=await viaGemini('fast');if(r!==undefined)return r;
    throw Error('번역하지 못했습니다 (폰 AI · Gemini 모두 실패)');
  }
  gemErr='';
  if(canGem()){const r=await viaGemini(mode);if(r!==undefined)return r}
  latencyMark(timing,'fallback');
  if(options.retranslate)throw Error(navigator.onLine?(gemErr||entryModeName(mode)+' 응답 실패'):'인터넷 없음'); // 다시 할 때 실패하면 폰 AI로 바꾸지 않고 지금 것을 그대로 둠
  if(localReady()){notify(entryModeName(mode)+(navigator.onLine?' 응답 실패'+(gemErr?' ('+gemErr+')':''):' · 인터넷 없음')+' · 폰 AI로 이어서 번역합니다.');return viaLocal()} // 소리만 있는 줄이면 저장된 소리를 Whisper로 받아 적어 번역
  throw Error(navigator.onLine?(geminiKey()?entryModeName(mode)+' 응답 실패':NO_ENGINE):'인터넷 연결을 확인해 주세요');
}
/* 소리를 Gemini가 직접 듣고 받아 적은 글(s)과 번역(t)을 한 번에 만듦. 실패하면 예외.
   snd = 저장된 소리의 자리 {f,a,b} 또는 녹음 조각 {blob,mime,sec}. src가 'auto'이면 한국어인지 외국어인지 Gemini가 판단(lang).
   소리만 보냄 — 앞 문장 글은 같이 보내지 않음 (균형·정확 모델이 그 글을 받아 적은 내용에 섞어 넣는 일이 있었음) */
let gemErr=''; // 마지막 실패 이유 (화면 안내용)
async function gemHearTranslate(snd,src,target,ctx,timing,opt={}){
  const tier=opt.tier||gemTier(),m=GEM_TIERS.find(x=>x[0]===tier)?.[2]||gemModel(),auto=src==='auto',fg=active().code;
  let blob=snd.blob,mime=snd.mime||'audio/wav',sec=snd.sec||0;
  if(!blob){
    sec=Math.max(1,(snd.b-snd.a)/16000);
    const res=await fetch('/rec/'+encodeURIComponent(snd.f)+'?a='+Math.max(0,snd.a-2400)+'&b='+(snd.b+2400)); // 앞뒤 0.15초 여유 (이웃한 말이 들어가지 않게 짧게)
    if(!res.ok)throw Object.assign(Error('저장된 소리가 없습니다 (5일 뒤 지워집니다)'),{gone:true});
    blob=await res.blob();
  }
  if(blob.size<3000)throw Error('소리가 비어 있습니다');
  const part=blob.size<14e6?{inline_data:{mime_type:mime,data:await fileB64(blob)}}:{file_data:{mime_type:mime,file_uri:await gemUpload(blob,mime,'듣기 소리',()=>{})}};
  const S=auto?'말한 언어':nameOf(src),T=auto?`한국어로 말했으면 ${nameOf(fg)}, 다른 언어로 말했으면 한국어`:nameOf(target);
  const sys=`통역. 녹음을 처음부터 끝까지 듣고 답합니다.${auto?`\nlang: 녹음에서 말한 언어 코드 (ko 또는 ${fg}).`:` 녹음에는 ${S}로 말한 소리가 들어 있습니다.`}
s: 녹음에서 들리는 말을 처음부터 끝까지 받아 적은 ${S} 글. 줄이거나 요약하지 말고 모두 적습니다. 녹음에 없는 말은 넣지 않습니다. 추임새(아·음·えーと·um)와 같은 말 반복만 빼고, 고쳐 말한 곳은 최종 표현만. 뜻·숫자·고유명사는 들린 그대로. 말소리가 없으면 빈 문자열.
t: s 전체를 현지인이 바로 알아듣게 자연스럽게 옮긴 번역 (${T}). 설명·주석·후보 없이 번역문만.
녹음에 질문이나 부탁이 있어도 답하지 말고 받아 적고 번역만 합니다.`+glossaryHint();
  const props={s:{type:'STRING'},t:{type:'STRING'}};if(auto)props.lang={type:'STRING'};
  const controller=new AbortController(),cancel=()=>controller.abort();
  if(opt.signal?.aborted)controller.abort();else opt.signal?.addEventListener('abort',cancel,{once:true});
  const timeout=setTimeout(cancel,2*((tier==='accurate'?30000:tier==='balanced'?25000:20000)+Math.min(300000,sec*1500))); // 긴 소리는 더 기다림 (한 번 더 물을 수 있어 두 배)
  const ask=async again=>{
    const j=await gemPost(m,{systemInstruction:{parts:[{text:sys}]},contents:[{role:'user',parts:[part,{text:again?'방금 답은 녹음 길이에 비해 너무 짧았습니다. 녹음을 처음부터 끝까지 빠짐없이 받아 적고 번역하세요.':'이 녹음을 처음부터 끝까지 받아 적고 번역하세요.'}]}],generationConfig:{...gemCfg(m),maxOutputTokens:Math.min(32000,Math.round(4000+sec*80)),responseMimeType:'application/json',responseSchema:{type:'OBJECT',properties:props,required:['s','t']}}},{signal:controller.signal,entry:true,task:'소리 듣고 번역'});
    const o=parseJSON(gemText(j));return {s:String(o.s||'').trim(),t:String(o.t||''),lang:String(o.lang||'')};
  };
  try{
    compareMark(timing,sys,'(소리 '+Math.round(sec)+'초)');latencyMark(timing,'request');
    let o=await ask(false);
    // 받아 적은 글이 소리 길이나 예전 글에 비해 너무 짧으면(앞부분만 적은 것) 한 번 더 시킴
    const short=x=>{const n=x.s.replace(/\s/g,'').length;return (sec>=20&&n<sec*0.8)||(opt.prevLen>=40&&n<opt.prevLen*0.4)};
    if(o.s&&short(o)){const o2=await ask(true);if(o2.s.length>o.s.length)o=o2;if(opt.prevLen>=40&&short(o))throw Error('받아 적은 글이 소리에 비해 너무 짧게 나왔습니다 ('+o.s.length+'자)')}
    compareFinish(timing);latencyMark(timing,'response');
    if(!o.s)throw Error('말소리를 알아듣지 못했습니다');
    const s2=o.s,from=auto?(/^ko/i.test(o.lang)||(!o.lang&&hangulRatio(s2)>0.3)?'ko':fg):src,to=auto?(from==='ko'?fg:'ko'):target;
    const {out,noisy}=gemClean(JSON.stringify({t:o.t}),to);
    if(!out||noisy||(to!=='ko'&&hangulRatio(out)>0.3))throw Error('번역이 올바르지 않게 나왔습니다');
    return {s:from==='ko'?fixHeard(s2):s2,t:out,mode:tier,source:from,target:to};
  }catch(e){if(timing&&timing.compareStarted!=null&&!timing.compareComplete)compareFinish(timing);latencyMark(timing,'response');if(timing)timing.marks.requestFailed=1;
    gemErr=controller.signal.aborted&&!opt.signal?.aborted?'응답이 너무 늦습니다':String(e&&e.message||e);throw e}
  finally{clearTimeout(timeout);opt.signal?.removeEventListener('abort',cancel)}
}""")
rep("      if(!options.retranslate)entry.original=result.s;", "      if(!options.retranslate||result.fromSound)entry.original=result.s; // 소리부터 다시 들었으면 받아 적은 글도 새로")

# (3) Gemini 번역기일 때는 폰이 받아 적지 않고 소리 자리만 알려 줌 → 묶음·줄을 소리로만 만듦
rep("  const r=new SR();r._epoch=epoch;state.recognizer=r;srAll.add(r);", "  const r=new SR();r._epoch=epoch;state.recognizer=r;srAll.add(r);\n  r.noDecode=hearByGemini(); // Gemini 번역기: 폰은 받아 적지 않고 말소리 구간만 찾음 (Gemini가 저장된 소리를 직접 들음)")
rep("function startRecognition(){", "const hearByGemini=()=>NAT.on&&engine()==='gemini'&&navigator.onLine;\nfunction startRecognition(){")
rep("""        const au=r._lastMeta||null; // 이 문장의 소리가 저장된 자리와 들린 시각
""", """        const au=r._lastMeta||null; // 이 문장의 소리가 저장된 자리와 들린 시각
        if(!t&&au){ // 소리만 옴 (받아 적지 않는 방식): 이 묶음의 소리 자리만 모아 둠
          if(!turn||turn.finished)return;
          if(live&&turn.au&&au.t0-turn.au.t1>=listenQuiet()&&state.recognizer===r)r._cut();
          turnAudio(turn,au);turn.heard=true;if(!turn.firstAt)turn.firstAt=performance.now();
          if(owns&&manualTurn===turn){state.interim='🎧 '+Math.max(1,Math.round((turn.au.t1-turn.au.t0)/1000))+'초 들음';updateLive()}
          if(live){const tt=turn;clearTimeout(gapTimer);gapTimer=setTimeout(()=>{if(valid()&&state.recognizer===r)maybeCutListen(tt)},400);
            clearTimeout(listenQuietTimer);listenQuietTimer=setTimeout(function quiet(){if(!valid())return;if(NAT.on&&NAT.stt.busy()){listenQuietTimer=setTimeout(quiet,2000);return}maybeCutListen(manualTurn,true)},listenQuiet())}
          return}
""")
rep("  const text=turn.parts.join(' ').trim();if(isEmptyText(text))return;\n  const timing=latencyStart(turn.started);latencyMark(timing,'commit');",
    "  const text=turn.parts.join(' ').trim(),hear=isEmptyText(text)&&!!(turn.heard&&turn.au);if(isEmptyText(text)&&!hear)return; // hear = 글 없이 소리만 있는 묶음 (Gemini가 들음)\n  const timing=latencyStart(turn.started);latencyMark(timing,'commit');")
rep("timing,au:turn.au});", "timing,au:turn.au,hear});")
rep("  const text=turnText(turn);if(isEmptyText(text))return;\n  const sec=turn.au?", "  const text=turnText(turn);if(isEmptyText(text)&&!turn.heard)return;\n  const sec=turn.au?")
rep("(sec>=listenChunk()&&SENT_END.test(text.replace(/[\\s\"'”’」』)）]+$/,''))))cutListenTurn();", "(sec>=listenChunk()&&(turn.heard||SENT_END.test(text.replace(/[\\s\"'”’」』)）]+$/,'')))))cutListenTurn();")
rep("  text=String(text||'').trim();if(isEmptyText(text))return;\n  if(source==='ko')text=fixHeard(text);", "  text=String(text||'').trim();if(isEmptyText(text)&&!opt.hear)return;\n  if(opt.hear)text='';else if(source==='ko')text=fixHeard(text);")
rep("  if(opt.au){entry.au=opt.au;entry.heardAt=opt.au.t1} // 저장된 원본 소리의 자리 · 들린 시각", "  if(opt.au){entry.au=opt.au;entry.heardAt=opt.au.t1;if(text)entry.sttBy='phone'} // 저장된 원본 소리의 자리 · 들린 시각 · 누가 받아 적었는지")
# 나중에 듣기 + Gemini: 5분쯤씩 묶어 한 번에 듣게 함 (문맥이 길수록 정확). 그 밖에는 1분
rep("function listenChunk(){return 60}", "function listenChunk(){return listenLater()&&hearByGemini()?300:60}")
# 화면이 꺼지는 등으로 중간에 끊길 때 소리만 있는 묶음도 번역
rep("    if(!isEmptyText(left))consume(left,t.source,{toListen:true,fromMic:true,noMerge:true})}", "    if(!isEmptyText(left)||(t&&t.heard&&t.au))consume(left,t.source,{toListen:true,fromMic:true,noMerge:true,au:t.au,hear:isEmptyText(left)})}")

# (4) 여행 문구 기능 빼기
rep("['basic','기본'],...(NAT.on?[['ai','번역 AI']]:[]),['phrases','여행 문구'],['adv','고급']].forEach(", "['basic','기본'],...(NAT.on?[['ai','번역 AI']]:[]),['adv','고급']].forEach(")
rep("  if(state.setTab==='words'||state.setTab==='groups')state.setTab='basic';", "  if(['words','groups','phrases'].includes(state.setTab))state.setTab='basic';")
n=len(s); s=re.sub(r"\n  const p=button\('📚 여행 문구','drawer-item strong',\(\)=>openPhrases\(\),d\);[^\n]*\n", "\n", s); assert len(s)<n
rep("throw new Error('인터넷이 없습니다. 📚 여행 문구나 받아 둔 자주 쓰는 문장을 써 주세요');", "throw new Error('인터넷이 없습니다. 폰 AI를 받아 두면 인터넷 없이도 번역합니다.');")

# (5) 대화 모드 자동 버튼 빼기 · AI 통역사/AI 음성 버튼을 말하기 버튼 옆으로 · 화면 어둡게 빼기
rep("const recogModes=['ko','foreign','auto'];", "const recogModes=['ko','foreign']; // 앱: 자동 없음 (말할 언어를 직접 고름)")
cut("  if(NAT.on){ // AI 통역사 · AI 음성 (Gemini 키가 있을 때 쓸 수 있음)", "    button('🔊 AI 음성','ai-chip'+(load('ai_voice_on')==='1'?' on':''),toggleAiVoice,ar);\n  }\n",
    "  if(NAT.on&&interpNote){const ar=node('div','ai-row','',s);node('small','ai-note',interpNote,ar).onclick=()=>askConfirm(interpNote,'복사',()=>{try{navigator.clipboard.writeText(interpNote);notify('복사했습니다.')}catch{}})} // AI 통역사가 꺼진 이유 (누르면 전체 보기·복사)\n")
rep("  const keys=listen||interp?['ko','foreign']:['ko','foreign','auto']; // AI 통역사는 말할 언어를 직접 고름 (자동 없음)", "  if(state.recog==='auto')state.recog='ko';\n  const keys=['ko','foreign'];")
rep("  // V2: 듣기 모드 묶음 시간 — 누를 때마다 20초 → 40초 → 1분 → 5분 → 10분\n", """  if(NAT.on){ // AI 통역사 · AI 음성: 말하기 버튼 옆에 두 줄로
    const ac=node('div','ai-col','',tr2);
    button('🎙 AI 통역사','ai-chip'+(interp?(interpWait()?' wait':' live'):''),startInterp,ac);
    button('🔊 AI 음성','ai-chip'+(load('ai_voice_on')==='1'?' on':''),toggleAiVoice,ac);
  }
""")
rep(".ai-note{flex:1;min-width:0;", ".ai-col{display:flex;flex-direction:column;gap:4px;justify-content:center;flex:0 0 auto}\n.ai-col .ai-chip{min-width:88px;padding:6px 8px;font-size:12px;border-radius:12px}\n.ai-note{flex:1;min-width:0;")
rep("if(!state.items.length&&!state.interim)hint(parent,'아래 한국어·외국어 버튼을 누르고 말씀하세요.\\n말하는 동안 글자가 여기에 보이고,\\n같은 언어 버튼을 다시 누르면 전체 내용을 번역합니다.\\n자동 버튼은 기존처럼 계속 통역합니다.\\n\\n오른쪽 ◀ 탭에 자주 쓰는 문장이 있습니다.');",
    "if(!state.items.length&&!state.interim)hint(parent,'아래 한국어·외국어 버튼을 누르고 말씀하세요.\\n같은 언어 버튼을 다시 누르면 통역합니다.\\n\\n오른쪽 ◀ 탭에 자주 쓰는 문장이 있습니다.');")
n=len(s); s=re.sub(r"\n  if\(listen&&!state\.dim\)\{const mb=button\('🌙','moon-btn',[^\n]*\n", "\n", s); assert len(s)<n
rep("    if(state.mode==='listen'){\n      if(!state.dim)setDim(true);\n", "    if(state.mode==='listen'){\n")

# (6) 설정에서 뺀 것: 앱 주소 보내기 · 받아쓰기 정리 기록 · 다른 모델 직접 넣기 · 구글 음성 인식 → 마이크 고르기
rep("  button('🔗 앱 주소 복사·보내기','action primary',()=>shareAppLink(),fbtns);\n", "")
cut("    // V3: 받아쓰기 정리 기록 (문제 찾기용)\n", "    button('지우기','action',()=>{recogLog.length=0;store('recog_log','[]');render()},lb);\n", "")
cut("  sec=node('div','sec','',body);node('h4','','다른 모델 직접 넣기',sec);", "},sec).style.marginTop='8px';\n", "")
cut("  sec=node('div','sec','',body);node('h4','','음성 인식 (마이크)',sec);", "  if(!NAT.info.sttOffline)ob.style.opacity=.5;\n", """  sec=node('div','sec','',body);node('h4','','음성 인식 · 마이크',sec);
  node('p','tiny','폰 안 AI(Whisper)가 마이크를 끄지 않고 계속 듣고, 들은 소리는 긴 무음만 빼고 5일 동안 보관합니다. 번역기가 폰 AI이면 Whisper가 받아 적고, Gemini(빠름·균형·정확)이면 저장된 소리를 Gemini가 직접 듣습니다.',sec);
  node('label','field','마이크',sec);
  {const mr=node('div','chips','',sec),cur=load('mic_src','auto');
    [['auto','자동'],['phone','📱 폰 마이크'],['ear','🎧 이어폰 마이크']].forEach(([k,t])=>button(t,'chip'+(cur===k?' on':''),()=>{if(state.mic)stopMic();if(interp)stopInterp();store('mic_src',k);NAT.stt.setMic(k);render()},mr));
    node('p','tiny','폰 마이크: 이어폰을 껴도 폰으로 듣습니다 (폰을 TV·말하는 사람 가까이 두고 이어폰으로 들을 때). 이어폰 마이크: 폰이 가방 안에 있을 때. 이어폰 마이크는 내 목소리에 맞춰져 있어 멀리 있는 사람의 말은 작게 들릴 수 있고, 블루투스 이어폰은 통화 음질로 바뀝니다.',sec)}
""")
rep("\nrender();\nif(NAT.on){setTimeout(offerLocalAI,900);", "\nif(NAT.on){if(load('stt_engine')!=='local')store('stt_engine','local');NAT.stt.setMic(load('mic_src','auto'))} // 앱: 음성 인식은 폰 안 AI만 · 고른 마이크 적용\nrender();\nif(NAT.on){setTimeout(offerLocalAI,900);")

# (7) 듣기 모드: 저장 (녹음 모드 목록으로 — 소리·받아 적은 글·번역을 함께, 5일이 지나도 남음)
rep("  if(!rec)iconButton(ICON.share(21),'icon-btn','전체 보내기',shareAll,tr);", "  if(listen&&NAT.on&&state.listening.length&&!state.mic){const sv=button('','home-btn',saveListen,tl);sv.innerHTML='<span>💾 저장</span>';sv.title='지금 듣기 기록을 녹음 모드 목록에 저장 (소리와 글 · 5일이 지나도 남음)'}\n  if(!rec)iconButton(ICON.share(21),'icon-btn','전체 보내기',shareAll,tr);")
rep("async function recStart(){\n", r"""/* 듣기 기록 저장: 동그라미로 고른 줄(없으면 전체)의 원본 소리·받아 적은 글·번역을 녹음 모드 목록에 넣음.
   소리는 줄마다 저장된 구간을 차례로 이어 붙인 WAV (머리글 조각 + 소리 조각들). 녹음 모드에서 다시 듣기·요약·내보내기를 그대로 쓸 수 있음 */
let savingListen=false;
async function saveListen(){
  if(savingListen)return;
  const ok=x=>x.translation&&!x.failed&&!x.correcting&&!/번역 중/.test(x.translation),picked=state.listening.filter(x=>x.sel&&ok(x)),rows=picked.length?picked:state.listening.filter(ok);
  if(!rows.length)return notify('저장할 통역이 없습니다.');
  savingListen=true;notify('💾 저장하는 중…');
  try{
    const sound=rows.filter(x=>x.au&&x.au.f&&x.au.b>x.au.a),total=sound.reduce((n,x)=>n+(x.au.b-x.au.a),0);
    const meta={id:'rec-'+Date.now().toString(36),at:rows[0].heardAt||rows[0].createdAt||Date.now(),dur:total/16000,size:total?44+total*2:0,mime:'audio/wav',status:'done',fromListen:true,
      transcript:rows.map(x=>x.original).filter(Boolean).join('\n'),lang:rows[0].source,translation:rows.map(x=>x.translation).join('\n'),trLang:rows[0].target};
    if(total){
      const h=new DataView(new ArrayBuffer(44)),w=(o,t)=>{for(let i=0;i<t.length;i++)h.setUint8(o+i,t.charCodeAt(i))};
      w(0,'RIFF');h.setUint32(4,36+total*2,true);w(8,'WAVEfmt ');h.setUint32(16,16,true);h.setUint16(20,1,true);h.setUint16(22,1,true);h.setUint32(24,16000,true);h.setUint32(28,32000,true);h.setUint16(32,2,true);h.setUint16(34,16,true);w(36,'data');h.setUint32(40,total*2,true);
      await recAddChunk(meta.id,new Blob([h.buffer]));
      for(const x of sound)for(let p=x.au.a;p<x.au.b;p+=4800000){ // 5분씩 가져와 바로 저장 (메모리를 아낌)
        const res=await fetch('/rec/'+encodeURIComponent(x.au.f)+'?raw=1&a='+p+'&b='+Math.min(x.au.b,p+4800000));
        if(!res.ok)throw Error('저장된 소리를 찾을 수 없습니다 (5일이 지나 지워졌을 수 있습니다)');
        await recAddChunk(meta.id,await res.blob());
      }
    }
    await recPut(meta);recList.unshift(meta);navigator.storage?.persist?.().catch(()=>{});
    notify('💾 저장했습니다 · '+rows.length+'줄'+(total?' · 소리 '+fmtDur(total/16000):' (소리 없음)')+' · 녹음 모드 목록에서 볼 수 있습니다.');
  }catch(e){notify('저장하지 못했습니다 · '+(e&&e.message||e))}
  finally{savingListen=false;if(state.page==='main'&&!state.modal)render()}
}
async function recStart(){
""")

rep("외국어 표기는 번역할 때 그대로 씁니다 (무료 번역기도 적용).", "외국어 표기는 번역할 때 그대로 씁니다.")
rep("(무료 번역기·Gemini는 쓸 수 있습니다)", "(Gemini는 쓸 수 있습니다)")

rep("그동안은 마이크를 다시 누르면 무료 받아쓰기·무료 번역으로 이어서 쓸 수 있어요.", "그동안은 번역기를 폰 AI로 바꾸면 이어서 쓸 수 있어요.")

# ───── A12: AI 사용량 기록에 추정 금액(원) — 작업별·합계, 가격이 오르는 날짜 반영 ─────
# 가격은 공식 가격표(ai.google.dev/gemini-api/docs/pricing, 2026-11-15 확인). 실제 청구액과 다를 수 있는 추정값
rep("""function usageAdd(task,res){
  res.json().then(j=>{const u=j.usageMetadata;if(!u)return;const r=aiUsage.t[task||'기타']||(aiUsage.t[task||'기타']={n:0,i:0,o:0});
    r.n++;r.i+=u.promptTokenCount||0;r.o+=(u.candidatesTokenCount||0)+(u.thoughtsTokenCount||0);
    clearTimeout(usageTimer);usageTimer=setTimeout(()=>store('ai_usage',JSON.stringify(aiUsage)),1500)}).catch(()=>{});
}""", r"""/* AI 요금 추정. 100만 토큰당 달러 [입력, 출력]. 오르는 날짜: 정확(argon) 2026-12-01 · 균형(3.8 flash)과 AI 음성 2027-01-01 */
function gemPrice(model,at=Date.now()){
  const dec=at>=new Date(2026,11,1).getTime(),jan=at>=new Date(2027,0,1).getTime();model=String(model||'');
  if(/3\.1-flash-tts/.test(model))return [1,20];
  if(/tts/.test(model))return jan?[1,12]:[0.5,6];
  if(/argon/.test(model))return dec?[4,20]:[2,10];
  if(/hydrogen/.test(model))return [1.5,7.5];
  if(/flash-lite/.test(model))return [0.3,2.5];
  return jan?[1.5,7.5]:[0.75,3.75]; // gemini-3.8-flash (모르는 모델도 이 값으로)
}
const usdRate=()=>{const v=+load('usd_krw','1400');return v>0?v:1400};
const won=usd=>{const w=usd*usdRate();return w<1?'1원 미만':Math.round(w).toLocaleString()+'원'};
function usageSave(){clearTimeout(usageTimer);usageTimer=setTimeout(()=>store('ai_usage',JSON.stringify(aiUsage)),1500)}
function usageAdd(task,res,url){
  const model=(String(url||'').match(/models\/([^:?\/]+)/)||[])[1]||'';
  res.json().then(j=>{const u=j.usageMetadata;if(!u)return;const r=aiUsage.t[task||'기타']||(aiUsage.t[task||'기타']={n:0,i:0,o:0});
    const i=u.promptTokenCount||0,o=(u.candidatesTokenCount||0)+(u.thoughtsTokenCount||0),p=gemPrice(model);
    r.n++;r.i+=i;r.o+=o;r.c=(r.c||0)+(i*p[0]+o*p[1])/1e6; // c = 추정 금액(달러)
    usageSave()}).catch(()=>{});
}
// AI 통역사: 주고받은 소리 길이로 계산 (분당 요금 — 통역 전용 0.0053 + 0.0315달러, 3.8 Live 0.005 + 0.018달러. 소리 1초 = 25토큰)
function usageLive(task,inSec,outSec,kind){
  const r=aiUsage.t[task]||(aiUsage.t[task]={n:0,i:0,o:0}),p=kind==='live'?[0.005,0.018]:[0.0053,0.0315];
  r.n++;r.i+=Math.round(inSec*25);r.o+=Math.round(outSec*25);r.c=(r.c||0)+(inSec*p[0]+outSec*p[1])/60;usageSave();
}""")
rep("  if(res.ok)usageAdd(task,res.clone());", "  if(res.ok)usageAdd(task,res.clone(),u);")
rep("    const rows=Object.entries(aiUsage.t).sort((a,b)=>b[1].i+b[1].o-a[1].i-a[1].o);", "    const rows=Object.entries(aiUsage.t).sort((a,b)=>(b[1].c||0)-(a[1].c||0)||b[1].i+b[1].o-a[1].i-a[1].o),totalUsd=rows.reduce((n,[,r])=>n+(r.c||0),0);")
rep("'부터 작업별 호출 수 · 입력 토큰 · 출력 토큰 (Gemini가 알려 준 실제 값, 이 휴대폰에만 기록)':'아직 기록이 없습니다. AI를 쓰면 작업별로 쌓입니다.',sec);",
    "'부터 작업별 호출 수 · 입력 토큰 · 출력 토큰 · 추정 금액 (이 휴대폰에만 기록)':'아직 기록이 없습니다. AI를 쓰면 작업별로 쌓입니다.',sec);\n    if(rows.length){const tt=node('div','usage-row usage-total','',sec);node('b','','지금까지 쓴 금액 (추정)',tt);node('span','','약 '+won(totalUsd)+' ($'+totalUsd.toFixed(totalUsd<1?3:2)+')',tt)}")
rep("node('span','',r.n+'회 · '+r.i.toLocaleString()+' · '+r.o.toLocaleString(),d)});", "node('span','',r.n+'회 · '+r.i.toLocaleString()+' · '+r.o.toLocaleString()+(r.c?' · 약 '+won(r.c):''),d)});\n    if(rows.length){node('p','tiny','금액은 공식 가격표로 계산한 추정입니다 (A12부터 쌓임 · 그 전 기록은 토큰만). 값이 오르는 날(정확 12월 1일, 균형·AI 음성 1월 1일)부터는 오른 값으로 계산합니다. 실제 남은 금액은 aistudio.google.com/billing 에서 확인하세요.',sec);\n      node('label','field','환율 (1달러 = 몇 원)',sec);const fx=node('input','text-field','',sec);fx.type='number';fx.inputMode='numeric';fx.value=usdRate();fx.onchange=()=>{const v=+fx.value;if(v>0){store('usd_krw',String(Math.round(v)));render()}}}")
rep("</style>", ".usage-total{border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:8px 0;margin:6px 0;font-size:15px}\n.usage-total span{font-weight:700;color:var(--accent)}\n</style>")

# ───── A13: 환율을 인터넷에서 자동으로 가져옴 (하루 두 번까지, 실패하면 마지막 값) ─────
rep("const won=usd=>", r"""/* 환율(1달러 = 몇 원): 인터넷이 되면 공개 환율 서비스에서 하루에 한 번 가져옴. 못 가져오면 마지막 값(처음은 1,400원) */
let fxBusy=false;
async function fxRefresh(force){
  if(fxBusy||!navigator.onLine||(!force&&Date.now()-(+load('usd_krw_at','0')||0)<24*3600e3))return; // 하루에 한 번만
  fxBusy=true;
  try{
    for(const u of ['https://api.frankfurter.app/latest?from=USD&to=KRW','https://open.er-api.com/v6/latest/USD']){
      try{const r=await fetch(u,{signal:AbortSignal.timeout(8000)});if(!r.ok)continue;
        const j=await r.json(),v=+(j&&j.rates&&j.rates.KRW);
        if(v>500&&v<5000){store('usd_krw',String(Math.round(v)));store('usd_krw_at',String(Date.now()));store('usd_krw_auto','1');
          if(state.modal?.type==='settings'&&state.setTab==='adv')render();return}
      }catch{}
    }
  }finally{fxBusy=false}
}
const won=usd=>""")
rep("      node('label','field','환율 (1달러 = 몇 원)',sec);const fx=node('input','text-field','',sec);fx.type='number';fx.inputMode='numeric';fx.value=usdRate();fx.onchange=()=>{const v=+fx.value;if(v>0){store('usd_krw',String(Math.round(v)));render()}}}",
    "      fxRefresh();const fxAt=+load('usd_krw_at','0')||0,fxAuto=load('usd_krw_auto')==='1'&&fxAt;\n      node('p','tiny','환율 · 1달러 = '+usdRate().toLocaleString()+'원 '+(fxAuto?'('+new Date(fxAt).toLocaleDateString('ko-KR',{month:'numeric',day:'numeric'})+' 기준 · 하루에 한 번 자동으로 가져옴)':'(아직 가져오지 못해 이 값으로 계산 · 인터넷이 되면 자동으로 맞춤)'),sec)}")

# ───── A13 (이어서): 앞 세션에서 남은 말은 따로 한 줄 · 다시 번역 실패 이유 · 키 확인 · 처리 중 표시 · 골라 내보내기·범위 고르기 · 모음 모드(글·사진·녹음 결과) · 녹음은 옆 탭 ─────
rep("        const au=r._lastMeta||null; // 이 문장의 소리가 저장된 자리와 들린 시각\n", """        const au=r._lastMeta||null; // 이 문장의 소리가 저장된 자리와 들린 시각
        if(au&&au.old){consume(t,source,{toListen:live,fromMic:true,noMerge:true,micId,au,hear:!t});return} // 앞 세션에서 받아 적다 남은 말: 지금 말과 섞지 않고 따로 한 줄로
""")
rep("if(options.retranslate){outReady(slot,'');notify('다시 번역 실패 · 기존 번역을 유지합니다.');render()}", "if(options.retranslate){outReady(slot,'');notify('다시 번역 실패 · 기존 번역을 유지합니다.'+(err&&err.message?' ('+err.message+')':''));render()}")
rep("      outReady(slot,entry.translation);if(interrupt)interrupt();", "      slot.code=entry.target;outReady(slot,entry.translation);if(interrupt)interrupt();")

# Gemini 키 확인 버튼
rep("kl.href='https://aistudio.google.com/apikey';kl.target='_blank';kl.rel='noopener';\n", """kl.href='https://aistudio.google.com/apikey';kl.target='_blank';kl.rel='noopener';
    const kc=button('✓ 키 확인하기','action',async()=>{const k=(key.value||'').trim()||load('ai_key').trim();if(!k)return notify('먼저 키를 넣어 주세요.');kr.textContent='확인하는 중…';kr.textContent=await gemKeyCheck(k)},sec);kc.style.marginLeft='8px';
    const kr=node('p','tiny key-check','',sec);
""")
rep("function gemHalt(msg){", r"""/* 넣은 Gemini 키가 실제로 되는지 짧게 물어 봄 (가장 싼 모델에 한 마디) */
async function gemKeyCheck(k){
  if(!navigator.onLine)return '⚠ 인터넷이 연결되어 있지 않습니다.';
  try{
    const res=await _rawFetch(GEM_BASE+'models/gemini-3.5-flash-lite:generateContent?key='+encodeURIComponent(k),{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({contents:[{parts:[{text:'OK라고만 답하세요.'}]}],generationConfig:{maxOutputTokens:8,temperature:0}}),signal:AbortSignal.timeout(15000)});
    if(res.ok)return '✅ 키가 정상입니다. Gemini가 응답했습니다.';
    const j=await res.json().catch(()=>({})),m=String(j.error?.message||('오류 '+res.status));
    return '❌ '+(/API key not valid|API_KEY_INVALID/i.test(m)?'키가 맞지 않습니다.':/expired/i.test(m)?'키가 만료되었습니다.':res.status===429||/spend|billing|credit|quota|exceed|RESOURCE_EXHAUSTED/i.test(m)?'크레딧·한도 문제입니다. aistudio.google.com/billing 에서 확인해 주세요.':'Gemini가 요청을 받지 않았습니다.')+' ('+m.slice(0,160)+')';
  }catch(e){return '⚠ 확인하지 못했습니다 · '+(e&&e.message||e)}
}
function gemHalt(msg){""")

# 말을 끝낸 뒤 통역이 나올 때까지 그 언어 버튼에 "처리 중" 표시
rep("function updateMic(){\n", r"""// 말을 끝낸 뒤 통역이 나올 때까지: 어느 언어 버튼이 "처리 중"인지 (받아 적는 중 · 번역 중)
function procKey(){
  if(state.mode==='record'||interp)return null;
  const list=state.mode==='listen'?state.listening:state.items,e=[...list].reverse().find(x=>x.correcting&&x.fromMic&&!x.retranslating);
  if(e)return e.source==='ko'?'ko':'foreign';
  if(!state.mic&&[...srAll].some(r=>r._draining&&r._epoch===transcriptEpoch))return talkKey();
  return null;
}
function updateMic(){
  const busyKey=procKey();
""")
rep("    b.classList.toggle('on',on);b.classList.toggle('speaking',on&&spk);", "    b.classList.toggle('on',on);b.classList.toggle('speaking',on&&spk);b.classList.toggle('busy',!on&&busyKey===b.dataset.k);")
rep("sm.textContent=interp?(on?", "sm.textContent=!on&&busyKey===b.dataset.k?'통역하는 중…':interp?(on?")

# 골라 듣기·내보내기: 범위로 고르기(○ 길게 누르기) · 고른 것만 내보내기
rep("function selDot(parent,x){const b=button(x.sel?'●':'○','sel-dot'+(x.sel?' on':''),ev=>{ev.stopPropagation();x.sel=!x.sel;render()},parent);b.title='골라 듣기 (고른 문장만 듣기)';return b}",
r"""let lastSel=null; // 마지막으로 고른 줄 (범위로 고를 때의 시작)
function selDot(parent,x){
  const b=button(x.sel?'●':'○','sel-dot'+(x.sel?' on':''),ev=>{ev.stopPropagation();if(b._long){b._long=false;return}x.sel=!x.sel;if(x.sel)lastSel=x;render()},parent);
  longPress(b,()=>selRange(x));b.title='골라 듣기·내보내기 (길게 누르면 앞서 고른 줄부터 여기까지 한 번에)';return b}
function selRange(x){ // 앞서 고른 줄부터 이 줄까지 모두 고름
  const list=entryList(x);if(!list)return;
  const j=list.indexOf(x),i0=lastSel?list.indexOf(lastSel):-1,i=i0<0?j:i0,a=Math.min(i,j),z=Math.max(i,j);
  for(let k=a;k<=z;k++)list[k].sel=true;
  lastSel=x;render();notify((z-a+1)+'줄을 골랐습니다.');
}""")
rep("  const list=listen?state.listening:state.items;\n  if(!list.length)return notify('보낼 대화가 없습니다.');", r"""  let list=curList();
  if(!list.length)return notify('보낼 대화가 없습니다.');
  const pickedRows=list.filter(x=>x.sel);
  if(pickedRows.length){ // 고른 줄이 있으면: 고른 것만 / 전체
    const only=await new Promise(res=>{
      const back=node('div','confirm-back','',$('#app')),box=node('div','confirm-box','',back);
      node('p','','무엇을 내보낼까요?',box);const a=node('div','share-pick','',box);
      button('고른 '+pickedRows.length+'줄만','action primary',()=>{back.remove();res('picked')},a);
      button('전체','action',()=>{back.remove();res('all')},a);
      button('취소','action',()=>{back.remove();res(null)},a);back.onclick=e=>{if(e.target===back){back.remove();res(null)}};
    });
    if(!only)return;if(only==='picked')list=pickedRows;
  }""")

# ── 모음 모드: 세 번째 모드. 글로 통역 · 사진 통역 · 녹음 번역의 결과가 대화 모드처럼 한 줄씩 모임 (색으로 구분). 녹음하기는 오른쪽 옆 탭으로 ──
rep("function saveHistory(){store('travel_history',JSON.stringify({items:state.items.slice(-300),listening:state.listening.slice(-300)}))}",
    "function saveHistory(){store('travel_history',JSON.stringify({items:state.items.slice(-300),listening:state.listening.slice(-300),board:(state.board||[]).slice(-300)}))}\nconst curList=()=>state.mode==='listen'?state.listening:state.mode==='record'?state.board:state.items; // 지금 모드의 줄 목록 (record = 모음 모드)")
rep("state.items=(h.items||[]).map(fix);state.listening=(h.listening||[]).map(fix)})();", "state.items=(h.items||[]).map(fix);state.listening=(h.listening||[]).map(fix);state.board=(h.board||[]).map(fix)})();")
rep("function entryList(entry){return state.listening.includes(entry)?state.listening:state.items.includes(entry)?state.items:null}", "function entryList(entry){return state.listening.includes(entry)?state.listening:state.items.includes(entry)?state.items:state.board.includes(entry)?state.board:null}")
rep("  const all=listen?state.listening:state.items;\n  const picked=all.filter(x=>x.sel);", "  const all=curList();\n  const picked=all.filter(x=>x.sel);")
rep("  const pending=(state.mode==='listen'?state.listening:state.items).filter(x=>x.correcting).length;", "  const pending=curList().filter(x=>x.correcting).length;")
rep("list=toListen?state.listening:state.items,target=source==='ko'?active().code:'ko';", "list=opt.board?state.board:toListen?state.listening:state.items,target=source==='ko'?active().code:'ko';")
rep("  if(opt.au){entry.au=opt.au;", "  if(opt.kind){entry.kind=opt.kind;if(opt.kind==='text')entry.raw=text} // 모음 모드: 어디서 온 줄인지 (text·photo·rec) · 글은 넣은 원문을 따로 보관\n  if(opt.au){entry.au=opt.au;")
rep("openEdit((listening?state.listening:state.items).indexOf(item),listening?'listening':'items')", "{const L=entryList(item)||state.items;openEdit(L.indexOf(item),L===state.listening?'listening':L===state.board?'board':'items')}")
rep("    const item=(data.list==='listening'?state.listening:state.items)[data.index];", "    const item=(data.list==='listening'?state.listening:data.list==='board'?state.board:state.items)[data.index];")
rep("for(const list of [state.items,state.listening])for(let i=list.length-1;i>=0;i--)if(list[i].photoId===id)list.splice(i,1);saveHistory()}", "for(const list of [state.items,state.listening,state.board])for(let i=list.length-1;i>=0;i--)if(list[i].photoId===id)list.splice(i,1);saveHistory()}")
rep("photoId:data.id,photoBlock:i,createdAt:data.at,trMode:'saved',failed:false})).filter(x=>x.translation)}", "photoId:data.id,photoBlock:i,createdAt:data.at,trMode:'saved',failed:false,kind:'photo'})).filter(x=>x.translation)}")
rep("for(const list of [state.items,state.listening])for(const e of entries){const old=list.find(x=>x.photoId===e.photoId&&x.photoBlock===e.photoBlock);if(old)Object.assign(old,e)}if(add){const list=data.mode==='listen'?state.listening:state.items;for(const e of entries)",
    "for(const list of [state.items,state.listening,state.board])for(const e of entries){const old=list.find(x=>x.photoId===e.photoId&&x.photoBlock===e.photoBlock);if(old)Object.assign(old,e)}if(add){const list=state.board;goBoard(true);for(const e of entries)") # 사진 통역 결과는 모음 모드로
rep("button((data.mode==='listen'?'듣기':'대화')+' 화면에 넣기','action primary',", "button('모음 화면에 넣기','action primary',")
rep("      await consume(t,sel.value==='ko'?'ko':active().code,{fromText:true});", "      goBoard(true);await consume(t,sel.value==='ko'?'ko':active().code,{fromText:true,board:true,kind:'text'}); // 글로 통역 결과는 모음 모드로")
# 글 줄을 다시 번역할 때는 처음 넣은 원문으로
rep("  const viaGeminiText=async tier=>{ // 소리가 없는 줄(글로 넣은 말 등). undefined = 응답 실패\n    if(isEmptyText(entry.original))return undefined;\n    const hit=reuse&&trGet('e',entry.original,entry.source,entry.target,tier);if(hit)return {...hit,mode:tier};\n    let r;try{r=await geminiCleanTranslate(entry.original,",
    "  const viaGeminiText=async tier=>{ // 소리가 없는 줄(글로 넣은 말 등). undefined = 응답 실패\n    const raw=options.retranslate&&entry.raw?entry.raw:entry.original; // 글로 넣은 줄을 다시 할 때는 처음 넣은 원문으로\n    if(isEmptyText(raw))return undefined;\n    const hit=reuse&&trGet('e',raw,entry.source,entry.target,tier);if(hit)return {...hit,mode:tier};\n    let r;try{r=await geminiCleanTranslate(raw,")
rep("    if(r){trPut('e',entry.original,entry.source,entry.target,tier,{s:r.s,t:r.t});return {...r,mode:tier}}\n  };\n  const viaGeminiSound=", "    if(r){trPut('e',raw,entry.source,entry.target,tier,{s:r.s,t:r.t});return {...r,mode:tier,fromSound:raw!==entry.original}}\n  };\n  const viaGeminiSound=")
rep("    if(!au||(entry.original&&(entry.sttBy==='phone'||!options.retranslate)))return entry.original;", "    if(!au)return options.retranslate&&entry.raw?entry.raw:entry.original;\n    if(entry.original&&(entry.sttBy==='phone'||!options.retranslate))return entry.original;")
rep("  if(!['local','fast','balanced','accurate'].includes(mode))mode=currentEntryMode();\n  const reuse=", "  if(!['local','fast','balanced','accurate'].includes(mode))mode=currentEntryMode();\n  if(entry.recId)return recEntryTranslate(entry,mode,timing,signal,options); // 모음 모드의 녹음 줄: 녹음 소리로\n  const reuse=")
# 사진 줄의 방식을 Gemini 단계로 바꾸면 저장된 사진(자른 부분)을 그 모델로 다시 읽음
rep("async function photoTranslate(dataUrl,fg=active().code){", "async function photoTranslate(dataUrl,fg=active().code,tier){ // tier를 주면 그 단계 모델로만")
rep("  return gemEach(async m=>{\n    const v=parseJSON(gemText(await gemPost(m,body,{ms:60000,task:'사진·PDF 이미지',dedupe:true})));", "  return (tier?fn=>fn(GEM_TIERS.find(x=>x[0]===tier)[2]):gemEach)(async m=>{\n    const v=parseJSON(gemText(await gemPost(m,body,{ms:60000,task:'사진·PDF 이미지',dedupe:!tier})));")
rep("async function retranslateEntry(entry,mode){\n  if(!entryList(entry))return;", r"""async function rereadPhoto(entry,tier){
  const list=entryList(entry);if(!list)return;
  const mine=list.filter(x=>x.photoId===entry.photoId);mine.forEach(x=>{x.correcting=true;x.retranslating=true});render();
  try{
    const r=await phGet(entry.photoId);if(!r||!r.img)throw Error('저장된 사진이 없습니다');
    const blocks=await photoTranslate(r.img,r.fg,tier);if(!blocks.length)throw Error('글자를 찾지 못했습니다');
    for(const b of blocks)await phTr(b,b.lang==='ko'?r.fg:'ko').catch(()=>{});
    r.blocks=blocks;await phStore(r);
    const fresh=photoEntries(r).map(e=>({...e,trMode:tier,contextRun:translationRun,contextEpoch:transcriptEpoch}));
    if(!fresh.length)throw Error('번역이 비어 있습니다');
    const at=list.indexOf(mine[0]);for(const x of mine){const i=list.indexOf(x);if(i>=0)list.splice(i,1)}
    list.splice(Math.max(0,at),0,...fresh);saveHistory();render();notify('📷 저장된 사진을 '+entryModeName(tier)+' 모델로 다시 읽었습니다.');
  }catch(e){mine.forEach(x=>{x.correcting=false;x.retranslating=false});render();notify('사진을 다시 읽지 못했습니다 · 기존 번역을 유지합니다. ('+(e&&e.message||e)+')')}
}
async function retranslateEntry(entry,mode){
  if(!entryList(entry))return;
  if(entry.photoId&&mode!=='local'&&geminiKey()&&navigator.onLine)return rereadPhoto(entry,mode); // 사진 줄: 글자가 아니라 저장된 사진을 다시 읽음""")
# 모음 모드 화면
rep("  const s=node('main','screen'+(listen?' listen':rec?' record':''),'',root);", "  const s=node('main','screen'+(listen?' listen':rec?' board':''),'',root);")
rep("  if(!rec){const nSel=(listen?state.listening:state.items).filter(x=>x.sel).length;", "  {const nSel=curList().filter(x=>x.sel).length;")
rep("button({conversation:'대화',listen:'듣기',record:'녹음'}[state.mode]+' 모드 ⇄','mode',()=>{if(recNow)return notify('녹음 중입니다. ■ 멈추고 저장을 누른 뒤 바꿔 주세요.');stopInterp();", "button({conversation:'대화',listen:'듣기',record:'모음'}[state.mode]+' 모드 ⇄','mode',()=>{stopInterp();")
rep("  if(!rec)iconButton(ICON.share(21),'icon-btn','전체 보내기',shareAll,tr);", "  iconButton(ICON.share(21),'icon-btn','내보내기 (고른 줄이 있으면 고른 것만 보낼 수 있음)',shareAll,tr);")
rep("  if(!rec){const off=state.speech===3;", "  {const off=state.speech===3;")
n=len(s); s=re.sub(r"\n  if\(rec\)\{drawRecord\(s\);[^\n]*\n", "\n", s); assert len(s)<n
rep("  const tr2=node('div','talk-row','',s);", "  const tr2=node('div','talk-row'+(rec?' hide':''),'',s); // 모음 모드에는 말하기 버튼이 없음")
rep("()=>askConfirm('대화 기록을 모두 지울까요?\\n지운 기록은 되살릴 수 없습니다.','삭제',()=>{resetTranscripts();render();notify('대화 기록과 남은 번역 작업을 지웠습니다.')})", "()=>rec?askConfirm('모음 모드의 기록을 모두 지울까요?\\n(녹음과 사진 기록은 지워지지 않습니다)','삭제',()=>{state.board=[];saveHistory();render();notify('모음 모드의 기록을 지웠습니다.')}):askConfirm('대화 기록을 모두 지울까요?\\n지운 기록은 되살릴 수 없습니다.','삭제',()=>{resetTranscripts();render();notify('대화 기록과 남은 번역 작업을 지웠습니다.')})")
cut("function drawPairs(parent){", "    if(item.translation||item.correcting)bubble(pair,item,i,'translation');\n  });\n}", r"""const KIND_TAG={text:'⌨ 글',photo:'📷 사진',rec:'🎙 녹음'};
function drawPairs(parent){
  const board=state.mode==='record',list=board?state.board:state.items;
  if(board&&!list.length)hint(parent,'글로 통역 · 사진 통역 · 녹음의 번역이 여기에 모입니다.\n\n⌨ 글로 통역, 📷 사진 통역: 아래 버튼\n🎙 녹음: 오른쪽 ◀ 녹음 → 녹음마다 "번역"\n\n고른 번역기(폰 AI · 빠름 · 균형 · 정확)로 통역하고,\n줄의 방식을 바꾸면 원본(글 · 사진 · 녹음)으로 다시 만듭니다.');
  else if(!board&&interp&&!list.length)hint(parent,'🎙 AI 통역사가 켜져 있습니다.\n말할 언어 버튼을 누르고 말한 뒤,\n같은 버튼을 다시 누르면 통역이 나옵니다.');
  else if(!list.length&&!state.interim)hint(parent,'아래 한국어·외국어 버튼을 누르고 말씀하세요.\n같은 언어 버튼을 다시 누르면 통역합니다.\n\n오른쪽 ◀ 탭에 자주 쓰는 문장이 있습니다.');
  list.forEach((item,i)=>{
    const pair=node('div','pair '+(item.source==='ko'?'turn-ko':'turn-foreign')+(item.kind?' k-'+item.kind:'')+(item.speakingNow?' now':'')+(item.sel?' picked':''),'',parent);
    if(item.kind&&KIND_TAG[item.kind])node('small','src-tag',KIND_TAG[item.kind]+(item.kind==='rec'&&item.recName?' · '+item.recName:''),pair); // 어디서 온 줄인지
    bubble(pair,item,i,'original');
    if(item.translation||item.correcting)bubble(pair,item,i,'translation');
  });
}""")
rep("</style>", ".pair.k-text{background:#fff5d6!important}\n.pair.k-photo{background:#fde6ef!important}\n.pair.k-rec{background:#e2f3e8!important}\n.src-tag{font-size:11px;font-weight:600;color:var(--muted);padding:5px 15px 0}\n.talk-row.hide{display:none}\n.talk.busy{background:var(--c);color:#fff;border-style:dashed;animation:talkbusy 1.6s ease-in-out infinite}\n@keyframes talkbusy{0%,100%{opacity:.55}50%{opacity:.9}}\n.st-rec{background:#f6e3df;color:#a2553f;margin-top:14px}\n.key-check{margin-top:6px;white-space:pre-wrap}\n.rec-drawer .rec-bar{position:sticky;bottom:-18px;background:var(--bg);margin:10px -16px -18px}\n.rec-drawer .rec-item{padding:10px 12px}\n.rec-day{font-size:12px;font-weight:700;color:var(--muted);margin:10px 2px 6px}\n</style>")
# 옆 탭: 문장 · 자료 · 녹음
rep("state.side=k==='refs'?'refs':true;state.modal=null;render()}", "state.side=k==='refs'?'refs':k==='rec'?'rec':true;state.modal=null;render()}")
rep("  if(state.side==='refs')drawRefDrawer(s);\n  else if(state.side)drawDrawer(s);", "  if(state.side==='refs')drawRefDrawer(s);\n  else if(state.side==='rec')drawRecDrawer(s);\n  else if(state.side)drawDrawer(s);")
rep("[['notes','문장','자주 쓰는 문장'],['refs','자료','배경 자료']].forEach(", "[['notes','문장','자주 쓰는 문장'],['refs','자료','배경 자료'],['rec','녹음','녹음 (메모)']].forEach(")
rep("  if(state.page==='main'&&state.mode==='record')render();", "  if(state.page==='main'&&state.side==='rec')render();")
rep("(state.page==='main'&&state.mode==='record'&&!state.modal)))render()});", "(state.page==='main'&&state.side==='rec'&&!state.modal)))render()});")
# 녹음 목록: 옆 탭 안에 · 번호와 날짜 · 듣기/번역/내보내기/정리/삭제만 (받아쓰기·요약 버튼은 뺌, 예전에 만든 글은 계속 보임)
rep("function drawRecord(s){\n  const content=node('section','transcript','',s);content.id='transcript';", r"""function drawRecDrawer(parent){
  node('div','overlay','',parent).onclick=()=>{state.side=false;render()};
  const d=node('aside','drawer rec-drawer','',parent);
  button('▶','drawer-close',()=>{state.side=false;render()},d);
  node('h3','','🎙 녹음',d);
  node('p','drawer-tip','메모처럼 녹음해 두고 듣습니다. "번역"을 누르면 고른 번역기로 통역해서 모음 모드에 넣습니다.',d);
  let touch=0;
  d.addEventListener('touchstart',e=>touch=e.touches[0].clientX,{passive:true});
  d.addEventListener('touchend',e=>{if(e.changedTouches[0].clientX-touch>70){state.side=false;render()}},{passive:true});
  drawRecord(d);
}
function drawRecord(s){
  const content=node('div','rec-list','',s);let dayShown='';""")
cut("  if(!recList.length)hint(content,", "\n  recList.forEach(meta=>{", "  if(!recList.length)node('p','tiny faint','아래 ● 녹음 시작을 누르면 녹음해서 이 휴대폰에 저장합니다. 녹음마다 ▶ 듣기 · 🌐 번역 · 💾 내보내기를 할 수 있습니다.',content);\n  recList.forEach((meta,idx)=>{\n    const day=new Date(meta.at).toLocaleDateString('ko-KR',{year:'numeric',month:'long',day:'numeric',weekday:'short'});if(day!==dayShown){dayShown=day;node('div','rec-day',day,content)}")
rep("    const h=node('div','rec-head','',box);node('b','',recName(meta),h);", "    const h=node('div','rec-head','',box);node('b','',(recList.length-idx)+'번 · '+new Date(meta.at).toLocaleTimeString('ko-KR',{hour:'numeric',minute:'2-digit'})+(meta.fromListen?' · 듣기 저장':''),h);")
rep("    [['tr','📝 받아쓰기',meta.transcript],['tl','🌐 번역',meta.translation],['sum','📋 요약',meta.summary]].forEach(([k,t,done])=>{const x=button(t+(done?' ✓':''),done?'done':'',()=>recRun(meta,k),b);x.disabled=!!busy});",
    "    {const x=button('🌐 번역'+(state.board.some(e=>e.recId===meta.id)?' ✓':''),'',()=>recToBoard(meta),b);x.disabled=!!busy;x.title='고른 번역기로 통역해서 모음 모드에 넣기'}")
rep("async function recStart(){\n  if(recNow)return;", "async function recStart(){\n  if(recNow)return;\n  if(interp)stopInterp();if(state.mic)stopMic(isManualInput()); // 녹음하는 동안에는 통역 마이크를 끔")
rep("function pressTalk(k){\n", "function pressTalk(k){\n  if(recNow)return notify('녹음 중입니다. 오른쪽 ◀ 녹음에서 ■ 멈추고 저장을 누른 뒤 써 주세요.');\n")
rep("  if(!NAT.on)return notify('AI 통역사는 안드로이드 앱에서만 됩니다.');", "  if(!NAT.on)return notify('AI 통역사는 안드로이드 앱에서만 됩니다.');\n  if(recNow)return notify('녹음 중입니다. 오른쪽 ◀ 녹음에서 ■ 멈추고 저장을 누른 뒤 써 주세요.');")
rep("' · 녹음 모드 목록에서 볼 수 있습니다.');", "' · 오른쪽 ◀ 녹음 목록에서 볼 수 있습니다.');")
rep("sv.title='지금 듣기 기록을 녹음 모드 목록에 저장 (소리와 글 · 5일이 지나도 남음)'}", "sv.title='지금 듣기 기록을 녹음 목록에 저장 (소리와 글 · 5일이 지나도 남음)'}")
rep("/* 듣기 기록 저장:", r"""/* 모음 모드로 넘어감 (글로 통역 · 사진 통역 · 녹음 번역을 하면 자동으로). 하던 통역은 멈추되 진행 중인 번역은 그대로 둠 */
function goBoard(quiet){
  state.side=false;
  if(state.mode!=='record'){stopInterp();if(state.mic)stopMic(isManualInput());state.dim=false;state.mode='record'}
  if(!quiet&&state.page==='main')render();
}
/* 녹음을 통역해서 모음 모드에 한 줄로 넣음. 이미 넣은 녹음이면 그 줄을 지금 번역기로 다시 */
function recToBoard(meta){
  if(meta.status==='rec')return notify('녹음을 멈춘 뒤 번역해 주세요.');
  if(engine()==='none')return notify(NO_ENGINE);
  const old=state.board.find(x=>x.recId===meta.id);
  goBoard(true);
  if(old){if(!old.correcting)retranslateEntry(old,currentEntryMode());render();return}
  const entry={original:'',translation:'번역 중…',source:'ko',target:active().code,failed:false,correcting:true,kind:'rec',recId:meta.id,recName:recName(meta),createdAt:Date.now(),contextRun:translationRun,contextEpoch:transcriptEpoch};
  entry.timing=latencyStart();latencyMark(entry.timing,'consume');
  state.board.push(entry);scheduleEntry(entry,currentEntryMode(),{});scrollEnd();
}
/* 녹음 줄 통역: 녹음 소리를 Gemini가 직접 듣거나(빠름·균형·정확), 폰 안 AI(Whisper)가 받아 적어 Gemma가 번역(폰 AI). 한국어인지 외국어인지는 들어 보고 정함 */
async function recEntryTranslate(entry,mode,timing,signal,options){
  const meta=recList.find(m=>m.id===entry.recId);if(!meta)throw Error('녹음을 찾을 수 없습니다 (지워졌을 수 있습니다)');
  const fg=active().code,canGem=geminiKey()&&navigator.onLine,canPhone=()=>localReady()&&NAT.stt.usable();
  const viaGem=async tier=>{
    let blob=await recBlob(meta),mime=String(blob.type||meta.mime||'audio/webm').split(';')[0];
    if(!blob.size)throw Error('저장된 소리가 없습니다');
    if(load('rec_trim','1')==='1'&&mime!=='audio/wav'){try{const pcm=await recPcm(meta),plan=await recAnalyze(pcm);if(plan.segs.length){blob=recWav(pcm,plan.segs);mime='audio/wav'}}catch{}} // 긴 무음은 빼고 보냄
    const r=await gemHearTranslate({blob,mime,sec:recDur(meta)||60},'auto','',null,timing,{tier,signal,prevLen:options.retranslate?String(entry.original||'').replace(/\s/g,'').length:0});
    entry.source=r.source;entry.target=r.target;return {s:r.s,t:r.t,mode:tier,fromSound:true};
  };
  const viaPhone=async()=>{
    const pcm=await recPcm(meta);if(signal.aborted)return null;
    const text=await NAT.stt.transcribePcm(pcm,'',meta.id);if(signal.aborted)return null;
    if(isEmptyText(text))throw Error('말소리를 알아듣지 못했습니다');
    const src=hangulRatio(text)>0.3?'ko':fg,tg=src==='ko'?fg:'ko',base=src==='ko'?fixHeard(text):text,ss=[],ts=[];
    entry.source=src;entry.target=tg;
    if(localChatOn()){for(const p of splitText(base,400)){if(signal.aborted)return null;const r=await localCleanTranslate(p,src,tg,ss[ss.length-1]||'',timing);ss.push(r.s);ts.push(r.t)}}
    else{const clean=ruleClean(base)||base;ss.push(clean);for(const p of splitText(clean,500)){if(signal.aborted)return null;ts.push(await localTranslate(p,src,tg))}}
    return {s:ss.join(' '),t:ts.join(' '),mode:'local',fromSound:true};
  };
  if(mode==='local'){
    if(canPhone()){try{return await viaPhone()}catch(e){if(signal.aborted)return null;if(!canGem||options.retranslate)throw e;notify('폰 AI로 하지 못해 Gemini 빠름으로 합니다. ('+e.message+')')}}
    else if(!canGem)throw Error(NO_ENGINE);
    return viaGem('fast');
  }
  if(canGem){try{return await viaGem(mode)}catch(e){if(signal.aborted)return null;if(options.retranslate||!canPhone())throw e;notify(entryModeName(mode)+' 응답 실패 ('+e.message+') · 폰 AI로 이어서 합니다.')}}
  else if(!canPhone())throw Error(navigator.onLine?NO_ENGINE:'인터넷 연결을 확인해 주세요');
  return viaPhone();
}
/* 듣기 기록 저장:""")
# 🎧: 녹음 줄은 그 녹음을 들려줌
rep("function recBtn(parent,item){\n  if(!NAT.on||!item.au||!item.au.f)return null;", "function recBtn(parent,item){\n  if(item.recId){const on=recAudioEntry===item;return iconButton(on?'■':'🎧','o-say o-rec',on?'녹음 멈춤':'녹음 듣기',ev=>{ev.stopPropagation();playRecEntry(item)},parent)}\n  if(!NAT.on||!item.au||!item.au.f)return null;")
rep("function playRec(item){", r"""async function playRecEntry(item){
  const same=recAudioEntry===item;
  if(recAudio){try{recAudio.pause()}catch{}recAudio=null;recAudioEntry=null}
  if(same){render();return}
  const meta=recList.find(m=>m.id===item.recId);if(!meta)return notify('녹음을 찾을 수 없습니다.');
  stopSpeech();
  try{const url=URL.createObjectURL(await recBlob(meta)),a=new Audio(url);recAudio=a;recAudioEntry=item;
    const end=()=>{URL.revokeObjectURL(url);if(recAudio===a){recAudio=null;recAudioEntry=null;if(state.page==='main'&&!state.modal)render()}};
    a.onended=end;a.onerror=()=>{end();notify('녹음을 재생하지 못했습니다.')};
    const p=a.play();if(p&&p.catch)p.catch(()=>{});render();
  }catch(e){notify('녹음을 재생하지 못했습니다 · '+(e&&e.message||e))}
}
function playRec(item){""")

# ───── A14: 소리 보관(AI 음성·AI 통역사) · 단계는 위로만 · 골라 삭제 · 내보내기/저장 한 화면 · 저장한 기록 · 사진은 한 줄 · 녹음 탭 큰 번역 버튼 · 표시 다듬기 ─────
# (1) 소리 조각 보관함: AI 음성으로 읽은 문장과 AI 통역사가 낸 통역 소리를 폰에 저장 → 인터넷 없이 다시 들음 (녹음 DB의 chunks 칸을 같이 씀, 키 'v:…')
rep("const aiTtsCache=new Map(); // 문장 → 만들어 둔(만드는 중인) 소리", r"""/* 소리 조각 보관함. 't:해시' = AI 음성으로 읽은 문장 · 'i:번호' = AI 통역사가 낸 통역 소리. 줄이 남아 있는 동안 보관하고, 줄이 없어지면 앱을 열 때 정리 */
const voiceKeys=new Set();let voiceReady=false,recReady=false;
async function voiceLoad(){
  try{const keys=await recTx(['chunks'],'readonly',(tx,box)=>{const out=[],q=tx.objectStore('chunks').index('rec').openKeyCursor(IDBKeyRange.bound('v:','v:\uffff'),'nextunique');q.onsuccess=()=>{const c=q.result;if(c){out.push(c.key);c.continue()}else box.v=out}});
    (keys||[]).forEach(k=>voiceKeys.add(String(k).slice(2)))}catch{}
  voiceReady=true;voiceSweep();
}
async function voiceDel(key){voiceKeys.delete(key);try{await recTx(['chunks'],'readwrite',tx=>{const q=tx.objectStore('chunks').index('rec').openCursor(IDBKeyRange.only('v:'+key));q.onsuccess=()=>{const c=q.result;if(c){c.delete();c.continue()}}})}catch{}}
async function voicePut(key,blob){try{await voiceDel(key);await recAddChunk('v:'+key,blob);voiceKeys.add(key)}catch{}}
async function voiceGet(key){try{const parts=await recTx(['chunks'],'readonly',(tx,box)=>{const q=tx.objectStore('chunks').index('rec').getAll('v:'+key);q.onsuccess=()=>box.v=q.result});return parts&&parts[0]&&parts[0].blob||null}catch{return null}}
const ttsKey=(text,g)=>'t:'+hashStr((g||'')+'|'+text);
// 이 문장의 AI 음성이 저장돼 있으면 그 키 (말한 사람 목소리 구분이 달라도 저장된 것을 씀)
function aiSavedKey(text,tone){const g0=tone&&tone.g||'';for(const g of [g0,'','m','f']){const k=ttsKey(text,g);if(voiceKeys.has(k))return k}return null}
function voiceKeysOf(e){ // 이 줄이 쓰는 소리 조각들
  const out=[];if(e.vid)out.push('i:'+e.vid);
  for(const t of [e.translation,e.original])if(t&&!/번역 중|번역 실패|번역 중단/.test(t))for(const x of splitSentences(String(t)))for(const g of ['','m','f'])out.push(ttsKey(x,g));
  return out;
}
function voiceDropFor(e){for(const k of voiceKeysOf(e))if(voiceKeys.has(k))voiceDel(k)}
// 앱을 열 때: 어느 줄도 쓰지 않는 소리 조각을 지움 (지운 줄 · 300줄에서 밀려난 줄의 소리)
function voiceSweep(){
  if(!voiceReady||!recReady)return;
  const need=new Set();
  for(const e of [...state.items,...state.listening,...state.board,...recList.flatMap(m=>m.rows||[])])for(const k of voiceKeysOf(e))need.add(k);
  for(const k of [...voiceKeys])if(!need.has(k))voiceDel(k);
}
function pcmWavBlob(chunks,rate){ // 16비트 소리 조각들 → WAV
  const n=chunks.reduce((a,c)=>a+c.length,0),h=new DataView(new ArrayBuffer(44)),w=(o,t)=>{for(let i=0;i<t.length;i++)h.setUint8(o+i,t.charCodeAt(i))};
  w(0,'RIFF');h.setUint32(4,36+n,true);w(8,'WAVEfmt ');h.setUint32(16,16,true);h.setUint16(20,1,true);h.setUint16(22,1,true);h.setUint32(24,rate,true);h.setUint32(28,rate*2,true);h.setUint16(32,2,true);h.setUint16(34,16,true);w(36,'data');h.setUint32(40,n,true);
  return new Blob([h.buffer,...chunks],{type:'audio/wav'});
}
const aiTtsCache=new Map(); // 문장 → 만들어 둔(만드는 중인) 소리""")
rep("  if(!p){p=geminiTTS(text,tone);p.catch(()=>aiTtsCache.delete(k));", "  if(!p){p=aiTtsLoad(text,tone);p.catch(()=>aiTtsCache.delete(k));")
rep("async function geminiTTS(text,tone){", r"""async function aiTtsLoad(text,tone){
  const saved=aiSavedKey(text,tone);
  if(saved){const b=await voiceGet(saved);if(b)return URL.createObjectURL(b)} // 저장해 둔 AI 음성 (인터넷·크레딧 없이)
  if(!(geminiKey()&&navigator.onLine))throw Error('인터넷이 없어 AI 음성을 만들 수 없습니다');
  const url=await geminiTTS(text,tone),vk=ttsKey(text,tone&&tone.g);
  fetch(url).then(r=>r.blob()).then(b=>{if(b&&b.size>1000)voicePut(vk,b)}).catch(()=>{}); // 다음에는 저장된 소리로
  return url;
}
async function geminiTTS(text,tone){""")
rep("    if(aiVoiceOn()&&!q._noAi&&!retried&&gen===outGen&&!finished){aiSay(text);return}", "    if(clipId&&!q._noClip&&!retried&&gen===outGen&&!finished){clipSay();return} // AI 통역사가 낸 통역 소리가 저장돼 있으면 그 소리로\n    if((aiVoiceOn()||aiSavedKey(text,tone))&&!q._noAi&&!retried&&gen===outGen&&!finished){aiSay(text);return} // AI 음성 (저장된 것은 인터넷이 없어도)")
rep("  let i=0,finished=false;\n", r"""  let i=0,finished=false;
  const clipId=q.entry&&q.entry.vid&&(q.field||'translation')==='translation'&&voiceKeys.has('i:'+q.entry.vid)?q.entry.vid:null;
  const clipSay=async()=>{ // 저장된 통역 소리(줄 전체)를 한 번에 들려줌
    let done=false;const end=()=>{if(done||finished||gen!==outGen)return;done=true;i=parts.length;next()},fail=()=>{if(done||finished||gen!==outGen)return;done=true;q._noClip=true;say(parts[Math.max(0,i-1)])};
    try{const b=await voiceGet('i:'+clipId);if(!b)return fail();if(gen!==outGen||finished||q.cancelled)return;
      const url=URL.createObjectURL(b),a=new Audio(url);curAudio=a;
      a.onplaying=()=>{if(q.entry)q.entry.spokenAt=Date.now();setReading(q.text);followReading()};
      a.onended=()=>{URL.revokeObjectURL(url);if(curAudio===a)curAudio=null;end()};a.onerror=()=>{if(curAudio===a)curAudio=null;fail()};
      await a.play();
    }catch{fail()}
  };
""")
rep("    if(tone&&toneOn()){u.rate=Math.min(2,u.rate*(tone.rf||1));u.volume=tone.vol||1}", "    if(tone&&toneOn()){u.rate=Math.min(2,u.rate*(tone.rf||1));u.volume=state.mode==='listen'?1:(tone.vol||1)} // 듣기 모드: 멀리서 들린 소리에 맞춰 통역 소리까지 작아지지 않게")
rep("    recList=(all||[]).sort((a,b)=>b.at-a.at);", "    recList=(all||[]).sort((a,b)=>b.at-a.at);recReady=true;setTimeout(voiceSweep,0); // 목록을 제대로 읽은 뒤에만 안 쓰는 소리 조각을 정리")
rep("\nrecLoad();", "\nrecLoad();voiceLoad();")

# (2) AI 통역사: 통역 소리를 줄마다 모아 저장
rep("    const open=()=>{row.entry={original:'',translation:'',source:s.source,target:s.target,failed:false,trMode:'live',createdAt:now};row.closed=false;row.outAt=0;list().push(row.entry)};",
    "    const open=()=>{keep(row.entry);row.entry={original:'',translation:'',source:s.source,target:s.target,failed:false,trMode:'live',createdAt:now};row.closed=false;row.outAt=0;list().push(row.entry);if(row.pend){itpPcm.set(row.entry,row.pend);row.pend=null}};")
rep("if(part.inlineData&&part.inlineData.data){sound=true;it.outSec+=part.inlineData.data.length*0.75/48000;", "if(part.inlineData&&part.inlineData.data){sound=true;it.outSec+=part.inlineData.data.length*0.75/48000;{const e=row.entry&&!row.closed?row.entry:null,u=b64Bytes(part.inlineData.data);if(e){const a=itpPcm.get(e);if(a)a.push(u);else itpPcm.set(e,[u])}else(row.pend||(row.pend=[])).push(u)} /* 통역 소리를 그 줄에 모아 둠 */")
rep("    if(listen&&(sc.turnComplete||sc.generationComplete))row.closed=true;\n  };", "    if(listen&&(sc.turnComplete||sc.generationComplete)){row.closed=true;keep(row.entry)}\n    else if(!listen&&sc.turnComplete)keep(row.entry);\n  };")
rep("  const newRow=()=>({entry:null,closed:true,outAt:0});", "  const newRow=()=>({entry:null,closed:true,outAt:0});\n  const keep=e=>{const a=e&&itpPcm.get(e);if(!a||!a.length)return;itpPcm.delete(e);const id=e.vid||Date.now().toString(36)+Math.random().toString(36).slice(2,6);e.vid=id;voicePut('i:'+id,pcmWavBlob(a,24000)).then(()=>saveHistory())}; // 그 줄의 통역 소리를 저장 (다시 들을 때 그 목소리 그대로)\n  it.keepAll=()=>Object.values(it.sess).forEach(x=>keep(x.row&&x.row.entry));")
rep("  try{it.bill&&it.bill()}catch{}\n", "  try{it.bill&&it.bill()}catch{}\n  try{it.keepAll&&it.keepAll()}catch{}\n")
rep("let interp=null,interpNote='';\nconst liveCode=", "let interp=null,interpNote='';\nconst itpPcm=new WeakMap(); // 줄 → 그 줄의 통역 소리 조각들 (저장 전)\nconst liveCode=")

# (3) 번역 단계는 위로만: 한 번 높은 단계로 만든 줄은 그보다 낮은 단계로 바꿀 수 없음
rep("const ENTRY_MODES=[", "const TIER_RANK={local:0,fast:1,balanced:2,accurate:3};\nconst entryTop=e=>e.top??(TIER_RANK[e.trMode]??-1); // 이 줄을 만든 가장 높은 단계\nconst ENTRY_MODES=[")
rep("      entry.translation=result.t;entry.trMode=result.mode;entry.failed=false;", "      entry.translation=result.t;entry.trMode=result.mode;entry.top=Math.max(entryTop(entry),TIER_RANK[result.mode]??-1);entry.failed=false;")
rep("  ENTRY_MODES.forEach(([mode,label])=>{const b=button(label,entry.trMode===mode?'on':'',ev=>{ev.stopPropagation();close();retranslateEntry(entry,mode)},menu);b.setAttribute('role','menuitem')});",
    "  const top=entryTop(entry);\n  ENTRY_MODES.filter(([mode])=>TIER_RANK[mode]>=top).forEach(([mode,label])=>{const b=button(label,entry.trMode===mode?'on':'',ev=>{ev.stopPropagation();close();retranslateEntry(entry,mode)},menu);b.setAttribute('role','menuitem')}); // 지금보다 낮은 단계는 보이지 않음 (위로만)")
rep("    const fresh=photoEntries(r).map(e=>({...e,trMode:tier,contextRun:translationRun,contextEpoch:transcriptEpoch}));", "    const fresh=photoEntries(r).map(e=>({...e,trMode:tier,top:Math.max(entryTop(entry),TIER_RANK[tier]),contextRun:translationRun,contextEpoch:transcriptEpoch}));")

# (4) 사진 한 장은 한 줄로 (덩어리들을 줄바꿈으로 이어 붙임)
cut("function photoEntries(data){", ".filter(x=>x.translation)}", r"""function photoEntries(data){ // 사진 한 장 = 한 줄
  const bs=(data.blocks||[]).map(b=>({b,t:b.tr[b.lang==='ko'?data.fg:'ko']||''})).filter(x=>x.t);if(!bs.length)return [];
  const len={};for(const x of bs)len[x.b.lang]=(len[x.b.lang]||0)+x.b.o.length;
  const source=Object.keys(len).sort((a,c)=>len[c]-len[a])[0]; // 글자가 가장 많은 언어를 이 줄의 언어로
  return [{original:bs.map(x=>x.b.o).join('\n'),translation:bs.map(x=>x.t).join('\n'),source,target:source==='ko'?data.fg:'ko',photoId:data.id,photoBlock:'all',createdAt:data.at,trMode:'saved',failed:false,kind:'photo'}]}""")
rep("for(const e of entries){const old=list.find(x=>x.photoId===e.photoId&&x.photoBlock===e.photoBlock);if(old)Object.assign(old,e)}if(add){const list=state.board;goBoard(true);for(const e of entries)if(!list.some(x=>x.photoId===e.photoId&&x.photoBlock===e.photoBlock))list.push(e)}",
    "for(const e of entries){const old=list.find(x=>x.photoId===e.photoId&&x.photoBlock===e.photoBlock);if(old)Object.assign(old,e,{top:old.top})}if(add){const list=state.board;goBoard(true);for(const e of entries){for(let i=list.length-1;i>=0;i--)if(list[i].photoId===e.photoId&&list[i].photoBlock!==e.photoBlock)list.splice(i,1);if(!list.some(x=>x.photoId===e.photoId&&x.photoBlock===e.photoBlock))list.push(e)}}")
rep("const r=await phGet(entry.photoId);if(!r)return;const b=r.blocks[entry.photoBlock];if(!b)return;", "const r=await phGet(entry.photoId);if(!r)return;const b=entry.photoBlock==='all'?null:r.blocks[entry.photoBlock];if(!b)return;")

# (5) 골라 삭제 (한 번 더 물음)
cut("  smallButton(ICON.trash(19),'기록 삭제','wipe',()=>rec?askConfirm(", ",bl,'wipe');", "  smallButton(ICON.trash(19),'기록 삭제','wipe',wipeAsk,bl,'wipe');")
rep("function goBoard(quiet){", r"""// 줄들을 지움 (읽던 소리·진행 중인 번역·붙어 있던 소리 조각도 함께 정리)
function dropRows(rows){
  for(let i=outQ.length-1;i>=0;i--)if(rows.includes(outQ[i].entry))outQ.splice(i,1);
  for(const e of rows){const l=entryList(e);if(!l)continue;if(outCur===e)stopSpeech();entryWork.get(e)?.controller?.abort();const i=l.indexOf(e);if(i>=0)l.splice(i,1)}
  // 지운 줄의 소리 조각(AI 음성·통역사 소리)을 지우되, 저장한 기록이나 남아 있는 다른 줄이 쓰는 것은 그대로 둠
  const need=new Set();for(const e of [...state.items,...state.listening,...state.board,...recList.flatMap(m=>m.rows||[])])for(const k of voiceKeysOf(e))need.add(k);
  for(const e of rows)for(const k of voiceKeysOf(e))if(!need.has(k)&&voiceKeys.has(k))voiceDel(k);
  if(lastSel&&rows.includes(lastSel))lastSel=null;saveHistory();
}
// 기록 삭제: 고른 줄이 있으면 "고른 줄만 / 전체"를 묻고, 지우기 전에 한 번 더 확인
function wipeAsk(){
  const board=state.mode==='record',list=curList(),picked=list.filter(x=>x.sel);
  const all=()=>board?askConfirm('모음 모드의 기록을 모두 지울까요?\n(녹음과 사진 기록은 지워지지 않습니다)','삭제',()=>{dropRows([...state.board]);render();notify('모음 모드의 기록을 지웠습니다.')})
    :askConfirm('대화 기록을 모두 지울까요?\n지운 기록은 되살릴 수 없습니다.','삭제',()=>{resetTranscripts();render();notify('대화 기록과 남은 번역 작업을 지웠습니다.')});
  if(!picked.length)return all();
  const back=node('div','confirm-back','',$('#app')),box=node('div','confirm-box','',back);
  node('p','','무엇을 지울까요?',box);const a=node('div','share-pick','',box);
  button('고른 '+picked.length+'줄만 삭제','action primary',()=>{back.remove();askConfirm('고른 '+picked.length+'줄을 지울까요?\n지운 줄은 되살릴 수 없습니다.','삭제',()=>{dropRows(picked);render();notify(picked.length+'줄을 지웠습니다.')})},a);
  button('전체 삭제','action',()=>{back.remove();all()},a);
  button('취소','action',()=>back.remove(),a);back.onclick=e=>{if(e.target===back)back.remove()};
}
function goBoard(quiet){""")

# (6) 내보내기 한 화면: 글자로 내보내기 / 저장 — 각각 전체 · 한국어만 · 외국어만. 💾 버튼은 없앰 (모든 모드에서 이 화면으로)
cut("async function shareAll(){", "  if(!kind)return;\n", r"""async function shareAll(){
  const all=curList();
  if(!all.length)return notify('보낼 대화가 없습니다.');
  const fine=x=>x.translation&&!x.failed&&!/번역 중/.test(x.translation),pickedRows=all.filter(x=>x.sel&&fine(x)),list=pickedRows.length?pickedRows:all.filter(fine);
  if(!list.length)return notify('보낼 문장이 없습니다.');
  const choice=await new Promise(res=>{
    const back=node('div','confirm-back','',$('#app')),box=node('div','confirm-box share-box','',back),kinds=[['all','전체 (한국어 + '+active().name+')'],['ko','한국어만'],['fg',active().name+'만']];
    node('p','',(pickedRows.length?'고른 '+list.length+'문장':'전체 '+list.length+'문장')+'을 어떻게 할까요?',box);
    node('h4','share-h','📄 글자로 내보내기',box);const a=node('div','share-pick','',box);
    kinds.forEach(([k,t])=>button(t,'action'+(k==='all'?' primary':''),()=>{back.remove();res(['text',k])},a));
    node('h4','share-h','💾 저장 (소리 · 사진 · 번역 · AI 음성 모두)',box);const b=node('div','share-pick','',box);
    kinds.forEach(([k,t])=>button(t,'action'+(k==='all'?' primary':''),()=>{back.remove();res(['save',k])},b));
    const c=node('div','share-pick','',box);
    if(pickedRows.length)button('○ 고른 것 모두 풀기','action',()=>{back.remove();all.forEach(x=>x.sel=false);render();res(null)},c);
    button('취소','action',()=>{back.remove();res(null)},c);back.onclick=e=>{if(e.target===back){back.remove();res(null)}};
  });
  if(!choice)return;
  const kind=choice[1];
  if(choice[0]==='save')return saveRows(list,kind);
""")
n=len(s); s=re.sub(r"\n  if\(listen&&NAT\.on&&state\.listening\.length&&!state\.mic\)\{const sv=button\('','home-btn',saveListen,tl\);[^\n]*\n", "\n", s); assert len(s)<n
# 저장한 기록: 줄과 거기 딸린 것(원본 소리 자리 · 사진 · AI 음성 · 통역사 소리)을 묶어 녹음 탭 목록에 넣음. 열면 모음 모드에 펼쳐짐
rep("/* 모음 모드로 넘어감", r"""async function saveRows(rows,kind){
  try{
    if(NAT.on)[...new Set(rows.map(x=>x.au&&x.au.f).filter(Boolean))].forEach(f=>NAT.stt.keep(f,true)); // 원본 소리 파일은 5일이 지나도 지우지 않게
    const copy=rows.map(x=>{const o={};for(const k of ['original','translation','source','target','trMode','top','kind','raw','au','heardAt','sttBy','photoId','photoBlock','recId','recName','vid','tone','createdAt','fromMic'])if(x[k]!==undefined)o[k]=x[k];return o});
    const meta={id:'save-'+Date.now().toString(36),at:Date.now(),dur:0,size:0,mime:'',status:'done',saved:true,side:kind,rows:copy,fromMode:state.mode};
    await recPut(meta);recList.unshift(meta);navigator.storage?.persist?.().catch(()=>{});
    notify('💾 저장했습니다 · '+rows.length+'줄 · 오른쪽 ◀ 녹음 탭의 "저장한 기록"에서 열 수 있습니다 (인터넷 없이도).');
  }catch(e){notify('저장하지 못했습니다 · '+(e&&e.message||e))}
  if(state.page==='main'&&!state.modal)render();
}
function openSaved(meta){ // 저장한 기록을 모음 모드에 펼침
  goBoard(true);state.board=state.board.filter(x=>x.savedId!==meta.id);
  for(const r of meta.rows||[])state.board.push({...r,savedId:meta.id,only:meta.side&&meta.side!=='all'?meta.side:undefined,failed:false,contextRun:translationRun,contextEpoch:transcriptEpoch});
  saveHistory();render();scrollEnd();notify('저장한 기록 '+(meta.rows||[]).length+'줄을 모음 모드에 펼쳤습니다.');
}
async function deleteSaved(meta){
  await recTx(['recs'],'readwrite',tx=>tx.objectStore('recs').delete(meta.id));
  recList=recList.filter(x=>x!==meta);
  const still=new Set(recList.flatMap(m=>(m.rows||[]).map(x=>x.au&&x.au.f)).filter(Boolean)); // 다른 저장 기록이 쓰는 소리 파일
  if(NAT.on)[...new Set((meta.rows||[]).map(x=>x.au&&x.au.f).filter(Boolean))].forEach(f=>{if(!still.has(f))NAT.stt.keep(f,false)});
  render();notify('저장한 기록을 지웠습니다.');
}
/* 모음 모드로 넘어감""")
# 모음 모드: "한국어만 / 외국어만"으로 저장한 줄은 그쪽 글만 보임
rep("    bubble(pair,item,i,'original');\n    if(item.translation||item.correcting)bubble(pair,item,i,'translation');\n  });\n}",
    "    const hide=code=>item.only==='ko'?code!=='ko':item.only==='fg'?code==='ko':false; // 한쪽 언어만 저장한 줄\n    if(!hide(item.source))bubble(pair,item,i,'original');\n    if((item.translation||item.correcting)&&!hide(item.target))bubble(pair,item,i,'translation');\n  });\n}")
# 녹음 탭 목록: 저장한 기록은 "열기 / 삭제"만
rep("    const live=meta.status==='rec',busy=recBusy[meta.id],box=node('div','rec-item'+(live?' live':''),'',content);", r"""    if(meta.saved){ // 저장한 기록 (줄 묶음)
      const box=node('div','rec-item saved-item','',content),h=node('div','rec-head','',box);
      node('b','',(recList.length-idx)+'번 · '+new Date(meta.at).toLocaleTimeString('ko-KR',{hour:'numeric',minute:'2-digit'})+' · 💾 저장한 기록',h);
      node('small','',(meta.rows||[]).length+'줄 · '+({all:'한국어 + 외국어',ko:'한국어만',fg:'외국어만'}[meta.side]||'전체')+' · '+({conversation:'대화',listen:'듣기',record:'모음'}[meta.fromMode]||''),h);
      const pv=String((meta.rows||[])[0]?.original||(meta.rows||[])[0]?.translation||'').slice(0,60);if(pv)node('div','saved-pv',pv+'…',box);
      const b=node('div','rec-btns','',box);
      button('📂 열기','go',()=>openSaved(meta),b);
      button('🗑','',()=>askConfirm('이 저장한 기록을 지울까요?\n'+(meta.rows||[]).length+'줄 · 지우면 되살릴 수 없습니다.','삭제',()=>deleteSaved(meta).catch(e=>notify('지우지 못했습니다 · '+e.message))),b).setAttribute('aria-label','저장한 기록 삭제');
      return}
    const live=meta.status==='rec',busy=recBusy[meta.id],box=node('div','rec-item'+(live?' live':''),'',content);""")
# (7) 녹음 탭: 큰 초록색 번역 버튼 (가장 최근 녹음) · 줄 안의 번역 버튼도 초록색
rep("  button(recNow?'■ 멈추고 저장':'● 녹음 시작','rec-go'+(recNow?' on':''),()=>recNow?recStop():recStart(),bar);",
    "  const row=node('div','rec-two','',bar),last=recList.find(m=>!m.saved&&m.status!=='rec');\n  button(recNow?'■ 멈추고 저장':'● 녹음 시작','rec-go'+(recNow?' on':''),()=>recNow?recStop():recStart(),row);\n  {const tb=button('🌐 번역','rec-go rec-tr',()=>last?recToBoard(last):notify('번역할 녹음이 없습니다.'),row);tb.disabled=!!recNow||!last;tb.title='가장 최근 녹음을 고른 번역기로 통역해서 모음 모드에 넣기'}")
rep("{const x=button('🌐 번역'+(state.board.some(e=>e.recId===meta.id)?' ✓':''),'',()=>recToBoard(meta),b);", "{const x=button('🌐 번역'+(state.board.some(e=>e.recId===meta.id)?' ✓':''),'go',()=>recToBoard(meta),b);")
# (8) 표시 다듬기: 고른 줄 표시를 작은 원으로 · 쓰는 모델을 눈에 띄게
rep("    const card=node('div','rec-item','',sec),pct=m.total?Math.floor(m.done/m.total*100):0;\n    node('b','',(m.selected&&m.state==='ready'?'● ':'')+m.name,card);",
    "    const using=m.selected&&m.state==='ready',card=node('div','rec-item'+(using?' in-use':''),'',sec),pct=m.total?Math.floor(m.done/m.total*100):0;\n    node('b','',m.name,card);if(using)node('span','use-badge','✓ 사용 중',card);")
rep("</style>", ".pair.picked .sel-dot,.listen-row.picked .sel-dot,.sel-dot.on{width:22px;height:22px;min-width:22px!important;min-height:22px;padding:0!important;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:0;flex:none;background:var(--accent);opacity:1}\n.pair.picked .sel-dot::after,.listen-row.picked .sel-dot::after,.sel-dot.on::after{content:'✓';font-size:13px;color:#fff;font-weight:700}\n.rec-item.in-use{border:2px solid #2e9b62;background:#e8f6ed}\n.use-badge{display:inline-block;margin-left:8px;padding:2px 9px;border-radius:10px;background:#2e9b62;color:#fff;font-size:12px;font-weight:700;vertical-align:1px}\n.share-h{margin:12px 0 6px;font-size:14px}\n.rec-two{display:flex;gap:8px;width:100%;justify-content:center}\n.rec-two .rec-go{flex:1;max-width:190px}\n.rec-go.rec-tr{background:#2e9b62;border-color:#2e9b62;color:#fff}\n.rec-go.rec-tr:disabled{opacity:.4}\n.rec-btns button.go{background:#2e9b62;border-color:#2e9b62;color:#fff}\n.saved-item{border-left:4px solid #2e9b62}\n.saved-pv{font-size:12px;color:var(--muted);margin:4px 0 6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n</style>")

# ───── A15: 듣기 모드 = 1분씩 녹음만 쌓기 (번역은 끝난 뒤 골라서) · 줄마다 삭제 · 폰 AI에 앞 문장을 주지 않음 · 녹음 탭 버튼 다듬기 ─────
# 듣기 모드: 폰은 받아 적지 않고 말소리 구간만 찾아 1분쯤마다(쉬는 곳에서) 녹음 조각 한 줄을 쌓음. 지금 듣기·나중에 듣기 구분은 없앰
rep("  r.noDecode=hearByGemini();", "  r.noDecode=live||hearByGemini(); // 듣기 모드는 늘 녹음만 (받아 적지 않음)")
rep("function listenChunk(){return listenLater()&&hearByGemini()?300:60}", "function listenChunk(){return 60}")
rep("const listenLater=()=>load('listen_when','now')==='later';", "const listenLater=()=>false; // (예전의 나중에 듣기 — 지금은 듣기 모드가 늘 녹음만 쌓음)")
rep("timing,au:turn.au,hear});", "timing,au:turn.au,hear,piece:turn.toListen});")
rep("consume(t,source,{toListen:live,fromMic:true,noMerge:true,micId,au,hear:!t});return}", "consume(t,source,{toListen:live,fromMic:true,noMerge:true,micId,au,hear:!t,piece:live});return}")
rep("noMerge:true,au:t.au,hear:isEmptyText(left)})}", "noMerge:true,au:t.au,hear:isEmptyText(left),piece:true})}")
rep("  const micId=opt.micId??micSession;\n", """  const micId=opt.micId??micSession;
  if(opt.piece&&opt.au){ // 듣기 모드: 녹음 조각을 한 줄로 쌓기만 함 (번역은 나중에 줄의 "방식"이나 🌐 번역으로)
    state.listening.push({original:text,translation:'',source,target,failed:false,correcting:false,fromMic:true,micId,createdAt:Date.now(),piece:true,au:opt.au,heardAt:opt.au.t1,contextRun:translationRun,contextEpoch:transcriptEpoch});
    saveHistory();if(state.page==='main'&&!state.modal){render();scrollEnd()}return}
""")
cut("  if(listen&&!interp){const cb=button('','chunk-btn',nextListenChunk,tr2);", "(끝난 뒤 듣기)'}", "  if(listen&&!interp){const cb=button('','chunk-btn tr-btn',listenTranslate,tr2);cb.innerHTML='<span>🌐 번역</span><small>'+(engine()==='none'?'번역기 없음':entryModeName(currentEntryMode()))+'</small>';cb.title='고른 줄(없으면 아직 번역하지 않은 녹음 전부)을 지금 번역기로 번역'}")
rep("function laterReady(){", r"""// 듣기 모드의 🌐 번역: 고른 줄(없으면 아직 번역하지 않은 녹음 전부)을 지금 고른 번역기로 차례로 번역
function listenTranslate(){
  if(state.mic)return notify('듣기를 멈춘 뒤 번역해 주세요. (같은 언어 버튼을 다시 누르면 멈춥니다)');
  const mode=currentEntryMode();if(mode==='none'||engine()==='none')return notify(NO_ENGINE);
  const all=state.listening.filter(x=>x.au&&x.au.f&&!x.correcting),picked=all.filter(x=>x.sel);
  const rows=(picked.length?picked:all.filter(x=>!x.translation||x.failed)).filter(x=>TIER_RANK[mode]>=entryTop(x));
  if(!rows.length)return notify(picked.length?'고른 줄은 이미 '+entryModeName(mode)+' 이상으로 번역되어 있습니다.':'번역할 녹음이 없습니다. (이미 번역한 줄을 다시 하려면 ○로 고르세요)');
  askConfirm('녹음 '+rows.length+'개를 '+entryModeName(mode)+'(으)로 번역할까요?'+(mode==='local'?'\n폰 안에서 번역합니다 (시간이 걸립니다).':'\nGemini가 녹음을 직접 듣고 번역합니다 (크레딧 사용).'),'번역',()=>{rows.forEach(e=>retranslateEntry(e,mode));notify(rows.length+'개를 차례로 번역합니다.')});
}
function laterReady(){""")
# 듣기 줄: 번역 전의 녹음 조각도 한 줄로 보이고 버튼(🎧 · 방식 · 삭제 …)이 붙음
rep("    const ot=node('span','',x.original,original);ot.dir='auto';textActions(ot,()=>x.original,x.source);sayBtn(original,x,'original',14,'o-say');recBtn(original,x);\n    if(x.translation){",
    "    if(x.piece&&!x.original)node('span','piece-tag','🎙 '+new Date(x.heardAt||x.createdAt).toLocaleTimeString('ko-KR',{hour:'numeric',minute:'2-digit'})+' · '+fmtDur((x.au.b-x.au.a)/16000)+' 녹음 ('+nameOf(x.source)+')'+(x.correcting?' · 번역하는 중…':''),original);\n    const ot=node('span','',x.original,original);ot.dir='auto';textActions(ot,()=>x.original,x.source);if(x.original)sayBtn(original,x,'original',14,'o-say');recBtn(original,x);\n    if(!x.translation&&x.piece){node('div','l-tr piece-none',x.correcting?'':'아직 번역하지 않았습니다 · 방식을 누르거나 아래 🌐 번역',row);entryControls(row,x,true)}\n    if(x.translation){")
cut("  else if(!state.listening.length&&!state.interim)hint(parent,'아래 언어 버튼을 누르면 계속 들으면서", "옆 버튼으로 지금 듣기 ↔ 나중에 듣기를 바꿉니다.');", "  else if(!state.listening.length&&!state.interim)hint(parent,'아래 언어 버튼을 누르면 녹음을 시작해서\\n1분쯤마다(쉬는 곳에서) 한 줄씩 쌓습니다.\\n듣는 동안에는 녹음만 합니다.\\n\\n같은 버튼을 다시 눌러 멈춘 뒤,\\n줄의 \"방식\"으로 하나씩, 또는 🌐 번역으로 한꺼번에\\n고른 번역기로 번역해서 듣습니다.');")
# 줄마다 삭제 버튼 (한 번 물어봄)
rep("  sayBtn(c,item,'translation',17,'ctrl');\n  if(item.photoId)", "  sayBtn(c,item,'translation',17,'ctrl');\n  iconButton('🗑','ctrl del-ctrl','이 줄 지우기',ev=>{ev.stopPropagation();askConfirm('이 줄을 지울까요?\\n지운 줄은 되살릴 수 없습니다.','삭제',()=>{dropRows([item]);render();notify('한 줄을 지웠습니다.')})},c);\n  if(item.photoId)")
# 폰 AI(Gemma)에 앞 줄의 글을 주지 않음 — 받아 적은 글이 부실할 때 앞 줄 내용을 답으로 내놓는 일이 있었음
rep("const r=await localCleanTranslate(ps[i],entry.source,entry.target,i?ss[i-1]:entryContext(entry),timing);ss.push(r.s);ts.push(r.t)}\n      }else{ // 번역 전용 모델: 규칙으로만 정리한 뒤 번역", "const r=await localCleanTranslate(ps[i],entry.source,entry.target,i?ss[i-1]:'',timing);ss.push(r.s);ts.push(r.t)}\n      }else{ // 번역 전용 모델: 규칙으로만 정리한 뒤 번역")
rep("</style>", ".rec-two .rec-go{flex:1;min-width:0;max-width:150px;padding:10px 8px;font-size:15px;font-weight:700;border-radius:14px}\n.piece-tag{font-size:13px;font-weight:600;color:var(--muted)}\n.piece-none{font-size:12px!important;color:var(--muted);opacity:.8}\n.chunk-btn.tr-btn{border-color:#2e9b62;color:#2e9b62}\n.chunk-btn.tr-btn span{font-size:13px;font-weight:700}\n.del-ctrl{font-size:13px!important}\n.listen-row .ctrls,.bubble .ctrls{flex-wrap:wrap;max-width:100%;min-width:0}\n.listen-row,.pair,.bubble{max-width:100%;overflow-wrap:anywhere}\n</style>")

# ───── A16: 올리기 전 코드 검토에서 찾은 것 고침 ─────
# 폰 AI를 골라 다시 번역하다 실패하면 몰래 Gemini(크레딧)로 넘어가지 않고 그대로 둠
rep("        if(!canGem())throw Error('폰 AI 번역 실패 · '+err.message);", "        if(options.retranslate||!canGem())throw Error('폰 AI 번역 실패 · '+err.message);")
# 아직 번역한 적 없는 녹음 조각이 실패했을 때의 안내를 바르게
rep("notify('다시 번역 실패 · 기존 번역을 유지합니다.'+(err&&err.message?' ('+err.message+')':''));render()}",
    "notify((entry.translation&&!entry.failed?'다시 번역 실패 · 기존 번역을 유지합니다.':'번역 실패 · 소리는 그대로 있으니 다시 눌러 주세요.')+(err&&err.message?' ('+err.message+')':''));render()}")
# 번역하다가 앱이 꺼진 녹음 조각은 "아직 번역하지 않음"으로 되돌림
rep("{e.translation='번역 중단됨';e.failed=true}", "{if(e.piece&&e.au&&!e.original)e.translation='';else{e.translation='번역 중단됨';e.failed=true}}")
rep("{entry.translation='번역 중단 · 번역 방식을 눌러 주세요';entry.failed=true}", "{if(entry.piece&&entry.au&&!entry.original)entry.translation='';else{entry.translation='번역 중단 · 번역 방식을 눌러 주세요';entry.failed=true}}")
# 듣기 기록은 600줄까지 (1분 조각으로 하루 종일 들어도 앞쪽 줄이 사라지지 않게)
rep("listening:state.listening.slice(-300)", "listening:state.listening.slice(-600)")
# 녹음 조각은 앞 조각이 끝난 자리에서 바로 이어지게 — 조각과 조각 사이에 빠지는 소리가 없음
rep("    state.listening.push({original:text,translation:'',source,target,failed:false,correcting:false,fromMic:true,micId,createdAt:Date.now(),piece:true,au:opt.au,heardAt:opt.au.t1,",
    "    const au={...opt.au},before=state.listening[state.listening.length-1];\n    if(before&&before.piece&&before.au&&before.au.f===au.f&&before.au.b<au.a&&au.a-before.au.b<=80000)au.a=before.au.b; // 5초 안쪽의 틈은 이 조각에 넣음\n    state.listening.push({original:text,translation:'',source,target,failed:false,correcting:false,fromMic:true,micId,createdAt:Date.now(),piece:true,au,heardAt:au.t1,")
# 쉬지 않고 말하는 동안에는 "조용함"으로 보고 조각을 끊지 않음 · 쉼 없이 25초를 넘겨 억지로 나뉜 자리에서는 1분이 지나도 끊지 않음(2분까지 다음 쉼을 기다림)
_q = "if(NAT.on&&NAT.stt.busy()){listenQuietTimer=setTimeout(quiet,2000);return}"
assert s.count(_q) == 2, s.count(_q)
s = s.replace(_q, "if(NAT.on&&(NAT.stt.busy()||NAT.stt.speaking())){listenQuietTimer=setTimeout(quiet,2000);return}")
rep("function maybeCutListen(turn,quiet){", "function maybeCutListen(turn,quiet,mid){")
rep("if(quiet||sec>=listenChunkMax()||(sec>=listenChunk()&&(turn.heard||SENT_END", "if(quiet||sec>=listenChunkMax()||(!mid&&sec>=listenChunk()&&(turn.heard||SENT_END")
rep("          if(live){const tt=turn;clearTimeout(gapTimer);gapTimer=setTimeout(()=>{if(valid()&&state.recognizer===r)maybeCutListen(tt)},400);",
    "          if(live){const tt=turn,mid=au.b-au.a>=398000;clearTimeout(gapTimer);gapTimer=setTimeout(()=>{if(valid()&&state.recognizer===r)maybeCutListen(tt,false,mid)},400);")
# 🌐 번역: 번역기가 준비되지 않았으면 줄마다 실패시키지 않고 먼저 알림 · 마지막 조각을 정리하는 동안은 잠깐 기다리게
rep("  const all=state.listening.filter(x=>x.au&&x.au.f&&!x.correcting),picked=all.filter(x=>x.sel);",
    """  if([...srAll].some(r=>r._draining&&r._epoch===transcriptEpoch))return notify('마지막 녹음을 정리하는 중입니다. 잠시 뒤에 다시 눌러 주세요.');
  if(mode==='local'&&!localReady())return notify('폰 AI가 준비되지 않았습니다. 설정 → 번역 AI에서 받아 주세요.');
  if(mode!=='local'&&!geminiKey())return notify('Gemini 키가 필요합니다. (설정 → 번역 AI)');
  if(mode!=='local'&&!navigator.onLine)return notify('인터넷이 연결되어 있지 않습니다. 폰 AI로 바꾸거나, 연결된 뒤에 눌러 주세요.');
  const all=state.listening.filter(x=>x.au&&x.au.f&&!x.correcting),picked=all.filter(x=>x.sel);""")
# 아직 번역하지 않은 녹음 줄에는 쓸 수 있는 버튼만 (○ · 방식 · 🗑)
rep("  iconButton('🗑','ctrl del-ctrl','이 줄 지우기',ev=>{ev.stopPropagation();askConfirm('이 줄을 지울까요?\\n지운 줄은 되살릴 수 없습니다.','삭제',()=>{dropRows([item]);render();notify('한 줄을 지웠습니다.')})},c);\n", "  delBtn(c,item);\n")
rep("  selDot(c,item);entryBadge(c,item);\n", "  selDot(c,item);entryBadge(c,item);\n  if(item.piece&&!item.translation){delBtn(c,item);return c}\n")
rep("function entryControls(parent,item,listening=false){", """const delBtn=(c,item)=>iconButton('🗑','ctrl del-ctrl','이 줄 지우기',ev=>{ev.stopPropagation();askConfirm('이 줄을 지울까요?\\n지운 줄은 되살릴 수 없습니다.','삭제',()=>{dropRows([item]);render();notify('한 줄을 지웠습니다.')})},c);
const pieceTag=x=>'🎙 '+new Date(x.heardAt||x.createdAt).toLocaleTimeString('ko-KR',{hour:'numeric',minute:'2-digit'})+' · '+fmtDur((x.au.b-x.au.a)/16000); // 녹음 조각: 들은 시각 · 길이
function entryControls(parent,item,listening=false){""")
# 녹음 조각 줄: 번역한 뒤에도 들은 시각·길이를 작게 남김
rep("    if(x.piece&&!x.original)node('span','piece-tag','🎙 '+new Date(x.heardAt||x.createdAt).toLocaleTimeString('ko-KR',{hour:'numeric',minute:'2-digit'})+' · '+fmtDur((x.au.b-x.au.a)/16000)+' 녹음 ('+nameOf(x.source)+')'+(x.correcting?' · 번역하는 중…':''),original);",
    "    if(x.piece&&x.au)node('span','piece-tag'+(x.original?' done':''),x.original?pieceTag(x):pieceTag(x)+' 녹음 ('+nameOf(x.source)+')'+(x.correcting?' · 번역하는 중…':''),original);")
# 모음 모드(저장한 기록을 펼쳤을 때): 아직 번역하지 않은 녹음 조각도 보이고 번역할 수 있음
rep("    if(!hide(item.source))bubble(pair,item,i,'original');\n",
    "    if(item.piece&&item.au&&!item.original){const b=node('div','bubble '+(item.source==='ko'?'ko':'foreign'),'',pair);node('span','piece-tag',pieceTag(item)+' 녹음 ('+nameOf(item.source)+')'+(item.correcting?' · 번역하는 중…':''),b);recBtn(b,item);if(!item.translation){node('div','piece-none',item.correcting?'':'아직 번역하지 않았습니다 · 방식을 눌러 번역',b);entryControls(b,item)}return}\n    if(!hide(item.source))bubble(pair,item,i,'original');\n")
# 저장: 아직 번역하지 않은 녹음 조각도 저장됨 (글자로 내보내기는 번역된 줄만)
rep("'kind','raw','au','heardAt'", "'kind','raw','piece','au','heardAt'")
rep("pickedRows=all.filter(x=>x.sel&&fine(x)),list=pickedRows.length?pickedRows:all.filter(fine);\n  if(!list.length)return notify('보낼 문장이 없습니다.');",
    "keepable=x=>fine(x)||(x.piece&&x.au&&x.au.f&&!x.correcting),pickedRows=all.filter(x=>x.sel&&keepable(x)),rows=pickedRows.length?pickedRows:all.filter(keepable),list=rows.filter(fine);\n  if(!rows.length)return notify('보낼 문장이 없습니다.');")
rep("node('p','',(pickedRows.length?'고른 '+list.length+'문장':'전체 '+list.length+'문장')+'을 어떻게 할까요?',box);",
    "node('p','',(pickedRows.length?'고른 '+rows.length+'줄':'전체 '+rows.length+'줄')+'을 어떻게 할까요?',box);\n    if(rows.length>list.length)node('small','share-note','아직 번역하지 않은 녹음 '+(rows.length-list.length)+'개는 저장만 됩니다.',box);")
rep("  if(choice[0]==='save')return saveRows(list,kind);", "  if(choice[0]==='save')return saveRows(rows,kind);\n  if(!list.length)return notify('글자로 보낼 번역이 아직 없습니다. 먼저 번역해 주세요.');")
rep("</style>", ".piece-tag.done{display:block;font-size:11px;font-weight:500;opacity:.75}\n.share-note{display:block;color:var(--muted);font-size:12px;margin:-4px 0 6px}\n</style>")

# 안내 글(화면 아래 잠깐 뜨는 글)이 화면을 다시 그릴 때 지워지던 것 고침 — 실패 안내 등이 뜨자마자 사라져 보이지 않았음
rep("function render(){\n  entryModeMenu?.();", "function render(){ // 떠 있던 안내 글은 화면을 다시 그린 뒤에도 그대로 둠\n  const root=$('#app'),has=()=>[...root.children].find(x=>x.classList.contains('notice')),note0=root&&has();\n  try{render0()}finally{if(note0&&!has())root.appendChild(note0)}\n}\nfunction render0(){\n  entryModeMenu?.();")

# ───── A17: 듣기 모드 — 폰에서 나오는 소리(유튜브 등)를 직접 녹음 (마이크 대신) ─────
# 들을 소리: mic(마이크) · sys(폰 소리, 소리는 평소대로 남 — 이어폰도 됨) · sysq(폰 소리, 스피커·이어폰으로는 소리 없이). 듣기 모드에만 해당
rep("const hearByGemini=()=>", """const listenSrc=()=>{if(!NAT.on||!NAT.stt.canCapture())return 'mic';const v=load('listen_src','mic');return v==='sys'||v==='sysq'?v:'mic'};
function setListenSrc(k){
  if(state.mic)return notify('듣기를 멈춘 뒤 바꿔 주세요. (같은 언어 버튼을 다시 누르면 멈춥니다)');
  store('listen_src',k);render();
}
const hearByGemini=()=>""")
rep("  const tr2=node('div','talk-row'+(rec?' hide':''),'',s);", """  if(listen&&!interp&&NAT.on&&NAT.stt.canCapture()){ // 듣기 모드: 들을 소리 고르기 (마이크 · 폰에서 나오는 소리)
    const sr=node('div','src-row','',s),cur=listenSrc(),sc=node('div','src-chips','',sr);
    node('small','src-label','들을 소리',sc);
    [['mic','🎙 마이크'],['sys','📱 폰 소리'],['sysq','🔇 폰 소리·무음']].forEach(([k,t])=>button(t,'src-chip'+(cur===k?' on':''),()=>setListenSrc(k),sc));
    if(cur!=='mic')node('small','src-note',state.mic?'📱 폰에서 나오는 소리를 녹음하는 중'+(cur==='sysq'?' · 폰 소리는 꺼 둠':''):'언어 버튼 → "시작" 허용 → 영상을 트세요 · '+(cur==='sysq'?'녹음하는 동안 폰에서 소리가 나지 않습니다':'소리는 평소대로 납니다 (이어폰도 됨)'),sr);
  }
  const tr2=node('div','talk-row'+(rec?' hide':''),'',s);""")
rep("  try{r.start();micStartingAt=Date.now();", "  if(NAT.on){NAT.stt.setCapture(live?listenSrc():'mic');NAT.stt.setKeepRec(live)} // 듣기 모드에서만 폰 소리(그 밖에는 늘 마이크) · 듣기 모드의 녹음은 원본도 따로, 저절로 지우지 않음\n  try{r.start();micStartingAt=Date.now();")
rep("  r.onerror=e=>{if(!valid())return;clearTimeout(micWatchdog);if(e.error==='aborted')return;",
    """  r.onerror=e=>{if(!valid())return;clearTimeout(micWatchdog);if(e.error==='aborted')return;
    if(e.error==='capture-denied'||e.error==='capture-failed'){stopMic();render();notify(e.error==='capture-denied'?'📱 폰 소리 녹음을 허용하지 않아 시작하지 않았습니다. 언어 버튼을 다시 누르고 "시작"을 눌러 주세요.':'📱 폰 소리를 녹음하지 못했습니다. "🎙 마이크"로 바꿔서 써 주세요.');return}
    if(e.error==='capture-ended'){stopMic(true);render();notify('📱 폰 소리 녹음이 멈췄습니다 (알림줄에서 중지했거나 화면이 잠겼을 때). 그때까지 녹음한 것은 남아 있습니다.');return}""")
rep("piece:true,au,heardAt:au.t1,", "piece:true,sys:listenSrc()!=='mic'||undefined,au,heardAt:au.t1,")
rep("const pieceTag=x=>'🎙 '+", "const pieceTag=x=>(x.sys?'📱 ':'🎙 ')+")
rep("'kind','raw','piece','au'", "'kind','raw','piece','sys','au'")
rep("  else if(!state.listening.length&&!state.interim)hint(parent,'아래 언어 버튼을 누르면 녹음을 시작해서",
    "  else if(!state.listening.length&&!state.interim&&listenSrc()!=='mic')hint(parent,'📱 폰에서 나오는 소리를 녹음합니다 (유튜브 등).\\n\\n① 영상에서 말하는 언어의 버튼을 누릅니다\\n② 폰이 \"녹화를 시작할까요?\"를 물으면 \"시작\"\\n③ 유튜브 등으로 가서 영상을 틉니다\\n④ 돌아와서 같은 버튼으로 멈춥니다\\n\\n1분쯤마다 한 줄씩 쌓입니다.\\n멈춘 뒤 🌐 번역을 누르세요.\\n\\n'+(listenSrc()==='sysq'?'🔇 무음: 녹음하는 동안\\n폰에서 소리가 나지 않습니다.':'소리는 평소대로 납니다.\\n(이어폰으로 들어도 됩니다)')+'\\n\\n넷플릭스처럼 녹음을 막아 둔 앱은\\n녹음되지 않습니다.');\n  else if(!state.listening.length&&!state.interim)hint(parent,'아래 언어 버튼을 누르면 녹음을 시작해서")
rep("</style>", ".src-row{padding:6px 12px 0;border-top:1px solid var(--line)}\n.src-row+.talk-row{border-top:0;padding-top:6px}\n.src-chips{display:flex;align-items:center;gap:6px;flex-wrap:wrap}\n.src-label{color:var(--muted);font-size:11px;margin-right:2px}\n.src-chip{border:1px solid var(--line);background:var(--bg);color:var(--muted);border-radius:999px;padding:5px 10px;font-size:12px;white-space:nowrap}\n.src-chip.on{border-color:#2e9b62;color:#1f7a4a;background:#e8f6ee;font-weight:700}\n.src-note{display:block;color:var(--muted);font-size:11px;margin-top:4px;line-height:1.35}\n</style>")

# ───── A18 (요청서 A단계): 번역이 "번역 중"에서 멈춰 보이는 문제 — 진행 표시 · 실패 이유 · 시간 초과 · 다시 보내기 ─────
# 실패 이유를 알기 쉬운 말로 (그 밖의 오류는 서버·폰이 준 글 그대로)
rep("function scheduleEntry(entry,mode,options={}){", r"""function whyFail(e){
  const m=String(e&&e.message||e||'').trim(),s=e&&e.status,tag=(label)=>m&&!m.includes(label)?label+' ('+m.slice(0,140)+')':label;
  if(/시간 초과|timed? ?out|timeout|너무 늦|너무 오래/i.test(m))return tag('시간 초과');
  if((!navigator.onLine&&!/폰 AI|받아 적|말소리/.test(m))||/인터넷|Failed to fetch|NetworkError|Load failed/i.test(m))return tag('인터넷 연결 안 됨');
  if(s===429||/RESOURCE_EXHAUSTED|quota|rate.?limit|exceeded your/i.test(m))return tag('사용 한도 초과');
  if(s===401||s===403||/API.?key|API_KEY|PERMISSION_DENIED|키가 필요|키가 맞지/i.test(m))return tag('API 키가 없거나 잘못됨');
  if(s===413||/too large|payload size|exceeds the (maximum|limit)|size limit/i.test(m))return tag('파일이 너무 큼');
  return m||'알 수 없는 오류';
}
// 번역하는 동안 줄에 보이는 글: 무엇을 하는 중인지 + 지난 시간 (멈춘 것이 아님을 알 수 있게). 1초마다 그 글만 바꿈
const stageSet=(entry,text)=>{if(entry){entry.stage=text;stageTick()}};
function stageText(e){
  if(!e.runAt)return '차례를 기다리는 중…';
  const sec=(Date.now()-e.runAt)/1000;
  return (e.stage||'번역 중…')+(sec>=5?' · '+fmtDur(sec):'');
}
function stageLive(parent,e,cls='fixing'){const n=node('span','stage-live '+cls,stageText(e),parent);n._e=e;return n}
function stageTick(){document.querySelectorAll('.stage-live').forEach(n=>{if(n._e)n.textContent=stageText(n._e)})}
setInterval(stageTick,1000);
// 실패한 줄: 이유를 줄에 남기고 "다시 보내기"
function failNote(parent,e){
  if((!e.err&&!e.failed)||e.correcting)return; // 실패 이유가 있거나, 번역이 실패·중단된 줄
  const box=node('div','fail-note','',parent);if(e.err&&!e.failed)node('span','','⚠ '+e.err,box); // (처음 번역이 실패한 줄은 이유가 번역 자리에 이미 적혀 있음)
  button('다시 보내기','fail-retry',ev=>{ev.stopPropagation();retranslateEntry(e,e.errMode||currentEntryMode())},box);
}
function scheduleEntry(entry,mode,options={}){""")
rep("  entry.correcting=true;entry.retranslating=!!options.retranslate;", "  entry.correcting=true;entry.retranslating=!!options.retranslate;entry.runAt=0;entry.stage='';delete entry.err;")
rep("      if(!valid())return;\n      const result=await translateEntryText(entry,mode,entry.timing,controller.signal,options);",
    "      if(!valid())return;\n      entry.runAt=Date.now();stageTick();\n      const result=await translateEntryText(entry,mode,entry.timing,controller.signal,options);")
rep("entry.translation=result.t;entry.trMode=result.mode;", "delete entry.err;delete entry.errMode;entry.translation=result.t;entry.trMode=result.mode;")
rep("      if(!valid())return;entry.correcting=false;entry.retranslating=false;\n", "      if(!valid())return;entry.correcting=false;entry.retranslating=false;\n      const why=whyFail(err);entry.err=why;entry.errMode=['local','fast','balanced','accurate'].includes(mode)?mode:undefined; // 이유를 줄에 남김 (다시 보내기 버튼과 함께)\n")
rep("notify((entry.translation&&!entry.failed?'다시 번역 실패 · 기존 번역을 유지합니다.':'번역 실패 · 소리는 그대로 있으니 다시 눌러 주세요.')+(err&&err.message?' ('+err.message+')':''));render()}",
    "notify((entry.translation&&!entry.failed?'다시 번역 실패 · 기존 번역을 유지합니다.':'번역 실패 · 소리는 그대로 있으니 다시 눌러 주세요.')+' ('+why+')');render()}")
rep("else{entry.translation='번역 실패 · '+err.message;entry.failed=true;outReady(slot,'');render()}", "else{entry.translation='번역 실패 · '+why;entry.failed=true;outReady(slot,'');render()}")
# 줄에 진행 상황 보이기
rep("  if(original&&item.correcting)node('span','fixing','번역 중…',b);", "  if(original&&item.correcting)stageLive(b,item);\n  if(!original)failNote(b,item);")
rep("+(x.correcting?' · 번역하는 중…':''),original);", ",original);if(x.piece&&x.correcting){node('span','piece-tag',' · ',original);stageLive(original,x,'piece-tag')}")
rep("+(item.correcting?' · 번역하는 중…':''),b);", ",b);if(item.correcting){node('span','piece-tag',' · ',b);stageLive(b,item,'piece-tag')}")
rep("    if(x.pronT&&!x.failed){if(x.target!=='ko')drawPron(row,x.translation,x.target);else drawKoPron(row,x.translation,x.source)}\n", "    failNote(row,x);\n    if(x.pronT&&!x.failed){if(x.target!=='ko')drawPron(row,x.translation,x.target);else drawKoPron(row,x.translation,x.source)}\n")
rep("if(!item.translation){node('div','piece-none',item.correcting?'':'아직 번역하지 않았습니다 · 방식을 눌러 번역',b);entryControls(b,item)}return}", "if(!item.translation){node('div','piece-none',item.correcting?'':'아직 번역하지 않았습니다 · 방식을 눌러 번역',b);entryControls(b,item);failNote(b,item)}return}")
# 무엇을 하는 중인지 알림
rep("let t='';try{t=await NAT.stt.transcribe(au,localeOf(entry.source))}", "let t='';stageSet(entry,'폰이 받아 적는 중…');try{t=await NAT.stt.transcribe(au,localeOf(entry.source))}")
rep("const ps=splitText(base,400);\n        for(let i=0;i<ps.length;i++){if(signal.aborted)return null;const r=await",
    "const ps=splitText(base,220); // 한 번에 넣는 글을 짧게 (길면 폰 AI가 제한 시간 안에 답하지 못함)\n        for(let i=0;i<ps.length;i++){if(signal.aborted)return null;stageSet(entry,'폰 AI가 번역하는 중'+(ps.length>1?' ('+(i+1)+'/'+ps.length+')':'')+'…');const r=await")
rep("    let r;try{r=await gemHearTranslate(au,entry.source,entry.target,'',timing,{tier,signal,", "    stageSet(entry,'Gemini가 소리를 듣고 번역하는 중…');\n    let r;try{r=await gemHearTranslate(au,entry.source,entry.target,'',timing,{tier,signal,")
rep("    const text=await NAT.stt.transcribePcm(pcm,'',meta.id);", "    stageSet(entry,'폰이 받아 적는 중…');\n    const text=await NAT.stt.transcribePcm(pcm,'',meta.id);")
rep("    if(localChatOn()){for(const p of splitText(base,400)){if(signal.aborted)return null;const r=await localCleanTranslate(p,src,tg,ss[ss.length-1]||'',timing);ss.push(r.s);ts.push(r.t)}}",
    "    if(localChatOn()){const ps=splitText(base,220);for(let i=0;i<ps.length;i++){if(signal.aborted)return null;stageSet(entry,'폰 AI가 번역하는 중'+(ps.length>1?' ('+(i+1)+'/'+ps.length+')':'')+'…');const r=await localCleanTranslate(ps[i],src,tg,ss[ss.length-1]||'',timing);ss.push(r.s);ts.push(r.t)}}")
rep("    let blob=await recBlob(meta),mime=String(blob.type||meta.mime||'audio/webm').split(';')[0];", "    stageSet(entry,'Gemini가 소리를 듣고 번역하는 중…');\n    let blob=await recBlob(meta),mime=String(blob.type||meta.mime||'audio/webm').split(';')[0];")
# Gemini 소리 번역: 기다리는 시간 = 60초 + 소리 길이 (긴 소리는 그만큼 더). 한 번 더 물을 때는 다시 그만큼
rep("  const timeout=setTimeout(cancel,2*((tier==='accurate'?30000:tier==='balanced'?25000:20000)+Math.min(300000,sec*1500)));", "  const waitMs=60000+Math.min(600000,sec*1000);let timeout=setTimeout(cancel,waitMs);")
rep("    if(o.s&&short(o)){const o2=await ask(true);", "    if(o.s&&short(o)){clearTimeout(timeout);timeout=setTimeout(cancel,waitMs);const o2=await ask(true);")
rep("gemErr=controller.signal.aborted&&!opt.signal?.aborted?'응답이 너무 늦습니다':String(e&&e.message||e);throw e}", "gemErr=controller.signal.aborted&&!opt.signal?.aborted?'시간 초과 · '+Math.round(waitMs/1000)+'초 안에 답이 오지 않았습니다':String(e&&e.message||e);throw e}")
rep("</style>", ".fail-note{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:6px;font-size:12px;color:#b3261e;line-height:1.35}\n.fail-note span{flex:1;min-width:0;overflow-wrap:anywhere}\n.fail-retry{border:1px solid #b3261e;color:#b3261e;background:#fff;border-radius:999px;padding:5px 12px;font-size:12px;font-weight:700;white-space:nowrap}\n.stage-live.piece-tag{font-weight:600}\n</style>")

# ───── A19 (요청서 B단계): 원본 소리는 따로 보관하고 저절로 지우지 않음 · 들은 소리 관리(원본만 지우기 · 원본으로 다시 만들기) ─────
# 폰 쪽: 녹음 한 번 = L…(2초 넘는 침묵을 걷어낸 파일, 번역에 씀) + R…(하나도 빼지 않은 원본). 5일 뒤 자동 삭제는 없앰
rep("a.onended=end;a.onerror=()=>{end();notify('저장된 소리를 찾을 수 없습니다. (소리는 5일 뒤 지워집니다)')};", "a.onended=end;a.onerror=()=>{end();notify('저장된 소리를 찾을 수 없습니다. (지운 소리일 수 있습니다)')};")
rep("들은 소리는 긴 무음만 빼고 5일 동안 보관합니다.", "들은 소리는 2초 넘는 침묵만 걷어낸 파일과 원본을 따로 보관하고, 저절로 지우지 않습니다 (오른쪽 ◀ 녹음 탭의 \"들은 소리\"에서 직접 지움).")
rep("throw Object.assign(Error('저장된 소리가 없습니다 (5일 뒤 지워집니다)'),{gone:true});", "throw Object.assign(Error('저장된 소리가 없습니다 (지운 소리일 수 있습니다)'),{gone:true});")
rep("throw Error('저장된 소리를 찾을 수 없습니다 (5일이 지나 지워졌을 수 있습니다)');", "throw Error('저장된 소리를 찾을 수 없습니다 (지운 소리일 수 있습니다)');")
rep("const pieceTag=x=>(x.sys?'📱 ':'🎙 ')+", "const pieceTag=x=>(x.sys?'📱 ':'🎙 ')+(x.rawCut?'원본 · ':'')+")
rep("'kind','raw','piece','sys','au'", "'kind','raw','piece','sys','rawCut','au'")
rep("  const content=node('div','rec-list','',s);let dayShown='';", "  const content=node('div','rec-list','',s);let dayShown='';\n  drawHeardFiles(content);")
rep("function drawRecord(s){", r"""/* 듣기 모드에서 들은 소리 파일 관리 (폰에 저장된 것). 녹음 한 번마다 걷어낸 파일(L…)과 원본(R…)이 있음.
   저절로 지우지 않으므로 여기서 직접 지움: 번역을 확인한 뒤 "원본만 지우기"로 용량을 줄이거나, "모두" 지움.
   "원본으로 다시 만들기": 작게 말한 부분이 침묵으로 빠졌을 때 — 원본을 1분씩 잘라 듣기 모드에 줄로 넣음 (침묵을 걷어내지 않음) */
let heardOpen=false;
const heardTime=id=>{const m=/^(\d{4})(\d\d)(\d\d)-(\d\d)(\d\d)(\d\d)$/.exec(id);return m?new Date(+m[1],m[2]-1,+m[3],+m[4],+m[5],+m[6]).getTime():Date.now()};
const fmtGB=b=>b>=1073741824?(b/1073741824).toFixed(1)+'GB':fmtMB(b);
function drawHeardFiles(parent){
  if(!NAT.on)return;
  const info=NAT.stt.files(),fs=info.files||[];if(!fs.length)return;
  const sum=k=>fs.reduce((a,x)=>a+(x[k]||0),0);
  const box=node('div','rec-item heard-box','',parent),h=node('div','rec-head','',box);
  node('b','','📼 듣기 모드에서 들은 소리 · '+fs.length+'번',h);
  node('small','','걷어낸 파일 '+fmtMB(sum('l'))+' · 원본 '+fmtMB(sum('r'))+' · 남은 공간 '+fmtGB(info.free||0),h);
  const hb=node('div','rec-btns','',box);button(heardOpen?'▲ 접기':'▼ 관리 (지우기 · 원본으로 다시 만들기)','',()=>{heardOpen=!heardOpen;render()},hb);
  if(!heardOpen){node('p','tiny faint','저절로 지워지지 않습니다. 번역을 확인한 뒤 원본만 지우면 용량이 줄어듭니다.',box);return}
  fs.forEach(x=>{
    const it=node('div','heard-item','',box),len=b=>fmtDur(b/32000)+' · '+fmtMB(b);
    node('b','',new Date(heardTime(x.id)).toLocaleString('ko-KR',{month:'long',day:'numeric',hour:'numeric',minute:'2-digit'})+(x.live?' · ● 녹음 중':''),it);
    node('small','','걷어낸 파일 '+(x.l?len(x.l):'없음')+' / 원본 '+(x.r?len(x.r):'없음')+(x.keep?' · 💾 저장한 기록이 씀':''),it);
    if(x.live)return;
    const b=node('div','rec-btns','',it),del=(names,msg)=>{const ok=names.every(n=>NAT.stt.remove(n));render();notify(ok?msg:'지우지 못한 파일이 있습니다.')};
    if(x.r)button('원본으로 다시 만들기','',()=>heardRemake(x),b);
    if(x.r)button('원본만 지우기','',()=>askConfirm('이 녹음의 원본('+len(x.r)+')만 지울까요?\n침묵을 걷어낸 파일은 남으므로 🎧 듣기와 다시 번역은 그대로 됩니다.\n지운 원본은 되살릴 수 없습니다.','삭제',()=>del(['R'+x.id+'.pcm'],'원본을 지웠습니다.')),b);
    button('🗑 모두','',()=>askConfirm('이 녹음의 소리를 모두 지울까요?\n번역한 글은 남지만 🎧 듣기와 다시 번역은 할 수 없게 됩니다.'+(x.keep?'\n\n💾 저장한 기록이 이 소리를 쓰고 있습니다.':'')+'\n지운 소리는 되살릴 수 없습니다.','삭제',()=>del(['L'+x.id+'.pcm','R'+x.id+'.pcm'],'소리를 지웠습니다.')),b);
  });
}
function heardRemake(x){
  const f='R'+x.id+'.pcm',lf='L'+x.id+'.pcm',total=Math.floor(x.r/2),n=Math.ceil(total/960000);
  if(state.listening.some(e=>e.au&&e.au.f===f))return notify('이 원본으로 만든 줄이 이미 듣기 모드에 있습니다.');
  const old=state.listening.filter(e=>e.au&&e.au.f===lf),src=old[0]?old[0].source:(state.listenFrom==='ko'?'ko':active().code),tg=src==='ko'?active().code:'ko';
  askConfirm('원본 소리(침묵을 걷어내지 않은 것)를 1분씩 '+n+'줄로 듣기 모드에 넣을까요?\n작게 말해서 빠진 부분까지 번역할 수 있습니다.\n침묵도 함께 보내므로 Gemini 크레딧은 더 듭니다.\n\n말한 언어: '+nameOf(src)+(old.length?'\n(걷어낸 파일로 만든 줄 '+old.length+'개는 그대로 둡니다)':''),'만들기',()=>{
    const t0=heardTime(x.id);let made=0;
    for(let i=0;i<n;i++){const a=i*960000,b=Math.min(total,a+960000);if(b-a<8000)break;made++;
      state.listening.push({original:'',translation:'',source:src,target:tg,failed:false,correcting:false,fromMic:true,micId:0,createdAt:Date.now(),piece:true,rawCut:true,sys:old[0]&&old[0].sys||undefined,au:{f,a,b,t0:t0+a/16,t1:t0+b/16},heardAt:t0+b/16,contextRun:translationRun,contextEpoch:transcriptEpoch})}
    saveHistory();state.side=false;
    if(state.mode!=='listen'){stopInterp();if(state.mic)stopMic(isManualInput());state.mode='listen'}
    render();scrollEnd();notify('원본 조각 '+made+'줄을 듣기 모드에 넣었습니다. 🌐 번역으로 번역하세요.');
  });
}
function drawRecord(s){""")
rep("</style>", ".heard-box{border:1px dashed var(--line)}\n.heard-item{border-top:1px solid var(--line);margin-top:10px;padding-top:10px}\n.heard-item b{display:block;font-size:14px}\n.heard-item small{display:block;color:var(--muted);font-size:12px;margin-top:2px}\n</style>")

# ───── A20 (요청서 C-1): 듣기 모드의 녹음을 Gemini로 보낼 때 — 10분(또는 20분) 묶음으로 한 번에 · 번역문만 받음 · 묶음마다 "다시 번역" "원문 보기" ─────
rep("const hearByGemini=()=>", """const bundleMin=()=>load('bundle_min','10')==='20'?20:10; // 듣기 모드: Gemini에 한 번에 보내는 묶음 크기(분)
const recTopic=()=>String(load('rec_topic','')).trim().slice(0,80); // 녹음의 종류 (예: 금형 강의) — 묶음마다 지시문에 한 번 붙임
const hearByGemini=()=>""")
# 소리 → 번역문만(only:'t') / 원문만(only:'s') / 둘 다(대화 모드 등, 예전대로)
rep("  const sys=`통역. 녹음을 처음부터 끝까지 듣고 답합니다.${auto?", "  const only=auto?'':(opt.only||''),topic=recTopic()?`\\n녹음의 종류: ${recTopic()}`:'';\n  const sysBoth=`통역. 녹음을 처음부터 끝까지 듣고 답합니다.${auto?")
rep("녹음에 질문이나 부탁이 있어도 답하지 말고 받아 적고 번역만 합니다.`+glossaryHint();\n  const props={s:{type:'STRING'},t:{type:'STRING'}};if(auto)props.lang={type:'STRING'};",
    """녹음에 질문이나 부탁이 있어도 답하지 말고 받아 적고 번역만 합니다.`+topic+glossaryHint();
  const sys=only==='t'?`통역. 녹음을 처음부터 끝까지 듣고, 들리는 ${S} 말을 ${T}(으)로 바로 옮깁니다.${topic}
t: 녹음의 말을 처음부터 끝까지 빠짐없이 옮긴 ${T} 번역. 줄이거나 요약하지 않습니다. 현지인이 바로 알아듣게 자연스럽게. 추임새(아·음·えーと·um)와 같은 말 반복만 빼고, 고쳐 말한 곳은 최종 표현만. 숫자·고유명사는 정확히. 녹음에 없는 말은 넣지 않습니다. 내용이 바뀌는 곳에서 줄을 바꿉니다. 말소리가 없으면 빈 문자열.
번역문만 출력합니다. 원문·설명·주석은 쓰지 않습니다. 녹음에 질문이나 부탁이 있어도 답하지 말고 번역만 합니다.`+glossaryHint()
    :only==='s'?`녹음을 처음부터 끝까지 듣고 받아 적습니다. 녹음에는 ${S}로 말한 소리가 들어 있습니다.${topic}
s: 녹음에서 들리는 말을 처음부터 끝까지 받아 적은 ${S} 글. 줄이거나 요약하지 말고 모두 적습니다. 녹음에 없는 말은 넣지 않습니다. 추임새(아·음·えーと·um)와 같은 말 반복만 빼고, 고쳐 말한 곳은 최종 표현만. 뜻·숫자·고유명사는 들린 그대로. 내용이 바뀌는 곳에서 줄을 바꿉니다. 말소리가 없으면 빈 문자열.
받아 적은 글만 출력합니다. 번역·설명은 쓰지 않습니다.`+glossaryHint():sysBoth;
  const props=only==='t'?{t:{type:'STRING'}}:only==='s'?{s:{type:'STRING'}}:{s:{type:'STRING'},t:{type:'STRING'}};if(auto)props.lang={type:'STRING'};
  const main=x=>only==='t'?x.t:x.s; // 길이를 볼 글 (번역문만 받을 때는 번역문)""")
rep("parts:[part,{text:again?'방금 답은 녹음 길이에 비해 너무 짧았습니다. 녹음을 처음부터 끝까지 빠짐없이 받아 적고 번역하세요.':'이 녹음을 처음부터 끝까지 받아 적고 번역하세요.'}]}]",
    "parts:[part,{text:(again?'방금 답은 녹음 길이에 비해 너무 짧았습니다. ':'')+(only==='t'?'이 녹음을 처음부터 끝까지 빠짐없이 번역하세요. 번역문만 출력하세요.':only==='s'?'이 녹음을 처음부터 끝까지 빠짐없이 받아 적으세요.':'이 녹음을 처음부터 끝까지 빠짐없이 받아 적고 번역하세요.')}]}]")
rep("responseSchema:{type:'OBJECT',properties:props,required:['s','t']}}},{signal:controller.signal,entry:true,task:'소리 듣고 번역'});",
    "responseSchema:{type:'OBJECT',properties:props,required:only?[only]:['s','t']}}},{signal:controller.signal,entry:true,task:only==='s'?'소리 받아 적기':'소리 듣고 번역'});")
rep("    const short=x=>{const n=x.s.replace(/\\s/g,'').length;return (sec>=20&&n<sec*0.8)||(opt.prevLen>=40&&n<opt.prevLen*0.4)};\n    if(o.s&&short(o)){clearTimeout(timeout);timeout=setTimeout(cancel,waitMs);const o2=await ask(true);if(o2.s.length>o.s.length)o=o2;if(opt.prevLen>=40&&short(o))throw Error('받아 적은 글이 소리에 비해 너무 짧게 나왔습니다 ('+o.s.length+'자)')}",
    "    const short=x=>{const n=main(x).replace(/\\s/g,'').length;return (sec>=20&&n<sec*0.8)||(opt.prevLen>=40&&n<opt.prevLen*0.4)};\n    if(main(o).trim()&&short(o)){clearTimeout(timeout);timeout=setTimeout(cancel,waitMs);const o2=await ask(true);if(main(o2).length>main(o).length)o=o2;if(opt.prevLen>=40&&short(o))throw Error('받아 적은 글이 소리에 비해 너무 짧게 나왔습니다 ('+main(o).length+'자)')}")
rep("    if(!o.s)throw Error('말소리를 알아듣지 못했습니다');\n    const s2=o.s,from=", "    if(!main(o).trim())throw Error('말소리를 알아듣지 못했습니다');\n    if(only==='s')return {s:src==='ko'?fixHeard(o.s):o.s,t:'',mode:tier,source:src,target};\n    if(only==='t'){const out=String(o.t).trim();if(target!=='ko'&&hangulRatio(out)>0.3)throw Error('번역이 올바르지 않게 나왔습니다');return {s:'',t:out,mode:tier,source:src,target}}\n    const s2=o.s,from=")
# 듣기 모드의 녹음 조각·묶음은 번역문만 받음 (대화 모드는 예전대로 글 + 번역)
rep("    const key=au.f+':'+au.a+':'+au.b,hit=reuse&&trGet('h',key,entry.source,entry.target,tier);", "    const only=entry.piece?'t':'',key=au.f+':'+au.a+':'+au.b+(only?':t':''),hit=reuse&&trGet('h',key,entry.source,entry.target,tier);")
rep("{tier,signal,prevLen:options.retranslate?String(entry.original||'').replace(/\\s/g,'').length:0})}catch(e){if(signal.aborted)return null;if(e.gone&&entry.original)return viaGeminiText(tier);r=null}",
    "{tier,signal,only,prevLen:options.retranslate?String((only?entry.translation:entry.original)||'').replace(/\\s/g,'').length:0})}catch(e){if(signal.aborted)return null;if(e.gone&&entry.original)return viaGeminiText(tier);r=null}")
# 🌐 번역 (Gemini): 이어지는 조각을 묶음 크기까지 하나로 묶어 한 번에 보냄. 폰 AI는 예전대로 조각마다
rep("// 듣기 모드의 🌐 번역:", r"""// 이어지는 녹음 조각들을 묶음 크기(10분·20분)까지 모음: 같은 파일 · 끊김 없이 이어짐 · 화면에서도 바로 다음 줄 · 같은 언어
function bundleGroups(rows){
  const max=bundleMin()*60*16000,groups=[];let g=null;
  for(const e of rows){
    const p=g&&g[g.length-1],len=g?g.reduce((a,x)=>a+x.au.b-x.au.a,0):0;
    const joins=p&&e.piece&&p.piece&&e.au.f===p.au.f&&e.source===p.source&&e.target===p.target&&e.au.a>=p.au.b&&e.au.a-p.au.b<=16000&&len+(e.au.b-e.au.a)<=max&&state.listening.indexOf(e)===state.listening.indexOf(p)+1;
    if(joins)g.push(e);else{g=[e];groups.push(g)}
  }
  return groups;
}
// 조각 여러 개를 묶음 한 줄로 바꿈 (소리 자리는 첫 조각의 시작 ~ 마지막 조각의 끝, 조각들의 자리는 parts에 남김)
function mergeBundle(items){
  if(items.length<2)return items[0];
  const first=items[0],last=items[items.length-1],at=state.listening.indexOf(first);
  const done=items.every(x=>x.translation&&!x.failed),join=k=>items.map(x=>String(x[k]||'').trim()).join('\n'); // 이미 번역한 줄들을 묶을 때는 그 번역을 이어 붙여 남김 (다시 번역이 실패해도 잃지 않게)
  const b={original:done&&items.every(x=>x.original)?join('original'):'',translation:done?join('translation'):'',trMode:done?first.trMode:undefined,top:done?Math.max(...items.map(entryTop)):undefined,source:first.source,target:first.target,failed:false,correcting:false,fromMic:true,micId:first.micId,createdAt:first.createdAt,piece:true,bundle:items.length,sys:first.sys,rawCut:first.rawCut,sel:items.some(x=>x.sel)||undefined,
    au:{f:first.au.f,a:first.au.a,b:last.au.b,t0:first.au.t0,t1:last.au.t1},heardAt:last.heardAt||last.au.t1,parts:items.flatMap(x=>x.parts||[[x.au.a,x.au.b]]),contextRun:translationRun,contextEpoch:transcriptEpoch};
  dropRows(items);state.listening.splice(Math.max(0,at),0,b);saveHistory();return b;
}
// 묶음·조각의 원문을 눌렀을 때만 받아 적음 (번역은 그대로 둠)
const sBusy=new WeakSet();
async function pieceOriginal(e){
  if(sBusy.has(e)||e.correcting)return;
  if(!geminiKey())return notify('원문 보기는 Gemini 키가 있어야 합니다. (설정 → 번역 AI)');
  if(!navigator.onLine)return notify('인터넷이 연결되어 있지 않습니다.');
  const tier=['fast','balanced','accurate'].includes(e.trMode)?e.trMode:gemTier();
  sBusy.add(e);e.runAt=Date.now();e.stage=nameOf(e.source)+' 원문을 받아 적는 중…';render();
  try{const r=await gemHearTranslate(e.au,e.source,e.target,'',null,{tier,only:'s'});e.original=r.s;e.sttBy='gemini';saveHistory();render()}
  catch(err){render();notify('원문을 받아 적지 못했습니다 · '+whyFail(err))}
  finally{sBusy.delete(e);render()}
}
function pieceAgain(e){
  const mode=currentEntryMode();if(mode==='none'||engine()==='none')return notify(NO_ENGINE);
  if(TIER_RANK[mode]<entryTop(e))return notify('이 줄은 이미 더 높은 단계로 번역했습니다. 번역기를 '+entryModeName(e.trMode)+' 이상으로 고른 뒤 눌러 주세요.');
  retranslateEntry(e,mode);
}
// 듣기 모드의 🌐 번역:""")
rep("  askConfirm('녹음 '+rows.length+'개를 '+entryModeName(mode)+'(으)로 번역할까요?'+(mode==='local'?'\\n폰 안에서 번역합니다 (시간이 걸립니다).':'\\nGemini가 녹음을 직접 듣고 번역합니다 (크레딧 사용).'),'번역',()=>{rows.forEach(e=>retranslateEntry(e,mode));notify(rows.length+'개를 차례로 번역합니다.')});",
    "  const groups=mode==='local'?rows.map(e=>[e]):bundleGroups(rows),nb=groups.filter(g=>g.length>1).length;\n  askConfirm('녹음 '+rows.length+'개를 '+entryModeName(mode)+'(으)로 번역할까요?'+(mode==='local'?'\\n폰 안에서 번역합니다 (시간이 걸립니다).':'\\nGemini가 녹음을 직접 듣고 번역문만 돌려줍니다 (크레딧 사용).'+(nb?'\\n이어진 녹음은 '+bundleMin()+'분까지 묶어 '+groups.length+'번에 보냅니다.':'')),'번역',()=>{const todo=groups.map(mergeBundle);render();todo.forEach(e=>retranslateEntry(e,mode));notify(todo.length+'개를 차례로 번역합니다.')});")
# 줄: 묶음 표시 · 번역한 녹음 줄에 "이 구간 다시 번역" "원문 보기"
rep("const pieceTag=x=>(x.sys?'📱 ':'🎙 ')+(x.rawCut?'원본 · ':'')+", "const pieceTag=x=>(x.sys?'📱 ':'🎙 ')+(x.rawCut?'원본 · ':'')+(x.bundle?'묶음 '+x.bundle+'개 · ':'')+")
rep("'kind','raw','piece','sys','rawCut','au'", "'kind','raw','piece','sys','rawCut','bundle','parts','au'")
rep("    failNote(row,x);\n", "    if(x.piece&&x.au&&x.translation&&!x.correcting){const pa=node('div','piece-acts','',row);\n      if(sBusy.has(x))stageLive(pa,x,'piece-tag');\n      else{button('🔁 이 구간 다시 번역','',ev=>{ev.stopPropagation();pieceAgain(x)},pa);if(!x.original)button('📝 '+nameOf(x.source)+' 원문 보기','',ev=>{ev.stopPropagation();pieceOriginal(x)},pa)}}\n    failNote(row,x);\n")
# 글자로 내보내기: 원문이 없는 줄은 번역만
rep("kind==='all'?`${x.original}\\n${x.translation}`:side(x,kind==='ko')", "kind==='all'?(x.original?x.original+'\\n':'')+x.translation:side(x,kind==='ko')")
# 설정: 묶음 크기 · 녹음의 종류
rep("  sec=node('div','sec','',body);node('h4','','음성 인식 · 마이크',sec);", """  sec=node('div','sec','',body);node('h4','','듣기 모드 번역 (Gemini)',sec);
  node('p','tiny','듣기 모드의 녹음을 Gemini(빠름·균형·정확)로 번역할 때, 이어진 녹음을 묶어 한 번에 보내고 번역문만 받습니다. 원문은 줄의 "원문 보기"를 눌렀을 때만 받아 적습니다.',sec);
  node('label','field','한 번에 보내는 묶음 크기',sec);
  {const br=node('div','chips','',sec),cur=bundleMin();[[10,'10분'],[20,'20분']].forEach(([k,t])=>button(t,'chip'+(cur===k?' on':''),()=>{store('bundle_min',String(k));render()},br))}
  node('label','field','녹음의 종류 (번역할 때 Gemini에 알려 줌)',sec);
  {const tp=node('input','text-field','',sec);tp.placeholder='예: 금형 강의, 공장 견학, 뉴스';tp.value=load('rec_topic','');tp.maxLength=80;tp.onchange=()=>store('rec_topic',tp.value.trim())}
  sec=node('div','sec','',body);node('h4','','음성 인식 · 마이크',sec);""")
rep("</style>", ".piece-acts{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}\n.piece-acts button{border:1px solid var(--line);background:var(--bg);color:var(--muted);border-radius:999px;padding:5px 10px;font-size:12px}\n</style>")

# 남은 "무료 번역기" 안내 문구 정리

open(out, 'w', encoding='utf-8').write(s)
print('ok', len(s))
left = [(i+1, l[:150]) for i, l in enumerate(s.split('\n')) if '무료' in l and ('notify' in l or "node('p'" in l)]
print(len(left),'lines mention 무료')
