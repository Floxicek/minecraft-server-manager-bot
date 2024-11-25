import ctypes
import time
import threading

# Define Windows API structures and constants
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.wintypes.UINT),
        ('dwTime', ctypes.wintypes.DWORD),
    ]

# Global variables to control monitoring
SCRIPT_ENABLED = False
MONITOR_THREAD = None
SHOULD_STOP = threading.Event()

def get_idle_time():
    """
    Get the idle time in seconds since the last user input.
    """
    last_input_info = LASTINPUTINFO()
    last_input_info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input_info)):
        millis = ctypes.windll.kernel32.GetTickCount() - last_input_info.dwTime
        return millis / 1000.0
    else:
        return 0

def sleep_system():
    """
    Puts the system to sleep.
    """
    ctypes.windll.powrprof.SetSuspendState(False, False, False)

def monitor_idle_time(idle_threshold):
    """
    Monitor system idle time and put the PC to sleep if idle.
    """
    while not SHOULD_STOP.is_set():
        if SCRIPT_ENABLED:
            idle_time = get_idle_time()
            print(f"Idle Time: {idle_time:.2f} seconds")

            if idle_time > idle_threshold:
                print("System is idle. Putting the PC to sleep...")
                sleep_system()
                break  # Exit monitoring after putting the PC to sleep

        time.sleep(30)  # Check every 30 seconds

def start_monitoring(idle_threshold=300):
    """
    Start the idle time monitoring in a separate thread.
    """
    global MONITOR_THREAD, SHOULD_STOP
    if MONITOR_THREAD is None or not MONITOR_THREAD.is_alive():
        SHOULD_STOP.clear()
        MONITOR_THREAD = threading.Thread(target=monitor_idle_time, args=(idle_threshold,))
        MONITOR_THREAD.daemon = True
        MONITOR_THREAD.start()
        print("Monitoring started.")

def stop_monitoring():
    """
    Stop the idle time monitoring.
    """
    global MONITOR_THREAD, SHOULD_STOP
    if MONITOR_THREAD and MONITOR_THREAD.is_alive():
        SHOULD_STOP.set()
        MONITOR_THREAD.join()
        MONITOR_THREAD = None
        print("Monitoring stopped.")

def set_enabled(enabled: bool):
    """
    Enable or disable the monitoring script.
    """
    global SCRIPT_ENABLED
    SCRIPT_ENABLED = enabled
    status = "enabled" if enabled else "disabled"
    print(f"Script {status}.")
