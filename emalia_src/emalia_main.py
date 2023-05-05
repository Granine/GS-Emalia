import EmailManager
import FileManager
import threading
import time
import datetime

"""Emalia: an email interacted system that manages and perform a list of predefined tasks.
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
    instance_name = "Emalia" # name of the service robot, Emalia is her default name
    def __init__(self, permission:str="default", HANDLER_EMAIL:str="", HANDLER_PASSWORD:str="", HANDLER_SMTP:str|dict="smtp.gmail.com", HANDLER_IMAP:str|dict="imap.gmail.com"):
        """Create a email service robot instance. Make sure you run mainloop to start service
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
        
    def main_loop(self, scan_interval:float=5):
        """Start the email listener
        @param `scan_interval:float` the time to pause between each email scan session, if processing tie (request time >= scan_interval, there will be no pause)
        Info: Only one main_loop or async_main_loop can run, all other calls will not create new Emalia loops. Please create new Emalia Object to do such task
        """
        # TODO check running
        # TODO enforce time between scan
        self.running = True
        self.server_start_time = datetime.datetime.now()
        # infinitly loop unless self.running is changed in loop or from other functions in separate process
        while self.running:
            time.sleep(scan_interval)
            print(self.email_handler.fetch_unread_email(1, False))
            pass
        # return servver completion time
        return datetime.datetime.now()
        
    def break_loop(self):
        self.running = False
        
if __name__ == "__main__":
    emalia_instance = Emalia()
    main_loop_thread = threading.Thread(target=emalia_instance.main_loop)
    main_loop_thread.start()
    supported_command = ["stop"]
    while selection:=input("Command: ") not in supported_command:
        print(f"input {selection} is not a valid command from list: {supported_command}")
    emalia_instance.break_loop()
    main_loop_thread.join()
    print("Tasks complete")
        
        