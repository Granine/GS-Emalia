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
import gpt_request

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
        7. GPT query: GPT/7 <gpt settings> [query body]: Get a gpt response to email body
        
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
    _save_path = f"{__file__}/../../history.csv" # a history file with .csv extension, create if DNE 
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
            response_email = None
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
                    # save email
                    self.email_handler.store_email_to_csv(unseen_email_parsed, self._save_path, "received"  )
                    # parse command
                    user_command = re.search("^\w*", unseen_email_parsed["body"][0][0]).group().lower() # normalize to lower case
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
            if unseen_email or response_email:
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
    def _validate_password(password:str):
        """Check if a user provided password is the save as record
        """
        pass
    
    def _new_emalia_email(self, email_received:dict, email_subject:str="", email_body:str="", attachments:list|str=[]):
        """Prepare emalia format email for reply
        @param `email_received:dict` the parsed email from sender (extract sender)
        @param `email_subject:str` subject of the email 
        @param `email_body:str` subject of the email 
        @param `attachments:list of str` the list of file path to attach with email, auto zip if dir
        TODO add footer to body
        TODO reply format
        """
        target_email = email_received["sender"]
        email_body = email_body
        return self.email_handler.new_email(target_email=target_email, email_subject=email_subject, email_body=email_body, attachments=attachments)
    
    def _parse_email_part(self, email_body:str)->tuple:
        """Return a tuple of 3 that contains (Raw body part, [] options, <> options) make sure to strip reply section before requesting
        @param `email_body:str` the email body to be parse, must be plain string, not html or rich
        @return `:tuple of size 3` 
        response will not contain <> or [], will escape with "\". So <123> with return 123, \<123\> will not
        Requires brackets to be paired, there cannot be floating brackets
        """
        # find<>
        email_sharp_bracket_pattern = r"(?<!\\)<([^<>]*)(?<!\\)>"
        matches = re.findall(email_sharp_bracket_pattern, email_body)
        # replace <> with empty [] to simplify raw body parsing. can remove this and spend more time to update raw_body parsing to handle both [] and <>
        email_body = re.sub(email_sharp_bracket_pattern, "[]", email_body)
        email_sharp_bracket_part = []
        # append <> found to save list
        for match in matches:
            if match.strip():
                email_sharp_bracket_part.append(match.strip())
                
        # find []
        email_square_bracket_pattern = r"(?<!\\)\[([^\[\]]*)(?<!\\)\]"
        matches = re.findall(email_square_bracket_pattern, email_body)
        email_square_bracket_part = []
        for match in matches:
            if match.strip(">").strip():
                email_square_bracket_part.append(match.strip())
            
        # find and store body content
        email_raw_body_pattern = r"(?<!\\)(?:^|\])([^\[\]]*)(?<!\\)(?:$|\[)"
        matches = re.findall(email_raw_body_pattern, email_body)
        email_raw_body_part = []
        for match in matches:
            if match.strip():
                email_raw_body_part.append(match.strip())
                    
        return (email_raw_body_part, email_square_bracket_part, email_sharp_bracket_part)
        
    @property
    def task_list(self):
        """stores Worker function list, access keys and corresponding action functions
        TODO: Redesign task_list so it is more concise
        """
        # keys must be lower case!
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
            "7": {"function": self._action_gpt_request,
                "name":"GPT query", "trigger": ["7", "gpt"], "description": "Get a gpt response to email body", "help": ""},
            "9": {"function": self._action_register_custom_task,
                "name":"Custom Tasks", "trigger": ["9", "custom"], "description": "Store a new user defined task chian", "help": ""}
        }
        default_worker_functions.update(self.custom_tasks)
        return default_worker_functions
        
    def _action_manage_emalia(self, email_received:dict, emalia_command:str=""):
        """0 Alter emalia behaviour (settings) by permission
        @param `email_received:dict` the email sent by sender
        """
        main_menu = """Options"""
        response_email_subject = f"MANAGE: complete"
        response_email_body = main_menu
        return self._new_emalia_email(email_received, response_email_subject, response_email_body, attachments=[path])
    
    def _action_read_file(self, email_received:dict)->Message:
        """1 find one file and attach it as attachment to response email by emalia permission and return it
        @param `email_received:dict` the email sent by sender
        @return `:dict` the response email to sender
        """
        main_menu = """Options"""
        path = self._parse_email_part(email_received["body"][0][0])[0][-1]
        # if path is passed in
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
        # help menu
        else:
            # return main options
            response_email_subject = f"READ: Main Menu"
            response_email_body = main_menu
            return self._new_emalia_email(email_received, response_email_subject, response_email_body, attachments=[path])
                    
    
    def _action_write_file(self, email_received:dict, content:bytes, path:str="DEFAULT"):
        """2 write the content of a file by emalia permission
        """
        pass
        
    def _action_make_request(self, email_received:dict, http_method, http_url, http_header, http_body):
        """3 make an external request by emalia permission
        """
        pass
    
    def _action_execute_powershell(self, email_received:dict, command):
        """4 Execute a powershell command by emalia permission
        """
        pass
    
    def _action_execute_python(self, email_received:dict, python):
        """5 Execute a python script in current process by emalia permission
        """
        pass
    
    def _action_gpt_request(self, email_received:dict):
        """7 make gpt request and return result 
        """
        
        main_menu = """Options"""
        email_gpt_request = self._parse_email_part(email_received["body"][0][0])
        if email_gpt_request:
            # populate settings
            gpt_settings = {}
            for gpt_setting in email_gpt_request[2]:
                key_parsed = gpt_setting.split(":", 1)[0]
                value_parsed = gpt_setting.split(":", 1)[0]
                if key_parsed in ["temperature", "top_p"]:
                    value_parsed = float(value_parsed)
                elif key_parsed in ["n", "max_tokens", "presence_penalty", "frequency_penalty"]:
                    value_parsed = int(value_parsed)
                gpt_settings[key_parsed] = value_parsed
            # make request
            chat_history = gpt_request.gpt_list_to_chat([email_gpt_request[0][-1]])
            gpt_response = gpt_request.gpt_request(chat_history, **gpt_settings)
            if gpt_response[1] == "chat":
                gpt_response_string = gpt_response[0]["choices"][0]["message"]["content"]
            else:
                gpt_response_string = gpt_response[0]["choices"][0]["text"]
            response_email_subject = f"GPT: request complete"
            response_email_body = f"{gpt_response_string}"
            return self._new_emalia_email(email_received, response_email_subject, response_email_body)
        else:
            # return main options
            response_email_subject = f"GPT: Main Menu"
            response_email_body = main_menu
            return self._new_emalia_email(email_received, response_email_subject, response_email_body)
    
    def _action_register_custom_task(self, email_received:dict, task):
        """9 user can store custom tasks (nest multiple or define new)
        """
        self.custom_tasks = {}
        pass
        
    def _action_run_custom_task(self, email_received:dict, name):
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
        
        