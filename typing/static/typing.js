class TypingChecker {
    constructor() {
        this.lastInputKey = '';
        this.currentInput = null;
        this.checkInterval = 100; // ms
        this.boundCheckTyping = this.checkTyping.bind(this);
    }

    cleanText(text) {
        return text.trim().replace(/\s+/g, ' ');
    }

    checkTyping() {
        const doc = window.parent.document;
        const input = doc.querySelector('input[type="text"]');
        const words = doc.querySelectorAll('.word');
        
        if (!input) return;
        
        const inputWords = this.cleanText(input.value).split(' ');
        
        // 모든 단어 스타일 초기화
        words.forEach(word => {
            word.classList.remove('correct', 'incorrect');
        });
        
        // 입력된 단어 체크
        inputWords.forEach((word, i) => {
            if (i < words.length) {
                const targetWord = this.cleanText(words[i].textContent);
                const inputWord = this.cleanText(word);
                if (inputWord === targetWord) {
                    words[i].classList.add('correct');
                } else if (inputWord) {
                    words[i].classList.add('incorrect');
                }
            }
        });
    }

    setupTypingInput() {
        const doc = window.parent.document;
        const input = doc.querySelector('input[type="text"]');
        
        if (!input) return;
        
        // 새로운 입력창이 감지되면
        if (input !== this.currentInput) {
            this.currentInput = input;
            this.lastInputKey = input.getAttribute('data-testid') || '';
            
            // 이벤트 리스너 제거 후 다시 설정
            input.removeEventListener('input', this.boundCheckTyping);
            input.addEventListener('input', this.boundCheckTyping);
            
            // Enter 키 이벤트
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const submitBtn = doc.querySelector('button[kind="primaryFormSubmit"]');
                    if (submitBtn) submitBtn.click();
                }
            });
            
            // 새 문장이 나타났을 때 포커스
            setTimeout(() => {
                input.focus();
                this.checkTyping();
            }, 100);
        }
    }

    start() {
        // 초기 설정
        this.setupTypingInput();
        this.checkTyping();

        // 주기적으로 체크
        setInterval(() => {
            this.setupTypingInput();
            this.checkTyping();
        }, this.checkInterval);
    }
}

// Streamlit 로드 완료 후 실행
window.addEventListener('load', () => {
    // 약간의 지연 후 시작 (Streamlit UI 로드 대기)
    setTimeout(() => {
        const typingChecker = new TypingChecker();
        typingChecker.start();
    }, 500);
}); 