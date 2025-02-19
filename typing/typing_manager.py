"""타이핑 관련 핵심 로직"""
import time
from typing import List, Dict
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from url_processor import URLProcessor

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
        self.total_keystrokes = 0

    def count_keystrokes(self, text: str) -> int:
        """한글/영어 각각의 실제 타자수를 계산합니다."""
        total_strokes = 0
        for char in text:
            if '가' <= char <= '힣':  # 한글인 경우
                # 초성, 중성, 종성 분해
                char_code = ord(char) - 0xAC00
                
                # 종성이 있는지 확인
                jong = char_code % 28
                jung = ((char_code - jong) // 28) % 21
                cho = ((char_code - jong) // 28) // 21
                
                # 실제 타자수 계산
                strokes = 0
                if cho >= 0:  # 초성
                    strokes += 1
                if jung >= 0:  # 중성
                    strokes += 1
                if jong > 0:   # 종성이 있는 경우
                    strokes += 1
                
                total_strokes += strokes
            else:  # 영어 및 기타 문자
                total_strokes += 1
        
        return total_strokes

    def update(self, input_words: List[str], target_words: List[str]) -> None:
        """단어 단위로 정확도를 체크하고 통계를 업데이트합니다."""
        elapsed = time.time() - self.start_time
        self.elapsed_times.append(elapsed)
        self.start_time = time.time()
        
        self.word_stats.update(input_words, target_words)
        
        # 타자수 계산
        for word in input_words:
            self.total_keystrokes += self.count_keystrokes(word)

    def _get_minutes(self) -> float:
        """경과 시간을 분 단위로 반환합니다."""
        if not self.elapsed_times:
            return 0.0
        return sum(self.elapsed_times) / 60

    def get_cpm(self) -> float:
        """평균 분당 타자수를 계산합니다."""
        minutes = self._get_minutes()
        if minutes == 0:
            return 0.0
        return round(self.total_keystrokes / minutes, 1)

    def get_wpm(self) -> float:
        """평균 분당 단어 속도를 계산합니다."""
        minutes = self._get_minutes()
        if minutes == 0:
            return 0.0
        return round(self.word_stats.total / minutes, 1)

    def to_dict(self) -> Dict[str, float]:
        """통계를 딕셔너리 형태로 반환합니다."""
        return {
            'total_words': self.word_stats.total,
            'correct_words': self.word_stats.correct,
            'incorrect_words': self.word_stats.incorrect,
            'wpm': self.get_wpm(),
            'cpm': self.get_cpm(),
            'accuracy': self.word_stats.accuracy
        }

    def reset(self) -> None:
        """통계를 초기화합니다."""
        self.word_stats.reset()
        self.start_time = time.time()
        self.elapsed_times = []
        self.total_keystrokes = 0

class TypingManager:
    """타이핑 세션을 관리하는 클래스"""
    def __init__(self):
        self.stats = TypingStats()
        self.current_index = 0
        self.current_sentences: List[str] = []
        self.total_sentences_completed = 0
        self.input_key = 0
        self.current_input_method = ""

    def reset_session(self) -> None:
        """현재 세션의 상태를 초기화합니다."""
        self.current_index = 0
        self.input_key = 0

    def reset_all(self) -> None:
        """모든 상태를 초기화합니다."""
        self.reset_session()
        self.stats.reset()
        self.current_sentences = []
        self.total_sentences_completed = 0
        self.current_input_method = ""

    def process_input_text(self, text: str) -> List[str]:
        """입력된 텍스트를 문장 리스트로 변환"""
        if URLProcessor.is_url(text):
            text = URLProcessor.extract_text_from_url(text)
        return [line.strip() for line in text.split('\n') if line.strip()]

    def set_input_method(self, method: str) -> None:
        """입력 방식을 설정합니다."""
        self.current_input_method = method

    def load_sentences(self, sentences: List[str]) -> None:
        """문장 목록을 로드하고 초기 상태를 설정합니다."""
        if not sentences:
            raise ValueError("Empty sentences list")
        self.current_sentences = sentences
        self.reset_session()

    def get_current_sentence(self) -> str:
        """현재 문장을 반환합니다."""
        if not self.current_sentences or self.current_index >= len(self.current_sentences):
            return ""
        return self.current_sentences[self.current_index]

    def handle_input(self, input_text: str) -> bool:
        """사용자 입력을 처리하고 성공 여부를 반환합니다."""
        current_sentence = self.get_current_sentence()
        if not input_text or not current_sentence:
            return False

        # 통계 업데이트
        input_words = input_text.strip().split()
        target_words = current_sentence.split()
        self.stats.update(input_words, target_words)

        return self.move_to_next()

    def move_to_next(self) -> bool:
        """다음 문장으로 이동하고 성공 여부를 반환합니다."""
        if not self.current_sentences:
            return False

        next_index = self.current_index + 1
        is_set_completed = next_index >= len(self.current_sentences)
        
        if is_set_completed:
            self.total_sentences_completed += len(self.current_sentences)
            if self.current_input_method == "AI 생성 문장":
                return True
            self.current_index = 0
        else:
            self.current_index = next_index

        self.input_key += 1
        return True

    def get_progress(self) -> Dict[str, int]:
        """현재 진행 상황을 반환합니다."""
        return {
            'current_index': self.current_index + 1,
            'total_sentences': len(self.current_sentences),
            'completed_sentences': self.total_sentences_completed
        }

    @staticmethod
    def get_default_text() -> str:
        """기본 연습 문장 반환"""
        return DEFAULT_SENTENCES

    def to_dict(self) -> Dict[str, float]:
        """통계를 딕셔너리 형태로 반환합니다."""
        return self.stats.to_dict() 