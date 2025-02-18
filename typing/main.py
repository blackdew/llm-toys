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
    if 'total_sentences_completed' not in st.session_state:
        st.session_state.total_sentences_completed = 0
    if 'current_input_method' not in st.session_state:
        st.session_state.current_input_method = "직접 입력"
    
    # 인덱스가 범위를 벗어났는지 확인하고 수정
    if (st.session_state.current_sentence_index >= len(st.session_state.current_sentences) or 
        st.session_state.current_sentence_index < 0):
        st.session_state.current_sentence_index = 0

def display_stats(stats: TypingStats, current_sentences: int):
    """통계를 표시합니다."""
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        # 현재 문장 인덱스 + 이전에 완료한 문장 수를 합산하여 표시
        current_progress = st.session_state.current_sentence_index + 1 + st.session_state.total_sentences_completed
        total_sentences = current_sentences + st.session_state.total_sentences_completed
        st.markdown(f"**진행률:** {current_progress} / {total_sentences}")
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
    sentences = st.session_state.current_sentences
    next_index = st.session_state.current_sentence_index + 1

    # AI 생성 문장 모드에서 마지막 문장 완료 시 자동으로 새로운 문장 생성
    if (st.session_state.current_input_method == "AI 생성 문장" and 
        next_index >= len(sentences)):
        # 완료한 문장 세트 카운트 증가
        st.session_state.total_sentences_completed += len(sentences)
        # 새로운 문장 생성
        new_sentences = generate_practice_sentences(
            st.session_state.get('current_language', '한국어'), 
            num_sentences=5
        )
        st.session_state.current_sentences = new_sentences
        next_index = 0
    else:
        next_index = next_index % len(sentences)

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
        index=0
    )

    # 입력 방식이 변경되면 상태 초기화
    if st.session_state.current_input_method != input_method:
        st.session_state.current_input_method = input_method
        st.session_state.current_sentence_index = 0
        st.session_state.input_key = 0
        st.session_state.stats = TypingStats()
        st.session_state.total_sentences_completed = 0
        if 'current_sentences' in st.session_state:
            del st.session_state.current_sentences

    # 각 모드별 설정
    sentences = []  # 초기화

    if input_method == "직접 입력":
        text_input = st.sidebar.text_area(
            "연습할 텍스트를 입력하세요 (각 줄이 하나의 문장이 됩니다)",
            value=get_default_text(),
            height=200
        )
        
        if 'current_sentences' not in st.session_state:
            st.markdown("""
                <div style='text-align: center; padding: 50px;'>
                    <h2>직접 입력 연습</h2>
                    <p>연습할 텍스트를 입력하고 '연습시작' 버튼을 클릭하여 시작하세요.</p>
                    <p>각 줄이 하나의 문장으로 처리됩니다.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            sentences = st.session_state.current_sentences

    elif input_method == "AI 생성 문장":
        language = st.sidebar.selectbox(
            "언어 선택",
            ["한국어", "English"],
            index=0
        )
        st.session_state.current_language = language
        
        if 'current_sentences' not in st.session_state:
            st.markdown("""
                <div style='text-align: center; padding: 50px;'>
                    <h2>AI 생성 문장 연습</h2>
                    <p>원하는 언어를 선택하고 '연습시작' 버튼을 클릭하여 시작하세요.</p>
                    <p>한 번에 5개의 문장이 생성되며, 자동으로 다음 문장 세트가 생성됩니다.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            sentences = st.session_state.current_sentences

    else:  # 파일 업로드
        uploaded_file = st.sidebar.file_uploader("텍스트 파일을 업로드하세요", type=['txt'])
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_line = st.number_input(
                "시작 문장 위치",
                min_value=0,
                value=0,
                help="연습을 시작할 문장의 위치를 지정합니다. (0부터 시작)"
            )
        with col2:
            lines_per_set = st.number_input(
                "연습할 문장 수",
                min_value=1,
                max_value=50,
                value=10,
                help="한 번에 연습할 문장의 수를 설정합니다."
            )
            
        if 'current_sentences' not in st.session_state:
            st.markdown("""
                <div style='text-align: center; padding: 50px;'>
                    <h2>파일 업로드 연습</h2>
                    <p>텍스트 파일(.txt)을 업로드하고 '연습시작' 버튼을 클릭하여 시작하세요.</p>
                    <p>시작 위치와 연습할 문장 수를 설정할 수 있습니다.</p>
                </div>
            """, unsafe_allow_html=True)

        if 'current_sentences' in st.session_state:
            sentences = st.session_state.current_sentences

    # 공통 연습 시작 버튼
    st.sidebar.markdown("---")
    if st.sidebar.button("연습 시작", use_container_width=True):
        # 진행률 초기화
        st.session_state.current_sentence_index = 0
        st.session_state.input_key = 0
        st.session_state.stats = TypingStats()
        st.session_state.total_sentences_completed = 0

        if input_method == "직접 입력":
            if text_input:
                sentences = process_input_text(text_input)
                st.session_state.current_text = text_input
                st.session_state.current_sentences = sentences
            else:
                st.sidebar.warning("텍스트를 입력해주세요.")
                return

        elif input_method == "AI 생성 문장":
            with st.spinner(f"{language} 문장을 생성하는 중..."):
                sentences = generate_practice_sentences(language, num_sentences=5)
                st.session_state.current_sentences = sentences

        else:  # 파일 업로드
            if not uploaded_file:
                st.sidebar.warning("파일을 업로드해주세요.")
                return
                
            text_content = uploaded_file.getvalue().decode('utf-8')
            all_sentences = process_input_text(text_content)
            start_line = min(start_line, len(all_sentences))
            
            st.session_state.current_file = uploaded_file.name
            st.session_state.start_line = start_line
            st.session_state.lines_per_set = lines_per_set
            
            end_line = start_line + lines_per_set
            sentences = all_sentences[start_line:end_line]
            st.session_state.current_sentences = sentences
            st.session_state.remaining_sentences = all_sentences[end_line:]

    # 문장이 비어있으면 나머지 UI를 표시하지 않음
    if not sentences:
        return

    # 인덱스가 범위를 벗어났는지 확인
    if st.session_state.current_sentence_index >= len(sentences):
        st.session_state.current_sentence_index = 0

    current_sentence = sentences[st.session_state.current_sentence_index]
    
    # 통계 표시
    display_stats(st.session_state.stats, len(sentences))
        
    # 사이드바에 현재 진행 상황 표시
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**현재 진행 상황**")
    current_progress = st.session_state.current_sentence_index + 1 + st.session_state.total_sentences_completed
    total_sentences = len(sentences) + st.session_state.total_sentences_completed
    st.sidebar.markdown(f"전체 문장 수: {total_sentences}")
    st.sidebar.markdown(f"현재 문장: {current_progress}")

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
            
            // 모든 단어 스타일 초기화
            words.forEach(word => {
                word.classList.remove('correct', 'incorrect');
            });
            
            // 입력된 단어 체크
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

        let lastInputKey = '';
        let currentInput = null;

        function setupTypingInput() {
            const doc = window.parent.document;
            const input = doc.querySelector('input[type="text"]');
            
            if (!input) return;
            
            // 새로운 입력창이 감지되면
            if (input !== currentInput) {
                currentInput = input;
                lastInputKey = input.getAttribute('data-testid') || '';
                
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
                setTimeout(() => {
                    input.focus();
                    checkTyping();
                }, 100);
            }
        }

        // 주기적으로 체크
        setInterval(() => {
            setupTypingInput();
            checkTyping();  // 실시간 체크 추가
        }, 100);

        // 초기 설정
        setupTypingInput();
        checkTyping();
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

if __name__ == "__main__":
    main()
