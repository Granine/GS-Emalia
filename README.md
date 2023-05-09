# GS-Emalia
A centralized email controller that provide various python application control capability through email.

# WIP
Please note Emalia is under active development and is not currently functional

## Emalia
an email interacted system that manages and perform a list of predefined tasks.

### Task list (WIP)
0. manage emalia: [Emalia Instance Name]/0 [command]: various command to manage emalia
1. read file: READ/1 [PATH]: zip if directory
2. write file: WRITE/2 [(optional)PATH to directory] + attachment list: write all to a directory (auto create if DNE)
3. make request: REQUEST/3 [Method] // [URL] // [HEADER] // [BODY]: enter None for a field that is not needed, result will be returned
4. execute powershell: SHELL/POWERSHELL/4 [command]: (DANGER) run powershell command
5. execute python: PYTHON/5 [code]: (DANGER) run python in-process

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
    - (1/5) Worker functions (0-5)
    - (o) Task distribution system (need improvements for more entry keyword support)
    - () Security
      - () enable/disable functions
    - () Attach basic footer to emails
- Stage Piston 
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
- Version 0.0.1
    - () Basic UI

