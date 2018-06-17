from platform import system

def detectOpSystem(bypass=False):
    """Check OS, as multiprocessing may not work properly on Windows and macOS"""

    if bypass is True:
        return

    os = system()

    if os in ['Windows']:
        print("[WARNING] Detector is running on Windows")
        print("[INFO] Consider running this code on Linux.")
        print("[INFO] Exiting..")
        exit()
    else:
        print("[INFO] Detector is running on Linux")
