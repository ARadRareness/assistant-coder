import sys
import tkinter
from tkinter import messagebox


def get_user_permission(message):
    # Create a Tkinter root window
    root = tkinter.Tk()
    # root.overrideredirect(1)
    root.wm_attributes("-topmost", 1)
    root.withdraw()  # Hide the root window

    # Create a message box
    result = messagebox.askquestion("Permission to Run Tool", message, icon="question")

    root.destroy()

    # Check the result of the message box
    return result == "yes"


if len(sys.argv) > 1:
    if get_user_permission(sys.argv[1]):
        sys.exit(0)
    else:
        sys.exit(1)
