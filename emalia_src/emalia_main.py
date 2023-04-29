import EmailManager

"""Emalia logic
Standard mode
- actively check email
* Future version may support google api, ifttt or zappier for passive trigger
- check request
- check permission
- complete request
- return confirmation email that may contain the next step

- Each "session" or "conversation" is a new reply chain
- sending new email starts a new emalia session
"""

class Emalia():
    def __init__(self, HANDLER_EMAIL:str="", HANDLER_PASSWORD:str="", HANDLER_SMTP:str|dict="smtp.gmail.com", HANDLER_IMAP:str|dict="imap.gmail.com"):
        self.email_handler = EmailManager.EmailManager(HANDLER_PASSWORD=HANDLER_PASSWORD, HANDLER_EMAIL=HANDLER_EMAIL, HANDLER_SMTP=HANDLER_SMTP, HANDLER_IMAP=HANDLER_IMAP)
        
if __name__ == "__main__":
    emalia_instance = Emalia()
    