# GS-Emalia
A centralized email controller that provide various python application control capability through email
# WIP
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
    - Functional email receive and sending
    - Functional auto reply
    - Basic test structure

