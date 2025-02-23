# -*- coding: utf-8 -*-
import pytest
from unittest.mock import patch, mock_open
import os
from dotenv import load_dotenv
from utils.my_tushare import get_pro_api, convert_to_tushare_code

# Test data
TEST_TOKEN = "test_token_12345"


def test_convert_to_tushare_code():
    # Test Shanghai stock codes
    assert convert_to_tushare_code("600000") == "600000.SH"
    assert convert_to_tushare_code("600000.SH") == "600000.SH"

    # Test Shenzhen stock codes
    assert convert_to_tushare_code("000001") == "000001.SZ"
    assert convert_to_tushare_code("000001.SZ") == "000001.SZ"
    assert convert_to_tushare_code("300750") == "300750.SZ"

    # Test invalid codes
    with pytest.raises(ValueError):
        convert_to_tushare_code("123456")  # Invalid prefix
    with pytest.raises(ValueError):
        convert_to_tushare_code("ABCDEF")  # Non-numeric
    with pytest.raises(ValueError):
        convert_to_tushare_code("")  # Empty string


@patch.dict(os.environ, {"TUSHARE_TOKEN": TEST_TOKEN})
@patch("tushare.set_token")
@patch("tushare.pro_api")
def test_get_pro_api_success(mock_pro_api, mock_set_token):
    # Test successful token retrieval
    result = get_pro_api()
    mock_set_token.assert_called_once_with(TEST_TOKEN)
    mock_pro_api.assert_called_once()
    assert result == mock_pro_api.return_value


def test_get_pro_api_missing_token():
    # Test missing token in environment
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            get_pro_api()
        assert "Tushare token not found" in str(exc_info.value)


def test_get_pro_api_empty_token():
    # Test empty token in environment
    with patch.dict(os.environ, {"TUSHARE_TOKEN": ""}):
        with pytest.raises(ValueError) as exc_info:
            get_pro_api()
        assert "Tushare token not found" in str(exc_info.value)
