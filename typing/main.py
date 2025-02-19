import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
from typing_manager import TypingManager
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

def load_javascript() -> str:
    """JavaScript 코드를 별도 파일에서 로드합니다."""
    return Path('static/typing.js').read_text(encoding='utf-8')

def load_styles():
    """CSS 스타일을 로드합니다."""
    st.markdown(f"""
        <style>
        :root {{
            --correct-color: #28a745;
            --incorrect-color: #dc3545;
            --background-color: #f8f9fa;
        }}
        
        .{CSS_CLASSES["word"]} {{
            display: inline-block;
            margin-right: 0.5em;
        }}
        
        .{CSS_CLASSES["correct"]} {{
            color: var(--correct-color);
        }}
        
        .{CSS_CLASSES["incorrect"]} {{
            color: var(--incorrect-color);
            text-decoration: underline;
        }}
        
        .{CSS_CLASSES["target_text"]} {{
            background-color: var(--background-color);
            padding: {UI_CONFIG["padding"]["target_text"]};
            font-size: {UI_CONFIG["font_size"]["target_text"]};
            border-radius: 5px;
            margin-bottom: 1em;
        }}
        </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """세션 상태를 초기화합니다."""
    if 'typing_manager' not in st.session_state:
        st.session_state.typing_manager = TypingManager()
        st.session_state.typing_manager.set_input_method(INPUT_MODES["default"])
        st.session_state.practice_started = False
        st.session_state.current_input_method = INPUT_MODES["default"]
        st.session_state.input_key = 0  # input_key도 초기화
    
    # 나머지 상태는 typing_manager에서 관리
    update_session_state(st.session_state.typing_manager)

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
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="단어",
            value=f"{int(stats.get('correct_words', 0))} / {int(stats.get('total_words', 0))}",
            delta=f"{stats.get('accuracy', 0.0):.1f}% 정확도"
        )
    
    with col2:
        st.metric(
            label="오타",
            value=int(stats.get('incorrect_words', 0)),
            delta="틀린 단어 수",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="분당 단어 수",
            value=f"{stats.get('wpm', 0.0):.1f}",
            delta="WPM"
        )
    
    with col4:
        st.metric(
            label="분당 타자 수",
            value=f"{stats.get('cpm', 0.0):.1f}",
            delta="CPM"
        )

def display_sentence(sentence: str):
    """현재 문장을 표시합니다."""
    words_html = ' '.join([
        f'<span class="{CSS_CLASSES["word"]}" id="word-{i}">{word}</span>' 
        for i, word in enumerate(sentence.split())
    ])
    st.markdown(
        f'<div class="{CSS_CLASSES["target_text"]}" '
        f'style="padding: {UI_CONFIG["padding"]["target_text"]}; '
        f'font-size: {UI_CONFIG["font_size"]["target_text"]};">'
        f'{words_html}</div>',
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
                st.session_state.current_language,  # 현재 선택된 언어 사용
                num_sentences=AI_CONFIG["sentences_per_set"]
            )
            st.session_state.typing_manager.load_sentences(new_sentences)
            st.session_state.current_sentences = new_sentences

        # 상태 업데이트
        st.session_state.current_sentence_index = st.session_state.typing_manager.current_index
        st.session_state.input_key = st.session_state.typing_manager.input_key
        st.session_state.stats = st.session_state.typing_manager.stats
        st.session_state.total_sentences_completed = st.session_state.typing_manager.total_sentences_completed

def generate_practice_sentences(language: str, num_sentences: int = 5) -> List[str]:
    """AI를 사용하여 연습 문장을 생성합니다."""
    client = OpenAI()
    
    prompt = AI_CONFIG["prompts"][language].format(num_sentences=num_sentences)
    
    response = client.chat.completions.create(
        model=AI_CONFIG["model"],
        temperature=AI_CONFIG["temperature"],
        max_tokens=AI_CONFIG["max_tokens"],
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    text = response.choices[0].message.content
    return st.session_state.typing_manager.process_input_text(text)

def get_default_text() -> str:
    """기본 연습 문장들을 문자열로 반환합니다."""
    return DEFAULT_SENTENCES

def update_session_state(typing_manager: TypingManager):
    """세션 상태를 타이핑 매니저의 상태로 업데이트합니다."""
    st.session_state.current_sentence_index = typing_manager.current_index
    st.session_state.input_key = typing_manager.input_key
    st.session_state.total_sentences_completed = typing_manager.total_sentences_completed
    st.session_state.current_sentences = typing_manager.current_sentences

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
            "연습할 문장 입력 또는 URL 붙여넣기",
            value=DEFAULT_SENTENCES,
            height=UI_CONFIG["text_area_height"],
            help="웹 페이지 URL을 입력하면 해당 페이지의 내용을 가져옵니다."
        )

    elif input_method == "AI 생성 문장":
        language = st.sidebar.selectbox(
            "언어 선택",
            AI_CONFIG["languages"],
            index=AI_CONFIG["languages"].index(AI_CONFIG["default_language"])
        )
        # 선택된 언어를 session_state에 저장
        st.session_state.current_language = language

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
                try:
                    with st.spinner("텍스트 처리 중..."):
                        sentences = st.session_state.typing_manager.process_input_text(text_input)
                        if sentences:
                            st.session_state.typing_manager.load_sentences(sentences)
                            st.session_state.current_sentences = sentences
                            st.session_state.practice_started = True
                        else:
                            st.sidebar.warning("처리할 텍스트가 없습니다.")
                except ValueError as e:
                    st.sidebar.error(str(e))
                except Exception as e:
                    st.sidebar.error(f"오류가 발생했습니다: {str(e)}")

        elif input_method == "AI 생성 문장":
            with st.spinner(f"{language} 문장을 생성하는 중..."):
                sentences = generate_practice_sentences(language, num_sentences=AI_CONFIG["sentences_per_set"])
                st.session_state.typing_manager.load_sentences(sentences)
                st.session_state.current_sentences = sentences
                st.session_state.practice_started = True
                st.session_state.current_language = language  # 현재 언어 저장

        else:  # 파일 업로드
            if not uploaded_file:
                st.sidebar.warning("파일을 업로드해주세요.")
                return
                
            text_content = uploaded_file.getvalue().decode('utf-8')
            all_sentences = st.session_state.typing_manager.process_input_text(text_content)
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
