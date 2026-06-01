"""
Tests for common/helpers/string_utils.py
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
)


class TestNormalUrlSafeB64Encode:
    """Test cases for normal_url_safe_b64_encode function."""

    def test_encode_simple_string(self):
        """Test encoding a simple string."""
        result = normal_url_safe_b64_encode("hello")
        assert isinstance(result, str)
        assert result != "hello"

    def test_encode_with_special_chars(self):
        """Test encoding string with special characters."""
        result = normal_url_safe_b64_encode("hello world! @#$%")
        assert isinstance(result, str)

    def test_encode_empty_string(self):
        """Test encoding an empty string."""
        result = normal_url_safe_b64_encode("")
        assert isinstance(result, str)

    def test_encode_unicode(self):
        """Test encoding Unicode characters."""
        result = normal_url_safe_b64_encode("hello 世界")
        assert isinstance(result, str)


class TestNormalUrlSafeB64Decode:
    """Test cases for normal_url_safe_b64_decode function."""

    def test_decode_simple_string(self):
        """Test decoding a simple encoded string."""
        encoded = normal_url_safe_b64_encode("hello")
        decoded = normal_url_safe_b64_decode(encoded)
        assert decoded == "hello"

    def test_decode_with_special_chars(self):
        """Test decoding string with special characters."""
        original = "hello world! @#$%"
        encoded = normal_url_safe_b64_encode(original)
        decoded = normal_url_safe_b64_decode(encoded)
        assert decoded == original

    def test_decode_empty_string(self):
        """Test decoding an empty encoded string."""
        encoded = normal_url_safe_b64_encode("")
        decoded = normal_url_safe_b64_decode(encoded)
        assert decoded == ""

    def test_decode_unicode(self):
        """Test decoding Unicode characters."""
        original = "hello 世界"
        encoded = normal_url_safe_b64_encode(original)
        decoded = normal_url_safe_b64_decode(encoded)
        assert decoded == original

    def test_decode_invalid_base64(self):
        """Test decoding invalid base64 string."""
        with pytest.raises(Exception):  # Will raise binascii.Error
            normal_url_safe_b64_decode("not valid base64!!!")


class TestUrlsafeBase64Encode:
    """Test cases for urlsafe_base64_encode function."""

    def test_encode_bytes(self):
        """Test encoding bytes."""
        result = urlsafe_base64_encode(b"hello")
        assert isinstance(result, str)
        assert '=' not in result  # No padding
        assert '\n' not in result  # No newlines

    def test_encode_empty_bytes(self):
        """Test encoding empty bytes."""
        result = urlsafe_base64_encode(b"")
        assert isinstance(result, str)

    def test_encode_long_bytes(self):
        """Test encoding long byte string."""
        long_bytes = b"a" * 1000
        result = urlsafe_base64_encode(long_bytes)
        assert isinstance(result, str)
        assert '=' not in result


class TestUrlsafeBase64Decode:
    """Test cases for urlsafe_base64_decode function."""

    def test_decode_bytes(self):
        """Test decoding encoded bytes."""
        original = b"hello"
        encoded = urlsafe_base64_encode(original)
        decoded = urlsafe_base64_decode(encoded)
        assert decoded == original

    def test_decode_empty(self):
        """Test decoding empty encoded string."""
        original = b""
        encoded = urlsafe_base64_encode(original)
        decoded = urlsafe_base64_decode(encoded)
        assert decoded == original

    def test_decode_with_padding(self):
        """Test decoding string that needs padding."""
        # Create an encoded string without padding
        encoded = "aGVsbG8"  # "hello" in base64 without padding
        decoded = urlsafe_base64_decode(encoded)
        assert decoded == b"hello"


    def test_decode_long_bytes(self):
        """Test decoding long encoded string."""
        original = b"a" * 1000
        encoded = urlsafe_base64_encode(original)
        decoded = urlsafe_base64_decode(encoded)
        assert decoded == original

    def test_decode_binascii_error(self):
        """Test decoding when urlsafe_b64decode raises BinasciiError."""
        from unittest.mock import patch
        from binascii import Error as BinasciiError

        # Mock urlsafe_b64decode to raise BinasciiError
        with patch('common.helpers.string_utils.base64.urlsafe_b64decode', side_effect=BinasciiError("Invalid base64")):
            with pytest.raises(ValueError):
                urlsafe_base64_decode("test")


class TestIsProtectedType:
    """Test cases for is_protected_type function."""

    def test_none_is_protected(self):
        """Test that None is a protected type."""
        assert is_protected_type(None) is True

    def test_int_is_protected(self):
        """Test that int is a protected type."""
        assert is_protected_type(42) is True
        assert is_protected_type(0) is True
        assert is_protected_type(-100) is True

    def test_float_is_protected(self):
        """Test that float is a protected type."""
        assert is_protected_type(3.14) is True
        assert is_protected_type(0.0) is True

    def test_decimal_is_protected(self):
        """Test that Decimal is a protected type."""
        assert is_protected_type(Decimal("10.5")) is True

    def test_datetime_is_protected(self):
        """Test that datetime is a protected type."""
        assert is_protected_type(datetime.now()) is True

    def test_date_is_protected(self):
        """Test that date is a protected type."""
        assert is_protected_type(date.today()) is True

    def test_time_is_protected(self):
        """Test that time is a protected type."""
        assert is_protected_type(time()) is True

    def test_string_not_protected(self):
        """Test that string is not a protected type."""
        assert is_protected_type("hello") is False

    def test_bytes_not_protected(self):
        """Test that bytes is not a protected type."""
        assert is_protected_type(b"hello") is False

    def test_list_not_protected(self):
        """Test that list is not a protected type."""
        assert is_protected_type([1, 2, 3]) is False

    def test_dict_not_protected(self):
        """Test that dict is not a protected type."""
        assert is_protected_type({'key': 'value'}) is False


class TestForceStr:
    """Test cases for force_str function."""

    def test_force_str_on_string(self):
        """Test force_str on a string returns same string."""
        result = force_str("hello")
        assert result == "hello"
        assert isinstance(result, str)

    def test_force_str_on_bytes(self):
        """Test force_str on bytes."""
        result = force_str(b"hello")
        assert result == "hello"
        assert isinstance(result, str)

    def test_force_str_on_bytes_with_encoding(self):
        """Test force_str on bytes with specific encoding."""
        result = force_str(b"hello", encoding='utf-8')
        assert result == "hello"

    def test_force_str_on_int(self):
        """Test force_str on integer."""
        result = force_str(42)
        assert result == "42"
        assert isinstance(result, str)

    def test_force_str_on_protected_type_strings_only(self):
        """Test force_str on protected type with strings_only=True."""
        result = force_str(42, strings_only=True)
        assert result == 42  # Should return original
        assert isinstance(result, int)

    def test_force_str_on_none_strings_only(self):
        """Test force_str on None with strings_only=True."""
        result = force_str(None, strings_only=True)
        assert result is None

    def test_force_str_on_float(self):
        """Test force_str on float."""
        result = force_str(3.14)
        assert result == "3.14"
        assert isinstance(result, str)

    def test_force_str_on_list(self):
        """Test force_str on list."""
        result = force_str([1, 2, 3])
        assert result == "[1, 2, 3]"
        assert isinstance(result, str)

    def test_force_str_with_unicode(self):
        """Test force_str with unicode characters."""
        result = force_str("hello 世界")
        assert result == "hello 世界"

    def test_force_str_bytes_with_unicode(self):
        """Test force_str on bytes with unicode."""
        result = force_str("hello 世界".encode('utf-8'))
        assert result == "hello 世界"

    def test_force_str_with_errors_param(self):
        """Test force_str with errors parameter."""
        # Valid UTF-8 sequence
        result = force_str(b"hello", errors='strict')
        assert result == "hello"


class TestForceBytes:
    """Test cases for force_bytes function."""

    def test_force_bytes_on_bytes(self):
        """Test force_bytes on bytes returns same bytes."""
        result = force_bytes(b"hello")
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_force_bytes_on_string(self):
        """Test force_bytes on string."""
        result = force_bytes("hello")
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_force_bytes_on_string_with_encoding(self):
        """Test force_bytes on string with specific encoding."""
        result = force_bytes("hello", encoding='utf-8')
        assert result == b"hello"

    def test_force_bytes_on_int(self):
        """Test force_bytes on integer."""
        result = force_bytes(42)
        assert result == b"42"
        assert isinstance(result, bytes)

    def test_force_bytes_on_protected_type_strings_only(self):
        """Test force_bytes on protected type with strings_only=True."""
        result = force_bytes(42, strings_only=True)
        assert result == 42  # Should return original
        assert isinstance(result, int)

    def test_force_bytes_on_none_strings_only(self):
        """Test force_bytes on None with strings_only=True."""
        result = force_bytes(None, strings_only=True)
        assert result is None

    def test_force_bytes_on_memoryview(self):
        """Test force_bytes on memoryview."""
        mv = memoryview(b"hello")
        result = force_bytes(mv)
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_force_bytes_with_unicode(self):
        """Test force_bytes with unicode characters."""
        result = force_bytes("hello 世界")
        assert result == "hello 世界".encode('utf-8')

    def test_force_bytes_with_different_encoding(self):
        """Test force_bytes with non-utf-8 encoding."""
        result = force_bytes("hello", encoding='ascii')
        assert result == b"hello"

    def test_force_bytes_reencoding(self):
        """Test force_bytes re-encoding from utf-8 to different encoding."""
        # Start with UTF-8 bytes
        utf8_bytes = "hello".encode('utf-8')
        # Re-encode to ASCII
        result = force_bytes(utf8_bytes, encoding='ascii')
        assert result == b"hello"

    def test_force_bytes_with_errors_param(self):
        """Test force_bytes with errors parameter."""
        result = force_bytes("hello", errors='strict')
        assert result == b"hello"
