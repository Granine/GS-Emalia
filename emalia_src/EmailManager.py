import imaplib
import smtplib
from email.mime.text import MIMEText
from email.parser import BytesParser
from email.policy import default
from email.message import Message
import os

# Set up IMAP connection to read emails
class EmailManager(): 
    """ A GS email manager
    TODO: support reply to emails
    TODO: support passwording
    TODO: support saving attachments
    TODO: support common smtp and imap
    """
    def __init__(self, enable_history:bool=True, HANDLER_EMAIL:str="", HANDLER_PASSWORD:str="", HANDLER_SMTP:str|dict="smtp.gmail.com", HANDLER_IMAP:str|dict="imap.gmail.com"):
        """initialize email manager service
        TODO @param `enable_history:str` if not False will record email sent and received, takes "local", [FILE PATH], "cache", "cache-[Int]" and "all"
          if local: save to a local file that can be accessed later at default location __file__/..
          if [FILE PATH]: save the local file to FILE PATH
          if cache: email in variable, unlimited size list from earliest to latest
          if cache-[INT]: save a max of INT email in cache, then delete from latest 
          if all, [FILE PATH]-[INT]: save to both variable and file
        @param `HANDLER_EMAIL:str` email address (also login email to smtp and imap), if not provided, attempt to read from environmental var
        @param `HANDLER_PASSWORD:str` login password, if not provided, attempt to read from environmental var
        @param `HANDLER_SMTP:str|dict` smtp server configuration, str for server address, dict for elements supported by smtplib.SMTP_SSL, enter None or "" or 0 to read from Environmental variable
        @param `HANDLER_IMAP:str|dict` imap server configuration, str for server address, dict for elements supported by imaplib.IMAP4_SSL, enter None or "" or 0 to read from Environmental variable
        """
        self.HANDLER_EMAIL = HANDLER_EMAIL if HANDLER_EMAIL else os.environ.get("HANDLER_EMAIL")
        assert self.HANDLER_EMAIL and isinstance(self.HANDLER_EMAIL, str)
        self.HANDLER_PASSWORD = HANDLER_PASSWORD if HANDLER_PASSWORD else os.environ.get("HANDLER_PASSWORD")
        assert self.HANDLER_PASSWORD and isinstance(self.HANDLER_PASSWORD, str)
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
    
    def send_email(self, target_email:str, email_subject:str, email_body:str=""):
        """Send a email to target email
        @param `target_email:str` to whom the email will be sent
        @param `email_subject:str` subject of email to send
        @param `email_body:str` body of the email
        TODO: support attachments
        """
        # Create response email
        outgoing_email = MIMEText(email_body)
        outgoing_email["From"] = self.HANDLER_EMAIL
        outgoing_email["To"] = target_email
        outgoing_email["Subject"] = email_subject

        # Send the response email
        with smtplib.SMTP_SSL(**self.HANDLER_SMTP) as server:
            server.login(self.HANDLER_EMAIL, self.HANDLER_PASSWORD)
            server.send_message(outgoing_email)
            
    def fetch_unread_email(self, count:int, mark_read:bool=True)->list:
        """ Fetch unread emails by count number
        @param `count:int` Number of latest unread to fetch, <0 for all
        @param `mark_read:bool` if true, mark fetched email as "\seen"
        @return `:list` return a list of email fetched. Format: [[unread_email_id, unread_email_status, email, unread_email raw]]
        """
        with imaplib.IMAP4_SSL(**self.HANDLER_IMAP) as imap:
            imap.login(self.HANDLER_EMAIL, self.HANDLER_PASSWORD)
            imap.select("inbox")

            # Search for all unread emails
            status, response = imap.search(None, "UNSEEN")
            # return based on count number
            unread_emails_ids = response[0].split()[count:] if count < len(response[0].split()) else response[0].split()
            unread_emails_list = []
            # fetch and record each email by ID
            for unread_email_id in unread_emails_ids:
                unread_email_status, unread_email = imap.fetch(unread_email_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)] BODY.PEEK[TEXT])")
                raw_email = unread_email[0][1]
                #!
                email = BytesParser(policy=default).parsebytes(raw_email)
                unread_emails_list.append([unread_email_id, unread_email_status, email, unread_email])
                # for somereason BODY.PEEK[] does not work, so label as seen/unseen
                if mark_read:
                    # Mark the email as read
                    imap.store(unread_email_id, "+FLAGS", "\\Seen")
                else:
                    imap.store(unread_email_id, "-FLAGS", "\\Seen")
        return unread_emails_list
    
    def mark_email(self, target:int|str, action:str="+FLAGS", flag:str="\\Seen")->list[Message]:
        """ Fetch unread emails by count number
        @param `count:int` Number of latest unread to fetch, <0 for all
        @param `mark_read:bool` if true, mark fetched email as "\seen"
        @return `:list` return a list of email fetched. Format: [[unread_email_id, unread_email_status, email, unread_email raw]]
        """
        if action.lower() == "add":
            action = "+FLAGS"
        elif action.lower() == "remove":
            action = "+FLAGS"
        elif action.lower() == "replace":
            action = "FLAGS"
        
        with imaplib.IMAP4_SSL(**self.HANDLER_IMAP) as imap:
            imap.login(self.HANDLER_EMAIL, self.HANDLER_PASSWORD)
            imap.select("inbox")

            # Search for all unread emails
            status, response = imap.search(None, "ALL")
            # return based on count number
            unread_emails_ids = response[0].split()[target:] if target < len(response[0].split()) else response[0].split()
            unread_emails_list = []
            # fetch and record each email by ID
            for unread_email_id in unread_emails_ids:
                    imap.store(unread_email_id, action, flag)
    
    
    
    def parse_email(self, email:Message):
        def clean(text):
        # clean text for creating a folder
            return "".join(c if c.isalnum() else "_" for c in text)
        subject = email["Subject"]
        body = ""
        if email.is_multipart():
            for part in email.walk():
                content_type = part.get_content_type()
                content_disposition = part.get("Content-Disposition", None)
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body = part.get_payload(decode=True).decode()
                elif content_disposition is not None and content_disposition.strip().startswith("attachment"):
                    file_data = part.get_payload(decode=True)
                    file_name = part.get_filename()
                    attachments.append((file_name, file_data))
                    
                    if file_name:
                        folder_name = clean(subject)
                        if not os.path.isdir(folder_name):
                            # make a folder for this email (named after the subject)
                            os.mkdir(folder_name)
                        filepath = os.path.join(folder_name, file_name)
                        # download attachment and save it
                        open(filepath, "wb").write(part.get_payload(decode=True))
        else:
            body = email.get_payload(decode=True).decode()

        # Get the attachments
        attachments = []
        if email.is_multipart():
            for part in email.walk():
                content_disposition = part.get("Content-Disposition", None)
            
        print("Subject:", subject)
        print("Body:", body)


a = EmailManager()
print(a_r:=a.fetch_unread_email(2, False))
a.parse_email(a_r[0][2])