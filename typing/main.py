import time
import json
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class TypingStats:
    def __init__(self):
        self.total_words = 0
        self.correct_words = 0
        self.incorrect_words = 0
        self.start_time = time.time()
        self.elapsed_times = []  # 각 문장별 소요 시간 저장

    def update(self, input_words: List[str], target_words: List[str]):
        # 현재 문장 완료 시간 기록
        elapsed = time.time() - self.start_time
        self.elapsed_times.append(elapsed)
        
        # 다음 문장을 위한 시작 시간 초기화
        self.start_time = time.time()
        
        self.total_words += len(target_words)
        
        # 입력된 단어 체크
        for i, word in enumerate(input_words):
            if i < len(target_words):
                if word == target_words[i]:
                    self.correct_words += 1
                else:
                    self.incorrect_words += 1
            else:
                self.incorrect_words += 1
        
        # 누락된 단어 처리
        if len(input_words) < len(target_words):
            self.incorrect_words += (len(target_words) - len(input_words))

    def get_wpm(self) -> float:
        """평균 분당 타자 속도를 계산합니다."""
        if not self.elapsed_times:
            return 0.0
        
        total_time_minutes = sum(self.elapsed_times) / 60
        if total_time_minutes == 0:
            return 0.0
            
        return round(self.total_words / total_time_minutes, 1)

    def to_dict(self) -> Dict[str, int]:
        return {
            'total_words': self.total_words,
            'correct_words': self.correct_words,
            'incorrect_words': self.incorrect_words,
            'wpm': self.get_wpm()
        }

def load_template(template_path: str) -> str:
    """HTML 템플릿 파일을 로드합니다."""
    return Path(template_path).read_text(encoding='utf-8')

def load_default_sentences() -> List[str]:
    """기본 연습 문장들을 로드합니다."""
    return [
        "수고했어 오늘도 좋은 하루 보내세요",
        "타이핑 연습을 시작해 보겠습니다",
        "하나 둘 셋 넷 다섯 여섯 일곱",
        "오늘 날씨가 참 좋네요"
    ]

def process_input_text(text: str) -> List[str]:
    """입력된 텍스트를 문장 리스트로 변환합니다."""
    # 빈 줄 제거하고 각 줄을 문장으로 처리
    sentences = [line.strip() for line in text.split('\n') if line.strip()]
    return sentences

def load_javascript() -> str:
    """JavaScript 코드를 별도 파일에서 로드합니다."""
    return Path('static/typing.js').read_text(encoding='utf-8')

def load_styles() -> str:
    """CSS 스타일을 별도 파일에서 로드합니다."""
    return Path('static/styles.css').read_text(encoding='utf-8')

def initialize_session_state():
    """세션 상태를 초기화합니다."""
    if 'current_sentence_index' not in st.session_state:
        st.session_state.current_sentence_index = 0
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0
    if 'stats' not in st.session_state:
        st.session_state.stats = TypingStats()

def display_stats(stats: TypingStats, total_sentences: int):
    """통계를 표시합니다."""
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"**진행률:** {st.session_state.current_sentence_index + 1} / {total_sentences}")
    with col2:
        st.markdown(f"**전체 단어:** {stats.total_words}")
    with col3:
        st.markdown(f"**정확한 단어:** {stats.correct_words}")
    with col4:
        st.markdown(f"**틀린 단어:** {stats.incorrect_words}")
    with col5:
        st.markdown(f"**타자 속도:** {stats.get_wpm()} WPM")

def handle_input(current_sentence: str):
    """입력을 처리하고 상태를 업데이트합니다."""
    input_key = f"typing_input_{st.session_state.input_key}"
    if input_key not in st.session_state:
        return

    input_text = st.session_state[input_key]
    if not input_text:
        return

    # 통계 업데이트
    input_words = input_text.strip().split()
    target_words = current_sentence.split()
    st.session_state.stats.update(input_words, target_words)

    # 다음 문장으로 이동
    sentences = load_default_sentences()
    next_index = (st.session_state.current_sentence_index + 1) % len(sentences)
    st.session_state.current_sentence_index = next_index
    st.session_state.input_key += 1
    st.session_state[f"typing_input_{st.session_state.input_key}"] = ""

def main():
    # 페이지 설정
    st.set_page_config(layout="wide")
    initialize_session_state()
    
    # 스타일 적용
    st.markdown("""
        <style>
        .target-text {
            font-size: 24px;
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .stTextInput > div > div > input {
            font-size: 18px;
        }
        .correct {
            color: #28a745;
        }
        .incorrect {
            color: #dc3545;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin: 20px 0;
            font-size: 16px;
        }
        .stats-item {
            padding: 10px;
            border-radius: 5px;
            background-color: #f8f9fa;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 사이드바에 입력 방식 선택
    input_method = st.sidebar.radio(
        "연습할 텍스트 선택",
        ["기본 문장", "직접 입력", "파일 업로드"]
    )

    # 선택된 입력 방식에 따라 문장 로드
    if input_method == "기본 문장":
        sentences = load_default_sentences()
    elif input_method == "직접 입력":
        text_input = st.sidebar.text_area(
            "연습할 텍스트를 입력하세요 (각 줄이 하나의 문장이 됩니다)",
            height=200
        )
        if text_input:
            sentences = process_input_text(text_input)
            # 새로운 텍스트가 입력되면 세션 상태 초기화
            if 'current_text' not in st.session_state or st.session_state.current_text != text_input:
                st.session_state.current_text = text_input
                st.session_state.current_sentence_index = 0
                st.session_state.input_key = 0
                st.session_state.stats = TypingStats()
        else:
            sentences = load_default_sentences()
    else:  # 파일 업로드
        uploaded_file = st.sidebar.file_uploader("텍스트 파일을 업로드하세요", type=['txt'])
        if uploaded_file:
            text_content = uploaded_file.getvalue().decode('utf-8')
            sentences = process_input_text(text_content)
            # 새로운 파일이 업로드되면 세션 상태 초기화
            if 'current_file' not in st.session_state or st.session_state.current_file != uploaded_file.name:
                st.session_state.current_file = uploaded_file.name
                st.session_state.current_sentence_index = 0
                st.session_state.input_key = 0
                st.session_state.stats = TypingStats()
        else:
            sentences = load_default_sentences()

    # 문장이 비어있으면 기본 문장 사용
    if not sentences:
        st.sidebar.warning("텍스트가 비어있어 기본 문장을 사용합니다.")
        sentences = load_default_sentences()

    current_sentence = sentences[st.session_state.current_sentence_index]
    
    # 통계 표시
    display_stats(st.session_state.stats, len(sentences))
    
    # 현재 문장 표시
    words_html = ' '.join([
        f'<span class="word" id="word-{i}">{word}</span>' 
        for i, word in enumerate(current_sentence.split())
    ])
    st.markdown(f'<div class="target-text">{words_html}</div>', unsafe_allow_html=True)
    
    # 실시간 타이핑 체크와 자동 포커스를 위한 JavaScript
    check_script = """
    <script>
        function cleanText(text) {
            return text.trim().replace(/\\s+/g, ' ');
        }

        function checkTyping() {
            const doc = window.parent.document;
            const input = doc.querySelector('input[type="text"]');
            const words = doc.querySelectorAll('.word');
            
            if (!input) return;
            
            const inputWords = cleanText(input.value).split(' ');
            
            words.forEach(word => {
                word.classList.remove('correct', 'incorrect');
            });
            
            inputWords.forEach((word, i) => {
                if (i < words.length) {
                    const targetWord = cleanText(words[i].textContent);
                    const inputWord = cleanText(word);
                    if (inputWord === targetWord) {
                        words[i].classList.add('correct');
                    } else if (inputWord) {
                        words[i].classList.add('incorrect');
                    }
                }
            });
        }

        let lastInputValue = '';

        function setupTypingInput() {
            const doc = window.parent.document;
            const input = doc.querySelector('input[type="text"]');
            
            if (!input) return;
            
            // 새로운 입력창 감지 (value가 빈 문자열인 경우)
            if (input.value === '' && lastInputValue !== '') {
                lastInputValue = '';
                
                // 이벤트 리스너 설정
                if (!input.dataset.hasTypingListener) {
                    input.addEventListener('input', checkTyping);
                    input.addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            const submitBtn = doc.querySelector('button[kind="primaryFormSubmit"]');
                            if (submitBtn) submitBtn.click();
                        }
                    });
                    input.dataset.hasTypingListener = 'true';
                }
                
                // 새 문장이 나타났을 때 포커스
                setTimeout(() => input.focus(), 100);
            }
            
            lastInputValue = input.value;
        }

        // 주기적으로 체크
        setInterval(() => {
            checkTyping();
            setupTypingInput();
        }, 100);

        // 초기 설정
        setupTypingInput();
    </script>
    """
    
    components.html(check_script, height=0)
    
    # 입력창
    st.text_input(
        "Type the text above",
        key=f"typing_input_{st.session_state.input_key}",
        label_visibility="collapsed",
        on_change=lambda: handle_input(current_sentence)
    )

    # 사이드바에 현재 진행 상황 표시
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**현재 진행 상황**")
    st.sidebar.markdown(f"전체 문장 수: {len(sentences)}")
    st.sidebar.markdown(f"현재 문장: {st.session_state.current_sentence_index + 1}")

if __name__ == "__main__":
    main()
