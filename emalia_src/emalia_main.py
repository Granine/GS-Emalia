from EmailManager import EmailManager
import FileManager
import threading
import time
from datetime import datetime
import os

class Emalia():
    """an email interacted system that manages and perform a list of predefined tasks.
    Basic:
        - can set different security levels for each task (free, restricted(can set multiple password or let emalia remember vip sender emails), locked)
        - can set a range files to access, support directory depth control, whitelist and blacklist
        - conversation through email and reply
    Receive Email Structure:
        body: [action] [command(s)] [password] + [attachments]
    Reply Email Structure:
        body: [response] [potential next step command(s)] [footer]] + [attachments]
    Supported tasks: (not case sensitive)
        0. manage emalia: [Emalia Instance Name]/0 [command]: various command to manage emalia
        1. read file: READ/1 [PATH]: zip if directory
        2. write file: WRITE/2 [(optional)PATH to directory] + attachment list: write all to a directory (auto create if DNE)
        3. make request: REQUEST/3 [Method] // [URL] // [HEADER] // [BODY]: enter None for a field that is not needed, result will be returned
        4. execute powershell: SHELL/POWERSHELL/4 [command]: (DANGER) run powershell command
        5. execute python: PYTHON/5 [code]: (DANGER) run python in-process
        6. email action: EMAIL/6 [action]: perform actions like send or forward new email 
        
        9. custom tasks: CUSTOM/9 [task]: store custom tasks, one can run with their custom command
    """
    instance_name:str = "Emalia" # name of the service robot, Emalia is her default name
    server_start_time:datetime = None # tracks the start time of last server
    server_running:bool = False # if True, a server is running, set to false will stop server at next loop
    max_send_count = 0 # max email emalia can send per instance, <0 for infinite
    statistics:dict = {"sent": None, "received": None} # track statistics for current/last running instance, {"sent":int, "received":int}
    
    def __init__(self, permission:str="default", HANDLER_EMAIL:str="", HANDLER_PASSWORD:str="", HANDLER_SMTP:str|dict="smtp.gmail.com", HANDLER_IMAP:str|dict="imap.gmail.com"):
        """Create a email service robot instance. Make sure you run mainloop to start service
        @param permission (str, optional): What Emalia is allowed to do to local file
            {"action": ACTION, range": RANGE}
                ACTION(str|list): "read", "write", "shell", "all", "none" what Emalia is allowed to do with data
                RANGE(int|list): directory Emalia can access
                    if int: directory levels Emalia is allowed to perform the action relative to __FILE__, negative for all range
                        eg: if 1 directory a/b/emlia_main.py, Emalia can access a/b/text.txt, a/b/c/text.text but not nothing in a/ or a/b/c/d please see check_path_in_range->example for more information
                    if list of string: directories (and subdirectory) Emalia can access 
                    <=0 for no access, but one should really set action instead
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
        self.PID = os.getpid()
        self.email_handler = EmailManager(HANDLER_PASSWORD=HANDLER_PASSWORD, HANDLER_EMAIL=HANDLER_EMAIL, HANDLER_SMTP=HANDLER_SMTP, HANDLER_IMAP=HANDLER_IMAP)
        
    def main_loop(self, scan_interval:float=5.0):
        """Start the email listener
        @param `scan_interval:float` the time to pause between each email scan session, if processing tie (request time >= scan_interval, there will be no pause)
        @return `:datetime` time of main_loop completion
        Info: Only one main_loop or async_main_loop can run, all other calls will not create new Emalia loops. Please create new Emalia Object to do such task
        """
        self.PID = os.getpid()
        self.server_running = True
        self.server_start_time = datetime.now()
        # infinity loop unless self.server_running is changed in loop or from other functions in separate process
        self.statistics = {"sent": 0, "received": 0}
        while self.server_running:
            loop_start_time = datetime.now()
            #print(self.email_handler.fetch_unread_email(1, False))
            print(unseen_email_ids:=self.email_handler.unseen_emails())
            unseen_email_body = self.email_handler.fetch_email(unseen_email_ids[0])
            unseen_email_parsed = self.email_handler.parse_email(unseen_email_body)
            print(unseen_email_parsed["body"])
            # test reply
            if self.statistics["sent"] < self.max_sent_count or self.max_sent_count <= 0:
                self.email_handler.send_email(unseen_email_parsed["sender"], "Reply: " + unseen_email_parsed["subject"], "sample body", attachments=[])
                self.statistics["sent"] += 1
                print(f"Sent email to {unseen_email_parsed['sender']}")
            # calculate and sleep for desired scan_interval - current loop_time
            loop_end_time = datetime.now()
            loop_time = (loop_end_time - loop_start_time).total_seconds()
            if (scan_interval - loop_time) > 0:
                time.sleep(scan_interval - loop_time)
            print("Loop time" + str(loop_time))
        # return server completion time
        return datetime.now()
        
    def break_loop(self):
        """Stop the execution of mainloop externally
        Repeated call have no effect"""
        self.server_running = False
        
    def _validate_password(password):
        """Check if a user provided password is the save as record
        """
        pass
        
    def _action_manage_emalia(self, emalia_command):
        """0 Alter emalia behaviour by emalia permission
        """
        pass
        
    def _action_read_file(self, path:str):
        """1 read the content of a file by emalia permission
        """
        pass
    
    def _action_write_file(self, content:bytes, path:str="DEFAULT"):
        """2 write the content of a file by emalia permission
        """
        pass
        
    def _action_make_request(self, http_method, http_url, http_header, http_body):
        """3 make an external request by emalia permission
        """
        pass
    
    def _action_execute_powershell(self, command):
        """4 Execute a powershell command by emalia permission
        """
        pass
    
    def _action_execute_python(self, python):
        """5 Execute a python script in current process by emalia permission
        """
        pass
    
    def _store_custom_task(self, task):
        """9 user can store custom tasks (nest multiple or define new)
        """
        
    def _run_custom_task(self, name):
        """? run user stored custom tasks 
        """
    
if __name__ == "__main__":
    #TODO support comamndline trigger of emalia_main.py
    emalia_instance = Emalia()
    print("PID:" + str(emalia_instance.PID))
    # start emalia in different thread to prevent blocking
    main_loop_thread = threading.Thread(target=emalia_instance.main_loop)
    main_loop_thread.start()
    # exit emalia and external controls
    supported_command = ["stop"]
    while selection:=input("Command: ") not in supported_command:
        print(f"Input {selection} is not a valid command from list: {supported_command}")
    emalia_instance.break_loop()
    main_loop_thread.join()
    print("Tasks complete")
        
        