"""타이핑 관련 핵심 로직"""
import time
from typing import List, Dict
from config import DEFAULT_SENTENCES
from dataclasses import dataclass

@dataclass
class WordStats:
    total: int = 0
    correct: int = 0
    incorrect: int = 0

    def update(self, input_words: List[str], target_words: List[str]) -> None:
        """단어 통계를 업데이트합니다."""
        self.total += len(target_words)
        
        for i, word in enumerate(input_words):
            if i < len(target_words):
                if word == target_words[i]:
                    self.correct += 1
                else:
                    self.incorrect += 1
            else:
                self.incorrect += 1
        
        if len(input_words) < len(target_words):
            self.incorrect += (len(target_words) - len(input_words))

    def reset(self) -> None:
        """통계를 초기화합니다."""
        self.total = 0
        self.correct = 0
        self.incorrect = 0

    @property
    def accuracy(self) -> float:
        """정확도를 계산합니다."""
        if self.total == 0:
            return 0.0
        return round((self.correct / self.total) * 100, 1)

class TypingStats:
    """타이핑 통계를 관리하는 클래스"""
    def __init__(self):
        self.word_stats = WordStats()
        self.start_time = time.time()
        self.elapsed_times: List[float] = []

    def update(self, input_words: List[str], target_words: List[str]) -> None:
        """단어 단위로 정확도를 체크하고 통계를 업데이트합니다."""
        # 현재 문장 완료 시간 기록
        elapsed = time.time() - self.start_time
        self.elapsed_times.append(elapsed)
        
        # 다음 문장을 위한 시작 시간 초기화
        self.start_time = time.time()
        
        self.word_stats.update(input_words, target_words)

    def get_wpm(self) -> float:
        """평균 분당 타자 속도를 계산합니다."""
        if not self.elapsed_times:
            return 0.0
        
        total_time_minutes = sum(self.elapsed_times) / 60
        if total_time_minutes == 0:
            return 0.0
            
        return round(self.word_stats.total / total_time_minutes, 1)

    def to_dict(self) -> Dict[str, int]:
        """통계를 딕셔너리 형태로 반환합니다."""
        return {
            'total_words': self.word_stats.total,
            'correct_words': self.word_stats.correct,
            'incorrect_words': self.word_stats.incorrect,
            'wpm': self.get_wpm(),
            'accuracy': self.word_stats.accuracy
        }

    def reset(self) -> None:
        """통계를 초기화합니다."""
        self.word_stats.reset()
        self.start_time = time.time()
        self.elapsed_times = []

class TypingManager:
    """타이핑 세션을 관리하는 클래스"""
    def __init__(self):
        self.stats = TypingStats()
        self.current_index = 0
        self.current_sentences: List[str] = []
        self.total_sentences_completed = 0
        self.input_key = 0
        self.current_input_method = ""

    def load_sentences(self, sentences: List[str]) -> None:
        """문장 목록을 로드하고 초기 상태를 설정합니다."""
        if not sentences:
            raise ValueError("Empty sentences list")
        self.current_sentences = sentences
        self.reset_session()

    def get_current_sentence(self) -> str:
        """현재 문장을 반환합니다. 문장이 없으면 빈 문자열을 반환합니다."""
        if not self.current_sentences:
            return ""
        if self.current_index >= len(self.current_sentences):
            return ""
        return self.current_sentences[self.current_index]

    def handle_input(self, input_text: str) -> bool:
        """사용자 입력을 처리하고 성공 여부를 반환합니다."""
        if not input_text or not self.current_sentences:
            return False

        current_sentence = self.get_current_sentence()
        if not current_sentence:
            return False

        # 통계 업데이트
        input_words = input_text.strip().split()
        target_words = current_sentence.split()
        self.stats.update(input_words, target_words)

        # 다음 문장으로 이동
        return self.move_to_next()

    def move_to_next(self) -> bool:
        """다음 문장으로 이동하고 성공 여부를 반환합니다."""
        if not self.current_sentences:
            return False

        next_index = self.current_index + 1
        is_set_completed = next_index >= len(self.current_sentences)
        
        # 현재 세트 완료 처리
        if is_set_completed:
            self.total_sentences_completed += len(self.current_sentences)
            
            # AI 생성 문장 모드인 경우
            if self.current_input_method == "AI 생성 문장":
                return True  # 새로운 문장 생성이 필요함을 알림
            
            # 일반 모드인 경우
            self.current_index = 0
        else:
            self.current_index = next_index

        self.input_key += 1
        return True

    def reset_session(self) -> None:
        """현재 세션의 상태를 초기화합니다."""
        self.current_index = 0
        self.input_key = 0
        self.stats.reset()

    def reset_all(self) -> None:
        """모든 상태를 초기화합니다."""
        self.reset_session()
        self.current_sentences = []
        self.total_sentences_completed = 0
        self.current_input_method = ""

    def get_progress(self) -> Dict[str, int]:
        """현재 진행 상황을 반환합니다."""
        return {
            'current_index': self.current_index + 1,
            'total_sentences': len(self.current_sentences),
            'completed_sentences': self.total_sentences_completed
        }

    @staticmethod
    def process_input_text(text: str) -> List[str]:
        """입력된 텍스트를 문장 리스트로 변환"""
        return [line.strip() for line in text.split('\n') if line.strip()]

    @staticmethod
    def get_default_text() -> str:
        """기본 연습 문장 반환"""
        return DEFAULT_SENTENCES

    def set_input_method(self, method: str) -> None:
        """입력 방식을 설정합니다."""
        self.current_input_method = method 