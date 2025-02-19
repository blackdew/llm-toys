import unittest
import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from typing_manager import TypingStats, TypingManager, WordStats

class TestWordStats(unittest.TestCase):
    def setUp(self):
        self.word_stats = WordStats()

    def test_update_correct_words(self):
        input_words = ["hello", "world"]
        target_words = ["hello", "world"]
        self.word_stats.update(input_words, target_words)
        self.assertEqual(self.word_stats.total, 2)
        self.assertEqual(self.word_stats.correct, 2)
        self.assertEqual(self.word_stats.incorrect, 0)

    def test_update_incorrect_words(self):
        input_words = ["hello", "word"]
        target_words = ["hello", "world"]
        self.word_stats.update(input_words, target_words)
        self.assertEqual(self.word_stats.total, 2)
        self.assertEqual(self.word_stats.correct, 1)
        self.assertEqual(self.word_stats.incorrect, 1)

    def test_accuracy_calculation(self):
        input_words = ["hello", "word"]
        target_words = ["hello", "world"]
        self.word_stats.update(input_words, target_words)
        self.assertEqual(self.word_stats.accuracy, 50.0)

class TestTypingStats(unittest.TestCase):
    def setUp(self):
        self.typing_stats = TypingStats()

    def test_count_keystrokes_english(self):
        text = "hello"
        strokes = self.typing_stats.count_keystrokes(text)
        self.assertEqual(strokes, 5)  # 영어는 한 글자당 1타

    def test_count_keystrokes_korean(self):
        text = "안녕"  # ㅇ+ㅏ+ㄴ + ㄴ+ㅕ+ㅇ = 6타
        strokes = self.typing_stats.count_keystrokes(text)
        self.assertEqual(strokes, 6)

    def test_cpm_calculation(self):
        # 시간 계산을 위해 elapsed_times를 직접 설정
        self.typing_stats.elapsed_times = [30.0]  # 30초
        self.typing_stats.total_keystrokes = 300  # 300타
        cpm = self.typing_stats.get_cpm()
        self.assertEqual(cpm, 600.0)  # 분당 600타

    def test_wpm_calculation(self):
        self.typing_stats.elapsed_times = [60.0]  # 1분
        self.typing_stats.word_stats.total = 50  # 50단어
        wpm = self.typing_stats.get_wpm()
        self.assertEqual(wpm, 50.0)  # 분당 50단어

    def test_to_dict_contains_all_required_keys(self):
        """to_dict 메서드가 모든 필수 키를 포함하는지 테스트합니다."""
        stats_dict = self.typing_stats.to_dict()
        required_keys = {
            'total_words',
            'correct_words',
            'incorrect_words',
            'wpm',
            'cpm',
            'accuracy'
        }
        
        # 모든 필수 키가 존재하는지 확인
        for key in required_keys:
            self.assertIn(key, stats_dict, f"'{key}' key is missing in stats dictionary")
            
        # 모든 값이 숫자형인지 확인
        for key, value in stats_dict.items():
            self.assertIsInstance(value, (int, float), f"Value for '{key}' should be numeric")

    def test_to_dict_initial_values(self):
        """초기 상태의 to_dict 반환값을 테스트합니다."""
        stats_dict = self.typing_stats.to_dict()
        
        # 초기값 확인
        self.assertEqual(stats_dict['total_words'], 0)
        self.assertEqual(stats_dict['correct_words'], 0)
        self.assertEqual(stats_dict['incorrect_words'], 0)
        self.assertEqual(stats_dict['wpm'], 0.0)
        self.assertEqual(stats_dict['cpm'], 0.0)
        self.assertEqual(stats_dict['accuracy'], 0.0)

    def test_to_dict_after_update(self):
        """업데이트 후의 to_dict 반환값을 테스트합니다."""
        # 테스트 데이터 설정
        self.typing_stats.elapsed_times = [60.0]  # 1분
        self.typing_stats.total_keystrokes = 300  # 300타
        self.typing_stats.word_stats.total = 50
        self.typing_stats.word_stats.correct = 45
        self.typing_stats.word_stats.incorrect = 5
        
        stats_dict = self.typing_stats.to_dict()
        
        # 업데이트된 값 확인
        self.assertEqual(stats_dict['total_words'], 50)
        self.assertEqual(stats_dict['correct_words'], 45)
        self.assertEqual(stats_dict['incorrect_words'], 5)
        self.assertEqual(stats_dict['wpm'], 50.0)
        self.assertEqual(stats_dict['cpm'], 300.0)
        self.assertEqual(stats_dict['accuracy'], 90.0)

class TestTypingManager(unittest.TestCase):
    def setUp(self):
        self.manager = TypingManager()

    def test_load_sentences(self):
        sentences = ["First sentence.", "Second sentence."]
        self.manager.load_sentences(sentences)
        self.assertEqual(self.manager.current_sentences, sentences)
        self.assertEqual(self.manager.current_index, 0)

    def test_empty_sentences_raises_error(self):
        with self.assertRaises(ValueError):
            self.manager.load_sentences([])

    def test_get_current_sentence(self):
        sentences = ["First sentence.", "Second sentence."]
        self.manager.load_sentences(sentences)
        self.assertEqual(self.manager.get_current_sentence(), "First sentence.")

    def test_handle_input_correct(self):
        sentences = ["test sentence"]
        self.manager.load_sentences(sentences)
        result = self.manager.handle_input("test sentence")
        self.assertTrue(result)
        self.assertEqual(self.manager.stats.word_stats.correct, 2)

    def test_handle_input_incorrect(self):
        sentences = ["test sentence"]
        self.manager.load_sentences(sentences)
        result = self.manager.handle_input("wrong sentence")
        self.assertTrue(result)
        self.assertEqual(self.manager.stats.word_stats.correct, 1)
        self.assertEqual(self.manager.stats.word_stats.incorrect, 1)

    def test_move_to_next(self):
        sentences = ["First", "Second", "Third"]
        self.manager.load_sentences(sentences)
        self.manager.move_to_next()
        self.assertEqual(self.manager.current_index, 1)
        self.assertEqual(self.manager.input_key, 1)

    def test_reset_session(self):
        sentences = ["First", "Second"]
        self.manager.load_sentences(sentences)
        self.manager.move_to_next()
        self.manager.reset_session()
        self.assertEqual(self.manager.current_index, 0)
        self.assertEqual(self.manager.input_key, 0)

    def test_reset_all(self):
        sentences = ["First", "Second"]
        self.manager.load_sentences(sentences)
        self.manager.move_to_next()
        self.manager.stats.total_keystrokes = 100
        self.manager.reset_all()
        self.assertEqual(self.manager.current_index, 0)
        self.assertEqual(self.manager.input_key, 0)
        self.assertEqual(self.manager.stats.total_keystrokes, 0)
        self.assertEqual(self.manager.current_sentences, [])

    def test_ai_mode_completion(self):
        self.manager.set_input_method("AI 생성 문장")
        sentences = ["First", "Second"]
        self.manager.load_sentences(sentences)
        self.manager.current_index = len(sentences) - 1
        result = self.manager.move_to_next()
        self.assertTrue(result)  # AI 모드에서는 문장 세트 완료 시 True 반환

if __name__ == '__main__':
    unittest.main() 