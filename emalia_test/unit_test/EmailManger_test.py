import pytest
import sys
from unittest import mock
sys.path.append(f"{__file__}/../../../emalia_src")
import EmailManager
import smtplib
import imaplib
from email.parser import BytesParser
from email.policy import default

def test_EmailManager_basic_init():
    # mock smtp
    mock_smtp_value = mock.MagicMock(spec=smtplib.SMTP_SSL)
    mock_smtp_value.login.return_value = "True"
    mock_smtp_value.send_message.return_value = "Complete"
    # Implement the __enter__ and __exit__ methods to support the context management protocol
    mock_smtp_value.__enter__.return_value = mock_smtp_value
    mock_smtp_value.__exit__.return_value = None
    
    # mock imap
    mock_imap_value = mock.MagicMock(spec=imaplib.IMAP4_SSL)
    mock_imap_value.login.return_value = "True"
    # Implement the __enter__ and __exit__ methods to support the context management protocol
    mock_imap_value.__enter__.return_value = mock_imap_value
    mock_imap_value.__exit__.return_value = None
    mock_select_response = ""
    mock_imap_value.select.return_value = mock_select_response
    mock_search_response = ('OK', [b'1 2 3'])
    mock_imap_value.search.return_value = mock_search_response
    mock_fetch_response = ('OK', [(b'1', b'SOME_DATA')])
    mock_imap_value.fetch.return_value = mock_fetch_response
    
    