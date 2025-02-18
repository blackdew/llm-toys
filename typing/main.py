import time
import os
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
from typing_manager import TypingManager, TypingStats
from config import (
    DEFAULT_SENTENCES,
    INPUT_MODES,
    AI_CONFIG,
    FILE_CONFIG,
    UI_CONFIG,
    CSS_CLASSES
)

def load_template(template_path: str) -> str:
    """HTML 템플릿 파일을 로드합니다."""
    return Path(template_path).read_text(encoding='utf-8')

def process_input_text(text: str) -> List[str]:
    """입력된 텍스트를 문장 리스트로 변환합니다."""
    return [line.strip() for line in text.split('\n') if line.strip()]

def load_javascript() -> str:
    """JavaScript 코드를 별도 파일에서 로드합니다."""
    return Path('static/typing.js').read_text(encoding='utf-8')

def load_styles():
    """스타일을 로드합니다."""
    # main.py 파일이 있는 디렉토리를 기준으로 static 폴더 접근
    css_path = Path(__file__).parent / 'static' / 'styles.css'
    css_content = css_path.read_text()
    
    css_vars = f"""
    <style>
    :root {{
        --target-text-font-size: {UI_CONFIG["font_size"]["target_text"]};
        --input-text-font-size: {UI_CONFIG["font_size"]["input_text"]};
        --stats-font-size: {UI_CONFIG["font_size"]["stats"]};
        --correct-color: {UI_CONFIG["colors"]["correct"]};
        --incorrect-color: {UI_CONFIG["colors"]["incorrect"]};
        --background-color: {UI_CONFIG["colors"]["background"]};
        --target-text-padding: {UI_CONFIG["padding"]["target_text"]};
        --stats-item-padding: {UI_CONFIG["padding"]["stats_item"]};
        --border-radius: {UI_CONFIG["border_radius"]};
    }}
    {css_content}
    </style>
    """
    
    st.markdown(css_vars, unsafe_allow_html=True)

def initialize_session_state():
    """세션 상태를 초기화합니다."""
    if 'current_sentence_index' not in st.session_state:
        st.session_state.current_sentence_index = 0
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0
    if 'current_sentences' not in st.session_state:
        st.session_state.current_sentences = []
    if 'total_sentences_completed' not in st.session_state:
        st.session_state.total_sentences_completed = 0
    if 'current_input_method' not in st.session_state:
        st.session_state.current_input_method = INPUT_MODES["default"]
    if 'practice_started' not in st.session_state:
        st.session_state.practice_started = False
    
    # TypingManager 추가
    if 'typing_manager' not in st.session_state:
        manager = TypingManager()
        if 'current_sentences' in st.session_state:
            manager.current_sentences = st.session_state.current_sentences
            manager.current_index = st.session_state.current_sentence_index
            manager.total_sentences_completed = st.session_state.total_sentences_completed
            manager.input_key = st.session_state.input_key
        st.session_state.typing_manager = manager

    # 인덱스가 범위를 벗어났는지 확인하고 수정
    if (st.session_state.current_sentence_index >= len(st.session_state.current_sentences) or 
        st.session_state.current_sentence_index < 0):
        st.session_state.current_sentence_index = 0

def display_progress(current_index: int, total_completed: int, total_sentences: int):
    """진행 상황을 표시합니다."""
    current = current_index + 1 + total_completed
    total = total_sentences + total_completed
    progress_pct = (current / total) * 100 if total > 0 else 0
    
    st.progress(progress_pct / 100)
    st.markdown(
        f"<div style='text-align: center; margin-bottom: 20px;'>"
        f"<h3>진행률: {current} / {total} ({progress_pct:.1f}%)</h3>"
        f"</div>",
        unsafe_allow_html=True
    )

def display_typing_stats(stats: Dict[str, float]):
    """타이핑 통계를 표시합니다."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="단어",
            value=f"{int(stats['correct_words'])} / {int(stats['total_words'])}",
            delta=f"{stats['accuracy']:.1f}% 정확도"
        )
    
    with col2:
        st.metric(
            label="오타",
            value=int(stats['incorrect_words']),
            delta="틀린 단어 수",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="타자 속도",
            value=f"{stats['wpm']:.1f}",
            delta="WPM (분당 단어 수)"
        )

def display_sentence(sentence: str):
    """현재 문장을 표시합니다."""
    words_html = ' '.join([
        f'<span class="{CSS_CLASSES["word"]}" id="word-{i}">{word}</span>' 
        for i, word in enumerate(sentence.split())
    ])
    st.markdown(
        f'<div class="{CSS_CLASSES["target_text"]}">{words_html}</div>', 
        unsafe_allow_html=True
    )

def display_welcome_message(mode: str):
    """모드별 환영 메시지를 표시합니다."""
    messages = {
        "직접 입력": {
            "title": "직접 입력 연습",
            "description": "연습할 텍스트를 입력하고 '연습시작' 버튼을 클릭하여 시작하세요.",
            "sub_text": "각 줄이 하나의 문장으로 처리됩니다."
        },
        "AI 생성 문장": {
            "title": "AI 생성 문장 연습",
            "description": "원하는 언어를 선택하고 '연습시작' 버튼을 클릭하여 시작하세요.",
            "sub_text": "한 번에 5개의 문장이 생성되며, 자동으로 다음 문장 세트가 생성됩니다."
        },
        "파일 업로드": {
            "title": "파일 업로드 연습",
            "description": "텍스트 파일(.txt)을 업로드하고 '연습시작' 버튼을 클릭하여 시작하세요.",
            "sub_text": "시작 위치와 연습할 문장 수를 설정할 수 있습니다."
        }
    }
    
    msg = messages[mode]
    st.markdown(f"""
        <div style='text-align: center; padding: 50px;'>
            <h2>{msg["title"]}</h2>
            <p>{msg["description"]}</p>
            <p>{msg["sub_text"]}</p>
        </div>
    """, unsafe_allow_html=True)

def handle_input(current_sentence: str):
    """입력을 처리하고 상태를 업데이트합니다."""
    if 'input_key' not in st.session_state:
        return

    input_key = f"typing_input_{st.session_state.input_key}"
    if input_key not in st.session_state:
        return

    input_text = st.session_state[input_key]
    if not input_text:
        return

    # 타이핑 매니저를 통한 입력 처리
    if st.session_state.typing_manager.handle_input(input_text):
        # AI 생성 문장 모드에서 새로운 문장 세트 생성
        if (st.session_state.current_input_method == "AI 생성 문장" and 
            st.session_state.typing_manager.current_index == 0):
            new_sentences = generate_practice_sentences(
                st.session_state.get('current_language', '한국어'), 
                num_sentences=5
            )
            st.session_state.typing_manager.load_sentences(new_sentences)
            st.session_state.current_sentences = new_sentences

        # 상태 업데이트
        st.session_state.current_sentence_index = st.session_state.typing_manager.current_index
        st.session_state.input_key = st.session_state.typing_manager.input_key
        st.session_state.total_sentences_completed = st.session_state.typing_manager.total_sentences_completed
        
        # 새 입력창 초기화
        st.session_state[f"typing_input_{st.session_state.input_key}"] = ""

def generate_practice_sentences(language: str, num_sentences: int = 4) -> List[str]:
    """ChatGPT를 사용하여 타이핑 연습 문장을 생성합니다."""
    client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY")))
    
    if language == "한국어":
        prompt = f"""
        다음 조건을 만족하는 {num_sentences}개의 한국어 문장을 생성해주세요:
        - 일상적이고 자연스러운 표현
        - 각 문장은 5-10개 단어로 구성
        - 다양한 주제 (일상, 직장, 취미 등)
        - 각 문장은 새로운 줄에 작성
        - 문장 앞에 번호를 붙이지 말 것
        """
    else:  # 영어
        prompt = f"""
        Generate {num_sentences} English sentences that meet these criteria:
        - Natural everyday expressions
        - Each sentence should have 5-10 words
        - Various topics (daily life, work, hobbies, etc.)
        - Write each sentence on a new line
        - Don't add numbers before sentences
        """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        
        # 응답에서 문장들을 추출하고 처리
        sentences = response.choices[0].message.content.strip().split('\n')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences[:num_sentences]  # 요청한 개수만큼만 반환
        
    except Exception as e:
        st.error(f"문장 생성 중 오류가 발생했습니다: {str(e)}")
        # 오류 시 기본 문장 반환
        return process_input_text(get_default_text())

def get_default_text() -> str:
    """기본 연습 문장들을 문자열로 반환합니다."""
    return DEFAULT_SENTENCES

def main():
    st.set_page_config(layout=UI_CONFIG["page_layout"])
    initialize_session_state()
    
    # 스타일 로드
    load_styles()
    
    # 입력 방식 선택
    input_method = st.sidebar.radio(
        "모드 선택",
        INPUT_MODES["options"],
        index=INPUT_MODES["options"].index(INPUT_MODES["default"])
    )

    # 입력 방식이 변경되면 상태 초기화
    if st.session_state.current_input_method != input_method:
        st.session_state.current_input_method = input_method
        st.session_state.typing_manager.set_input_method(input_method)
        st.session_state.current_sentence_index = 0
        st.session_state.input_key = 0
        st.session_state.total_sentences_completed = 0
        st.session_state.current_sentences = []
        st.session_state.practice_started = False

    # 각 모드별 설정
    sentences = []  # 초기화

    if input_method == "직접 입력":
        text_input = st.sidebar.text_area(
            "연습할 문장 입력 (줄바꿈으로 구분)",
            value=DEFAULT_SENTENCES,
            height=UI_CONFIG["text_area_height"]
        )

    elif input_method == "AI 생성 문장":
        language = st.sidebar.selectbox(
            "언어 선택",
            AI_CONFIG["languages"],
            index=AI_CONFIG["languages"].index(AI_CONFIG["default_language"])
        )

    elif input_method == "파일 업로드":
        uploaded_file = st.sidebar.file_uploader(
            "텍스트 파일(.txt)",
            type=FILE_CONFIG["allowed_types"],
            key="file_uploader"
        )

        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_line = st.number_input(
                "시작 문장",
                min_value=FILE_CONFIG["default_start_line"],
                value=FILE_CONFIG["default_start_line"],
                help="시작할 문장의 위치 (0부터 시작)",
                label_visibility="collapsed"
            )
            st.caption("시작 문장")
            
        with col2:
            lines_per_set = st.number_input(
                "문장 수",
                min_value=FILE_CONFIG["min_sentences"],
                max_value=FILE_CONFIG["max_sentences"],
                value=FILE_CONFIG["default_sentences"],
                help="연습할 문장의 수",
                label_visibility="collapsed"
            )
            st.caption("문장 수")

    # 공통 연습 시작 버튼
    st.sidebar.markdown("---")
    if st.sidebar.button("연습 시작", use_container_width=True):
        # 타이핑 매니저 초기화
        st.session_state.typing_manager.reset_all()

        if input_method == "직접 입력":
            if text_input:
                sentences = process_input_text(text_input)
                st.session_state.typing_manager.load_sentences(sentences)
                st.session_state.current_sentences = sentences
                st.session_state.practice_started = True
            else:
                st.sidebar.warning("텍스트를 입력해주세요.")
                return

        elif input_method == "AI 생성 문장":
            with st.spinner(f"{language} 문장을 생성하는 중..."):
                sentences = generate_practice_sentences(language, num_sentences=5)
                st.session_state.typing_manager.load_sentences(sentences)
                st.session_state.current_sentences = sentences
                st.session_state.practice_started = True

        else:  # 파일 업로드
            if not uploaded_file:
                st.sidebar.warning("파일을 업로드해주세요.")
                return
                
            text_content = uploaded_file.getvalue().decode('utf-8')
            all_sentences = process_input_text(text_content)
            start_line = min(start_line, len(all_sentences))
            
            end_line = start_line + lines_per_set
            sentences = all_sentences[start_line:end_line]
            st.session_state.typing_manager.load_sentences(sentences)
            st.session_state.current_sentences = sentences
            st.session_state.practice_started = True

        # 공통 초기화
        st.session_state.current_sentence_index = 0
        st.session_state.input_key = 0
        st.session_state.total_sentences_completed = 0

    # 연습이 시작되지 않았으면 환영 메시지만 표시
    if not st.session_state.practice_started:
        display_welcome_message(input_method)
        return

    # 연습이 시작되었으면 타이핑 UI 표시
    sentences = st.session_state.current_sentences
    if not sentences:
        return

    current_sentence = sentences[st.session_state.current_sentence_index]
    display_sentence(current_sentence)
    
    # 진행률과 통계 표시
    display_progress(
        st.session_state.current_sentence_index,
        st.session_state.total_sentences_completed,
        len(sentences)
    )
    display_typing_stats(st.session_state.typing_manager.stats.to_dict())

    # JavaScript 실시간 체크
    js_path = Path(__file__).parent / 'static' / 'typing.js'
    js_code = js_path.read_text()
    components.html(
        f"""
        <script>
        {js_code}
        </script>
        """,
        height=0
    )
    
    # 입력창
    st.text_input(
        "Type the text above",
        key=f"typing_input_{st.session_state.input_key}",
        label_visibility="collapsed",
        on_change=lambda: handle_input(current_sentence)
    )

if __name__ == "__main__":
    main()
