from typing import Any, Dict

from PySide6.QtWidgets import (
    QFileSystemModel,
)

from PySide6.QtCore import (
    Qt,
    Signal,
    QModelIndex,
    QPersistentModelIndex,
)


class CustomFileSystemModel(QFileSystemModel):
    """Original class created by musicamante"""

    checkStateChanged = Signal(str, bool)

    def __init__(self):
        super().__init__()
        self.checkStates: Dict[str, Qt.CheckState] = {}
        self.rowsInserted.connect(self.checkAdded)
        self.rowsRemoved.connect(self.checkParent)
        self.rowsAboutToBeRemoved.connect(self.checkRemoved)

    def checkState(self, index: QModelIndex | QPersistentModelIndex) -> Qt.CheckState:
        return self.checkStates.get(self.filePath(index), Qt.Unchecked)  # type: ignore

    def setCheckState(
        self,
        index: QModelIndex | QPersistentModelIndex,
        state: Qt.CheckState,
        emitStateChange: bool = True,
    ) -> None:
        path = self.filePath(index)
        if self.checkStates.get(path) == state:
            return
        self.checkStates[path] = state
        if emitStateChange:
            self.checkStateChanged.emit(path, bool(state))

    def checkAdded(self, parent: QModelIndex, first: int, last: int) -> None:
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

    def checkRemoved(self, parent: QModelIndex, first: int, last: int) -> None:
        # remove items from the internal dictionary when a file is deleted;
        # note that this *has* to happen *before* the model actually updates,
        # that's the reason this function is connected to rowsAboutToBeRemoved
        for row in range(first, last + 1):
            path = self.filePath(self.index(row, 0, parent))
            if path in self.checkStates:
                self.checkStates.pop(path)

    def checkParent(self, parent: QModelIndex) -> None:
        # verify the state of the parent according to the children states
        if not parent.isValid():
            return
        childStates = [
            self.checkState(self.index(r, 0, parent))
            for r in range(self.rowCount(parent))
        ]

        newState = Qt.Checked if all(childStates) else Qt.Unchecked  # type: ignore
        oldState = self.checkState(parent)

        if newState != oldState:
            self.setCheckState(parent, newState)  # type: ignore
            self.dataChanged.emit(parent, parent)
        self.checkParent(parent.parent())

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlags:  # type: ignore
        return super().flags(index) | Qt.ItemIsUserCheckable  # type: ignore

    def data(self, index: QModelIndex | QPersistentModelIndex, role=Qt.DisplayRole):  # type: ignore
        if role == Qt.CheckStateRole and index.column() == 0:  # type: ignore
            return self.checkState(index)
        return super().data(index, role)

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: Any,
        role: int = 0,
        checkParent: bool = True,
        emitStateChange: bool = True,
    ) -> bool:
        if role == Qt.CheckStateRole and index.column() == 0:  # type: ignore
            self.setCheckState(index, value, emitStateChange)

            for row in range(self.rowCount(index)):
                # set the data for the children, but do not emit the state change,
                # and don't check the parent state (to avoid recursion)
                child_index = self.index(row, 0, index)
                self.setData(
                    child_index,
                    value,
                    Qt.CheckStateRole,  # type: ignore
                    checkParent=False,
                    emitStateChange=False,
                )
            self.dataChanged.emit(index, index)
            if checkParent:
                self.checkParent(index.parent())
            return True

        return super().setData(index, value, role)
