# GS-Emalia
A centralized email controller that allow users to interact with their system with emails. Also supports features like gpt-over-email, http request, custom functions, function chains and more.

# WIP
Please note Emalia is under active development and is not currently functional

## Emalia
An email interacted system that manages and perform a list of predefined tasks.

### Feature/Tasks can handle
0. system configure: MANAGE/[Emalia Instance Name]/0 [command]: various command to manage emalia
1. read file: READ/1 [PATH]: return a local file, zip and return if directory
2. write file: WRITE/2 [(optional)PATH to directory] + attachment list: write all attachments to a directory (auto create if DNE)
3. make request: REQUEST/3 [Method] // [URL] // [HEADER] // [BODY]: Make a http request. Enter None for a field that is not needed, result will be returned
4. execute powershell: SHELL/POWERSHELL/4 [command]: (DANGER) run powershell command
5. execute python: PYTHON/5 [code]: (DANGER) run python code in-process
6. email action: EMAIL/6 [action] [body] [body_2]...: perform email action like send email, forward and others
7. GPT query: GPT/7 \<gpt settings\> [query body]: Get a gpt response to email body

9. custom tasks: CUSTOM/9 [task]: store custom tasks, one can run with their custom command

### Code flow
- actively check email
  \* Future version may support google api, ifttt or zappier for passive trigger
- perform action on request in email
    - check permission
    - save history
- return confirmation email that may contain the next step

- Each conversation "session" is maintained by replying to emails

## EmailManager
The process responsible for email management like reading email, sending email

## Version
- Stage Penpoint (Completed):
    - (o) Basic EmailManager functionality
      - (o) email receiving
      - (o) email sending
    - (o) Prepare test data and emails
- Stage REM (WIP):  
    - (o) EmailManager
      - (o) attachments r/s
    - (1/2) Basic test structure
    - (o) Basic FileManager functionality
      - (o) calculate file distance (depth wise)
      - (o) search files
    - (2/6) Worker functions (0-6)
      - (): 0. system configure: MANAGE/[Emalia Instance Name]/0 [command]: various command to manage emalia
      - (o): 1. read file: READ/1 [PATH]: return a local file, zip and return if directory
      - (o): 2. write file: WRITE/2 [(optional)PATH to directory] + attachment list: write all attachments to a directory (auto create if DNE)
      - (o): 3. make request: REQUEST/3 [Method] // [URL] // [HEADER] // [BODY]: Make a http request. Enter None for a field that is not needed, result will be returned
      - (o): 4. execute powershell: SHELL/POWERSHELL/4 [command]: (DANGER) run powershell command
      - (o): 5. execute python: PYTHON/5 [code]: (DANGER) run python code in-process
      - (o): 6. email action: EMAIL/6 [action] [body] [body_2]...: perform email action like send email, forward and others
      - (o): 7. GPT query: GPT/7 \<gpt settings\> [query body]: Get a gpt response to email body
      - (): 9. custom tasks: CUSTOM/9 [task]: store custom tasks, one can run with their custom command
    - (o) Task distribution system (need improvements for more entry keyword support)
    - () Security
      - () enable/disable functions
    - () Attach basic footer to emails
- Stage Piston 
    - () EmailManager
      - () Parse reply/body
    - () Maintain conversation
      - () have the ability to read response
    - () Security
      - () Support password
      - () Support file access range
      - () Email white/black list
      - () Worker functions (6, 9)
    - () Basic FileManager functionality
      - () safe file delete
    - () Save the current conversation chain to a file
    - () Read history emails conversation (local save)
    - () Dynamic email scan interval
- Version 0.0.1
    - () Basic UI

