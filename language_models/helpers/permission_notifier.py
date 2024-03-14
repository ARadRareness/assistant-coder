import os
import sys
import tkinter
from tkinter import messagebox


def read_file_content(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "r") as file:
        return file.read()


def get_user_permission(file_path: str) -> bool:
    message = read_file_content(file_path)

    # Create a Tkinter root window
    root = tkinter.Tk()
    # root.overrideredirect(1)
    root.wm_attributes("-topmost", 1)  # type: ignore
    root.withdraw()  # Hide the root window

    # Create a message box
    result = messagebox.askquestion("Permission to Run Tool", message, icon="question")  # type: ignore

    root.destroy()

    # Check the result of the message box
    return result == "yes"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if get_user_permission(sys.argv[1]):
            sys.exit(0)
        else:
            sys.exit(1)
