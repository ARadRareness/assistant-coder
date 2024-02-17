import os
from language_models.model_message import MessageMetadata
from language_models.tools.base_tool import BaseTool


class ReadFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            "read_file",
            "read the content of a specific file (selected by index)",
            [
                (
                    "FILEINDEX",
                    "(MANDATORY) specifies the index (from 1) of the file to read, only one file is allowed",
                )
            ],
        )

    def action(self, arguments, metadata: MessageMetadata):
        if "FILEINDEX" in arguments:
            file_index = int(arguments["FILEINDEX"])

            if not metadata or 0 >= file_index > len(metadata.selected_files):
                print("Invalid file index!")
                return None

            fpath = metadata.selected_files[file_index - 1]
            print(f"READ FILE with index {file_index}!")
            print(f"READ FILE with filepath {fpath}!")
            if os.path.isfile(fpath):
                with open(fpath, "r", encoding="utf8") as f:
                    return f"FILE CONTENT OF {fpath}:\n{f.read()}"
            else:
                print("FILE WAS NOT FOUND!")
        else:
            print("READ FILE with UNKNOWN ARGUMENTS")

    def get_example_messages(self):
        return self.get_example_dialogue(
            "Read the content of the selected file for me please.",
            '{"tool": "read_file", "arguments": {"FILEINDEX": "1"}}',
        )
