"""테스트 데이터"""
from dataclasses import dataclass
from typing import List, Dict, Tuple, Union, Literal
import requests

@dataclass
class URLTestData:
    valid: List[str]
    invalid: List[str]

@dataclass
class CharacterTestData:
    valid: Dict[Literal['korean', 'english', 'numbers', 'punctuation'], str]
    invalid: str

@dataclass
class HTMLTestData:
    content: str
    expected: List[str]
    excluded: List[str]

@dataclass
class ErrorTestData:
    exception: Exception
    message: str

@dataclass
class TestData:
    urls: URLTestData
    chars: CharacterTestData
    html: HTMLTestData
    errors: List[ErrorTestData]

# HTML 테스트 컨텐츠
HTML_CONTENT = """
<html><body>
    <header>Header text that should be excluded</header>
    <nav>Navigation text that should be excluded</nav>
    <h1>Main Title - This is a longer title that meets the minimum length</h1>
    <p>First paragraph with enough length to pass the filter</p>
    <script>JavaScript code</script>
    <style>CSS code</style>
    <h2>Subtitle - Also needs to be long enough to be included</h2>
    <p>Second paragraph that also meets the minimum length requirement</p>
    <footer>Footer text that should be excluded</footer>
</body></html>
"""

TEST_DATA = TestData(
    urls=URLTestData(
        valid=[
            "https://example.com",
            "http://example.com/page",
            "https://sub.domain.com/path?param=value",
            "http://localhost:8000",
            "https://example.com/path/to/page#section"
        ],
        invalid=[
            "not a url",
            "example.com",
            "http:/example.com",
            "https//example.com",
            "",
            "ftp://example.com",
            "   https://example.com   "
        ]
    ),
    chars=CharacterTestData(
        valid={
            'korean': '가힣ㄱㅎㅏㅣ',
            'english': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
            'numbers': '0123456789',
            'punctuation': '.,!?()[]{}":;\'- '
        },
        invalid='👋🌟⭐★☆♥♡©®™€£¥$\\|@#$%^&*+=`~'
    ),
    html=HTMLTestData(
        content=HTML_CONTENT,
        expected=[
            "Main Title - This is a longer title that meets the minimum length",
            "First paragraph with enough length to pass the filter",
            "Subtitle - Also needs to be long enough to be included",
            "Second paragraph that also meets the minimum length requirement"
        ],
        excluded=[
            "Header text that should be excluded",
            "Navigation text that should be excluded",
            "JavaScript code",
            "CSS code",
            "Footer text that should be excluded"
        ]
    ),
    errors=[
        ErrorTestData(
            exception=requests.exceptions.RequestException("Network error"),
            message="Network error"
        ),
        ErrorTestData(
            exception=requests.exceptions.InvalidURL("Invalid URL"),
            message="Invalid URL"
        )
    ]
) 