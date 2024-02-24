import os
from typing import Any, Dict, List
from language_models.model_message import MessageMetadata, ModelMessage
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
            True,
        )

    def ask_permission_message(
        self, arguments: Dict[str, Any], metadata: MessageMetadata
    ) -> str:
        fpath = self._get_file_argument(arguments, metadata)

        if fpath:
            return f"AC would like to READ the content of the following file:\n\n{fpath}\n\nDo you want to allow this?"
        else:
            return ""

    def action(self, arguments: Dict[str, Any], metadata: MessageMetadata) -> str:
        fpath = self._get_file_argument(arguments, metadata)

        if fpath:
            print(f"READ FILE with filepath {fpath}!")
            if os.path.isfile(fpath):
                with open(fpath, "r", encoding="utf8") as f:
                    return f"FILE CONTENT OF {fpath}:\n{f.read()}"
            else:
                print("FILE WAS NOT FOUND!")
        else:
            print("READ FILE with UNKNOWN ARGUMENTS")

        return ""

    def _get_file_argument(
        self, arguments: Dict[str, Any], metadata: MessageMetadata
    ) -> str:
        if "FILEINDEX" in arguments:
            file_index = int(arguments["FILEINDEX"])

            if not metadata or 0 >= file_index > len(metadata.selected_files):
                print("Invalid file index!")
                return ""

            return metadata.selected_files[file_index - 1]

        return ""

    def get_example_messages(self) -> List[ModelMessage]:
        return self.get_example_dialogue(
            "Read the content of the selected file for me please.",
            '{"tool": "read_file", "arguments": {"FILEINDEX": "1"}}',
        )
