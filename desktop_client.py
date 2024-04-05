import os
import argparse
import time
from typing import Any, Callable, Optional, Sequence, Set

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFrame,
    QVBoxLayout,
    QTreeView,
    QLabel,
    QPushButton,
    QDialog,
    QFileDialog,
    QTextEdit,
    QHBoxLayout,
    QSizePolicy,
    QSystemTrayIcon,
    QMenu,
    QStyle,
    QComboBox,
    QLineEdit,
)

from PySide6.QtGui import (
    QTextCursor,
    QColor,
    QTextCharFormat,
    QAction,
    QKeyEvent,
    QGuiApplication,
)

from PySide6.QtCore import QObject, QDir, Qt, Signal, QSize, QMetaObject, Q_ARG, Slot

from huggingface_hub import hf_hub_download  # type:ignore

from client.components.suggestions_dialog import SuggestionsDialog
from client.components.custom_file_system_model import CustomFileSystemModel

from client import client_api
import threading
import traceback

import shutil


from pydub import AudioSegment  # type: ignore
from pydub.playback import play  # type: ignore
import io
import queue
from client.components.voice_input import VoiceInput
from language_models.audio.text_to_speech_engine import TextToSpeechEngine

from dotenv import load_dotenv, dotenv_values

if not os.path.exists(".env"):
    shutil.copy(".env_defaults", ".env")

load_dotenv()


class AssistantCoder(QMainWindow):
    use_local_whisper = False

    def __init__(self, app: QApplication, server_url: str = "http://127.0.0.1:17173"):
        super().__init__()

        client_api.BASE_URL = server_url

        self.app = app
        self.resize(QSize(840, 480))

        self.setWindowTitle("Assistant Coder")

        self.conversation_id = client_api.start_conversation()

        self.checked_files: Set[str] = set()

        self.message_sender: MessageSender = MessageSender(self)
        self.message_sender.message_received.connect(
            lambda message: self.display_message(message, color="darkred")  # type: ignore
        )
        self.message_sender.suggestions_received.connect(
            lambda suggestions: self.display_suggestions(suggestions)  # type: ignore
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

        self.use_local_whisper = (
            os.getenv("CLIENT.USE_LOCAL_WHISPER", "false").lower() == "true"
        )

        self.use_local_tts = (
            os.getenv("CLIENT.USE_LOCAL_TTS", "false").lower() == "true"
        )

        self.allow_voice_interrupt = (
            os.getenv("CLIENT.VOICE_INTERRUPT", "false").lower() == "true"
        )

        self.text_to_speech_engine: Optional[TextToSpeechEngine] = None

        self.single_record_audio_enabled = False

    def init_ui(self):
        self.create_window_and_system_menu()

        central_widget = QFrame()
        # central_widget.setStyleSheet(
        #    f"background-color: {self.background_color.name()}; color: {self.text_color.name()};"
        # )
        self.setCentralWidget(central_widget)

        self.layout = lambda: QHBoxLayout(central_widget)

        layout = self.layout()

        tree_layout = QVBoxLayout()

        self.init_treeview(tree_layout)
        layout.addLayout(tree_layout)

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

        # Add Record Audio button under the command text for one-time voice input
        self.record_audio_button = QPushButton("Record Audio", self)
        self.record_audio_button.clicked.connect(self.record_audio)
        chat_layout.addWidget(self.record_audio_button)

        layout.addLayout(chat_layout)

        app.aboutToQuit.connect(self.cleanup_before_exit)

    def add_checkable_menu_action(
        self,
        action_text: str,
        window_menu: QMenu,
        option_menu: QMenu,
        checked_by_default: bool = False,
    ):
        action = self.add_menu_action(
            action_text, window_menu, option_menu, checkable=True
        )
        action.setChecked(checked_by_default)
        return action

    def update_env_option(self, action_text: str, checked: bool):
        # Map action text to .env key
        env_keys = {
            "Use chat mode": "CLIENT.TOGGLE_CHAT",
            "Use tools": "CLIENT.TOGGLE_TOOLS",
            "Use reflections": "CLIENT.TOGGLE_REFLECTIONS",
            "Use suggestions": "CLIENT.TOGGLE_SUGGESTIONS",
            "Use knowledge": "CLIENT.TOGGLE_KNOWLEDGE",
            "Use safety": "CLIENT.TOGGLE_SAFETY",
            "Use clipboard": "CLIENT.TOGGLE_CLIPBOARD",
            "Use text to speech": "CLIENT.TOGGLE_TTS",
            "Use voice input": "CLIENT.TOGGLE_VOICE_INPUT",
        }
        env_key = env_keys.get(action_text)
        if env_key:
            # Update the .env file
            self.set_env_value(env_key, str(checked).lower())

    @staticmethod
    def set_env_value(key: str, value: str):
        # Load the current .env file into memory
        dotenv_path = os.path.join(os.getcwd(), ".env")
        values = dotenv_values(dotenv_path)
        values[key] = value
        # Write the updated values back to the .env file
        with open(dotenv_path, "w") as f:
            for k, v in values.items():
                f.write(f"{k}={v}\n")

    def add_menu_action(
        self,
        action_text: str,
        window_menu: QMenu,
        options_menu: QMenu,
        checkable: bool = False,
    ):
        action = QAction(action_text, window_menu, checkable=checkable)  # type: ignore
        window_menu.addAction(action)  # type: ignore
        options_menu.addAction(action)  # type: ignore
        return action

    def create_window_and_system_menu(self):
        # Create the Window menu
        window_menu = self.menuBar().addMenu("Options")
        menu_bar_style_sheet = "QMenuBar { background-color: #f0f0f0; }"
        self.menuBar().setStyleSheet(menu_bar_style_sheet)

        # Create the system tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(self.app.style().standardIcon(QStyle.SP_DesktopIcon))  # type: ignore

        # Create the system tray menu
        self.menu = QMenu()

        # Add "Options" submenu with boolean options
        options_menu = QMenu("Options", self.menu)

        # Create actions for boolean options in the Window menu
        self.chat_mode_action = self.add_checkable_menu_action(
            "Use chat mode",
            window_menu,
            options_menu,
            checked_by_default=os.getenv("CLIENT.TOGGLE_CHAT", "true").lower()
            == "true",
        )
        self.use_tools_action = self.add_checkable_menu_action(
            "Use tools",
            window_menu,
            options_menu,
            checked_by_default=os.getenv("CLIENT.TOGGLE_TOOLS", "true").lower()
            == "true",
        )
        self.use_reflections_action = self.add_checkable_menu_action(
            "Use reflections",
            window_menu,
            options_menu,
            checked_by_default=os.getenv("CLIENT.TOGGLE_REFLECTIONS", "false").lower()
            == "true",
        )
        self.use_suggestions_action = self.add_checkable_menu_action(
            "Use suggestions",
            window_menu,
            options_menu,
            checked_by_default=os.getenv("CLIENT.TOGGLE_SUGGESTIONS", "false").lower()
            == "true",
        )

        self.use_knowledge_action = self.add_checkable_menu_action(
            "Use knowledge",
            window_menu,
            options_menu,
            checked_by_default=os.getenv("CLIENT.TOGGLE_KNOWLEDGE", "false").lower()
            == "true",
        )

        self.use_safety_action = self.add_checkable_menu_action(
            "Use safety",
            window_menu,
            options_menu,
            checked_by_default=os.getenv("CLIENT.TOGGLE_SAFETY", "true").lower()
            == "true",
        )

        self.use_clipboard_action = self.add_checkable_menu_action(
            "Use clipboard",
            window_menu,
            options_menu,
            checked_by_default=os.getenv("CLIENT.TOGGLE_CLIPBOARD", "false").lower()
            == "true",
        )

        self.use_tts_action = self.add_checkable_menu_action(
            "Use text to speech",
            window_menu,
            options_menu,
            checked_by_default=os.getenv("CLIENT.TOGGLE_TTS", "false").lower()
            == "true",
        )

        # Add "Use voice input" option below "Use text to speech"
        self.use_voice_input_action = self.add_checkable_menu_action(
            "Use voice input",
            window_menu,
            options_menu,
            checked_by_default=os.getenv("CLIENT.TOGGLE_VOICE_INPUT", "false").lower()
            == "true",
        )
        self.use_voice_input_action.triggered.connect(self.toggle_voice_input)
        if self.use_voice_input_action.isChecked():
            self.toggle_voice_input(True)

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

        self.chat_mode_action.triggered.connect(
            lambda checked: self.update_env_option("Use chat mode", checked)
        )
        self.use_tools_action.triggered.connect(
            lambda checked: self.update_env_option("Use tools", checked)
        )
        self.use_reflections_action.triggered.connect(
            lambda checked: self.update_env_option("Use reflections", checked)
        )
        self.use_suggestions_action.triggered.connect(
            lambda checked: self.update_env_option("Use suggestions", checked)
        )
        self.use_knowledge_action.triggered.connect(
            lambda checked: self.update_env_option("Use knowledge", checked)
        )
        self.use_safety_action.triggered.connect(
            lambda checked: self.update_env_option("Use safety", checked)
        )
        self.use_clipboard_action.triggered.connect(
            lambda checked: self.update_env_option("Use clipboard", checked)
        )
        self.use_tts_action.triggered.connect(
            lambda checked: self.update_env_option("Use text to speech", checked)
        )
        self.use_voice_input_action.triggered.connect(
            lambda checked: self.update_env_option("Use voice input", checked)
        )

        # Set the menu for the system tray icon
        self.tray_icon.setContextMenu(self.menu)

        # Show the system tray icon
        self.tray_icon.show()

    def init_treeview(self, layout: QVBoxLayout) -> None:
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

    def tree_state_changed(self, path: str, checked: bool) -> None:
        if checked:
            if os.path.isfile(path):
                self.checked_files.add(path)
        else:
            try:
                self.checked_files.remove(path)
            except:
                pass

    def init_command_entry(self, layout: QVBoxLayout):
        command_label = QLabel("Command:", self)
        layout.addWidget(command_label)

        self.command = CommandTextEdit(command_execution=self.execute_command)
        layout.addWidget(self.command)

    def display_message(self, message: str, color: Optional[str] = None) -> None:
        # Scroll to the bottom to always show the latest messages
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)  # type: ignore

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
        cursor.movePosition(QTextCursor.End)  # type: ignore

    def display_suggestions(self, suggestions: Sequence[str]) -> None:
        # Display suggestions in a separate pop-up window, where the user can click on a suggestion to send it as a command
        self.suggestions_dialog.set_suggestions(suggestions)
        self.suggestions_dialog.show()

    @Slot(bool)
    def toggle_voice_input(self, checked: bool):
        self.clear_voice_input()

        if checked:
            self.voice_input = VoiceInput(use_local_whisper=self.use_local_whisper)
            self.voice_input_thread = threading.Thread(target=self.process_voice_input)
            self.voice_input_thread.start()

            self.update_record_button_state_listening()

        else:
            self.update_record_button_state_record_audio()

    @Slot()
    def clear_voice_input(self):
        if hasattr(self, "voice_input"):
            del self.voice_input
            self.voice_input_thread.join()

    @Slot()
    def update_record_button_state_waiting(self):
        self.record_audio_button.setText("Waiting...")
        self.voice_input.set_ignore_audio(True)
        self.record_audio_button.setEnabled(False)

    @Slot()
    def update_record_button_state_listening(self):
        self.record_audio_button.setText("Listening...")
        self.voice_input.set_ignore_audio(False)
        self.record_audio_button.setEnabled(False)

    @Slot()
    def update_record_button_state_record_audio(self):
        self.record_audio_button.setText("Record Audio")
        self.record_audio_button.setEnabled(True)

    def record_audio(self):
        self.single_record_audio_enabled = True
        self.toggle_voice_input(checked=True)

    def process_voice_input(self):
        while hasattr(self, "voice_input"):
            try:
                time.sleep(0.1)
                message: Optional[str] = None
                # Safely check and get input from voice_input
                if hasattr(self, "voice_input"):
                    with threading.Lock():
                        message = self.voice_input.get_input()

                if message:
                    # Use a thread-safe way to check and use self.use_local_whisper
                    with threading.Lock():
                        use_local_whisper = self.use_local_whisper

                    if not use_local_whisper:
                        # Ensure client_api.transcribe_audio is thread-safe or consider making it thread-safe
                        message = client_api.transcribe_audio(message)

                    if message:
                        QMetaObject.invokeMethod(  # type: ignore
                            self,
                            "send_command",  # type: ignore
                            Qt.QueuedConnection,  # type: ignore
                            Q_ARG(str, message),
                        )

                        if not self.allow_voice_interrupt:
                            self.update_record_button_state_waiting()

                        # Safely update and check self.single_record_audio_enabled
                        if self.single_record_audio_enabled:
                            with threading.Lock():
                                QMetaObject.invokeMethod(  # type: ignore
                                    self,
                                    "clear_voice_input",  # type: ignore
                                    Qt.QueuedConnection,  # type: ignore
                                )
                                self.single_record_audio_enabled = False
                            break
            except queue.Empty:
                continue
            except Exception as e:
                # Log the exception or handle it as needed instead of silently breaking the loop
                print(f"Error processing voice input: {e}")
                break

    def cleanup_before_exit(self):
        # Ensure voice input is turned off before exiting
        if hasattr(self, "voice_input"):
            self.toggle_voice_input(checked=False)

    def populate_tree(self, directory: str, parent_index: int):
        model: CustomFileSystemModel = self.centralWidget().layout().itemAt(0).widget().model()  # type: ignore
        item_index = model.index(directory)  # type: ignore
        model.insertRow(0, item_index.parent())  # type: ignore

        for item_name in os.listdir(directory):
            item_path = os.path.join(directory, item_name)

            # Insert the item into the tree
            item_index: int = model.index(item_path)  # type: ignore
            model.insertRow(0, item_index.parent())  # type: ignore

            # If it's a directory, make a recursive call to populate its children
            if os.path.isdir(item_path):
                self.populate_tree(item_path, item_index)

    def item_selected(self, index: int) -> None:
        model: CustomFileSystemModel = (  # type: ignore
            self.centralWidget().layout().itemAt(0).widget().model()  # type: ignore
        )
        file_path: str = model.filePath(index)  # type: ignore

        self.file_clicked(file_path)  # type: ignore

    def file_clicked(self, file_path: str):
        print("File clicked:", file_path)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Override the keyPressEvent to capture Enter key press
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:  # type: ignore
            self.focus_command_input()
        else:
            super().keyPressEvent(event)

    def focus_command_input(self) -> None:
        self.command.setFocus()

    @Slot(str)
    def send_command(self, command: str) -> None:
        print("Sending command:", command)
        self.display_message("User: " + command, color="darkblue")
        self.message_sender.send_message(command)

    def execute_command(self) -> None:
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

        system_prompt = os.getenv(
            "CLIENT.SYSTEM_PROMPT",
            "You are AC, the helpful AI coding assistant. You are currently running through the following model: {model_path}.",
        )
        system_prompt = system_prompt.replace("{model_path}", model_path)

        client_api.add_system_message(self.conversation_id, system_prompt)
        print(system_prompt)

    def clear_chat(self):
        self.chat_display.clear()
        self.conversation_id = client_api.start_conversation()
        self.add_system_message()

    def download_model(self):
        dialog = DownloadModelDialog(self)
        if dialog.exec() == QDialog.Accepted:  # type: ignore
            pass

    def change_model(self):
        if not self.conversation_id:
            self.conversation_id = client_api.start_conversation()
        dialog = ChangeModelDialog(self)
        if dialog.exec() == QDialog.Accepted:  # type: ignore
            self.add_system_message()

    def download_method(self, repo_id: str, filename: str):
        print(f"Downloading model from {repo_id} with name {filename}")

        model_dir_paths = ["models", os.path.join("..", "models")]

        for model_dir_path in model_dir_paths:
            if os.path.exists(model_dir_path):
                model_path = os.path.join(model_dir_path, filename)
                if not os.path.exists(model_path):
                    downloaded_model_path = hf_hub_download(  # type: ignore
                        repo_id=repo_id,
                        filename=filename,
                    )

                    # Move the downloaded model to the models folder
                    os.rename(downloaded_model_path, model_path)
                break


class ChangeModelDialog(QDialog):
    def __init__(self, parent: Optional[AssistantCoder] = None):
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

        self._parent = parent

    def change(self):
        # Retrieve the values from the line edits and trigger the download method
        model_name = self.model_combo_box.currentText()
        self.accept()
        if self._parent:
            client_api.change_model(self._parent.conversation_id, model_name)


class CommandTextEdit(QTextEdit):
    def __init__(
        self,
        parent: Optional[AssistantCoder] = None,
        command_execution: Optional[Callable[[], Any]] = None,
    ):
        super().__init__(parent)
        self.command_execution = command_execution
        self.setMaximumHeight(int(self.document().size().height() * 3))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # type: ignore

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Return and not e.modifiers() == Qt.ShiftModifier:  # type: ignore
            # Enter without Shift pressed, execute the command
            if self.command_execution:
                self.command_execution()
        else:
            super().keyPressEvent(e)


class DownloadModelDialog(QDialog):
    def __init__(self, parent: AssistantCoder):
        super().__init__(parent)
        self.setWindowTitle("Download Model")

        self.repo_id_label = QLabel("Repo id:")
        self.repo_id_edit = QLineEdit()
        self.repo_id_edit.setPlaceholderText("TheBloke/Mistral-7B-Instruct-v0.2-GGUF")
        self.filename_label = QLabel("Filename:")
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("mistral-7b-instruct-v0.2.Q5_K_M.gguf")

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

        self.assistant_coder = parent

    def download(self):
        # Retrieve the values from the line edits and trigger the download method
        repo_id = self.repo_id_edit.text().strip()
        filename = self.filename_edit.text().strip()
        self.accept()  # Close the dialog
        self.assistant_coder.download_method(
            repo_id, filename
        )  # Call the download method


class MessageSender(QObject):
    message_received = Signal(str)
    suggestions_received = Signal(list)

    def __init__(self, parent: AssistantCoder):
        super().__init__(parent)
        self._parent = parent

    def send_message(self, command: str):
        selected_files = list(self._parent.checked_files)

        chat_mode = self._parent.chat_mode_action.isChecked()
        use_tools = self._parent.use_tools_action.isChecked()
        use_reflections = self._parent.use_reflections_action.isChecked()
        use_suggestions = self._parent.use_suggestions_action.isChecked()
        use_knowledge = self._parent.use_knowledge_action.isChecked()
        use_safety = self._parent.use_safety_action.isChecked()
        use_clipboard = self._parent.use_clipboard_action.isChecked()
        use_tts = self._parent.use_tts_action.isChecked()
        use_voice_input = self._parent.use_voice_input_action.isChecked()

        clipboard_content = QGuiApplication.clipboard().text() if use_clipboard else ""

        def generate_response_thread():
            suggestions = []
            response = None
            try:
                for i in range(2):
                    if use_suggestions:
                        response, suggestions = (
                            client_api.generate_response_with_suggestions(
                                self._parent.conversation_id,
                                command,
                                selected_files=selected_files,
                                single_message_mode=not chat_mode,
                                use_tools=use_tools,
                                use_reflections=use_reflections,
                                use_knowledge=use_knowledge,
                                max_tokens=1000,
                                ask_permission_to_run_tools=use_safety,
                                clipboard_content=clipboard_content,
                            )
                        )
                    else:
                        response = client_api.generate_response(
                            self._parent.conversation_id,
                            command,
                            selected_files=selected_files,
                            single_message_mode=not chat_mode,
                            use_tools=use_tools,
                            use_reflections=use_reflections,
                            use_knowledge=use_knowledge,
                            max_tokens=1000,
                            ask_permission_to_run_tools=use_safety,
                            clipboard_content=clipboard_content,
                        )

                    if not response and i == 0:
                        self._parent.conversation_id = client_api.start_conversation()
                        self._parent.add_system_message()
                    else:
                        break

                if response:
                    self.message_received.emit("AC: " + response)

                    if use_tts:

                        if self._parent.use_local_tts:
                            if not self._parent.text_to_speech_engine:
                                self._parent.text_to_speech_engine = (
                                    TextToSpeechEngine()
                                )
                            wav_file_paths = self._parent.text_to_speech_engine.text_to_speech_with_split(
                                response
                            )
                            for path in wav_file_paths:
                                with open(path, "rb") as f:
                                    audio = AudioSegment.from_file(f, format="wav")  # type: ignore
                                    play(audio)  # type: ignore
                        else:
                            for tts_response in client_api.generate_tts(response):
                                if tts_response:
                                    audio_stream = io.BytesIO(tts_response)
                                    audio = AudioSegment.from_file(audio_stream, format="wav")  # type: ignore
                                    play(audio)  # type: ignore

                    if not self._parent.allow_voice_interrupt:
                        if use_voice_input:
                            QMetaObject.invokeMethod(  # type: ignore
                                self._parent,
                                "update_record_button_state_listening",  # type: ignore
                                Qt.QueuedConnection,  # type: ignore
                            )
                        else:
                            QMetaObject.invokeMethod(  # type: ignore
                                self._parent,
                                "update_record_button_state_record_audio",  # type: ignore
                                Qt.QueuedConnection,  # type: ignore
                            )

                    if suggestions:
                        self.suggestions_received.emit(suggestions)

            except Exception as e:
                traceback.print_exc()
                print("Error in generate_response_thread:", e)

        response_thread = threading.Thread(target=generate_response_thread)
        response_thread.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Assistant Coder Desktop Client.",
        epilog="For more information, visit https://github.com/ARadRareness/assistant-coder.",
    )
    parser.add_argument(
        "--server-url",
        type=str,
        help="URL of the remote server to connect to. Default is http://127.0.0.1:17173.",
        default="http://127.0.0.1:17173",
    )
    args = parser.parse_args()

    app = QApplication([])
    window = AssistantCoder(app, server_url=args.server_url)
    window.show()
    app.exec()
