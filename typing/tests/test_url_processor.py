"""URL 처리 관련 테스트"""
import unittest
from unittest.mock import patch, Mock
import sys
import os
import requests

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from url_processor import URLProcessor

class TestURLProcessor(unittest.TestCase):
    def test_is_url_valid_cases(self):
        """유효한 URL 인식 테스트"""
        valid_urls = [
            "https://example.com",
            "http://example.com/page",
            "https://sub.domain.com/path?param=value",
            "http://localhost:8000",
            "https://example.com/path/to/page#section"
        ]
        for url in valid_urls:
            self.assertTrue(URLProcessor.is_url(url), f"Should recognize {url} as valid URL")

    def test_is_url_invalid_cases(self):
        """유효하지 않은 URL 인식 테스트"""
        invalid_urls = [
            "not a url",
            "example.com",
            "http:/example.com",
            "https//example.com",
            "",
            "ftp://example.com",  # 지원하지 않는 프로토콜
            "   https://example.com   "  # 공백 포함
        ]
        for url in invalid_urls:
            self.assertFalse(URLProcessor.is_url(url), f"Should recognize {url} as invalid URL")

    def test_is_allowed_char_korean(self):
        """한글 문자 허용 테스트"""
        # 한글 음절
        self.assertTrue(URLProcessor.is_allowed_char("가"))
        self.assertTrue(URLProcessor.is_allowed_char("힣"))
        # 자음/모음
        self.assertTrue(URLProcessor.is_allowed_char("ㄱ"))
        self.assertTrue(URLProcessor.is_allowed_char("ㅎ"))
        self.assertTrue(URLProcessor.is_allowed_char("ㅏ"))
        self.assertTrue(URLProcessor.is_allowed_char("ㅣ"))

    def test_is_allowed_char_english(self):
        """영문 문자 허용 테스트"""
        # 대소문자
        for c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
            self.assertTrue(URLProcessor.is_allowed_char(c), f"Should allow letter {c}")

    def test_is_allowed_char_numbers(self):
        """숫자 허용 테스트"""
        for n in '0123456789':
            self.assertTrue(URLProcessor.is_allowed_char(n), f"Should allow number {n}")

    def test_is_allowed_char_punctuation(self):
        """문장 부호 허용 테스트"""
        for p in '.,!?()[]{}":;\'- ':
            self.assertTrue(URLProcessor.is_allowed_char(p), f"Should allow punctuation {p}")

    def test_is_allowed_char_special_chars(self):
        """특수 문자 및 이모티콘 거부 테스트"""
        special_chars = [
            '👋', '🌟', '⭐', '★', '☆', '♥', '♡',
            '©', '®', '™', '€', '£', '¥', '$',
            '\\', '|', '@', '#', '$', '%', '^', '&', '*', '+', '=', '`', '~'
        ]
        for char in special_chars:
            self.assertFalse(URLProcessor.is_allowed_char(char), f"Should not allow special char {char}")

    @patch('requests.get')
    def test_extract_text_from_url_structure(self, mock_get):
        """HTML 구조에 따른 텍스트 추출 테스트"""
        mock_response = Mock()
        mock_response.text = """
        <html>
            <body>
                <header>Header text that should be excluded</header>
                <nav>Navigation text that should be excluded</nav>
                <h1>Main Title - This is a longer title that meets the minimum length</h1>
                <p>First paragraph with enough length to pass the filter</p>
                <script>JavaScript code</script>
                <style>CSS code</style>
                <h2>Subtitle - Also needs to be long enough to be included</h2>
                <p>Second paragraph that also meets the minimum length requirement</p>
                <footer>Footer text that should be excluded</footer>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        mock_response.raise_for_status = Mock()

        text = URLProcessor.extract_text_from_url("https://example.com")
        text_lines = text.split('\n')
        
        # 순서대로 확인
        self.assertIn("Main Title - This is a longer title that meets the minimum length", text_lines)
        self.assertIn("First paragraph with enough length to pass the filter", text_lines)
        self.assertIn("Subtitle - Also needs to be long enough to be included", text_lines)
        self.assertIn("Second paragraph that also meets the minimum length requirement", text_lines)
        
        # 제외되어야 할 내용
        self.assertNotIn("Header text that should be excluded", text)
        self.assertNotIn("Navigation text that should be excluded", text)
        self.assertNotIn("JavaScript code", text)
        self.assertNotIn("CSS code", text)
        self.assertNotIn("Footer text that should be excluded", text)

    @patch('requests.get')
    def test_extract_text_from_url_error_handling(self, mock_get):
        """URL 처리 오류 테스트"""
        # 네트워크 오류
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        with self.assertRaises(ValueError) as context:
            URLProcessor.extract_text_from_url("https://example.com")
        self.assertIn("URL에서 텍스트를 가져오는데 실패했습니다", str(context.exception))

        # 잘못된 URL
        mock_get.side_effect = requests.exceptions.InvalidURL("Invalid URL")
        with self.assertRaises(ValueError) as context:
            URLProcessor.extract_text_from_url("invalid-url")
        self.assertIn("URL에서 텍스트를 가져오는데 실패했습니다", str(context.exception))

    @patch('requests.get')
    def test_extract_text_minimum_length_filter(self, mock_get):
        """최소 문장 길이 필터 테스트"""
        mock_response = Mock()
        mock_response.text = """
        <html>
            <body>
                <p>짧은글</p>
                <p>이 문장은 최소 길이를 충족합니다.</p>
                <p>Hi</p>
                <p>This sentence meets the minimum length requirement.</p>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        mock_response.raise_for_status = Mock()

        text = URLProcessor.extract_text_from_url("https://example.com")
        
        self.assertNotIn("짧은글", text)
        self.assertNotIn("Hi", text)
        self.assertIn("이 문장은 최소 길이를 충족합니다", text)
        self.assertIn("This sentence meets the minimum length requirement", text)

if __name__ == '__main__':
    unittest.main() 