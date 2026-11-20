# 웹앱(V4) → 안드로이드 화면 만들기

`app/src/main/assets/index.html` 은 웹앱(travel 저장소의 index.html, V4)을 그대로 바탕으로,
아래 스크립트가 안드로이드용 변경만 얹어서 만든 파일입니다. 웹앱이 새 버전이 되면 같은 방법으로 다시 만들 수 있습니다.

    python3 tools/patch_v4.py <웹앱 index.html> app/src/main/assets/index.html
    node tools/smoke_v4.js app/src/main/assets app     # 화면 자동 시험 (jsdom 필요)
    node tools/check_a26.js app/src/main/assets .      # A26 검토 수정 재현 시험

- patch_v4.py: 변경 내용 전체 (patch_native.py · patch_a2.py 의 코드 조각을 가져다 씀)
- 빼는 것: 무료 번역기, 여행 문구, 대화 모드 자동, 화면 어둡게, "인터넷 연결 없음" 문구, 웹 전용(설치 띠·전체 화면·당겨서 새 버전), 기본 용어 (A11 기준 — 자세한 것은 HANDOFF.md)
- 얹는 것: 폰 안 번역 AI, 폰 안 음성 인식(끊기지 않는 마이크), AI 음성, AI 통역사, 화면 꺼도 듣기, 이어폰, 말한 사람 따라 하기
