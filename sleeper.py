import ctypes
import time
import os
from threading import Thread, Event

# Global control and state variables
is_running = False
_monitoring_thread = None
_stop_event = Event()

# Get idle time using ctypes
def get_idle_time():
    """Returns the idle time in seconds."""
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)

    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0  # Convert milliseconds to seconds
    else:
        return 0

# Function to show a popup message
def show_popup(message):
    """Displays a popup message with options. Returns True if user selects Cancel."""
    result = ctypes.windll.user32.MessageBoxW(
        0, message, "Idle Shutdown", 1  # 1 = OK/Cancel buttons
    )
    return result == 2 or result == 1  # 2 means "Cancel" was clicked

# Monitor system idle time
def _monitor_idle_time(idle_threshold):
    global is_running
    while is_running:
        idle_time = get_idle_time()
        print(f"Idle time: {idle_time:.1f} seconds")
        if idle_time >= idle_threshold:
            # Schedule shutdown before showing the popup
            os.system("shutdown /s /t 60")  # Schedule shutdown in 60 seconds

            # Show popup and allow user to cancel
            user_cancelled = show_popup(
                f"The computer has been idle for {idle_threshold} seconds. "
                "It will shut down in 1 minute. Click 'Cancel' to abort."
            )

            if user_cancelled:
                os.system("shutdown /a")  # Abort shutdown if user clicks 'Cancel'
                print("Shutdown canceled by the user.")
            

        if _stop_event.wait(5):  # Wait with early exit if stop event is set
            break

# Public functions to control the monitoring
def start_monitoring(idle_minutes=10):
    """Start monitoring for idle time."""
    global is_running, _monitoring_thread, _stop_event
    if is_running:
        return  # Already running

    is_running = True
    _stop_event.clear()
    idle_threshold = idle_minutes * 60  # Convert minutes to seconds

    _monitoring_thread = Thread(target=_monitor_idle_time, args=(idle_threshold,))
    _monitoring_thread.daemon = True
    _monitoring_thread.start()

def stop_monitoring():
    """Stop monitoring for idle time."""
    global is_running, _stop_event
    if not is_running:
        return  # Already stopped

    is_running = False
    _stop_event.set()  # Signal the thread to stop
    if _monitoring_thread is not None:
        _monitoring_thread.join()  # Wait for the thread to finish

def is_monitoring():
    """Check if the monitoring is currently running."""
    return is_running
