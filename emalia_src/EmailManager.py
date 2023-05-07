import imaplib
import smtplib
from email.mime.text import MIMEText
from email.contentmanager import ContentManager
from email.parser import BytesParser
from email.policy import default
from email.message import Message
from email import message_from_bytes
import os
import pathlib
import re

# Set up IMAP connection to read emails
class EmailManager(): 
    """ A GS email manager
    TODO: support reply to emails
    TODO: support passwording
    TODO: support saving attachments
    TODO: support common smtp and imap
    """
    def __init__(self, enable_history:bool=True, attachment_path:str="", HANDLER_EMAIL:str="", HANDLER_PASSWORD:str="", HANDLER_SMTP:str|dict="smtp.gmail.com", HANDLER_IMAP:str|dict="imap.gmail.com"):
        """initialize email manager service
        TODO @param `enable_history:str` if not False will record email sent and received, takes "local", [FILE PATH], "cache", "cache-[Int]" and "all"
          if local: save to a local file that can be accessed later at default location __file__/..
          if [FILE PATH]: save the local file to FILE PATH
          if cache: email in variable, unlimited size list from earliest to latest
          if cache-[INT]: save a max of INT email in cache, then delete from latest 
          if all, [FILE PATH]-[INT]: save to both variable and file
        @param `attachment_path:str` path to save attachments, attachment stored in folder named subject+id, default saved in par as EmailManager
        @param `HANDLER_EMAIL:str` email address (also login email to smtp and imap), if not provided, attempt to read from environmental var
        @param `HANDLER_PASSWORD:str` login password, if not provided, attempt to read from environmental var
        @param `HANDLER_SMTP:str|dict` smtp server configuration, str for server address, dict for elements supported by smtplib.SMTP_SSL, enter None or "" or 0 to read from Environmental variable
        @param `HANDLER_IMAP:str|dict` imap server configuration, str for server address, dict for elements supported by imaplib.IMAP4_SSL, enter None or "" or 0 to read from Environmental variable
        """
        self.HANDLER_EMAIL = HANDLER_EMAIL if HANDLER_EMAIL else os.environ.get("HANDLER_EMAIL")
        assert self.HANDLER_EMAIL and isinstance(self.HANDLER_EMAIL, str)
        self.HANDLER_PASSWORD = HANDLER_PASSWORD if HANDLER_PASSWORD else os.environ.get("HANDLER_PASSWORD")
        assert self.HANDLER_PASSWORD and isinstance(self.HANDLER_PASSWORD, str)
        self.attachment_path = pathlib.Path(attachment_path).resolve() if attachment_path else pathlib.Path( __file__ + "/..").resolve()
        assert self.attachment_path.exists()
        # SMTP
        if HANDLER_SMTP and isinstance(HANDLER_SMTP, str):
            self.HANDLER_SMTP = {"host": HANDLER_SMTP, "port": 465}
        elif HANDLER_SMTP and isinstance(HANDLER_SMTP, dict):
            self.HANDLER_SMTP = HANDLER_SMTP
        else:
            self.HANDLER_SMTP = eval(os.environ.get("HANDLER_SMTP"))
        # test dict is compilable with smtp
        with smtplib.SMTP_SSL(**self.HANDLER_SMTP) as test:
            pass
        
        # IMAP
        if HANDLER_IMAP and isinstance(HANDLER_IMAP, str):
            self.HANDLER_IMAP = {"host": HANDLER_IMAP, "port": 993}
        elif HANDLER_IMAP and isinstance(HANDLER_IMAP, dict):
            self.HANDLER_IMAP = HANDLER_IMAP
        else:
            self.HANDLER_IMAP = eval(os.environ.get("HANDLER_SMTP"))
        # test dict is compilable with imap
        with imaplib.IMAP4_SSL(**self.HANDLER_IMAP) as test:
            pass
        
    def unseen_emails(self):
        """Return a list of unseen email ids
        @return `:list` of unseen email ids
        """
        with imaplib.IMAP4_SSL(**self.HANDLER_IMAP) as imap:
            imap.login(self.HANDLER_EMAIL, self.HANDLER_PASSWORD)
            imap.select("inbox", readonly=True)

            # Search for all unread emails
            search_status, response = imap.search(None, "UNSEEN")
            if search_status.lower() != "ok":
                raise ConnectionError(f"Cannot perform search")
            unseen_email_ids = [s.decode() for s in response[0].split()]
        return unseen_email_ids
    
    def fetch_email(self, email_id:int, mark_read:bool=True)->Message:
        with imaplib.IMAP4_SSL(**self.HANDLER_IMAP) as imap:
            imap.login(self.HANDLER_EMAIL, self.HANDLER_PASSWORD)
            imap.select("inbox", readonly=True)
            email_status, email_content = imap.fetch(email_id, "(BODY.PEEK[])")
            if email_status.lower() != "ok":
                raise ConnectionError(f"Cannot fetch email {email_id}")
            raw_email = email_content[0][1]
            parsed_email = BytesParser(policy=default).parsebytes(raw_email)
            parsed_email = message_from_bytes(raw_email)
            # for some reason BODY.PEEK[] does not work, so label as seen/unseen
            if mark_read:
                # Mark the email as read
                imap.store(email_id, "+FLAGS", "\\Seen")
            else:
                imap.store(email_id, "-FLAGS", "\\Seen")
        return parsed_email
    
    def send_email(self, target_email:str, email_subject:str, email_body:str="")->Message:
        """Send a email to target email
        @param `target_email:str` to whom the email will be sent
        @param `email_subject:str` subject of email to send
        @param `email_body:str` body of the email
        @return `:Message` outgoing email
        TODO: support attachments
        """
        # Create response email
        outgoing_email = Message()
        outgoing_email.set_type("TEXT/ENRICHED")
        outgoing_email["From"] = self.HANDLER_EMAIL
        outgoing_email["To"] = target_email
        outgoing_email["Subject"] = email_subject
        outgoing_email.set_payload(email_body)

        # Send the response email
        with smtplib.SMTP_SSL(**self.HANDLER_SMTP) as server:
            server.login(self.HANDLER_EMAIL, self.HANDLER_PASSWORD)
            server.send_message(outgoing_email)
        return outgoing_email
            
    def fetch_unread_emails(self, count:int, mark_read:bool=True)->list:
        """ Fetch unread emails and body by count number
        @param `count:int` Number of latest unread to fetch, <0 for all
        @param `mark_read:bool` if true, mark fetched email as "\seen"
        @return `:list` return a list of email fetched. Format: [[unread_email_id, unread_email_status, email, unread_email raw]]
        """
        with imaplib.IMAP4_SSL(**self.HANDLER_IMAP) as imap:
            imap.login(self.HANDLER_EMAIL, self.HANDLER_PASSWORD)
            imap.select("inbox", readonly=True)

            # Search for all unread emails
            search_status, response = imap.search(None, "UNSEEN")
            if search_status.lower() != "ok":
                raise ConnectionError(f"Cannot perform search")
            # return based on count number
            unread_emails_ids = response[0].split()[-count:] if count < len(response[0].split()) else response[0].split()
            unread_emails_list = []
            # fetch and record each email by ID
            for unread_email_id in unread_emails_ids:
                unread_email_id = unread_email_id.decode()
                unread_email_status, unread_email = imap.fetch(unread_email_id, "(BODY.PEEK[])") # or RFC822
                if unread_email_status.lower() != "ok":
                    raise ConnectionError(f"Cannot fetch email {unread_email_id}: {unread_email}")
                raw_email = unread_email[0][1]
                email = BytesParser(policy=default).parsebytes(raw_email)
                email = message_from_bytes(raw_email)
                unread_emails_list.append([unread_email_id, email])
                # for some reason BODY.PEEK[] does not work, so label as seen/unseen
                if mark_read:
                    # Mark the email as read
                    imap.store(unread_email_id, "+FLAGS", "\\Seen")
                else:
                    imap.store(unread_email_id, "-FLAGS", "\\Seen")
        return unread_emails_list
    
    def mark_emails(self, target:int|list|str, action:str="+FLAGS", flag:str="\\Seen")->list[str]:
        """  Mark target emails with flag based on action
        @param `target:int|list|str`
          if int: the x most recent email to label in inbox
          if list of email ids: mark each id listed
          if str: mark the email in target
        @param `action:str` "add", "+FLAG", "remove", "-FLAG", "replace", "FLAGS"
        @param  `flag:str` tag to mark, must be supported tags, for example "\\Seen"
        @return `:list` return a list of email ids marked
        """
        if action.lower() == "add":
            action = "+FLAGS"
        elif action.lower() == "remove":
            action = "+FLAGS"
        elif action.lower() == "replace":
            action = "FLAGS"
        
        with imaplib.IMAP4_SSL(**self.HANDLER_IMAP) as imap:
            imap.login(self.HANDLER_EMAIL, self.HANDLER_PASSWORD)
            imap.select("inbox", readonly=True)

            if isinstance(target, int):
                status, response = imap.search(None, "ALL")
                emails_ids = response[0].split()[-target:] if target < len(response[0].split()) else response[0].split()
            elif (isinstance(target, list) or isinstance(target, tuple)) and target:
                emails_ids = target
            elif isinstance(target, str) and target:
                emails_ids = [target]
            else:
                raise AttributeError("Unknown target")
            emails_list = []
            
            # fetch and record each email by ID
            for email_id in emails_ids:
                if isinstance(email_id, bytes):
                    emails_list.append(email_id.decode())
                elif isinstance(email_id, str):
                    emails_list.append(email_id)
                else:
                    raise AttributeError("Unknown email ID type")
                imap.store(email_id, action, flag)
        return emails_list
    
    def parse_email(self, email:Message)->dict:
        """Parse a Message format email into simple, clean dict while downloading attachments
        @param `email:Message` the email to parse
        @return `:dict` with keys "body", "return_path", "received", date", "from", "subject", "sender", "to", "cc", "attachments:list of path"
        """
        def clean(text):
            # clean text for creating a folder
            return "".join(c if c.isalnum() else "_" for c in text)
        body = ""
        attachments = []
        if email.is_multipart():
            for part in email.walk():
                content_type = part.get_content_type()
                content_disposition = part.get("Content-Disposition", None)
                # Get body
                if content_type == "text/plain" and "attachment" not in str(content_disposition):
                    body = part.get_payload(decode=True).decode()
                # Get the attachments
                elif content_disposition is not None and content_disposition.strip().startswith("attachment"):
                    file_data = part.get_payload(decode=True)
                    file_name = part.get_filename()
                    attachments.append((file_name, file_data))
                    
                    if file_name:
                        folder_name = self.attachment_path
                        if not os.path.isdir(folder_name):
                            # make a folder for this email (named after the subject)
                            os.mkdir(folder_name)
                        filepath = os.path.join(folder_name, file_name)
                        # download attachment and save it
                        open(filepath, "wb").write(part.get_payload(decode=True))
        else:
            body = email.get_payload(decode=True).decode()
        if email["Sender"]:
            sender = email["Sender"]  
        elif "<" in email["From"] and ">" in email["From"]:
            sender = re.search("<.*?>", email["From"]).group(0)
        else:
            sender = None
        return {
            "body": body, 
            "return-Path": email["Return-Path"], 
            "received": email["Received"], 
            "date": email["Date"],  
            "from": email["From"],  
            "subject": email["Subject"],  
            "sender": sender,
            "to": email["To"], 
            "cc": email["cc"],
            "attachments": attachments
        }
        
