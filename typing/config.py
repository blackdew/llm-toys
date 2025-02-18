"""타이핑 앱 설정"""

# 기본 문장 설정
DEFAULT_SENTENCES = """타이핑 연습을 하는 어플입니다.
모드를 선택하고, 
연습할 문장을 넣어주세요.
한 문장씩 연습할 수 있습니다."""

# 입력 모드 설정
INPUT_MODES = {
    "options": ["직접 입력", "AI 생성 문장", "파일 업로드"],
    "default": "직접 입력"
}

# AI 생성 설정
AI_CONFIG = {
    "model": "gpt-3.5-turbo",
    "temperature": 1.2,
    "max_tokens": 200,
    "sentences_per_set": 5,
    "languages": ["한국어", "English"],
    "default_language": "한국어",
    "prompts": {
        "한국어": """
        다음 조건을 만족하는 {num_sentences}개의 한국어 문장을 생성해주세요:
        - 개인의 성장과 통찰을 담은 표현
        - 각 문장은 7-12개 단어로 구성
        - 다양한 주제 (자기계발, 새로운 기술, 인생의 지혜 등)
        - 영감을 주는 긍정적인 메시지 포함
        - 실용적인 조언이나 지식을 담을 것
        - 각 문장은 새로운 줄에 작성
        - 문장 앞에 번호를 붙이지 말 것
        """,
        "English": """
        Generate {num_sentences} English sentences that meet these criteria:
        - Expressions containing personal growth and insights
        - Each sentence should have 7-12 words
        - Various topics (self-improvement, new technologies, life wisdom)
        - Include inspiring and positive messages
        - Contain practical advice or knowledge
        - Write each sentence on a new line
        - Don't add numbers before sentences
        """
    }
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
    "page_layout": "wide",
    "font_size": {
        "target_text": "24px",
        "input_text": "18px",
        "stats": "16px"
    },
    "colors": {
        "correct": "#28a745",
        "incorrect": "#dc3545",
        "background": "#f8f9fa"
    },
    "padding": {
        "target_text": "20px",
        "stats_item": "10px"
    }
}

# CSS 클래스 이름
CSS_CLASSES = {
    "word": "word",
    "correct": "correct",
    "incorrect": "incorrect",
    "target_text": "target-text"
} 