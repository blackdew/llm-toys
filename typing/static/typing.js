function checkTyping() {
    const doc = window.parent.document;
    const input = doc.querySelector('input[type="text"]');
    const words = doc.querySelectorAll('.word');
    
    if (!input) return;
    
    const inputWords = input.value.trim().split(' ');
    
    words.forEach(word => {
        word.classList.remove('correct', 'incorrect');
    });
    
    inputWords.forEach((word, i) => {
        if (i < words.length) {
            const targetWord = words[i].textContent;
            if (word === targetWord) {
                words[i].classList.add('correct');
            } else if (word) {
                words[i].classList.add('incorrect');
            }
        }
    });
}

function focusInput() {
    const doc = window.parent.document;
    const input = doc.querySelector('input[type="text"]');
    if (input) {
        input.focus();
        
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
    }
}

setInterval(() => {
    focusInput();
    checkTyping();
}, 100);

focusInput();
checkTyping(); 