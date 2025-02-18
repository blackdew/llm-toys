# 타이핑 연습 앱

실시간으로 타이핑 정확도와 속도를 측정할 수 있는 웹 기반 타이핑 연습 애플리케이션입니다.

## 주요 기능

### 1. 다양한 연습 모드
- **직접 입력**: 사용자가 원하는 텍스트를 직접 입력하여 연습
- **AI 생성 문장**: GPT를 활용한 한국어/영어 연습 문장 자동 생성
- **파일 업로드**: 텍스트 파일(.txt)을 업로드하여 연습

### 2. 실시간 통계
- 진행률
- 전체 단어 수
- 정확한 단어 수
- 틀린 단어 수
- 분당 타자 속도(WPM)

### 3. 사용자 친화적 UI
- 실시간 타이핑 피드백
- 직관적인 진행 상황 표시
- 반응형 디자인

## 설치 및 실행

1. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

2. OpenAI API 키 설정 (AI 생성 문장 모드 사용 시)
```bash
export OPENAI_API_KEY='your-api-key'
```

3. 앱 실행
```bash
streamlit run main.py
```

## 기술 스택
- Python
- Streamlit
- OpenAI API
- JavaScript
- CSS

## 프로젝트 구조
```
typing/
├── main.py           # 메인 애플리케이션
├── config.py         # 설정 관리
├── typing_manager.py # 타이핑 로직 관리
├── static/
│   ├── styles.css   # 스타일시트
│   └── typing.js    # 실시간 타이핑 체크
└── README.md
```

## 라이선스
MIT License 