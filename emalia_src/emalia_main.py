import threading
import Emalia

setting_location = f"{__file__}/../emalia_setting.json"

if __name__ == "__main__":
    """Allow one button trigger of emalia mainloop, testing for now, may change to terminal configurable later"""
    #TODO support comamndline trigger of emalia_main.py
    emalia_instance = Emalia(setting_location=setting_location)
    print("PID:" + str(emalia_instance.PID))
    # start emalia in different thread to prevent blocking
    main_loop_thread = threading.Thread(target=emalia_instance.main_loop)
    main_loop_thread.start()
    # exit emalia and external controls
    supported_command = ["stop", "freeze"]
    # manu input detection
    while selection:=input("Command:\n"):
        if selection.lower() == "stop":
            break
        elif selection.lower() == "freeze":
            emalia_instance.freeze_server = True
        else:
            print(f"Input {selection} is not a valid command from list: {supported_command}")
    emalia_instance.break_loop() # safe break that only end when all tasks are complete
    main_loop_thread.join()
    print("Tasks complete")
        
        