import pytest
import sys
from unittest import mock
sys.path.append(f"{__file__}/../../../emalia_src")
import EmailManager
import smtplib

def test_EmailManager_basic():
        # Create a MagicMock object that returns "abc" when its read method is called
    mock_s = mock.MagicMock(spec=smtplib.SMTP_SSL)
    mock_s.login.return_value = "value"

    # Implement the __enter__ and __exit__ methods to support the context management protocol
    mock_s.__enter__.return_value = mock_s
    mock_s.__exit__.return_value = None

    # Replace smtplib.SMTP_SSL with the MagicMock object using patch
    with mock.patch('smtplib.SMTP_SSL', return_value=mock_s) as mock_smtp:
        emanager = EmailManager.EmailManager()
        assert emanager
