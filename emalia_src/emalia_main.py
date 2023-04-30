import EmailManager
import FileManager
import threading
import time

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
    def __init__(self, permission:str="default", HANDLER_EMAIL:str="", HANDLER_PASSWORD:str="", HANDLER_SMTP:str|dict="smtp.gmail.com", HANDLER_IMAP:str|dict="imap.gmail.com"):
        """Create a email service bot that start handling incomming emails

        @param permission (str, optional): What Emalia is allowed to do to local file
            {"action": ACTION, range": RANGE}
                ACTION(str|list): "read", "write", "shell", "all" what Emalia is allowed to do with data
                RANGE(int|list): directory Emalia can access
                    if int: directory levels Emalia is allowed to perform the action relative to __FILE__, negative for all range
                        eg: if 1 directory a/b/emlia_main.py, Emalia can access a/b/text.txt, a/b/c/text.text but not nothing in a/ or a/b/c/d please see check_path_in_range->example for more information
                    if list of string: directories (and subdirectory) Emalia can access 
            "default": short for {"action": ["read", "write"], "range": 1}
            "full": short for {"action": "all", "range": -1}
        @param HANDLER_EMAIL (str, optional): will attempt to read from env var if empty or not provided
        @param HANDLER_PASSWORD (str|optional): will attempt to read from env var if empty or not provided
        @param HANDLER_SMTP:str|dict SMTP default supports gmail, will attempt to read from env var if empty
        @param HANDLER_IMAP:str|dict IMAP default supports gmail, will attempt to read from env var if empty
        """
        if isinstance(permission, str):
            if permission.lower() == "default":
                self.permission = {"action": ["read", "write"], "range": 1}
            elif permission.lower() == "full":
                self.permission = {"action": "all", "range": -1}
        elif isinstance(permission, dict) and ("action" in permission.keys()) and ("range" in permission.keys()):
            self.permission = permission
        else:
            raise AttributeError("Unknown permission value")
        
        self.email_handler = EmailManager.EmailManager(HANDLER_PASSWORD=HANDLER_PASSWORD, HANDLER_EMAIL=HANDLER_EMAIL, HANDLER_SMTP=HANDLER_SMTP, HANDLER_IMAP=HANDLER_IMAP)
        
    def main_loop(self):
        self.running = True
        while self.running:
            time.sleep(2)
            print("loop")
            pass
        
    def break_loop(self):
        self.running = False
        
if __name__ == "__main__":
    emalia_instance = Emalia()
    main_loop_thread = threading.Thread(target=emalia_instance.main_loop)
    main_loop_thread.start()
    supported_command = ["stop"]
    while selection:=input("Command: ") not in supported_command:
        print(f"input {selection} is not a valid command: {supported_command}")
    emalia_instance.break_loop()
    main_loop_thread.join()
    print("Tasks complete")
        
        