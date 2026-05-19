import re
import logging
import time

# Keep only ASCII letters, digits, and CJK ideographs — strip everything else
# (dots, hyphens, spaces, punctuation, etc.) so "j.k" == "j k" == "jk"
_NORMALIZE_RE = re.compile(r'[^a-zA-Z0-9一-鿿㐀-䶿豈-﫿]')

logger = logging.getLogger(__name__)

class KeywordMatcher:
    @staticmethod
    def _normalize(text: str) -> str:
        """Remove all non-alphanumeric non-CJK characters and lowercase."""
        return _NORMALIZE_RE.sub('', text).lower()

    @staticmethod
    def tokenize(keyword: str) -> list[str]:
        """Split keyword into tokens by whitespace, filtering empty strings."""
        return [t for t in keyword.split() if t]

    @staticmethod
    def all_keywords_in_name(keyword: str, name: str) -> bool:
        """Return True if every token in *keyword* appears in *name* (case-insensitive).

        Both token and name are normalized before comparison, so 'jk' matches
        'j.k', 'j k', 'j-k', etc. CJK substrings are preserved for Chinese keywords.
        """
        logger.debug("keyword: '%s', name: '%s'", keyword, name)
        tokens = KeywordMatcher.tokenize(keyword)
        if not tokens:
            logger.debug("No valid tokens found in keyword.")
            return False
        normalized_name = KeywordMatcher._normalize(name)
        return all(KeywordMatcher._normalize(token) in normalized_name for token in tokens)
