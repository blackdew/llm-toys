"""URL 처리 관련 테스트"""
from unittest import TestCase, main
from unittest.mock import patch, Mock
import os
import sys
from typing import List, Callable, TypeVar, Sequence

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from url_processor import URLProcessor
from tests.test_data import TEST_DATA, ErrorTestData

T = TypeVar('T')

class TestURLProcessor(TestCase):
    test_url = "https://example.com"  # 클래스 변수로 직접 정의

    def test_url_validation(self):
        """URL 검증 테스트"""
        self._test_validation(
            TEST_DATA.urls.valid,
            TEST_DATA.urls.invalid,
            URLProcessor.is_url
        )

    def test_character_validation(self):
        """문자 검증 테스트"""
        for category, chars in TEST_DATA.chars.valid.items():
            self._test_chars(chars, True, category)
        self._test_chars(TEST_DATA.chars.invalid, False, 'invalid')

    @patch('requests.get')
    def test_text_extraction(self, mock_get: Mock) -> None:
        """텍스트 추출 테스트"""
        self._setup_mock_response(mock_get, TEST_DATA.html.content)
        text_lines = URLProcessor.extract_text_from_url(self.test_url).split('\n')
        self._verify_content(text_lines, TEST_DATA.html.expected, TEST_DATA.html.excluded)

    def test_error_handling(self):
        """오류 처리 테스트"""
        for error_data in TEST_DATA.errors:
            self._test_error_case(error_data)

    def _test_validation(self, valid_items: Sequence[T], invalid_items: Sequence[T], 
                        validator: Callable[[T], bool]) -> None:
        """검증 테스트를 위한 헬퍼 메서드"""
        for item in valid_items:
            with self.subTest(item=item, valid=True):
                self.assertTrue(validator(item))

        for item in invalid_items:
            with self.subTest(item=item, valid=False):
                self.assertFalse(validator(item))

    def _test_chars(self, chars: str, should_allow: bool, category: str) -> None:
        """문자 검증을 위한 헬퍼 메서드"""
        for char in chars:
            with self.subTest(category=category, char=char):
                result = URLProcessor.is_allowed_char(char)
                self.assertEqual(result, should_allow, 
                    f"Character '{char}' from category '{category}' "
                    f"{'should' if should_allow else 'should not'} be allowed")

    def _verify_content(self, text_lines: List[str], expected: List[str], 
                       excluded: List[str]) -> None:
        """컨텐츠 검증을 위한 헬퍼 메서드"""
        text = '\n'.join(text_lines)
        for content in expected:
            with self.subTest(content=content, check="included"):
                self.assertIn(content, text_lines)
        for content in excluded:
            with self.subTest(content=content, check="excluded"):
                self.assertNotIn(content, text)

    def _test_error_case(self, error_data: ErrorTestData) -> None:
        """오류 케이스 테스트를 위한 헬퍼 메서드"""
        with self.subTest(error=error_data.message):
            with patch('requests.get', side_effect=error_data.exception):
                with self.assertRaises(ValueError) as context:
                    URLProcessor.extract_text_from_url(self.test_url)
                self.assertIn("URL에서 텍스트를 가져오는데 실패했습니다", str(context.exception))

    @staticmethod
    def _setup_mock_response(mock_get: Mock, html_content: str) -> None:
        """Mock 응답 설정"""
        mock_response = Mock()
        mock_response.text = html_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

if __name__ == '__main__':
    main() 