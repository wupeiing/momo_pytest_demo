import re
import logging

# Keep only ASCII letters, digits, and CJK ideographs — strip everything else
# (dots, hyphens, spaces, punctuation, etc.) so "j.k" == "j k" == "jk"
_NORMALIZE_RE = re.compile(r'[^a-zA-Z0-9一-鿿㐀-䶿豈-﫿]')
_CJK_RE = re.compile(r'[一-鿿㐀-䶿豈-﫿]')

logger = logging.getLogger(__name__)

class KeywordMatcher:
    @staticmethod
    def _normalize(text: str) -> str:
        """Remove all non-alphanumeric non-CJK characters and lowercase."""
        return _NORMALIZE_RE.sub('', text).lower()

    @staticmethod
    def _is_subsequence(token: str, name: str) -> bool:
        """Return True if every character in *token* appears in *name* in order."""
        it = iter(name)
        return all(ch in it for ch in token)

    @staticmethod
    def _has_cjk(text: str) -> bool:
        return bool(_CJK_RE.search(text))

    @staticmethod
    def tokenize(keyword: str) -> list[str]:
        """Split keyword into tokens by whitespace, filtering empty strings."""
        return [t for t in keyword.split() if t]

    @staticmethod
    def _token_in_name(token: str, name: str) -> bool:
        """Check if a normalized token matches the normalized name.

        Tries substring match first. If the token contains CJK characters and
        substring match fails, falls back to subsequence matching so that
        e.g. "無線耳機" matches "真無線藍牙耳機".
        """
        norm_token = KeywordMatcher._normalize(token)
        if norm_token in name:
            return True
        if KeywordMatcher._has_cjk(norm_token):
            return KeywordMatcher._is_subsequence(norm_token, name)
        return False

    @staticmethod
    def all_keywords_in_name(keyword: str, name: str) -> bool:
        """Return True if every token in *keyword* appears in *name* (case-insensitive).

        Both token and name are normalized before comparison, so 'jk' matches
        'j.k', 'j k', 'j-k', etc. For CJK tokens, falls back to subsequence
        matching when substring match fails, so "無線耳機" matches "真無線藍牙耳機".
        """
        logger.debug("keyword: '%s', name: '%s'", keyword, name)
        tokens = KeywordMatcher.tokenize(keyword)
        if not tokens:
            logger.debug("No valid tokens found in keyword.")
            return False
        normalized_name = KeywordMatcher._normalize(name)
        return all(KeywordMatcher._token_in_name(token, normalized_name) for token in tokens)
