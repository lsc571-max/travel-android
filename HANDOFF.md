# 여행 통역 앱 (안드로이드) — 이어서 작업하기 위한 인수인계

2026-11-15 기준 · 현재 버전 **A8** · 사용자: 이승철 교수 (갤럭시 S24 울트라, 램 12GB)

## 1. 무엇을 만드는가

- 웹앱 "AI 실시간 여행 통역 앱"(`lsc571-max/travel`, GitHub Pages)의 **안드로이드 앱 판**.
- 지금은 **배포용이 아니라 사용자 본인 폰(S24 울트라) 전용**으로 안정화하는 단계. 배포용(가벼운 구성)은 나중.
- 목표: **인터넷 없이도** 폰 안의 오픈 모델로 듣기 → 한글 정리 → 번역 → 읽기. 정확도가 최우선, 그다음 속도.
- 기본 번역기는 폰 AI. Gemini와 무료 번역기(MyMemory)는 사용자가 고르는 선택 항목이자 실패 시 대체 경로.

## 2. 꼭 지킬 것 (사용자가 여러 번 강조)

- **웹앱(V4)의 기능을 빼지 말 것.** V4는 90번쯤 개선한 결과물. 안드로이드에서 정말 필요 없는 것만 뺀다. (한 번 "정리본"으로 기능을 덜어냈다가 전부 되돌린 일이 있음)
- `lsc571-max/travel` 저장소(동료들이 쓰는 웹앱)는 **읽기만**. 절대 수정·푸시하지 않는다.
- 사용자가 "수정하지 마", "듣기만 해"라고 하면 코드에 손대지 않고 목록만 모은다. "수정해", "만들어 줘"라고 할 때 반영한다.
- 답은 한국어, 휴대폰 화면에 맞게 짧게. 전문 용어는 풀어서.
- **실제 폰에서 확인하지 못한 것은 못 했다고 분명히 말한다.** (이 작업 환경에는 안드로이드 기기가 없다)
- 모델·API를 앱에 넣기 전에 **시험한 설정 그대로** 넣는다. (시험 때와 다른 요청을 넣어 폰에서 실패한 일이 두 번 있었음 — 아래 6번)

## 3. 저장소와 빌드

- 앱 저장소: `lsc571-max/travel-android` (공개), 브랜치 `main`
- 설치 파일: https://github.com/lsc571-max/travel-android/releases/latest/download/travel-interpreter.apk (덮어 설치, 받아 둔 모델 유지)
- `main`에 푸시하면 GitHub Actions(`.github/workflows/build.yml`)가 APK를 만들어 `latest` 릴리스에 올린다. `build` 작업과 `verify` 작업(실제 모델로 음성 인식 코드 시험, 모델 주소 확인)이 돈다.
- `eval` 브랜치: 후보 모델 시험용 워크플로(`eval/llm_eval.py`, `eval/stt_eval.py`). `probe` 브랜치: 예전 임시 가지(지울 권한이 없어 남아 있음).
- 작업 환경 제약: 셸에서 Hugging Face·Maven은 막혀 있음(403). GitHub 저장소 복제와 GitHub 릴리스 내려받기는 됨. HF 모델을 써야 하는 시험은 GitHub Actions에서 돌린다. `gh`는 REST(`gh api ...`)만 됨.

## 4. 구조

- 자바만 쓰는 WebView 껍데기 (`app/src/main/java/kr/pureun/travel/`, AndroidX·코틀린 없음). 화면은 `assets/index.html`을 `https://app.travel.local/`로 띄운다.
- `assets/native.js`: 웹 API를 안드로이드로 잇는 다리. `SpeechRecognition`(폰 안 인식/구글 인식 자동 선택), `speechSynthesis`, 공유·복사·화면 켜짐 유지, `window.NAT`(`NAT.llm`, `NAT.stt`, `NAT.pcm`, `NAT.playing`).
- 자바 쪽
  - `LlmEngine`: llama.cpp `llama-server`(태그 b12367, NDK로 빌드해 `libllama_server.so`로 포함)를 하위 프로세스로 띄우고 `/v1/chat/completions` 호출. 문맥 4096, 스레드 6.
  - `SttCore`(순수 자바, PC에서도 시험 가능) + `LocalStt`: sherpa-onnx v2.0.1 + silero VAD로 마이크를 끄지 않고 듣기. 문장이 끝나면 한 번만 받아 적음(임시 받아 적기 없음).
  - `ModelStore`: 모델 목록·내려받기(HF, 이어받기)·선택. `kind`: mt/stt, `type`: chat(정리+번역) / gguf(번역 전용) / whisper / sensevoice.
  - `MicService`(듣는 동안), `PlayService`(읽는 동안): 화면이 꺼져도 계속하기 위한 전경 서비스.
  - `Bridge`: JS ↔ 자바.
- **화면(index.html)은 직접 고치지 않는다.** 웹앱 V4 원본에 `tools/patch_v4.py`가 변경을 얹어 만든다.
  ```
  git clone https://github.com/lsc571-max/travel   # 읽기 전용, index.html = V4
  python3 tools/patch_v4.py travel/index.html app/src/main/assets/index.html
  node tools/smoke_v4.js app/src/main/assets app    # jsdom 필요. 가짜 휴대폰 다리로 화면 동작 시험 (현재 30개쯤, 모두 통과)
  ```
  `patch_v4.py`는 `tools/patch_native.py`, `tools/patch_a2.py` 안의 코드 조각을 가져다 쓰므로 세 파일을 같이 둔다. 변경은 `rep()`(정확히 한 번 일치해야 함)로 넣으므로, 웹앱이 바뀌면 일치 실패로 바로 드러난다.

## 5. 지금 들어 있는 것 (A8)

- V4 기능 전체: 대화/듣기/녹음 모드, 듣기 묶음 시간(20초~10분), 사진·PDF 통역, 자료·문장 서랍, 고급 설정(키 받으러 가기·AI 사용량·무음 빼기·받아쓰기 정리 기록), "○○자 · ○초" 표시 등
- 뺀 것: "인터넷 연결 없음" 문구, 설치 띠·전체 화면·당겨서 새 버전(웹 전용), 기본 용어(금형 등 — 빈 상태로 시작), 관리자 메뉴의 웹 올리기 링크(앱 링크로 교체)
- 폰 안 음성 인식: **Whisper turbo**(권장, 약 1GB) / small / SenseVoice
- 폰 AI: **Gemma 4 E4B**(정리+번역 한 번에, 5.15GB, 권장) / Gemma 4 E2B(빠름, 3.35GB) / Hy-MT2 1.8B(번역 전용)
  - 자료 서랍(관련 용어·요약)과 문장 서랍(비슷한 저장 문장)을 프롬프트에 넣음
  - 엉뚱한 답(용어 목록만 내는 등)은 버리고 규칙 정리 + 번역만 다시 시킴
- 번역기 선택: 폰 AI → Gemini 빠름/균형/정확 → 무료. 실패 시: 폰 AI → (키 있으면) Gemini 빠름 → 무료 / Gemini → 폰 AI → 무료
- 화면이 꺼져도 듣기(대화·듣기 모드, 폰 안 인식일 때), 읽는 중 화면이 꺼져도 끝까지 읽기, 5분 무음이면 마이크 끔
- 이어폰이면 통역 소리 중에도 듣기, 말한 사람 따라 하기(크기·속도·남녀)
- AI 음성(Gemini TTS, 다음 문장 미리 만들기), AI 통역사(Gemini Live Translate)

## 6. 시험으로 알게 된 것

- 음성 인식(한국어 낭독 25개, 글자 오류율): small 8.6% / medium 7.0% / **turbo 1.6%** / large-v3 0.9%(6배 느림). SenseVoice 2025-09-09판은 광둥어 특화라 한국어가 깨짐 → 2024-07-17판 사용.
- Whisper turbo는 소리 끝 여백이 짧으면 **같은 말을 되풀이**해 적음. 2~5초는 정상 문장에서도 되풀이, 6초부터 깨끗. 지금은 6초로 먼저 받아 적고 되풀이가 의심되면 10초로 한 번 더(`SttCore.decode`).
- 한글 정리(틀리게 받아 적힌 8문장): Gemma 4 E4B 8/8, E2B 8/8(정리만 시킬 때), Qwen3-4B 대체로, Kanana-2 3B 불안정, Hy-MT2 7B는 정리 못 함.
- 정리+번역 한 번에: E4B는 좋음, E2B는 없는 말을 보태거나 용어 목록을 그대로 내는 실수가 있었음.
- Hy-MT2는 용어를 자료 없이 번역하면 틀림(보압 → 圧力). 용어·자료를 넣어 주면 맞음.
- **Gemma 4는 "생각하기"를 꺼야 한다**: 요청에 `chat_template_kwargs:{enable_thinking:false}`를 넣지 않으면 생각만 하다 답이 빈다. (A4·A5에서 이게 빠져 폰에서 번역이 전부 실패했음. A6에서 수정)
- 폰에서 사용자가 잰 시간: Gemma E4B 문장당 4~5초, E2B 2.5~4.5초.

## 7. 아직 확인되지 않았거나 남은 문제

- **AI 통역사**: A7까지 누르면 "연결이 끊겼습니다 · INV…"로 바로 꺼짐. 서버가 setup을 거부하는 것으로 추정(`inputAudioTranscription`/`outputAudioTranscription`의 위치). A8에서 세 가지 형식을 차례로 시도하게 했으나 **실제 Gemini로는 한 번도 확인하지 못함**. 사용자가 A8에서 빨간 글씨 전체 문구(누르면 복사 가능)를 알려 주면 그걸로 확정할 것. 공식 문서: ai.google.dev/gemini-api/docs/live-api/live-translate
- AI 음성 문장 사이 5초 쉼: A8에서 미리 만들기로 고쳤으나 폰에서 미확인.
- 받아 적는 시간: A8에서 조금 줄였을 뿐(시험상 문장당 4분의 1쯤). 사용자는 여전히 느리다고 느낄 수 있음.
- 대화 모드 "자동"에서 1초짜리 짧은 말은 언어를 잘못 고를 수 있음(시험에서 한국어를 영어로 판단).
- Gemma 4의 배포 조건(라이선스)은 확인하지 않음. 남에게 나눠 주기 전에 확인.

## 8. 하기로 했지만 아직 안 한 것

1. 속도: 역할 나누기(한글 정리 Gemma + 번역 Hy-MT를 고를 수 있게), 번역을 쓰는 대로 보여 주고 읽기, GPU 가속 검토
2. 대화 모드에서 조각내지 않고 말 전체를 한 번에 받아 적기
3. 안 쓰는 모델을 목록에서 빼기(본인 폰 전용으로 안정되면)
4. 2단계: 사진·PDF·녹음 받아쓰기를 폰 안에서(글자 읽기는 ML Kit 후보)
5. 배포용 가벼운 구성
