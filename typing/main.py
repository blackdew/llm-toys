import time
import os
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from typing import List, Dict
from openai import OpenAI

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
        "타이핑 연습을 하는 어플입니다.",
        "문장을 연습할 문장을 넣어주세요.",
        "한 문장씩 연습할 수 있습니다."
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
    if 'current_sentences' not in st.session_state:
        st.session_state.current_sentences = process_input_text(get_default_text())

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
    if 'input_key' not in st.session_state:
        return

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
    sentences = st.session_state.current_sentences  # 현재 사용 중인 문장 세트 사용
    next_index = (st.session_state.current_sentence_index + 1) % len(sentences)
    st.session_state.current_sentence_index = next_index
    st.session_state.input_key += 1
    st.session_state[f"typing_input_{st.session_state.input_key}"] = ""

def generate_practice_sentences(language: str, num_sentences: int = 4) -> List[str]:
    """ChatGPT를 사용하여 타이핑 연습 문장을 생성합니다."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
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
    return """타이핑 연습을 하는 어플입니다.
문장을 연습할 문장을 넣어주세요.
한 문장씩 연습할 수 있습니다."""

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
        ["직접 입력", "AI 생성 문장", "파일 업로드"],
        index=0  # 직접 입력을 기본값으로 설정
    )

    # 선택된 입력 방식에 따라 문장 로드
    if input_method == "직접 입력":
        text_input = st.sidebar.text_area(
            "연습할 텍스트를 입력하세요 (각 줄이 하나의 문장이 됩니다)",
            value=get_default_text(),  # 기본 텍스트 미리 입력
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
                st.session_state.current_sentences = sentences
        else:
            # 빈 입력일 경우 AI 생성 문장으로 돌아감
            st.sidebar.warning("텍스트가 비어있어 AI 생성 문장을 사용합니다.")
            st.session_state.current_sentences = generate_practice_sentences("한국어", 4)
            sentences = st.session_state.current_sentences
    elif input_method == "AI 생성 문장":
        language = st.sidebar.radio("언어 선택", ["한국어", "English"])
        num_sentences = st.sidebar.slider("생성할 문장 수", 4, 10, 4)
        
        if 'current_sentences' not in st.session_state or st.sidebar.button("새로운 문장 생성"):
            with st.spinner(f"{language} 문장을 생성하는 중..."):
                sentences = generate_practice_sentences(language, num_sentences)
                # 새로운 문장이 생성되면 세션 상태 초기화
                st.session_state.current_sentence_index = 0
                st.session_state.input_key = 0
                st.session_state.stats = TypingStats()
                st.session_state.current_sentences = sentences
        else:
            sentences = st.session_state.current_sentences
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
                st.session_state.current_sentences = sentences
        else:
            # 파일이 없을 경우 AI 생성 문장으로 돌아감
            st.sidebar.warning("파일이 없어 AI 생성 문장을 사용합니다.")
            st.session_state.current_sentences = generate_practice_sentences("한국어", 4)
            sentences = st.session_state.current_sentences

    # 문장이 비어있으면 기본 문장 사용
    if not sentences:
        st.sidebar.warning("텍스트가 비어있어 기본 문장을 사용합니다.")
        sentences = process_input_text(get_default_text())

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
