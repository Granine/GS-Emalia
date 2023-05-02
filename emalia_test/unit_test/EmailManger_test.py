import pytest
import sys
from unittest import mock
sys.path.append(f"{__file__}/../../../emalia_src")
import EmailManager
import smtplib
import imaplib
from email.parser import BytesParser
from email.policy import default

# TODO test reading and saving attachments
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
    mock_search_response = ("OK", [b"123 234 345"])
    mock_imap_value.search.return_value = mock_search_response
    mock_fetch_response = ("OK", [(b"345", b"CONTENT")])
    mock_imap_value.fetch.return_value = mock_fetch_response
    mock_imap_value.store.return_value = ""
    
    
    # Replace smtplib.SMTP_SSL with the MagicMock object using patch
    with mock.patch("smtplib.SMTP_SSL", return_value=mock_smtp_value) as mock_smtp:
        with mock.patch("imaplib.IMAP4_SSL", return_value=mock_imap_value) as mock_imap:
            # init function
            emanager = EmailManager.EmailManager(HANDLER_EMAIL="1", HANDLER_PASSWORD="2")
            assert emanager
            
            # send email, use mask smtp
            emanager.send_email("1", "2", "3")
            mock_smtp_value.send_message.assert_called_once()
            
            # test fetch unread email
            email_list = emanager.fetch_unread_email(1)
            mock_imap_value.search.assert_called_once()
            assert len(email_list) == 1
            assert isinstance(email_list, list)
            assert email_list[0][0] == "345"
            
            # test parse email
            parsed_email = emanager.parse_email(email_list[0][1])
            assert parsed_email
            
            # test mark
            marked_email = emanager.mark_email(email_list[0][0])
            assert marked_email == [email_list[0][0]]
            marked_email = emanager.mark_email([email_list[0][0]])
            assert marked_email == [email_list[0][0]]
            marked_email = emanager.mark_email(1)
            assert isinstance(marked_email, list)