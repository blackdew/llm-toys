"""URL에서 텍스트를 추출하는 기능"""
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from typing import List

class URLProcessor:
    # 허용할 문자 범위 정의
    ALLOWED_CHARS = {
        'korean': ('\uAC00', '\uD7A3'),  # 한글
        'korean_jamo': ('\u3131', '\u318E'),  # 한글 자음/모음
        'punctuation': '.,!?()[]{}":;\'- ',  # 기본 문장 부호
    }
    
    MIN_SENTENCE_LENGTH = 10
    EXCLUDED_TAGS = ['script', 'style', 'header', 'footer', 'nav']
    TEXT_TAGS = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']

    @classmethod
    def is_url(cls, text: str) -> bool:
        """입력된 텍스트가 URL인지 확인합니다."""
        try:
            # 앞뒤 공백이 있거나 중간에 공백이 있으면 거부
            if text != text.strip() or ' ' in text:
                return False
            
            result = urlparse(text)
            # HTTP/HTTPS 프로토콜만 허용
            return all([
                result.scheme in ('http', 'https'),
                result.netloc
            ])
        except:
            return False

    @classmethod
    def is_allowed_char(cls, char: str) -> bool:
        """문자가 허용된 범위에 있는지 확인합니다."""
        if char.isalnum():  # 영문자와 숫자는 허용
            return True
        
        # 한글 검사
        if cls.ALLOWED_CHARS['korean'][0] <= char <= cls.ALLOWED_CHARS['korean'][1]:
            return True
            
        # 한글 자음/모음 검사
        if cls.ALLOWED_CHARS['korean_jamo'][0] <= char <= cls.ALLOWED_CHARS['korean_jamo'][1]:
            return True
            
        # 문장 부호 검사
        return char in cls.ALLOWED_CHARS['punctuation']

    @classmethod
    def extract_text_from_url(cls, url: str) -> str:
        """URL에서 텍스트를 추출합니다."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 불필요한 태그 제거
            for tag in soup(cls.EXCLUDED_TAGS):
                tag.decompose()
            
            text_content = []
            
            # 제목 태그들 먼저 처리 (h1-h6)
            for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                for tag in soup.find_all(tag_name):
                    text = tag.get_text().strip()
                    filtered_text = ''.join(
                        char for char in text 
                        if cls.is_allowed_char(char)
                    )
                    filtered_text = filtered_text.strip()
                    if len(filtered_text) > cls.MIN_SENTENCE_LENGTH:
                        text_content.append(filtered_text)
            
            # 그 다음 문단 태그 처리
            for tag in soup.find_all('p'):
                text = tag.get_text().strip()
                filtered_text = ''.join(
                    char for char in text 
                    if cls.is_allowed_char(char)
                )
                filtered_text = filtered_text.strip()
                if len(filtered_text) > cls.MIN_SENTENCE_LENGTH:
                    text_content.append(filtered_text)
            
            return '\n'.join(text_content)
        except Exception as e:
            raise ValueError(f"URL에서 텍스트를 가져오는데 실패했습니다: {str(e)}") 