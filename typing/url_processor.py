"""URL에서 텍스트를 추출하는 기능"""
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import re
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

    # 문장 구분자 정의
    SENTENCE_DELIMITERS = [
        r'(?<=[.!?])(?=[^.!?\s])',  # 마침표/느낌표/물음표 뒤에 다른 문자가 오는 경우
        r'(?<=[.!?])(?:\s+|["\']|\n|$)',  # 마침표/느낌표/물음표 + (공백 또는 따옴표 또는 줄바꿈 또는 문장끝)
        r'(?<=[:;])(?:\s+|\n|$)',          # 콜론/세미콜론 + (공백 또는 줄바꿈 또는 문장끝)
        r'\n{2,}',                          # 2개 이상의 줄바꿈
    ]
    
    # 문장 정리를 위한 패턴
    CLEANUP_PATTERNS = [
        (r'\s+', ' '),     # 연속된 공백을 하나로
        (r'^\s+', ''),     # 시작 공백 제거
        (r'\s+$', ''),     # 끝 공백 제거
    ]

    # 필터링할 패턴 추가
    FILTER_PATTERNS = [
        r'^https?:/?/?',  # URL 프로토콜
        r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}',  # 도메인
        r'^\d+$',  # 숫자로만 이루어진 텍스트
        r'^[a-zA-Z0-9_-]+$',  # 영문/숫자/특수문자로만 이루어진 텍스트
    ]

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
                    filtered_text = cls.filter_text(text)
                    if filtered_text:
                        text_content.append(filtered_text)
            
            # 그 다음 문단 태그 처리
            for tag in soup.find_all('p'):
                text = tag.get_text().strip()
                filtered_text = cls.filter_text(text)
                if filtered_text:
                    text_content.append(filtered_text)
            
            # 전체 텍스트를 문장 단위로 분리
            return cls.split_into_sentences('\n'.join(text_content))
            
        except Exception as e:
            raise ValueError(f"URL에서 텍스트를 가져오는데 실패했습니다: {str(e)}")

    @classmethod
    def filter_text(cls, text: str) -> str:
        """텍스트를 필터링합니다."""
        # 허용된 문자만 포함
        filtered_text = ''.join(
            char for char in text 
            if cls.is_allowed_char(char)
        )
        
        # 정리 패턴 적용
        for pattern, replacement in cls.CLEANUP_PATTERNS:
            filtered_text = re.sub(pattern, replacement, filtered_text)
            
        filtered_text = filtered_text.strip()
        
        # 의미 없는 텍스트 필터링
        if any(re.search(pattern, filtered_text) for pattern in cls.FILTER_PATTERNS):
            return ''
            
        return filtered_text if len(filtered_text) > cls.MIN_SENTENCE_LENGTH else ''

    @classmethod
    def split_into_sentences(cls, text: str) -> str:
        """텍스트를 문장 단위로 분리합니다."""
        # 초기 문장을 처리
        current_text = text.strip()
        
        # 각 구분자를 순차적으로 적용하여 문장 분리
        for delimiter in cls.SENTENCE_DELIMITERS:
            parts = re.split(delimiter, current_text)
            parts = [part.strip() for part in parts if part.strip()]
            current_text = '\n'.join(parts)
        
        # 문장들을 리스트로 변환
        sentences = [
            s.strip() for s in current_text.split('\n')
            if s.strip() and len(s.strip()) >= cls.MIN_SENTENCE_LENGTH
        ]
        
        # 중복 제거
        sentences = list(dict.fromkeys(sentences))
        
        return '\n'.join(sentences) 