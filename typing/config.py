"""타이핑 앱 설정"""

# 기본 문장 설정
DEFAULT_SENTENCES = """수고했어 오늘도 좋은 하루 보내세요
타이핑 연습을 시작해 보겠습니다
하나 둘 셋 넷 다섯 여섯 일곱
오늘 날씨가 참 좋네요"""

# 입력 모드 설정
INPUT_MODES = {
    "options": ["직접 입력", "AI 생성 문장", "파일 업로드"],
    "default": "직접 입력"
}

# AI 생성 설정
AI_CONFIG = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 200,
    "sentences_per_set": 5,
    "languages": ["한국어", "English"],
    "default_language": "한국어"
}

# 파일 업로드 설정
FILE_CONFIG = {
    "allowed_types": ["txt"],
    "default_start_line": 0,
    "min_sentences": 1,
    "max_sentences": 50,
    "default_sentences": 10
}

# UI 설정
UI_CONFIG = {
    "text_area_height": 200,
    "input_area_height": 100,
    "page_layout": "wide"
}

# CSS 클래스 이름
CSS_CLASSES = {
    "word": "word",
    "correct": "correct",
    "incorrect": "incorrect",
    "target_text": "target-text",
    "text_display": "text-display"
} 