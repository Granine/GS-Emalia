from EmailManager import EmailManager
import FileManager
import threading
import time
from datetime import datetime
import os
from email.message import Message # email template
import re
import logging
import traceback
import sys

class Emalia():
    """an email interacted system that manages and perform a list of predefined tasks.
    Basic:
        - can set different security levels for each task (free, restricted(can set multiple password or let emalia remember vip sender emails), locked)
        - can set a range files to access, support directory depth control, whitelist and blacklist
        - conversation through email and reply
    Receive Email Structure:
        body: [action] [command(s)] [password] + [attachments]
    Emalia Response Email Structure:
        body: [response] [potential next step command(s)] [footer] + [attachments]
    Supported tasks: (not case sensitive)
        0. manage emalia: MANAGE/[Emalia Instance Name]/0 [command]: various command to manage emalia
        1. read file: READ/1 [PATH]: zip if directory
        2. write file: WRITE/2 [(optional)PATH to directory] + attachment list: write all to a directory (auto create if DNE)
        3. make request: REQUEST/3 [Method] // [URL] // [HEADER] // [BODY]: enter None for a field that is not needed, result will be returned
        4. execute powershell: SHELL/POWERSHELL/4 [command]: (DANGER) run powershell command
        5. execute python: PYTHON/5 [code]: (DANGER) run python in-process
        6. email action: EMAIL/6 [action]: perform actions like send or forward new email 
        
        9. custom tasks: CUSTOM/9 [task]: store custom tasks, one can run with their custom command
    """
    # ==================Hot-edit Options==========================
    # can modify anytime, even externally
    instance_name:str = "Emalia" # name of the service robot, Emalia is her default name
    server_running:bool = False # if True, a server is running, set to false will stop server at next loop
    freeze_server:bool = False # if True, will temporarily stop tasks execution except emalia_manager. 
    statistics:dict = {"sent": None, "received": None} # track statistics for current/last running instance, {"sent":int, "received":int}
    permission = {} # holds information regarding what the user can/cannot access
    vip_list = {} # a list of senders with special permission
    custom_tasks = {} # user defined tasks on the run
    # =====================Configurable Settings=========================
    # should not be changed mid-execution or may error out
    _max_response_per_cycle = 3
    _max_send_count = 1 # max email emalia can send per instance, <0 for infinite
    _file_roots = f"{__file__}/../../" # should point to GS-Emalia directory
    # =====================Runtime Variable=========================
    # do not change unless confident
    server_start_time:datetime = None # tracks the start time of last server
    logger = None

    
    def __init__(self, permission:str="default", HANDLER_EMAIL:str="", HANDLER_PASSWORD:str="", HANDLER_SMTP:str|dict="smtp.gmail.com", HANDLER_IMAP:str|dict="imap.gmail.com", logger:logging.Logger=None):
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
        if not logger:
            self.logger = logging.Logger(name=__file__, level=logging.INFO)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)
        else:
            self.logger = logger
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
            try:
                # get unseen_emails
                unseen_email_ids = self.email_handler.unseen_emails()
                # fetch email by id
                
                if unseen_email_ids:
                    unseen_email_id_selected = unseen_email_ids[0]
                    unseen_email = self.email_handler.fetch_email(unseen_email_id_selected)
                    unseen_email_parsed = self.email_handler.parse_email(unseen_email)
                    self.email_handler.assert_valid_email_received(unseen_email_parsed)
                else:
                    unseen_email = None
                    unseen_email_parsed = None
            except Exception as err:
                self.logger.exception("Error when attempting to fetch new emails")
                unseen_email = None
                unseen_email_parsed = None
                
            # handle user request if new email detected
            if unseen_email:
                try:
                    user_command = re.search("^\w*", unseen_email_parsed["body"]).group()
                    # if server freeze, force all command to system manager
                    if self.freeze_server:
                        response_email = self.task_list[0]["function"](unseen_email_parsed)
                    elif user_command in self.task_list.keys():
                        response_email = self.task_list[user_command]["function"](unseen_email_parsed)
                    else:
                        response_email = self._new_emalia_email(unseen_email_parsed, f"Error: Unknown command {user_command}")
                except Exception as err:
                    self.logger.exception(f"Error: {user_command} failed")
                    response_email = self._new_emalia_email(unseen_email_parsed, f"Error: {err}", traceback.format_exc())
                # freeze if conditions not met
                if (self.statistics["sent"] >= self._max_send_count) and (self._max_send_count >= 0):
                    self.freeze_server = True
                # reply based on action
                try:
                    self.email_handler.send_email(response_email)
                    self.statistics["sent"] += 1
                    self.logger.info(f"Sent email to {unseen_email_parsed['sender']}")
                        
                except Exception as err:
                    self.logger.exception("Error when attempting send email")
                
            # calculate and sleep for desired scan_interval - current loop_time
            loop_end_time = datetime.now()
            loop_time = (loop_end_time - loop_start_time).total_seconds()
            if (scan_interval - loop_time) > 0:
                time.sleep(scan_interval - loop_time)
            self.logger.info(f"Loop time: {loop_time}")

        # return server completion time
        return datetime.now()
        
    def break_loop(self):
        """Stop the execution of mainloop externally
        Repeated call have no effect"""
        self.server_running = False
    
    # ========================== WORKER FUNCTIONs =========================
    def _validate_password(password):
        """Check if a user provided password is the save as record
        """
        pass
    
    def _new_emalia_email(self, email_received:Message, email_subject:str, email_body:str="", attachments:list=[]):
        """Prepare emalia format email
        TODO add footer to body
        """
        target_email = email_received["sender"]
        email_body = email_body
        return self.email_handler.new_email(target_email=target_email, email_subject=email_subject, email_body=email_body, attachments=attachments)
    
    
    @property
    def task_list(self):
        """Worker function list and access keys
        TODO: Redesign task_list so it is more concise
        """
        default_worker_functions = {
            "0": {"function": self._action_manage_emalia, 
                "name":"System Settings", "trigger": ["0", "manage", f"{self.instance_name}"], "description": "Edit system settings and trigger system commands", "help": ""},
            "1": {"function": self._action_read_file,
                "name":"Get File", "trigger": ["1", "read"], "description": "Search and return a file as attachment", "help": ""},
            "2": {"function": self._action_write_file,
                "name":"Write File", "trigger": ["2", "write"], "description": "Store an email attachment as file", "help": ""},
            "3": {"function": self._action_make_request,
                "name":"HTTP Request", "trigger": ["3", "request"], "description": "Make a http request and get the response", "help": ""},
            "4": {"function": self._action_execute_powershell,
                "name":"Execute Powershell", "trigger": ["4", "shell", "powershell"], "description": "Run a powershell script", "help": ""},
            "5": {"function": self._action_execute_python,
                "name":"Execute Python", "trigger": ["5", "python"], "description": "Run a python script in line", "help": ""},
            "6": {"function": self._action_execute_python,
                "name":"Email Action", "trigger": ["6", "email"], "description": "Manage and perform email related actions", "help": ""},
            "9": {"function": self._action_register_custom_task,
                "name":"Custom Tasks", "trigger": ["9", "custom"], "description": "Store a new user defined task chian", "help": ""}
        }
        default_worker_functions.update(self.custom_tasks)
        return default_worker_functions
        
    def _action_manage_emalia(self, email_received:Message, emalia_command:str=""):
        """0 Alter emalia behaviour by emalia permission
        """
        main_menu = """Options"""
        response_email_subject = f"MANAGE: complete"
        response_email_body = main_menu
        return self._new_emalia_email(email_received, response_email_subject, response_email_body, attachments=[path])
    
    def _action_read_file(self, email_received:Message)->Message:
        """1 find one file and attach it as attachment to response email by emalia permission and return it
        @param `email_received:Message` the email sent by sender
        @return `:Message` the response email to sender
        """
        main_menu = """Options"""
        path = email_received["body"].split(" ", 1)[1]
        if path:
            if os.path.exists(path):
                searched_path = path
            elif searched_path:=FileManager.search_exact(path, path=self._file_roots, ignore_type=True, exception=False):
                pass
            elif searched_path:=FileManager.search_exact(path, path=self._file_roots, ignore_type=False, exception=False):
                pass
            else:
                raise AttributeError(f"{path} does not exist")
            # after absolute path found, return email as attachment
            path = os.path.realpath(searched_path)
            path_name = os.path.basename(path)
            response_email_subject = f"READ: {path_name} complete"
            response_email_body = f"{path_name} found at {path}"
            return self._new_emalia_email(email_received, response_email_subject, response_email_body, attachments=[path])
        else:
            # return main options
            response_email_subject = f"READ: Main Menu"
            response_email_body = main_menu
            return self._new_emalia_email(email_received, response_email_subject, response_email_body, attachments=[path])
                    
    
    def _action_write_file(self, email_received:Message, content:bytes, path:str="DEFAULT"):
        """2 write the content of a file by emalia permission
        """
        pass
        
    def _action_make_request(self, email_received:Message, http_method, http_url, http_header, http_body):
        """3 make an external request by emalia permission
        """
        pass
    
    def _action_execute_powershell(self, email_received:Message, command):
        """4 Execute a powershell command by emalia permission
        """
        pass
    
    def _action_execute_python(self, email_received:Message, python):
        """5 Execute a python script in current process by emalia permission
        """
        pass
    
    def _action_register_custom_task(self, email_received:Message, task):
        """9 user can store custom tasks (nest multiple or define new)
        """
        self.custom_tasks = {}
        pass
        
    def _action_run_custom_task(self, email_received:Message, name):
        """? run user stored custom tasks 
        """
        pass

    
if __name__ == "__main__":
    """Allow one button trigger of emalia mainloop, testing for now, may change to terminal configurable later"""
    #TODO support comamndline trigger of emalia_main.py
    emalia_instance = Emalia()
    print("PID:" + str(emalia_instance.PID))
    # start emalia in different thread to prevent blocking
    main_loop_thread = threading.Thread(target=emalia_instance.main_loop)
    main_loop_thread.start()
    # exit emalia and external controls
    supported_command = ["stop"]
    while selection:=input("Command:\n") not in supported_command:
        print(f"Input {selection} is not a valid command from list: {supported_command}")
    emalia_instance.break_loop()
    main_loop_thread.join()
    print("Tasks complete")
        
        