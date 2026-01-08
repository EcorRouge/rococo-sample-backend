"""
Comprehensive tests for common/helpers/string_utils.py
"""
import pytest
from datetime import datetime, date, time
from decimal import Decimal
from common.helpers.string_utils import (
    normal_url_safe_b64_decode,
    normal_url_safe_b64_encode,
    is_protected_type,
    urlsafe_base64_encode,
    urlsafe_base64_decode,
    force_str,
    force_bytes,
    RANDOM_STRING_CHARS
)


class TestBase64Functions:
    """Tests for base64 encoding/decoding functions."""

    def test_normal_url_safe_b64_encode(self):
        """Test normal URL-safe base64 encoding."""
        # Test simple string
        result = normal_url_safe_b64_encode("hello world")
        assert isinstance(result, str)
        assert len(result) > 0

        # Test with special characters
        result = normal_url_safe_b64_encode("test@example.com")
        assert isinstance(result, str)

    def test_normal_url_safe_b64_decode(self):
        """Test normal URL-safe base64 decoding."""
        # Encode then decode
        original = "hello world"
        encoded = normal_url_safe_b64_encode(original)
        decoded = normal_url_safe_b64_decode(encoded)
        assert decoded == original

        # Test with special characters
        original = "test@example.com"
        encoded = normal_url_safe_b64_encode(original)
        decoded = normal_url_safe_b64_decode(encoded)
        assert decoded == original

    def test_urlsafe_base64_encode(self):
        """Test URL-safe base64 encoding with trailing equal sign removal."""
        # Test with bytes
        result = urlsafe_base64_encode(b"test")
        assert isinstance(result, str)
        assert '=' not in result  # Should strip trailing =

        # Test with longer string
        result = urlsafe_base64_encode(b"hello world test")
        assert isinstance(result, str)

    def test_urlsafe_base64_decode(self):
        """Test URL-safe base64 decoding."""
        # Encode then decode
        original = b"test data"
        encoded = urlsafe_base64_encode(original)
        decoded = urlsafe_base64_decode(encoded)
        assert decoded == original

        # Test with various lengths
        for text in [b"a", b"ab", b"abc", b"abcd", b"abcde"]:
            encoded = urlsafe_base64_encode(text)
            decoded = urlsafe_base64_decode(encoded)
            assert decoded == text

    def test_urlsafe_base64_decode_invalid(self):
        """Test URL-safe base64 decoding with invalid input."""
        with pytest.raises(ValueError):
            urlsafe_base64_decode("!!!invalid!!!")


class TestIsProtectedType:
    """Tests for is_protected_type function."""

    def test_is_protected_type_none(self):
        """Test None is a protected type."""
        assert is_protected_type(None) is True

    def test_is_protected_type_int(self):
        """Test int is a protected type."""
        assert is_protected_type(42) is True
        assert is_protected_type(0) is True
        assert is_protected_type(-100) is True

    def test_is_protected_type_float(self):
        """Test float is a protected type."""
        assert is_protected_type(3.14) is True
        assert is_protected_type(0.0) is True
        assert is_protected_type(-2.5) is True

    def test_is_protected_type_decimal(self):
        """Test Decimal is a protected type."""
        assert is_protected_type(Decimal('10.5')) is True
        assert is_protected_type(Decimal('0')) is True

    def test_is_protected_type_datetime(self):
        """Test datetime is a protected type."""
        assert is_protected_type(datetime.now()) is True

    def test_is_protected_type_date(self):
        """Test date is a protected type."""
        assert is_protected_type(date.today()) is True

    def test_is_protected_type_time(self):
        """Test time is a protected type."""
        assert is_protected_type(time()) is True

    def test_is_protected_type_string(self):
        """Test string is not a protected type."""
        assert is_protected_type("test") is False
        assert is_protected_type("") is False

    def test_is_protected_type_list(self):
        """Test list is not a protected type."""
        assert is_protected_type([1, 2, 3]) is False

    def test_is_protected_type_dict(self):
        """Test dict is not a protected type."""
        assert is_protected_type({"key": "value"}) is False


class TestForceStr:
    """Tests for force_str function."""

    def test_force_str_with_string(self):
        """Test force_str with already a string."""
        result = force_str("hello")
        assert result == "hello"
        assert isinstance(result, str)

    def test_force_str_with_bytes(self):
        """Test force_str with bytes."""
        result = force_str(b"hello")
        assert result == "hello"
        assert isinstance(result, str)

    def test_force_str_with_bytes_utf8(self):
        """Test force_str with UTF-8 encoded bytes."""
        result = force_str(b"caf\xc3\xa9")  # café in UTF-8
        assert result == "café"

    def test_force_str_with_bytes_different_encoding(self):
        """Test force_str with different encoding."""
        # Latin-1 encoded bytes
        text = "café"
        encoded = text.encode('latin-1')
        result = force_str(encoded, encoding='latin-1')
        assert result == "café"

    def test_force_str_with_int(self):
        """Test force_str with integer."""
        result = force_str(42)
        assert result == "42"
        assert isinstance(result, str)

    def test_force_str_with_float(self):
        """Test force_str with float."""
        result = force_str(3.14)
        assert result == "3.14"

    def test_force_str_with_none(self):
        """Test force_str with None."""
        result = force_str(None)
        assert result == "None"

    def test_force_str_strings_only_with_protected_type(self):
        """Test force_str with strings_only=True and protected type."""
        result = force_str(42, strings_only=True)
        assert result == 42  # Should not convert
        assert isinstance(result, int)

        result = force_str(None, strings_only=True)
        assert result is None

    def test_force_str_strings_only_with_string(self):
        """Test force_str with strings_only=True and string."""
        result = force_str("hello", strings_only=True)
        assert result == "hello"
        assert isinstance(result, str)

    def test_force_str_with_error_handling(self):
        """Test force_str with invalid bytes and error handling."""
        # Invalid UTF-8 sequence
        invalid_bytes = b'\xff\xfe'
        result = force_str(invalid_bytes, errors='ignore')
        assert isinstance(result, str)


class TestForceBytes:
    """Tests for force_bytes function."""

    def test_force_bytes_with_bytes(self):
        """Test force_bytes with already bytes."""
        result = force_bytes(b"hello")
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_force_bytes_with_string(self):
        """Test force_bytes with string."""
        result = force_bytes("hello")
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_force_bytes_with_unicode(self):
        """Test force_bytes with Unicode string."""
        result = force_bytes("café")
        assert isinstance(result, bytes)
        # Verify it can be decoded back
        assert result.decode('utf-8') == "café"

    def test_force_bytes_with_different_encoding(self):
        """Test force_bytes with different encoding."""
        result = force_bytes("café", encoding='latin-1')
        assert isinstance(result, bytes)
        assert result.decode('latin-1') == "café"

    def test_force_bytes_with_bytes_different_encoding(self):
        """Test force_bytes re-encoding bytes to different encoding."""
        utf8_bytes = "café".encode('utf-8')
        result = force_bytes(utf8_bytes, encoding='latin-1')
        assert isinstance(result, bytes)

    def test_force_bytes_with_int(self):
        """Test force_bytes with integer."""
        result = force_bytes(42)
        assert result == b"42"
        assert isinstance(result, bytes)

    def test_force_bytes_with_float(self):
        """Test force_bytes with float."""
        result = force_bytes(3.14)
        assert result == b"3.14"

    def test_force_bytes_strings_only_with_protected_type(self):
        """Test force_bytes with strings_only=True and protected type."""
        result = force_bytes(42, strings_only=True)
        assert result == 42  # Should not convert
        assert isinstance(result, int)

        result = force_bytes(None, strings_only=True)
        assert result is None

    def test_force_bytes_strings_only_with_string(self):
        """Test force_bytes with strings_only=True and string."""
        result = force_bytes("hello", strings_only=True)
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_force_bytes_with_memoryview(self):
        """Test force_bytes with memoryview."""
        data = b"test data"
        mv = memoryview(data)
        result = force_bytes(mv)
        assert result == data
        assert isinstance(result, bytes)

    def test_force_bytes_with_error_handling(self):
        """Test force_bytes with error handling."""
        # String with characters that can't be encoded in ascii
        text = "café"
        result = force_bytes(text, encoding='ascii', errors='ignore')
        assert isinstance(result, bytes)


class TestConstants:
    """Tests for module constants."""

    def test_random_string_chars(self):
        """Test RANDOM_STRING_CHARS constant."""
        assert isinstance(RANDOM_STRING_CHARS, str)
        assert len(RANDOM_STRING_CHARS) > 0
        assert 'a' in RANDOM_STRING_CHARS
        assert 'z' in RANDOM_STRING_CHARS
        assert '0' in RANDOM_STRING_CHARS
        assert '9' in RANDOM_STRING_CHARS
        # Should not contain uppercase or special characters
        assert 'A' not in RANDOM_STRING_CHARS
        assert '@' not in RANDOM_STRING_CHARS


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_force_str_empty_string(self):
        """Test force_str with empty string."""
        assert force_str("") == ""

    def test_force_bytes_empty_string(self):
        """Test force_bytes with empty string."""
        assert force_bytes("") == b""

    def test_force_str_empty_bytes(self):
        """Test force_str with empty bytes."""
        assert force_str(b"") == ""

    def test_force_bytes_empty_bytes(self):
        """Test force_bytes with empty bytes."""
        assert force_bytes(b"") == b""

    def test_urlsafe_base64_encode_empty(self):
        """Test URL-safe base64 encoding with empty bytes."""
        result = urlsafe_base64_encode(b"")
        assert isinstance(result, str)

    def test_base64_roundtrip_special_chars(self):
        """Test base64 encoding/decoding roundtrip with special characters."""
        special_strings = [
            "test@example.com",
            "hello+world=123",
            "user:password",
            "a/b/c",
            "!@#$%^&*()"
        ]
        for original in special_strings:
            encoded = normal_url_safe_b64_encode(original)
            decoded = normal_url_safe_b64_decode(encoded)
            assert decoded == original

    def test_force_str_with_subclass(self):
        """Test force_str with string subclass."""
        class MyStr(str):
            pass

        result = force_str(MyStr("test"))
        assert result == "test"
        assert isinstance(result, str)
