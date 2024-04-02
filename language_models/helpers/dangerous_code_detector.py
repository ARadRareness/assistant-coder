# Support detection of __import__, importlib, breakpoint, compile, exec, eval, input, open,

from typing import List


class DangerousCodeDetector:
    def __init__(self) -> None:
        self.potentially_harmful_functions = [
            "__import__",
            "breakpoint",
            "compile",
            "exec",
            # "eval", # NOT harmful in itself, but allows for running code from all other classes
            "input",
            "open",
        ]

        self.approved_imports = [
            "bisect",
            "calendar",
            "collections",
            "copy",
            "datetime",
            "fractions",
            "functools",
            "hashlib",
            "heapq",
            "itertools",
            "math",
            "operator",
            "random",
            "re",
            "statistics",
            "string",
            "typing",
        ]

    def detect_potentially_dangerous_code(self, code: str) -> bool:
        code = self._remove_comments(code)

        for line in code.lower().split("\n"):
            if self._detect_potentially_dangerous_code_in_line(line):
                return True
        return False

    def _remove_comments(self, code: str) -> str:
        lines: List[str] = []
        in_docstring = False
        in_docstring_single_quote = False

        for line in code.split("\n"):
            buffer = ""
            in_string = False
            in_single_quote_string = False

            docstring_quote_count = 0
            docstring_single_quote_count = 0

            i = 0
            while i < len(line):
                c = line[i]

                if in_string:
                    if c == '"':
                        in_string = False
                elif in_single_quote_string:
                    if c == "'":
                        in_single_quote_string = False
                elif in_docstring_single_quote:
                    if c == "'":
                        docstring_single_quote_count += 1
                        if docstring_single_quote_count == 3:
                            in_docstring_single_quote = False
                    else:
                        docstring_single_quote_count = 0
                elif in_docstring:
                    if c == '"':
                        docstring_quote_count += 1
                        if docstring_quote_count == 3:
                            in_docstring = False
                    else:
                        docstring_quote_count = 0
                else:
                    if c == "#":
                        break
                    if c == '"':
                        if (
                            i + 2 < len(line)
                            and line[i + 1] == '"'
                            and line[i + 2] == '"'
                        ):
                            i += 2
                            in_docstring = True
                        else:
                            in_string = True
                    elif c == "'":
                        if (
                            i + 2 < len(line)
                            and line[i + 1] == "'"
                            and line[i + 2] == "'"
                        ):
                            i += 2
                            in_docstring_single_quote = True
                        else:
                            in_single_quote_string = True
                    else:
                        buffer += c
                i += 1
            if buffer:
                lines.append(buffer)
        return "\n".join(lines)

    def _detect_potentially_dangerous_code_in_line(self, line: str) -> bool:
        parsed_parts = self._parse_line(line)
        for part in parsed_parts:
            for phf in self.potentially_harmful_functions:
                if phf == part:
                    print("")
                    return True

        # Detect potentially dangerous imports
        if self._detect_potentially_dangerous_imports(parsed_parts, line):
            return True
        return False

    def _parse_line(self, line: str) -> List[str]:
        parsed_parts: List[str] = []
        buffer = ""
        for c in line:
            if not c.isalnum() and c != "_":
                if buffer:
                    parsed_parts.append(buffer)
                    buffer = ""
            else:
                buffer += c

        if buffer:
            parsed_parts.append(buffer)

        return parsed_parts

    def _detect_potentially_dangerous_imports(
        self, parsed_parts: List[str], line: str
    ) -> bool:
        if "import" in parsed_parts:
            if len(parsed_parts) == 2:
                if parsed_parts[0] == "import":
                    return parsed_parts[1] not in self.approved_imports
                else:
                    return True  # Weird import statement
            elif len(parsed_parts) >= 4:
                if parsed_parts[0] == "from" and parsed_parts[2] == "import":
                    return parsed_parts[1] not in self.approved_imports
                else:
                    return True  # Weird from x import y statement
            else:
                return True  # Weird import statement
        return False
