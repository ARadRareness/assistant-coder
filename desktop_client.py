import os
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFrame,
    QVBoxLayout,
    QTreeView,
    QLineEdit,
    QLabel,
    QPushButton,
    QCheckBox,
    QFileSystemModel,
    QFileDialog,
)

from PySide6.QtCore import QDir, Qt, Signal

import client_api


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


class AssistantCoder(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Assistant Coder")

        self.conversation_id = client_api.start_conversation()

        self.add_system_message()

        self.init_ui()

    def init_ui(self):
        central_widget = QFrame()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout(central_widget)

        self.init_treeview(self.layout)
        self.init_command_entry(self.layout)

        # Add a button to open directories
        open_dir_button = QPushButton("Open Directory", self)
        open_dir_button.clicked.connect(self.open_directory)
        self.layout.addWidget(open_dir_button)

        self.chat_mode = QCheckBox("Chat mode", self)
        self.layout.addWidget(self.chat_mode)

    def init_treeview(self, layout):
        self.model = CustomFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        # self.model.setHeaderData(4, Qt.Horizontal, "Checked")

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(QDir.rootPath()))
        self.tree_view.setAnimated(False)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        self.model.checkStateChanged.connect(self.tree_state_changed)

        layout.addWidget(self.tree_view)

    def tree_state_changed(self, path, checked):
        # print(self.model.checkStates)
        print(path, checked)

    def init_command_entry(self, layout):
        command_label = QLabel("Command:", self)
        layout.addWidget(command_label)

        self.command = QLineEdit(self)
        self.command.returnPressed.connect(self.execute_command)
        layout.addWidget(self.command)

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

    def execute_command(self):
        command = self.command.text()
        self.command.clear()

        response = client_api.generate_response(
            self.conversation_id,
            command,
            single_message_mode=not self.chat_mode.isChecked(),
        )

        print(response)

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


if __name__ == "__main__":
    app = QApplication([])
    window = AssistantCoder()
    window.show()
    app.exec()
