import os
import subprocess
import sys
import time
import threading
import pystray
from pystray import Icon, MenuItem
from PIL import Image, ImageDraw


def create_icon():
    """Create an icon for the system tray."""
    image = Image.open('lulu.ico')
    return image


def on_quit(icon, item):
    """Function to handle the quit event."""
    icon.stop()


def run_python_script(script_path):
    """Function to run a Python script."""
    process = subprocess.Popen([sys.executable, script_path])
    return process


def run_cpp_executable(executable_name):
    """Function to run the bundled C++ executable."""
    executable_path = os.path.join(os.getcwd(), executable_name)
    process = subprocess.Popen([executable_path])
    return process


def close_program(processes):
    """Terminate all processes."""
    for process in processes:
        process.terminate()
        process.wait()  # Wait for the process to terminate
    print("All processes have been terminated.")


def main():
    """Main function to run the program."""
    python_script_1 = "speech.py"
    python_script_2 = "track.py"
    cpp_executable = "a.exe"

    # Start the processes
    processes = []
    processes.append(run_python_script(python_script_1))
    processes.append(run_python_script(python_script_2))
    processes.append(run_cpp_executable(cpp_executable))

    print("Running concurrently...")

    # Create the system tray icon
    icon_image = create_icon()
    menu = (MenuItem('Quit', on_quit),)
    icon = Icon("Program Active", icon_image, menu=menu)
    
    # Start the icon in a separate thread
    icon_thread = threading.Thread(target=icon.run)
    icon_thread.start()

    # Wait for the user to press Enter to terminate the program
    input("Press Enter to terminate all processes...")

    # Close the program
    close_program(processes)

    # Stop the icon when done
    icon.stop()
    print("System tray icon has been stopped.")


if __name__ == "__main__":
    main()
