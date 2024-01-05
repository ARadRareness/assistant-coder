import os
import sys
from tkinter import (
    BOTH,
    BOTTOM,
    LEFT,
    TOP,
    Y,
    Button,
    Checkbutton,
    Entry,
    Frame,
    IntVar,
    Label,
    Scrollbar,
    Tk,
    filedialog,
)
from tkinter import ttk

import client_api


class AssistantCoder(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)

        parent.title(
            "Assistant Coder"
        )  # This line sets the title of your Tkinter window

        self.conversation_id = client_api.start_conversation()

        self.add_system_message()

        self.pack()

        main_frame = Frame(parent)
        main_frame.pack(side=TOP, fill=BOTH, expand=True)

        self.init_treeview(main_frame)
        self.init_command_entry(parent)

        # Add a button to open directories
        Button(main_frame, text="Open Directory", command=self.open_directory).pack(
            side=TOP
        )

        self.chat_mode = IntVar()
        Checkbutton(main_frame, text="Chat mode", variable=self.chat_mode).pack(
            side=TOP
        )

    def init_treeview(self, main_frame):
        # Create the tree and scrollbars
        f1 = Frame(main_frame)
        f1.pack(side=LEFT, fill=BOTH, expand=True)
        vsb = Scrollbar(f1, orient="vertical")
        hsb = Scrollbar(f1, orient="horizontal")
        self.tree = ttk.Treeview(f1, yscrollcommand=vsb.set, xscrollcommand=hsb.set)  # type: ignore
        vsb["command"] = self.tree.yview
        hsb["command"] = self.tree.xview
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=LEFT, fill=Y)

        self.tree["show"] = "tree"  # No header
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)

        self.tree.bind("<Double-1>", self._item_selected)

    def init_command_entry(self, parent):
        # Create an entry for the command input
        commandFrame = Frame(parent)
        commandFrame.pack(side=BOTTOM, fill=BOTH)  # .grid(column=0, row=1, sticky='ew')

        Label(commandFrame, text="Command: ").grid(
            column=0, row=0
        )  # Add a label to the Entry widget
        self.command = Entry(commandFrame)
        self.command.bind(
            "<Return>", self.execute_command
        )  # Bind Enter key to execute command
        self.command.grid(
            column=1, row=0, sticky="ew"
        )  # Change the row number for the entry widget
        commandFrame.columnconfigure(
            1, weight=1
        )  # Set the first row (treeview and vsb) weight to 1

    def populate_tree(self, node):
        if self.tree.exists(node):
            for item in os.listdir(self.tree.item(node)["values"][0]):
                fullpath = os.path.join(self.tree.item(node)["values"][0], item)
                is_directory = os.path.isdir(fullpath)

                # Insert the node into the tree
                id = self.tree.insert(
                    node, "end", text=item, values=[fullpath], open=False
                )

                # If it's a directory, make recursive call to populate its children
                if is_directory:
                    self.populate_tree(id)

    def _item_selected(self, event):
        for selected_item in self.tree.selection():
            file = self.tree.item(selected_item, "values")[
                0
            ]  # Assuming the filename is stored as first value of item
            self.file_clicked(file)

    def file_clicked(self, fpath):
        print("File clicked:", fpath)

    def execute_command(self, event):
        command = self.command.get()  # Get the entered command
        self.command.delete(0, "end")

        response = client_api.generate_response(
            self.conversation_id, command, self.chat_mode.get() == 0
        )

        print(response)

    def open_directory(self):
        dirname = filedialog.askdirectory()

        if dirname:
            node = self.tree.insert(
                "", "end", text=dirname, values=[dirname, "Directory"], open=True
            )

            # Populate the tree with its contents
            self.populate_tree(node)

    def add_system_message(self):
        model_info = client_api.get_model_info(self.conversation_id)
        model_path = model_info["path"]
        print(model_path)

        prompt = f"You are AC, the helpful AI coding assistant. You are currently running through the following model: {model_path}."
        client_api.add_system_message(self.conversation_id, prompt)
        print(prompt)


if __name__ == "__main__":
    root = Tk()
    AssistantCoder(root).mainloop()
