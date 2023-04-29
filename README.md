# GS-Emalia
A centralized email controller that provide various python application control capability through email
# WIP
Please note Emalia is under active development and is not currently functional
## Emalia
the process responsible to handle user request through email
- sending new email ro emalia starts a new session
- Each "session" or "conversation" is maintained by replying to emails
- Currently, emalia is not designed to handle emails in parallel (eg: receive three email at the same time)

## EmailManager
The process responsible for email management like reading email, sending email

## Plan
- Control local data file through email
- Request password and other validation method from email sender when performing certain actions
- Email white/black list
- History Email storage
- Easily adaptable to other software
- UI to launch software
- Best if software can run backend

## Version
- Stage REM (WIP):
    - (o) Functional email receive and sending
    - () Functional auto reply
    - () Basic test structure
    - () Handle the following basic tasks on request
        - () Save the current conversation chain to a file
        - () Save a string passed with email to a file or process memory
        - () auto reply to confirm task complete

