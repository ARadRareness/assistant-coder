from typing import Callable, List, Optional, Sequence

from PySide6.QtWidgets import (
    QVBoxLayout,
    QDialog,
    QToolButton,
    QWidget,
)

from functools import partial


class SuggestionsDialog(QDialog):
    def __init__(
        self, send_command: Callable[[str], None], parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Suggestions")
        self.suggestions: List[str] = []  # suggestions
        self.init_ui()
        self.send_command = send_command
        self.buttons = []

    def set_suggestions(self, suggestions: Sequence[str]) -> None:
        self.suggestions = list(suggestions)

        # Remove previous widgets from self.layout
        for i in reversed(range(self.layout_actual.count())):
            self.layout_actual.itemAt(i).widget().setParent(None)

        for suggestion in self.suggestions:
            if suggestion:
                button = QToolButton(self)
                button.setText(self.split_suggestion(suggestion))
                button.clicked.connect(partial(self.send, suggestion))
                self.layout_actual.addWidget(button)

    def split_suggestion(self, suggestion: str) -> str:
        words = suggestion.split()
        lines: List[str] = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) <= 80:
                current_line += word + " "
            else:
                lines.append(current_line)
                current_line = word + " "

        if current_line:
            lines.append(current_line)

        return "\n".join(lines)

    def send(self, message: str) -> None:
        self.send_command(message)

    def init_ui(self):
        self.layout = lambda: QVBoxLayout()
        self.layout_actual = self.layout()
        self.setLayout(self.layout_actual)
