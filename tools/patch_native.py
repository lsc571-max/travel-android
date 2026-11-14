import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
def rep(old, new, count=1):
    global s
    assert s.count(old) >= 1, 'missing: ' + old[:70]
    assert count == 0 or s.count(old) == count, ('count', s.count(old), old[:70])
    s = s.replace(old, new)

rep("<script>\n'use strict';", "<script src=\"native.js\"></script>\n<script>\n'use strict';")
rep("if(load('defaults27')!=='1'){store('tr_engine','free');store('defaults27','1')}",
    "if(load('defaults27')!=='1'){store('tr_engine',NAT.on?'local':'free');store('defaults27','1')} // 앱에서는 폰 AI가 기본")
rep("const APP_VERSION='A0 · Claude · 안드로이드 앱용 정리본 · 2026.11.14';",
    "const APP_VERSION='A1 · Claude · 안드로이드 앱 · 폰 AI 번역 · 2026.11.14';")
rep("model:engine()==='gemini'?gemModel():'free'}}", "model:engine()==='gemini'?gemModel():engine()}}")
rep("function warmGemini(){if(!aiReady()||!navigator.onLine||", "function warmGemini(){if(engine()!=='gemini'||!navigator.onLine||")
rep("function goMain(){setTimeout(warmGemini,0);", "function goMain(){setTimeout(warmGemini,0);if(engine()==='local')NAT.llm.ensure();")
rep("node('div','offline-banner','인터넷 연결 없음 · 받아 둔 여행 문구와 자주 쓰는 문장만 쓸 수 있어요',s)",
    "node('div','offline-banner',engine()==='local'?'인터넷 연결 없음 · 폰 AI로 번역합니다 (음성 인식·사진 통역은 인터넷이 필요할 수 있어요)':'인터넷 연결 없음 · 받아 둔 여행 문구와 자주 쓰는 문장만 쓸 수 있어요',s)")
rep("const gb=node('span','ai-state tier'+(engine()==='gemini'?' on':''),engLabel(),mw);",
    "const gb=node('span','ai-state tier'+(engine()!=='free'?' on':''),engLabel(),mw);")
rep("""    if(!geminiKey()){notify('Gemini 키가 없어 무료 번역기를 사용합니다.');return}
    if(state.mic)stopMic();
    if(engine()==='free'){store('tr_engine','gemini');store('gem_tier','fast')}
    else {const i=GEM_TIERS.findIndex(x=>x[0]===gemTier());
      if(i===GEM_TIERS.length-1)store('tr_engine','free');else store('gem_tier',GEM_TIERS[i+1][0])}
    gemStop='';render();""",
"""    // 폰 AI → Gemini 빠름 → 균형 → 정확 → 무료 → … (쓸 수 있는 것만)
    const modes=engineChoices();
    if(modes.length<2){notify(NAT.on?'설정 → 번역 AI에서 폰 AI를 받거나, 고급 탭에 Gemini 키를 넣으면 번역기를 바꿀 수 있습니다.':'Gemini 키가 없어 무료 번역기를 사용합니다.');return}
    if(state.mic)stopMic();
    setEngineMode(modes[(modes.indexOf(currentEntryMode())+1)%modes.length]);
    gemStop='';render();""")
rep("function provider(){return engine()==='gemini'?'gemini':null}",
    "function provider(){return geminiKey()&&engine()!=='free'?'gemini':null} // 폰 AI가 기본이어도 키가 있으면 사진 통역·자료 정리는 Gemini로")
rep("async function aiPolish(area,code,onChange){\n  if(!aiReady()||!navigator.onLine)return;",
    "async function aiPolish(area,code,onChange){\n  if(engine()!=='gemini'||!navigator.onLine)return; // 자동 다듬기는 Gemini 번역기를 골랐을 때만 (크레딧 보호)")
rep("function engLabel(){if(engine()!=='gemini')return engineName();return 'Gemini '+GEM_TIERS.find(x=>x[0]===gemTier())[1]}",
    "function engLabel(){const e=engine();if(e==='local')return '📱 폰 AI 번역';if(e!=='gemini')return engineName();return 'Gemini '+GEM_TIERS.find(x=>x[0]===gemTier())[1]}")
rep("function engine(){const e=load('tr_engine','');if(e==='free')return'free';return geminiKey()?'gemini':'free'}\nconst engineName=()=>({free:'무료 번역기',gemini:'Gemini 번역기'})[engine()];",
r"""/* 번역기 세 가지: local = 폰 안 AI(무료·오프라인, 안드로이드 앱) · gemini · free = 무료 번역기(인터넷)
   고른 번역기를 못 쓰는 상태면(모델 안 받음·키 없음) 쓸 수 있는 것으로 자동으로 넘어감 */
function localReady(){return NAT.on&&NAT.llm.usable()}
function engine(){const e=load('tr_engine','');
  if(e==='free')return 'free';
  if(e==='gemini')return geminiKey()?'gemini':(localReady()?'local':'free');
  return localReady()?'local':(geminiKey()?'gemini':'free')}
const engineName=()=>({free:'무료 번역기',gemini:'Gemini 번역기',local:'폰 AI 번역'})[engine()];
function engineChoices(){const m=[];if(localReady())m.push('local');if(geminiKey())m.push('fast','balanced','accurate');m.push('free');return m}
function setEngineMode(m){if(m==='local'||m==='free')store('tr_engine',m);else{store('tr_engine','gemini');store('gem_tier',m)}if(m==='local')NAT.llm.ensure()}
/* 폰 AI 번역 (Hy-MT2): 모델 카드의 지시문 형식 그대로. 켜 둔 용어는 "참고 번역"으로 함께 보냄 */
const HY_EN={ko:'Korean',ja:'Japanese','zh-CN':'Chinese','zh-TW':'Traditional Chinese',en:'English',vi:'Vietnamese',th:'Thai',id:'Indonesian',ms:'Malay',tl:'Filipino',hi:'Hindi',mn:'Mongolian',ru:'Russian',fr:'French',de:'German',es:'Spanish',it:'Italian',pt:'Portuguese',pl:'Polish',cs:'Czech',tr:'Turkish',ar:'Arabic'};
const HY_ZH={ko:'韩语',ja:'日语','zh-CN':'中文','zh-TW':'繁体中文',en:'英语',vi:'越南语',th:'泰语',id:'印尼语',ms:'马来语',tl:'菲律宾语',hi:'印地语',mn:'蒙古语',ru:'俄语',fr:'法语',de:'德语',es:'西班牙语',it:'意大利语',pt:'葡萄牙语',pl:'波兰语',cs:'捷克语',tr:'土耳其语',ar:'阿拉伯语'};
function localPrompt(text,src,target){
  const zh=/^zh/.test(src)||/^zh/.test(target),name=(zh?HY_ZH:HY_EN)[target]||nameOf(target),pairs=[];
  for(const g of allGloss()){
    if(pairs.length>=8)break;if(!g.word||!g.out)continue;
    if(src==='ko'){if(termFor(g,target)&&text.includes(g.word))pairs.push([g.word,g.out])}
    else if(target==='ko'&&(!g.ol||g.ol===src)&&text.includes(g.out))pairs.push([g.out,g.word]);
  }
  if(zh)return (pairs.length?'参考下面的翻译：\n'+pairs.map(x=>x[0]+' 翻译成 '+x[1]).join('\n')+'\n\n':'')+'将以下文本翻译为'+name+'，注意只需要输出翻译后的结果，不要额外解释：\n\n'+text;
  return (pairs.length?'Refer to the following translations:\n'+pairs.map(x=>x[0]+' translates to '+x[1]).join('\n')+'\n\n':'')+'Translate the following text into '+name+'. Note that you should only output the translated result without any additional explanation:\n\n'+text;
}
async function localTranslate(text,src,target){
  text=stripFillers(String(text||'').trim());if(!text)return '';
  const raw=await NAT.llm.chat({messages:[{role:'user',content:localPrompt(text,src,target)}],temperature:0.3,top_k:20,top_p:0.6,repeat_penalty:1.05,max_tokens:Math.min(1024,text.length*4+64),stream:false});
  const out=String(raw||'').trim().replace(/^"([\s\S]*)"$/,'$1').trim();
  if(!out)throw Error('빈 응답');
  if(src==='ko'&&target!=='ko'){const L=out.replace(/[\s\d.,!?。、，！？…·:;"'()\[\]~-]/g,'');if(L&&(out.match(/[가-힣]/g)||[]).length/L.length>0.5)throw Error('번역되지 않은 답')}
  return out;
}""")
rep("  const e=engine();\n  if(e!=='free'){\n    try{return await geminiTranslate(text,src,target,ctx)}",
    "  const e=engine();\n  if(e==='gemini'){\n    try{return await geminiTranslate(text,src,target,ctx)}")
rep("""  const c=cached(text,src,target);if(c)return c;
  if(!navigator.onLine)throw new Error('인터넷이 없습니다. 📚 여행 문구나 받아 둔 자주 쓰는 문장을 써 주세요');
  // AI 엔진은 긴 글을 크게 나눠(앞뒤 뜻을 보며) 번역, 무료 번역기는 380자씩
  const ai=engine()!=='free';""",
"""  const c=cached(text,src,target);if(c)return c;
  if(engine()==='local'){ // 폰 AI: 인터넷 없이 번역. 실패하면 인터넷이 될 때만 무료 번역기로
    try{const out=[],parts=splitText(text,500);for(let i=0;i<parts.length;i++){out.push(await localTranslate(parts[i],src,target));if(parts.length>1)onProgress?.(out.join(' '),i+1,parts.length)}return out.join(' ')}
    catch(err){if(!navigator.onLine)throw err;if(Date.now()-lastEngineWarn>60000){lastEngineWarn=Date.now();notify('폰 AI 번역 실패 → 무료 번역기로 대신 번역합니다 ('+err.message+')')}}
  }
  if(!navigator.onLine)throw new Error('인터넷이 없습니다. 📚 여행 문구나 받아 둔 자주 쓰는 문장을 써 주세요');
  // AI 엔진은 긴 글을 크게 나눠(앞뒤 뜻을 보며) 번역, 무료 번역기는 380자씩
  const ai=engine()==='gemini';""")
rep("const ENTRY_MODES=[['fast','빠름'],['balanced','균형'],['accurate','정확'],['free','무료']];\nconst currentEntryMode=()=>engine()==='gemini'?gemTier():'free';",
    "const ENTRY_MODES=[['local','폰AI'],['fast','빠름'],['balanced','균형'],['accurate','정확'],['free','무료']];\nconst currentEntryMode=()=>{const e=engine();return e==='gemini'?gemTier():e};")
rep("  ENTRY_MODES.forEach(([mode,label])=>{const b=button(label,entry.trMode===mode?'on':'',",
    "  ENTRY_MODES.filter(([mode])=>mode!=='local'||NAT.on).forEach(([mode,label])=>{const b=button(label,entry.trMode===mode?'on':'',")
rep("""  if(!navigator.onLine)throw Error('인터넷 연결을 확인해 주세요');
  if(mode!=='free'&&geminiKey()){""",
"""  if(mode==='local'){ // 폰 AI: 인터넷이 없어도 됨. 실패하면 무료 번역기로
    if(localReady()){
      try{
        latencyMark(timing,'request');const parts=[];
        for(const part of splitText(entry.original,500)){if(signal.aborted)return null;parts.push(await localTranslate(part,entry.source,entry.target))}
        latencyMark(timing,'response');if(signal.aborted)return null;
        return {s:entry.original,t:parts.join(' '),mode:'local'};
      }catch(err){
        if(signal.aborted)return null;latencyMark(timing,'fallback');
        if(!navigator.onLine)throw Error('폰 AI 번역 실패 · '+err.message);
        notify('폰 AI 번역 실패 · 무료 번역기로 이어서 번역합니다. ('+err.message+')');
      }
    }
    mode='free';
  }
  if(!navigator.onLine)throw Error('인터넷 연결을 확인해 주세요');
  if(mode!=='free'&&geminiKey()){""")
rep("  if(mode!=='free'&&!geminiKey()){notify('Gemini 키가 필요합니다.');return}",
    "  if(mode==='local'&&!localReady()){notify('폰 AI가 준비되지 않았습니다. 설정 → 번역 AI에서 받아 주세요.');return}\n  if(mode!=='free'&&mode!=='local'&&!geminiKey()){notify('Gemini 키가 필요합니다.');return}")
# settings
rep("[['basic','기본'],['phrases','여행 문구'],['adv','고급']].forEach(", "[['basic','기본'],...(NAT.on?[['ai','번역 AI']]:[]),['phrases','여행 문구'],['adv','고급']].forEach(")
rep("  if(tab==='adv'){\n    sec=node('div','sec','',body);node('h4','','Gemini 키',sec);",
    "  if(tab==='ai'&&NAT.on)drawLocalAI(body);\n  if(tab==='adv'){\n    sec=node('div','sec','',body);node('h4','','Gemini 키',sec);")
rep("""      if(!geminiKey())store('tr_engine','free');
      else if(!had){store('tr_engine','gemini');store('gem_tier','fast')}""",
"""      if(!geminiKey()){if(load('tr_engine')==='gemini')store('tr_engine',NAT.on?'local':'free')}
      else if(!had&&!localReady()){store('tr_engine','gemini');store('gem_tier','fast')} // 폰 AI를 쓰는 중이면 기본 번역기는 그대로""")
rep("function drawSettings(body){", r"""/* ── 설정 → 번역 AI (안드로이드 앱): 기본 번역기 고르기 · 폰 AI 모델 받기/고르기/지우기 · 음성 인식 방식 ── */
function fmtMB(n){return n>=1e9?(n/1e9).toFixed(2)+'GB':Math.round(n/1e6)+'MB'}
function drawLocalAI(body){
  const st=NAT.llm.state,models=NAT.llm.models();
  let sec=node('div','sec','',body);node('h4','','기본 번역기',sec);
  node('p','tiny','폰 AI는 이 휴대폰 안에서 번역합니다. 무료이고 인터넷이 없어도 됩니다. 모델을 받아 두면 자동으로 기본 번역기가 됩니다. 번역 화면 아래 가운데 버튼으로도 바꿀 수 있습니다.',sec);
  const cur=engine(),row=node('div','chips','',sec);
  [['local','📱 폰 AI (무료·오프라인)'],['gemini','Gemini'],['free','무료 번역기 (인터넷)']].forEach(([k,t])=>{
    const ok=k==='local'?localReady():k==='gemini'?geminiKey():true;
    const b=button(t,'chip'+(cur===k?' on':''),()=>{
      if(!ok)return notify(k==='local'?'먼저 아래에서 폰 AI 모델을 받아 주세요.':'고급 탭에서 Gemini 키를 먼저 넣어 주세요.');
      if(state.mic)stopMic();store('tr_engine',k);if(k==='local')NAT.llm.ensure();render();
    },row);
    if(!ok)b.style.opacity=.5;
  });
  sec=node('div','sec','',body);node('h4','','폰 AI 상태',sec);
  const on=st.state==='ready'||st.state==='loading';
  node('p','tiny',!st.engine?'⚠ 이 설치 파일에는 번역 엔진이 들어 있지 않습니다. (무료 번역기·Gemini는 쓸 수 있습니다)':!st.hasModel?'모델을 아직 받지 않았습니다. 아래에서 받아 주세요.':st.state==='ready'?'✅ 준비됨':st.state==='loading'?'⏳ 불러오는 중… (처음엔 10~30초 걸립니다)':st.state==='error'?'⚠ '+st.error:'쉬는 중 (번역할 때 자동으로 켜집니다)',sec);
  if(st.engine&&st.hasModel){
    const tb=node('div','row-btns','',sec),out=node('p','ai-result','',sec);out.hidden=true;
    button('시험 번역','action',async()=>{
      out.hidden=false;out.textContent='번역 중…';const t0=performance.now();
      try{const r=await localTranslate('안녕하세요. 만나서 반갑습니다.','ko',active().code);out.textContent='안녕하세요. 만나서 반갑습니다.\n→ '+r+'  ('+((performance.now()-t0)/1000).toFixed(1)+'초)'}
      catch(e){out.textContent='실패 · '+e.message}
    },tb);
    button(on?'엔진 끄기 (메모리 비우기)':'엔진 켜기','action',()=>{if(on)NAT.llm.stop();else NAT.llm.ensure()},tb);
  }
  sec=node('div','sec','',body);node('h4','','폰 AI 모델',sec);
  node('p','tiny','오픈소스 번역 AI(텐센트 Hy-MT2 · 한국어·일본어·중국어·영어·베트남어 등 33개 언어)입니다. 한 번만 받으면 됩니다. 와이파이에서 받고, 받는 동안 앱을 켜 두세요.',sec);
  models.forEach(m=>{
    const card=node('div','recording-card','',sec),pct=m.total?Math.floor(m.done/m.total*100):0;
    node('b','',(m.selected&&m.state==='ready'?'● ':'')+m.name,card);
    node('p','',m.note+' · '+(m.total?fmtMB(m.total):'크기 모름')+' · '+({ready:m.selected?'사용 중':'받아 둠',downloading:'받는 중 '+pct+'% ('+fmtMB(m.done)+')',partial:'받다가 멈춤 '+pct+'%',none:'안 받음'})[m.state],card);
    const r=node('div','row-btns','',card);
    if(m.state==='none'||m.state==='partial')button(m.state==='partial'?'이어서 받기':'받기','action primary',()=>{if(!navigator.onLine)return notify('인터넷이 될 때 받을 수 있습니다.');NAT.llm.download(m.id);setTimeout(render,300)},r);
    if(m.state==='downloading')button('취소','action',()=>NAT.llm.cancel(m.id),r);
    if(m.state==='ready'&&!m.selected)button('이 모델 사용','action primary',()=>{NAT.llm.select(m.id);setTimeout(render,400)},r);
    if(m.state==='ready'||m.state==='partial')button('지우기','action',()=>askConfirm('「'+m.name+'」 모델 파일을 지울까요?','지우기',()=>{NAT.llm.remove(m.id);setTimeout(render,500)}),r);
  });
  sec=node('div','sec','',body);node('h4','','다른 모델 직접 넣기',sec);
  node('p','tiny','다른 오픈소스 번역 모델을 쓰고 싶으면, GGUF 형식 파일의 내려받기 주소(.gguf로 끝남)를 넣어 목록에 추가하세요.',sec);
  const nm=node('input','text-field','',sec);nm.placeholder='이름 (예: 다른 번역 모델)';
  const ur=node('input','text-field','',sec);ur.placeholder='https://…/model.gguf';ur.style.marginTop='6px';
  button('＋ 목록에 추가','action',()=>{if(!ur.value.trim())return notify('주소를 넣어 주세요.');const e=NAT.llm.add(nm.value,ur.value);if(e)return notify(e);render();notify('목록에 추가했습니다. "받기"를 눌러 주세요.')},sec).style.marginTop='8px';
  sec=node('div','sec','',body);node('h4','','음성 인식',sec);
  node('p','tiny','기본은 휴대폰의 구글 음성 인식입니다(인터넷 필요). "폰 안 인식"은 인터넷 없이 듣지만, 휴대폰에 그 언어의 오프라인 음성 인식이 깔려 있어야 합니다.',sec);
  const so=load('stt_offline')==='1',sr=node('div','chips','',sec);
  button('구글 기본','chip'+(!so?' on':''),()=>{if(state.mic)stopMic();store('stt_offline','0');render()},sr);
  const ob=button('폰 안 인식 (오프라인)','chip'+(so?' on':''),()=>{if(!NAT.info.sttOffline)return notify('이 휴대폰은 폰 안 음성 인식을 지원하지 않습니다.');if(state.mic)stopMic();store('stt_offline','1');render()},sr);
  if(!NAT.info.sttOffline)ob.style.opacity=.5;
}
/* 처음 설치했을 때: 폰 AI 모델을 받을지 한 번 물어봄 (다른 분께 앱을 드려도 같은 순서로 진행) */
function offerLocalAI(){
  if(!NAT.on||!NAT.llm.state.engine||NAT.llm.state.hasModel||load('local_offer')==='1')return;
  const list=NAT.llm.models(),m=list[0];if(!m||list.some(x=>x.state==='downloading'))return;
  const back=node('div','confirm-back','',$('#app')),box=node('div','confirm-box','',back);back.onclick=e=>e.stopPropagation();
  node('p','','📱 폰 안 번역 AI를 받을까요?\n\n무료이고, 받아 두면 인터넷 없이도 번역합니다.\n크기 약 '+fmtMB(m.total)+' · 와이파이 권장\n\n받는 동안에는 무료 번역기로 쓸 수 있고, 나중에 설정 → 번역 AI에서도 받을 수 있습니다.',box);
  const a=node('div','actions','',box);
  button('나중에','action',()=>{store('local_offer','1');back.remove()},a);
  button('지금 받기','action primary',()=>{
    store('local_offer','1');back.remove();
    if(!navigator.onLine)return notify('인터넷이 될 때 설정 → 번역 AI에서 받아 주세요.');
    NAT.llm.download(m.id);notify('폰 AI를 받는 중입니다. 다 받으면 자동으로 기본 번역기가 됩니다. (진행 상황: 설정 → 번역 AI)');
  },a);
}
if(NAT.on){
  NAT.toast=m=>notify(m);
  const refreshAI=()=>{if(state.modal?.type==='settings'&&state.setTab==='ai')render();else{const g=document.querySelector('.ai-state');if(g){g.textContent=engLabel();g.classList.toggle('on',engine()!=='free')}}};
  NAT.onchange=refreshAI;
  NAT.onmodel=m=>{
    if(m.state==='ready'){ // 다 받으면 자동으로 연결: 그 모델을 고르고 폰 AI를 기본 번역기로
      NAT.llm.select(m.id);if(load('tr_engine')!=='local')store('tr_engine','local');
      notify('📱 폰 AI 번역 준비 완료 · 기본 번역기로 설정했습니다.');
    }else if(m.state==='error')notify('폰 AI 받기 실패 · '+(m.msg||'')+' · 설정 → 번역 AI에서 다시 받아 주세요.');
    else if(m.state==='cancelled')notify('받기를 취소했습니다.');
    refreshAI();
  };
}
function drawSettings(body){""")
rep("    else if(e.error==='network')notify('음성 인식 서버와 연결할 수 없습니다. 인터넷 연결을 확인해 주세요.');",
    "    else if(e.error==='network')notify('음성 인식 서버와 연결할 수 없습니다. 인터넷 연결을 확인해 주세요.');\n    else if(e.error==='language-not-supported'){state.mic=false;state.recognizer=null;render();notify('이 언어의 음성 인식을 휴대폰이 지원하지 않습니다. 설정 → 번역 AI → 음성 인식을 \"구글 기본\"으로 바꿔 보세요.')}")
rep("\nrender();\n", "\nrender();\nif(NAT.on){setTimeout(offerLocalAI,900);if(engine()==='local')NAT.llm.ensure()}\n")
rep("</style>", ".ai-result{margin-top:8px;padding:10px 12px;border-radius:10px;background:var(--surface);font-size:14px;line-height:1.5;white-space:pre-wrap}\n</style>")
open(p, 'w', encoding='utf-8').write(s)
print('patched', len(s))
