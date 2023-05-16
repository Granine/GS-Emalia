import os
import pathlib
# email action
import imaplib
import smtplib
from email.message import Message
# email parsing
import re
from email.parser import BytesParser
from email import message_from_bytes
# for email formatting
from email.policy import default
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
# for zip file
import zipfile
from io import BytesIO
# file saving
import csv

# Set up IMAP connection to read emails
class EmailManager(): 
    """ An email manager class that scan, read and reply to emails
    Time analysis (second): imap: login ~ 1select, mainbox ~ 0.2, search ~ 0.2, fetch ~ 0.2/email
    smtp: login ~ 1, send ~ 0.3
    Combined: unseen_emails ~ 1.7, fetch_email ~ 1.7/email, parse ~ 0,label ~ 1+0.3/email
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
    
    def add_attachment(self, message:MIMEMultipart, attachment_path:str):
        # Ensure the message is a MIMEMultipart object
        if not isinstance(message, MIMEMultipart):
            raise AttributeError("message must be MIMEMultipart type")
        # Make sure the file exists
        if not os.path.exists(attachment_path):
            raise FileNotFoundError(f"{attachment_path} not found")
        # raw file, directly attachment
        if os.path.isfile(attachment_path):
            with open(attachment_path, "rb") as attachment_f:
                attachment_data = attachment_f.read()
        # directory, zip first
        elif os.path.isdir(attachment_path):
            # Create the zip file
            buffer = BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipped_file:
                # get each file for zipping
                for root, dirs, files in os.walk(attachment_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipped_file.write(file_path, os.path.relpath(file_path, dirs))
            buffer.seek(0)
            attachment_data = buffer.getvalue()
        else:
            raise AttributeError(f"{attachment_path} is an invalid file type")
            
        mime_attachment = MIMEApplication(bytes(attachment_data), Name=os.path.basename(attachment_path))
        mime_attachment.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
        message.attach(mime_attachment)

        return message
    
    def fetch_email(self, email_id:int, mark_read:bool=True)->Message:
        with imaplib.IMAP4_SSL(**self.HANDLER_IMAP) as imap:
            imap.login(self.HANDLER_EMAIL, self.HANDLER_PASSWORD)
            imap.select("inbox")
            if mark_read:
                email_status, email_content = imap.fetch(email_id, "(BODY[])")
            else:
                email_status, email_content = imap.fetch(email_id, "(BODY.PEEK[])")
            if email_status.lower() != "ok":
                raise ConnectionError(f"Cannot fetch email {email_id}")
            # basic parsing to Message
            raw_email = email_content[0][1]
            parsed_email = BytesParser(policy=default).parsebytes(raw_email)
            parsed_email = message_from_bytes(raw_email)
        return parsed_email
    
    def new_email(self, target_email:str, email_subject:str, email_body:str="", attachments:list|str=[], main_body_type="TEXT/PLAIN")->Message:
        """Prepare a new email
        @param `target_email:str` to whom the email will be sent
        @param `email_subject:str` subject of email to send
        @param `email_body:str` body of the email
        @param `attachments:list of str or path` for each path here, attempt to read and attach file
        @return `:Message` outgoing email
        TODO: support attachments
        """
        # Create response email
        outgoing_email = MIMEMultipart()
        outgoing_email["From"] = self.HANDLER_EMAIL
        outgoing_email["To"] = target_email
        outgoing_email["Subject"] = email_subject
        body = Message()
        body.set_type(main_body_type)
        body.set_payload(email_body)
        outgoing_email.attach(body)
        # handle payload
        if isinstance(attachments, str): attachments = [attachments]
        for attachment in attachments:
            # will modify attachment
            self.add_attachment(outgoing_email, attachment)
        # Send the response email
        return outgoing_email
        
    def send_email(self, outgoing_email:Message, target_email:str="")->Message:
        """Send a email to target email
        @param `outgoing_email:Message` email to send
        @param `target_email:str` the email address to send email, replace if provided. Will directly modify original
        @return `outgoing_email:str` return the outgoing email 
        Please prepare email with new_email()
        """
        # if target_email provided
        if target_email:
            outgoing_email["To"] = target_email
        # if target email DNE
        if not outgoing_email["To"]:
            raise AttributeError("Outgoing email do not have a valid receiver")
        # sending !
        with smtplib.SMTP_SSL(**self.HANDLER_SMTP) as server:
            server.login(self.HANDLER_EMAIL, self.HANDLER_PASSWORD)
            server.send_message(outgoing_email)
        return outgoing_email
        
            
    def fetch_unread_emails(self, count:int, mark_read:bool=True)->list:
        """ Fetch unread emails and body by count number
        @param `count:int` Number of latest unread to fetch, <0 for all
        @param `mark_read:bool` if true, mark fetched email as "\seen"
        @return `:list of tuple of len=2` return a list of email fetched. Format: [(unread_email_id:Str, email:Message)]
        """
        with imaplib.IMAP4_SSL(**self.HANDLER_IMAP) as imap:
            imap.login(self.HANDLER_EMAIL, self.HANDLER_PASSWORD)
            imap.select("inbox") #, readonly=True

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
                # make read of not
                if mark_read:
                    unread_email_status, unread_email = imap.fetch(unread_email_id, "(BODY[])") # or RFC822
                else:
                    unread_email_status, unread_email = imap.fetch(unread_email_id, "(BODY.PEEK[])")
                
                # check fetch is success
                if unread_email_status.lower() != "ok":
                    raise ConnectionError(f"Cannot fetch email {unread_email_id}: {unread_email}")
                raw_email = unread_email[0][1]
                email = BytesParser(policy=default).parsebytes(raw_email)
                email = message_from_bytes(raw_email)
                unread_emails_list.append([unread_email_id, email])
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
        @return `:dict` with keys "id", "content-type", "body:list", "return_path", "received", date", "from", "subject", "sender", "to", "cc", "attachments:list of path"
        if the email is standard format, [0] is body, [1] is the same body but html encoded
        """
        def clean(text):
            # clean text for creating a folder
            return "".join(c if c.isalnum() else "_" for c in text)
        body = []
        attachments = []
        if email.is_multipart():
            for part in email.walk():
                content_type = part.get_content_type()
                content_disposition = part.get("Content-Disposition", None)
                # Get body
                if content_type == "text/plain" and "attachment" not in str(content_disposition):
                    body.append((part.get_payload(decode=True).decode("utf-8-sig").replace("\ufeff", "").strip(), "plain"))
                elif content_type == "text/html" and "attachment" not in str(content_disposition):
                    body.append((part.get_payload(decode=True).decode("utf-8-sig").replace("\ufeff", "").strip(), "html"))
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
            body.append((email.get_payload(decode=True).decode("utf-8-sig"), email.get_content_type().split("/")[1]))
        if email["Sender"]:
            sender = email["Sender"]  
        elif "<" in email["From"] and ">" in email["From"]:
            sender = re.search("<.*?>", email["From"]).group(0)
        else:
            sender = None
        return {
            "id": email["Message-Id"],
            "content-type": email["Content-Type"],
            "body": body, 
            "return-path": email["Return-Path"], 
            "received": email["Received"], 
            "date": email["Date"],  
            "from": email["From"],  
            "subject": email["Subject"],  
            "sender": sender,
            "to": email["To"], 
            "cc": email["cc"],
            "attachments": attachments
        }
        
    def assert_valid_email_received(self, parsed_email:dict):
        """Assert and email have necessary component for responding
        @param `parsed_email:dict` the email sent by sender, parsed to dict format with EmailManager.parse_email
        @exception `:AssertionError` if file is not a valid email format needed to understand email and make reply
        """
        assert parsed_email["sender"] or parsed_email["return_path"]
        assert isinstance(parsed_email["subject"])
        # multiple body in email, check each is tuple with type at right
        for body in parsed_email["body"]:
            assert isinstance(body, tuple)
            assert isinstance(body[0], str)
            
    def split_by_reply(self, email_received:Message|str)->list:
        """split a email into series of replies [body, last reply, reply from 2 times before, ...]
        it appears there are 3 types of responses
        1 + 2 appear together, where 1 is pure text including response email
        2 is html version, with responses in quoteblocks
        3 is when response messages are raised by >, and >> levels
        1, 2 will be parsed later due to their difficulties
        3 will depend on key words like On XXX wrote: to determine the start of the message.
        """
        pass
        
    def store_email_to_csv(self, email_received:Message|str, path:str, action:str, comment:str=""):
        """Save full email content to csv (commonly used to track history)
        @param `email_received:Message|dict` parse or unparsed email
        @param `path:str` file location to save, create if dne
        @param `action:str` "received"|"sent", email type
        @param `comment:str` comment to add for email
        """
        # Check if the file exists and has data
        file_exists = False
        try:
            with open(path, 'r') as csvfile:
                file_exists = bool(csvfile.readline())
        except FileNotFoundError:
            pass
        # parse raw email
        if isinstance(email_received, Message):
            email_received = self.parse_email(email_received)
        # prepare for csv header insertion
        email_received_appended = email_received.copy()
        email_received_appended["action"] = action
        email_received_appended["comment"] = comment

        # Append the email to the CSV file
        with open(path, 'a', newline='', encoding="utf-8-sig") as csvfile:
            # col = parsed email keys
            fieldnames = email_received_appended.keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # writ col name if new file
            if not file_exists:
                writer.writeheader()

            writer.writerow(email_received_appended)
