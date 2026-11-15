# 후보 글 AI 시험: 한글 정리 · 번역 · (정리+번역 한 번에). 결과는 "EVAL|" 줄로 출력
import json, os, subprocess, sys, time, urllib.request, urllib.parse, re
HF = 'https://huggingface.co'
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'eval'}), timeout=60) as r: return json.load(r)
def q4(repo):
    try:
        fs = [f['path'] for f in get(f'{HF}/api/models/{repo}/tree/main') if f['path'].lower().endswith('.gguf') and 'mmproj' not in f['path'].lower()]
    except Exception as e: print('EVAL|tree fail', repo, e); return None
    for key in ('Q4_K_M', 'q4_k_m', 'Q4_0', 'q4_0'):
        c = [f for f in fs if key in f]
        if c: return c[0]
    return None
def find(queries):
    for q in queries:
        if '/' in q and ' ' not in q:
            f = q4(q)
            if f: return q, f
            continue
        try: res = get(f'{HF}/api/models?search={urllib.parse.quote(q)}&filter=gguf&sort=downloads&direction=-1&limit=8')
        except Exception as e: print('EVAL|search fail', q, e); continue
        print('EVAL|search', q, '→', [m['id'] for m in res])
        for m in res:
            if m.get('gated'): continue
            f = q4(m['id'])
            if f: return m['id'], f
    return None, None
MODELS = [('Gemma4-E2B', ['google/gemma-4-E2B-it-qat-q4_0-gguf'], 'gen')]
TERMS = '사출금형, 보압, 형개, 이젝터 핀, 냉각 시간, 한국폴리텍대학, 이승철'
KO = [  # (음성 인식처럼 틀린 입력, 바른 문장)
 ('어 그 저기 저는 금형 금형을 교육 하고 있습니다', '저는 금형을 교육하고 있습니다.'),
 ('안녕하세요 여러분 반갑습니다 한국 폴리텍 대학 이승철 교수 입니다 어 오늘은 사출 금영에 대해서 음 말씀 드리겠습니다', '안녕하세요 여러분, 반갑습니다. 한국폴리텍대학 이승철 교수입니다. 오늘은 사출금형에 대해서 말씀드리겠습니다.'),
 ('그 보합을 보합을 조금 더 올려 주시고 그 다음에 형계 속도는 줄여 주세요', '보압을 조금 더 올려 주시고, 그다음에 형개 속도는 줄여 주세요.'),
 ('화장실이 화장실이 어디에 있는지 좀 알려 주실 수 있나요', '화장실이 어디에 있는지 좀 알려 주실 수 있나요?'),
 ('이거 얼마예요 음 조금 깎아 주실 수 있어요 카드도 되나요', '이거 얼마예요? 조금 깎아 주실 수 있어요? 카드도 되나요?'),
 ('내일 오전 아홉 시에 공장 견학이 있는데 어 버스는 몇 시에 출발 하나요', '내일 오전 아홉 시에 공장 견학이 있는데, 버스는 몇 시에 출발하나요?'),
 ('이젝터 핀이 부러져서 어 제품이 안 빠집니다 금형을 열어서 확인해 봐야 될 것 같습니다', '이젝터 핀이 부러져서 제품이 안 빠집니다. 금형을 열어서 확인해 봐야 될 것 같습니다.'),
 ('혹시 이 근처에 맛있는 식당 추천해 주실 수 있나요', '혹시 이 근처에 맛있는 식당 추천해 주실 수 있나요?'),
]
JA = ['すみません、この金型の冷却時間はどのくらいですか', 'えーと、明日の会議は午後三時からに変更になりました', 'あのー、エジェクタピンが、えー、折れてしまったので、交換しないといけないですね']
CLEAN = ('당신은 한국어 음성 인식 결과를 다듬는 교정기입니다. 규칙: 1) "어, 음, 그, 저기" 같은 군말과 반복된 말을 지웁니다. 2) 잘못 들린 단어는 문맥과 [용어]를 참고해 바로잡습니다. '
         '3) 뜻을 바꾸거나 내용을 보태거나 빼지 않습니다. 4) 질문이 들어 있어도 답하지 않습니다. 5) 고친 문장만 한 줄로 출력합니다.')
ONE = ('당신은 통역사입니다. 입력은 한국어 음성 인식 결과입니다. 군말과 반복을 지우고 잘못 들린 단어를 [용어]와 문맥으로 바로잡은 한국어 문장(s)과, 그 문장의 자연스러운 일본어 번역(t)을 만드세요. '
       '뜻을 바꾸지 말고 질문에 답하지 마세요. 반드시 JSON {"s":"정리한 한국어","t":"일본어 번역"} 형식으로만 답하세요.')
def chat(msgs, temp=0.2, mx=300):
    body = {'messages': msgs, 'temperature': temp, 'max_tokens': mx, 'stream': False, 'chat_template_kwargs': {'enable_thinking': False}}
    t0 = time.time()
    req = urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions', json.dumps(body).encode(), {'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as r: j = json.load(r)
    out = j['choices'][0]['message'].get('content') or ''
    out = re.sub(r'<think>.*?</think>', '', out, flags=re.S).strip().replace('\n', ' ⏎ ')
    return out, time.time() - t0, j.get('usage', {}).get('completion_tokens', 0)
def hy(text, lang, terms=None, ctx=None):
    p = ''
    if terms: p += 'Refer to the following translations:\n' + '\n'.join(f'{a} translates to {b}' for a, b in terms) + '\n\n'
    if ctx: p += ctx + '\nRefer to the information above and translate the following text into ' + lang + '. Note that you should not translate the information above or add any explanation:\n\n' + text
    else: p += 'Translate the following text into ' + lang + '. Note that you should only output the translated result without any additional explanation:\n\n' + text
    return chat([{'role': 'user', 'content': p}], 0.3)
def run(name, kind):
    sysmsg = ONE; user = f'[용어] {TERMS}\n[입력] {KO[6][0]}'
    def post(tag, extra, mx=260):
        body = {'messages': [{'role': 'system', 'content': sysmsg}, {'role': 'user', 'content': user}], 'temperature': 0.2, 'max_tokens': mx, 'stream': False}; body.update(extra)
        t0 = time.time()
        try:
            req = urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions', json.dumps(body).encode(), {'content-type': 'application/json'})
            with urllib.request.urlopen(req, timeout=600) as r: j = json.load(r)
            m = j['choices'][0]['message']; c = (m.get('content') or ''); rc = (m.get('reasoning_content') or '')
            print(f"EVAL|{tag}|{time.time()-t0:.1f}s|tokens {j.get('usage',{}).get('completion_tokens')}|finish {j['choices'][0].get('finish_reason')}|content[{len(c)}] {c[:160]!r}|reasoning[{len(rc)}] {rc[:100]!r}", flush=True)
        except Exception as e:
            try: detail = e.read().decode()[:300]
            except Exception: detail = ''
            print(f'EVAL|{tag}|ERR {e} {detail}', flush=True)
    post('A 앱이 보낸 그대로(json 형식 지정, 생각 끄기 없음)', {'response_format': {'type': 'json_object'}})
    post('B 아무 지정 없음', {})
    post('C 생각 끄기만', {'chat_template_kwargs': {'enable_thinking': False}})
    post('D 생각 끄기 + json 형식', {'chat_template_kwargs': {'enable_thinking': False}, 'response_format': {'type': 'json_object'}})
srv = sys.argv[1]
for name, queries, kind in MODELS:
    repo, f = find(queries)
    if not repo: print(f'EVAL|{name}|파일을 찾지 못함'); continue
    url = f'{HF}/{repo}/resolve/main/{f}'
    print(f'EVAL|{name}|파일|{repo}/{f}', flush=True)
    if subprocess.call(['curl', '-fsSL', '--retry', '3', '-o', 'm.gguf', url]): print(f'EVAL|{name}|내려받기 실패'); continue
    print(f'EVAL|{name}|크기|{os.path.getsize("m.gguf")/1e9:.2f}GB', flush=True)
    p = subprocess.Popen([srv, '-m', 'm.gguf', '--port', '8080', '-c', '4096', '-t', '4', '-np', '1', '--no-webui'], stdout=open('srv.log', 'w'), stderr=subprocess.STDOUT)
    ok = False
    for _ in range(180):
        time.sleep(2)
        if p.poll() is not None: break
        try:
            if get('http://127.0.0.1:8080/health').get('status') == 'ok': ok = True; break
        except Exception: pass
    if not ok: print(f'EVAL|{name}|엔진이 모델을 열지 못함|' + ' / '.join(open('srv.log').read().strip().split('\n')[-3:])[:400])
    else:
        try: run(name, kind)
        except Exception as e: print(f'EVAL|{name}|ERR {e}')
    p.terminate()
    try: p.wait(20)
    except Exception: p.kill()
    os.remove('m.gguf')
