import os

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFrame,
    QVBoxLayout,
    QTreeView,
    QLabel,
    QPushButton,
    QDialog,
    QFileSystemModel,
    QFileDialog,
    QTextEdit,
    QHBoxLayout,
    QSizePolicy,
    QSystemTrayIcon,
    QMenu,
    QStyle,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QComboBox,
    QToolButton,
)

from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat, QAction

from PySide6.QtCore import QObject, QDir, Qt, Signal, QSize

from functools import partial

from huggingface_hub import hf_hub_download

import client_api
import threading


class AssistantCoder(QMainWindow):
    def __init__(self, app):
        super().__init__()

        self.app = app
        self.resize(QSize(840, 480))

        self.setWindowTitle("Assistant Coder")

        self.conversation_id = client_api.start_conversation()

        self.checked_files = set()

        self.message_sender = MessageSender(self)
        self.message_sender.message_received.connect(
            lambda message: self.display_message(message, color="darkred")
        )
        self.message_sender.suggestions_received.connect(
            lambda suggestions: self.display_suggestions(suggestions)
        )

        dark_mode = False

        self.background_color = QColor("#ffffff")
        self.text_color = QColor("#00000")
        self.button_color = QColor("#ffffff")

        if dark_mode:
            # Dark mode colors
            self.background_color = QColor("#1e1e1e")
            self.text_color = QColor("#ffffff")
            self.button_color = QColor("#404040")

        self.add_system_message()

        self.init_ui()

        self.suggestions_dialog = SuggestionsDialog(self.send_command)

    def init_ui(self):
        self.create_window_and_system_menu()

        central_widget = QFrame()
        # central_widget.setStyleSheet(
        #    f"background-color: {self.background_color.name()}; color: {self.text_color.name()};"
        # )
        self.setCentralWidget(central_widget)

        self.layout = QHBoxLayout(central_widget)

        tree_layout = QVBoxLayout()

        self.init_treeview(tree_layout)
        self.layout.addLayout(tree_layout)

        options_layout = QHBoxLayout()
        tree_layout.addLayout(options_layout)

        open_dir_button = QPushButton("Open Directory", self)
        # open_dir_button.setStyleSheet(
        #    f"background-color: {self.button_color.name()}; color: {self.text_color.name()};"
        # )

        open_dir_button.clicked.connect(self.open_directory)
        options_layout.addWidget(open_dir_button)

        # Add the chat interface to the right
        chat_layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setStyleSheet("background-color: #f7e9ef;")
        # self.chat_display.setStyleSheet(
        #    f"background-color: {self.background_color.name()}; color: {self.text_color.name()};"
        # )
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)
        self.init_command_entry(chat_layout)

        self.layout.addLayout(chat_layout)

    def add_checkable_menu_action(
        self, action_text, window_menu, option_menu, checked_by_default=False
    ):
        action = self.add_menu_action(
            action_text, window_menu, option_menu, checkable=True
        )
        action.setChecked(checked_by_default)
        return action

    def add_menu_action(self, action_text, window_menu, options_menu, checkable=False):
        action = QAction(action_text, window_menu, checkable=checkable)
        window_menu.addAction(action)
        options_menu.addAction(action)
        return action

    def create_window_and_system_menu(self):
        # Create the Window menu
        window_menu = self.menuBar().addMenu("Options")
        menu_bar_style_sheet = "QMenuBar { background-color: #f0f0f0; }"
        self.menuBar().setStyleSheet(menu_bar_style_sheet)

        # Create the system tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(self.app.style().standardIcon(QStyle.SP_DesktopIcon))

        # Create the system tray menu
        self.menu = QMenu()

        # Add "Options" submenu with boolean options
        options_menu = QMenu("Options", self.menu)

        # Create actions for boolean options in the Window menu
        self.chat_mode_action = self.add_checkable_menu_action(
            "Use chat mode", window_menu, options_menu, checked_by_default=True
        )
        self.use_tools_action = self.add_checkable_menu_action(
            "Use tools", window_menu, options_menu, checked_by_default=True
        )
        self.use_reflections_action = self.add_checkable_menu_action(
            "Use reflections", window_menu, options_menu, checked_by_default=False
        )
        self.use_suggestions_action = self.add_checkable_menu_action(
            "Use suggestions", window_menu, options_menu, checked_by_default=False
        )

        self.use_knowledge_action = self.add_checkable_menu_action(
            "Use knowledge", window_menu, options_menu, checked_by_default=False
        )

        window_menu.addSeparator()
        options_menu.addSeparator()

        clear_chat_action = self.add_menu_action(
            "Clear chat", window_menu, options_menu
        )

        clear_chat_action.triggered.connect(self.clear_chat)

        change_model_action = self.add_menu_action(
            "Change model", window_menu, options_menu
        )
        change_model_action.triggered.connect(self.change_model)

        download_model_action = self.add_menu_action(
            "Download model", window_menu, options_menu
        )
        download_model_action.triggered.connect(self.download_model)

        exit_action = self.add_menu_action("Exit", window_menu, options_menu)
        exit_action.triggered.connect(self.app.quit)

        # Add the options menu to the main menu
        self.menu.addMenu(options_menu)

        # Set the menu for the system tray icon
        self.tray_icon.setContextMenu(self.menu)

        # Show the system tray icon
        self.tray_icon.show()

    def init_treeview(self, layout):
        self.model = CustomFileSystemModel()
        self.model.setRootPath(QDir.rootPath())

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(QDir.rootPath()))
        self.tree_view.setAnimated(False)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        self.tree_view.setColumnWidth(0, 210)

        self.model.checkStateChanged.connect(self.tree_state_changed)

        layout.addWidget(self.tree_view)

    def tree_state_changed(self, path, checked):
        if checked:
            if os.path.isfile(path):
                self.checked_files.add(path)
        else:
            try:
                self.checked_files.remove(path)
            except:
                None

    def init_command_entry(self, layout):
        command_label = QLabel("Command:", self)
        layout.addWidget(command_label)

        self.command = CommandTextEdit(command_execution=self.execute_command)
        # self.command.returnPressed.connect(self.execute_command)
        layout.addWidget(self.command)

    def display_message(self, message, color=None):
        # Scroll to the bottom to always show the latest messages
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Create a new text block for the message
        cursor.insertBlock()

        # Apply color if provided to the new block
        if color:
            format = QTextCharFormat()
            format.setForeground(QColor(color))
            cursor.setCharFormat(format)

        # Insert the message text to the new block
        cursor.insertText(message)

        cursor.insertBlock()  # Optional added spacing between messages
        if color:
            format = QTextCharFormat()
            format.setForeground(QColor("black"))
            cursor.setCharFormat(format)

        self.chat_display.setTextCursor(cursor)
        cursor.movePosition(QTextCursor.End)

    def display_suggestions(self, suggestions):
        # Display suggestions in a separate pop-up window, where the user can click on a suggestion to send it as a command
        self.suggestions_dialog.set_suggestions(suggestions)
        self.suggestions_dialog.show()

    def populate_tree(self, directory, parent_index):
        model = self.centralWidget().layout().itemAt(0).widget().model()
        item_index = model.index(directory)
        model.insertRow(0, item_index.parent())

        for item_name in os.listdir(directory):
            item_path = os.path.join(directory, item_name)

            # Insert the item into the tree
            item_index = model.index(item_path)
            model.insertRow(0, item_index.parent())

            # If it's a directory, make a recursive call to populate its children
            if os.path.isdir(item_path):
                self.populate_tree(item_path, item_index)

    def item_selected(self, index):
        file_path = (
            self.centralWidget().layout().itemAt(0).widget().model().filePath(index)
        )
        self.file_clicked(file_path)

    def file_clicked(self, file_path):
        print("File clicked:", file_path)

    def keyPressEvent(self, event):
        # Override the keyPressEvent to capture Enter key press
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.focus_command_input()
        else:
            super().keyPressEvent(event)

    def focus_command_input(self):
        self.command.setFocus()

    def send_command(self, command):
        print("Sending command:", command)
        self.display_message("User: " + command, color="darkblue")
        self.message_sender.send_message(command)

    def execute_command(self):
        command = self.command.toPlainText().strip()
        self.command.clear()

        self.display_message("User: " + command, color="darkblue")

        self.message_sender.send_message(command)

    def open_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Open Directory", QDir.rootPath()
        )
        if directory:
            print(directory)

            self.model = CustomFileSystemModel()
            self.model.setRootPath(directory)

            self.tree_view.setModel(self.model)
            self.tree_view.setRootIndex(self.model.index(directory))

    def add_system_message(self):
        model_info = client_api.get_model_info(self.conversation_id)
        model_path = model_info["path"]
        print(model_path)

        prompt = f"You are AC, the helpful AI coding assistant. You are currently running through the following model: {model_path}."
        client_api.add_system_message(self.conversation_id, prompt)
        print(prompt)

    def clear_chat(self):
        self.chat_display.clear()
        self.conversation_id = client_api.start_conversation()
        self.add_system_message()

    def download_model(self):
        dialog = DownloadModelDialog(self)
        if dialog.exec() == QDialog.Accepted:
            None

    def change_model(self):
        dialog = ChangeModelDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.add_system_message()

    def download_method(self, repo_id, filename):
        print(f"Downloading model from {repo_id} with name {filename}")

        model_dir_paths = ["models", os.path.join("..", "models")]

        for model_dir_path in model_dir_paths:
            if os.path.exists(model_dir_path):
                model_path = os.path.join(model_dir_path, filename)
                if not os.path.exists(model_path):
                    downloaded_model_path = hf_hub_download(
                        repo_id=repo_id,
                        filename=filename,
                        use_auth_token=False,
                    )

                    # Move the downloaded model to the models folder
                    os.rename(downloaded_model_path, model_path)
                break


class DownloadModelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Model")

        self.repo_id_label = QLabel("Repo id:")
        self.repo_id_edit = QLineEdit()
        self.filename_label = QLabel("Filename:")
        self.filename_edit = QLineEdit()

        # Create buttons for downloading and canceling
        self.download_button = QPushButton("Download")
        self.cancel_button = QPushButton("Cancel")

        # Connect button clicks to slots
        self.download_button.clicked.connect(self.download)
        self.cancel_button.clicked.connect(self.reject)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.repo_id_label)
        layout.addWidget(self.repo_id_edit)
        layout.addWidget(self.filename_label)
        layout.addWidget(self.filename_edit)
        layout.addWidget(self.download_button)
        layout.addWidget(self.cancel_button)
        self.setLayout(layout)

    def download(self):
        # Retrieve the values from the line edits and trigger the download method
        repo_id = self.repo_id_edit.text()
        filename = self.filename_edit.text()
        self.accept()  # Close the dialog
        self.parent().download_method(repo_id, filename)  # Call the download method


class ChangeModelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Model")

        self.available_models = client_api.get_available_models()

        # Create a label and a combo box for selecting the model

        self.model_label = QLabel("Model:")
        self.model_combo_box = QComboBox()
        self.model_combo_box.addItems(self.available_models)

        # Create buttons for downloading and canceling
        self.change_button = QPushButton("Change")
        self.cancel_button = QPushButton("Cancel")

        # Connect button clicks to slots
        self.change_button.clicked.connect(self.change)
        self.cancel_button.clicked.connect(self.reject)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.model_label)
        layout.addWidget(self.model_combo_box)
        layout.addWidget(self.change_button)
        layout.addWidget(self.cancel_button)
        self.setLayout(layout)

    def change(self):
        # Retrieve the values from the line edits and trigger the download method
        model_name = self.model_combo_box.currentText()
        self.accept()
        client_api.change_model(model_name)


class CustomFileSystemModel(QFileSystemModel):
    """Original class created by musicamante"""

    checkStateChanged = Signal(str, bool)

    def __init__(self):
        super().__init__()
        self.checkStates = {}
        self.rowsInserted.connect(self.checkAdded)
        self.rowsRemoved.connect(self.checkParent)
        self.rowsAboutToBeRemoved.connect(self.checkRemoved)

    def checkState(self, index):
        return self.checkStates.get(self.filePath(index), Qt.Unchecked)

    def setCheckState(self, index, state, emitStateChange=True):
        path = self.filePath(index)
        if self.checkStates.get(path) == state:
            return
        self.checkStates[path] = state
        if emitStateChange:
            self.checkStateChanged.emit(path, bool(state))

    def checkAdded(self, parent, first, last):
        # if a file/directory is added, ensure it follows the parent state as long
        # as the parent is already tracked; note that this happens also when
        # expanding a directory that has not been previously loaded
        if not parent.isValid():
            return

        if self.filePath(parent) in self.checkStates:
            state = self.checkState(parent)
            for row in range(first, last + 1):
                index = self.index(row, 0, parent)
                path = self.filePath(index)
                if path not in self.checkStates:
                    self.checkStates[path] = state

        # self.checkParent(parent)

    def checkRemoved(self, parent, first, last):
        # remove items from the internal dictionary when a file is deleted;
        # note that this *has* to happen *before* the model actually updates,
        # that's the reason this function is connected to rowsAboutToBeRemoved
        for row in range(first, last + 1):
            path = self.filePath(self.index(row, 0, parent))
            if path in self.checkStates:
                self.checkStates.pop(path)

    def checkParent(self, parent):
        # verify the state of the parent according to the children states
        if not parent.isValid():
            return
        childStates = [
            self.checkState(self.index(r, 0, parent))
            for r in range(self.rowCount(parent))
        ]

        newState = Qt.Checked if all(childStates) else Qt.Unchecked
        oldState = self.checkState(parent)

        if newState != oldState:
            self.setCheckState(parent, newState)
            self.dataChanged.emit(parent, parent)
        self.checkParent(parent.parent())

    def flags(self, index):
        return super().flags(index) | Qt.ItemIsUserCheckable

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.CheckStateRole and index.column() == 0:
            return self.checkState(index)
        return super().data(index, role)

    def setData(self, index, value, role, checkParent=True, emitStateChange=True):
        if role == Qt.CheckStateRole and index.column() == 0:
            self.setCheckState(index, value, emitStateChange)

            for row in range(self.rowCount(index)):
                # set the data for the children, but do not emit the state change,
                # and don't check the parent state (to avoid recursion)
                child_index = self.index(row, 0, index)
                self.setData(
                    child_index,
                    value,
                    Qt.CheckStateRole,
                    checkParent=False,
                    emitStateChange=False,
                )
            self.dataChanged.emit(index, index)
            if checkParent:
                self.checkParent(index.parent())
            return True

        return super().setData(index, value, role)


class CommandTextEdit(QTextEdit):
    def __init__(self, parent=None, command_execution=None):
        super().__init__(parent)
        self.command_execution = command_execution
        self.setMaximumHeight(self.document().size().height() * 3)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not event.modifiers() == Qt.ShiftModifier:
            # Enter without Shift pressed, execute the command
            self.command_execution()
        else:
            super().keyPressEvent(event)


class MessageSender(QObject):
    message_received = Signal(str)
    suggestions_received = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent

    def send_message(self, command):
        selected_files = list(self._parent.checked_files)

        chat_mode = self._parent.chat_mode_action.isChecked()
        use_tools = self._parent.use_tools_action.isChecked()
        use_reflections = self._parent.use_reflections_action.isChecked()
        use_suggestions = self._parent.use_suggestions_action.isChecked()
        use_knowledge = self._parent.use_knowledge_action.isChecked()

        def generate_response_thread():
            suggestions = []
            try:
                for i in range(2):
                    if use_suggestions:
                        response, suggestions = client_api.generate_response(
                            self._parent.conversation_id,
                            command,
                            selected_files=selected_files,
                            single_message_mode=not chat_mode,
                            use_tools=use_tools,
                            use_reflections=use_reflections,
                            use_suggestions=use_suggestions,
                            use_knowledge=use_knowledge,
                            max_tokens=1000,
                            ask_permission_to_run_tools=True,
                        )
                        print(suggestions)
                    else:
                        response = client_api.generate_response(
                            self._parent.conversation_id,
                            command,
                            selected_files=selected_files,
                            single_message_mode=not chat_mode,
                            use_tools=use_tools,
                            use_reflections=use_reflections,
                            use_suggestions=use_suggestions,
                            use_knowledge=use_knowledge,
                            max_tokens=1000,
                            ask_permission_to_run_tools=True,
                        )

                    if not response and i == 0:
                        self._parent.conversation_id = client_api.start_conversation()
                        self._parent.add_system_message()
                    else:
                        break

                if response:
                    self.message_received.emit("AC: " + response)

                    if suggestions:
                        self.suggestions_received.emit(suggestions)

                    print(response)

            except Exception as e:
                print("Error in generate_response_thread:", e)

        response_thread = threading.Thread(target=generate_response_thread)
        response_thread.start()


class SuggestionsDialog(QDialog):
    def __init__(self, send_command, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Suggestions")
        self.suggestions = []  # suggestions
        self.init_ui()
        self.send_command = send_command
        self.buttons = []

    def set_suggestions(self, suggestions):
        self.suggestions = suggestions

        # Remove previous widgets from self.layout
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)

        for suggestion in self.suggestions:
            button = QToolButton(self)
            button.setText(self.split_suggestion(suggestion))
            button.clicked.connect(partial(self.send, suggestion))
            self.layout.addWidget(button)

    def split_suggestion(self, suggestion):
        words = suggestion.split()
        lines = []
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

    def send(self, message):
        self.send_command(message)

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)


if __name__ == "__main__":
    app = QApplication([])
    window = AssistantCoder(app)
    window.show()
    app.exec()
