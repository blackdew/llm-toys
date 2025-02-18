"""타이핑 관련 핵심 로직"""
import time
from typing import List, Dict
from config import DEFAULT_SENTENCES

class TypingStats:
    """타이핑 통계를 관리하는 클래스"""
    def __init__(self):
        self.total_words = 0
        self.correct_words = 0
        self.incorrect_words = 0
        self.start_time = time.time()
        self.elapsed_times = []

    def update(self, input_words: List[str], target_words: List[str]) -> None:
        """통계 업데이트"""
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
        """평균 분당 타자 속도를 계산"""
        if not self.elapsed_times:
            return 0.0
        
        total_time_minutes = sum(self.elapsed_times) / 60
        if total_time_minutes == 0:
            return 0.0
            
        return round(self.total_words / total_time_minutes, 1)

    def to_dict(self) -> Dict[str, float]:
        """통계를 딕셔너리로 반환"""
        return {
            'total_words': self.total_words,
            'correct_words': self.correct_words,
            'incorrect_words': self.incorrect_words,
            'wpm': self.get_wpm()
        }

class TypingManager:
    """타이핑 세션을 관리하는 클래스"""
    def __init__(self):
        self.stats = TypingStats()
        self.current_index = 0
        self.current_sentences = []
        self.total_sentences_completed = 0
        self.input_key = 0

    def load_sentences(self, sentences: List[str]) -> None:
        """문장 목록을 로드"""
        self.current_sentences = sentences
        self.current_index = 0
        self.input_key = 0

    def get_current_sentence(self) -> str:
        """현재 문장 반환"""
        if not self.current_sentences:
            return ""
        return self.current_sentences[self.current_index]

    def handle_input(self, input_text: str) -> None:
        """사용자 입력 처리"""
        if not input_text or not self.current_sentences:
            return

        # 통계 업데이트
        input_words = input_text.strip().split()
        target_words = self.get_current_sentence().split()
        self.stats.update(input_words, target_words)

        # 다음 문장으로 이동
        self.move_to_next()

    def move_to_next(self) -> None:
        """다음 문장으로 이동"""
        next_index = self.current_index + 1
        
        # 세트의 마지막 문장인 경우
        if next_index >= len(self.current_sentences):
            self.total_sentences_completed += len(self.current_sentences)
            self.current_index = 0
        else:
            self.current_index = next_index

        self.input_key += 1

    def reset(self) -> None:
        """상태 초기화"""
        self.stats = TypingStats()
        self.current_index = 0
        self.input_key = 0
        self.total_sentences_completed = 0

    @staticmethod
    def process_input_text(text: str) -> List[str]:
        """입력된 텍스트를 문장 리스트로 변환"""
        return [line.strip() for line in text.split('\n') if line.strip()]

    @staticmethod
    def get_default_text() -> str:
        """기본 연습 문장 반환"""
        return DEFAULT_SENTENCES 