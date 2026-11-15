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
n = len(s); s = re.sub(r"const APP_VERSION='[^']*';", "const APP_VERSION='A10 · Claude · 내 폰 전용 (S24 울트라) · 폰 안에서 한글 정리+번역 · 2026.11.15';", s, count=1); assert len(s) != n
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
  const it=interp={listen,kind:listen?'tr':interpConvKind(),sess:{},olds:[],dir:null,pending:false,ctx:new (window.AudioContext||window.webkitAudioContext)({sampleRate:24000}),next:0,srcs:[],timer:null,waitT:null,idle:null,lastAct:Date.now()};
  try{it.ctx.resume?.()}catch{}
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
    let sound=false;for(const part of (sc.modelTurn&&sc.modelTurn.parts)||[])if(part.inlineData&&part.inlineData.data){sound=true;if(listen||s.outOn)play(part.inlineData.data)} // 대화 모드: 새로 말하기 시작하면 앞 통역의 남은 소리는 내지 않음
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
    send(session(it.dir),{realtimeInput:{audio:{data:b64,mimeType:'audio/pcm;rate=16000'}}});
  },!ear);
  startPcm();
  it.idle=setInterval(()=>{if(alive()&&Date.now()-it.lastAct>300000)stopInterp('5분 동안 말소리가 없어 AI 통역사를 껐습니다.')},15000);
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

# 남은 "무료 번역기" 안내 문구 정리

open(out, 'w', encoding='utf-8').write(s)
print('ok', len(s))
left = [(i+1, l[:150]) for i, l in enumerate(s.split('\n')) if '무료' in l and ('notify' in l or "node('p'" in l)]
print(len(left),'lines mention 무료')
