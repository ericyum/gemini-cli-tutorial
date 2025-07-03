import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QAction, QFileDialog, 
                             QMessageBox, QTabWidget, QWidget, QVBoxLayout,
                             QInputDialog, QLineEdit, QPushButton, QHBoxLayout, QLabel)
from PyQt5.QtGui import QIcon, QTextCursor, QTextDocument, QTextDocument
from PyQt5.QtCore import Qt, QSettings

# --- Find Dialog ---
class FindDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Find")
        self.setWindowFlags(Qt.Tool)
        self.layout = QVBoxLayout()
        
        self.find_layout = QHBoxLayout()
        self.find_input = QLineEdit()
        self.find_layout.addWidget(QLabel("Find what:"))
        self.find_layout.addWidget(self.find_input)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.find_text)
        self.find_layout.addWidget(self.search_button)

        self.nav_layout = QHBoxLayout()
        self.next_button = QPushButton("Next")
        self.prev_button = QPushButton("Previous")
        self.next_button.clicked.connect(self.find_next)
        self.prev_button.clicked.connect(self.find_prev)
        self.nav_layout.addWidget(self.prev_button)
        self.nav_layout.addWidget(self.next_button)

        self.layout.addLayout(self.find_layout)
        self.layout.addLayout(self.nav_layout)
        self.setLayout(self.layout)
        
        self.find_input.returnPressed.connect(self.find_text)

    def find_text(self):
        text = self.find_input.text()
        if text and self.parent:
            self.parent.find_text(text)

    def find_next(self):
        text = self.find_input.text()
        if text and self.parent:
            self.parent.find_text(text, find_next=True)

    def find_prev(self):
        text = self.find_input.text()
        if text and self.parent:
            self.parent.find_text(text, find_next=True, backward=True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


# --- Main Notepad Window ---
class Notepad(QMainWindow):
    def __init__(self, restore=True):
        super().__init__()
        self.last_search = ""
        self.find_dialog = None
        self.is_closing_window = False # Flag to differentiate between close window and exit
        self.initUI()
        if restore:
            self.restore_session()
        elif self.tab_widget.count() == 0:
            self.new_tab()

    def initUI(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_current_tab_action)
        self.tab_widget.currentChanged.connect(self.update_edit_menu)
        self.setCentralWidget(self.tab_widget)

        self.setup_menus()
        
        self.setWindowTitle('PyQt Notepad')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon.fromTheme("accessories-text-editor"))
        self.statusBar()

    def setup_menus(self):
        menubar = self.menuBar()
        
        # --- File Menu ---
        file_menu = menubar.addMenu('&File')
        
        new_tab_action = QAction('New Tab', self)
        new_tab_action.setShortcut('Ctrl+T')
        new_tab_action.triggered.connect(self.new_tab)
        file_menu.addAction(new_tab_action)

        new_window_action = QAction('New Window', self)
        new_window_action.setShortcut('Ctrl+N')
        new_window_action.triggered.connect(self.new_window)
        file_menu.addAction(new_window_action)

        open_action = QAction('Open...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        self.recent_menu = file_menu.addMenu('Recent')
        self.update_recent_files_menu()

        file_menu.addSeparator()

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction('Save As...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        save_all_action = QAction('Save All', self)
        save_all_action.setShortcut('Ctrl+Alt+S')
        save_all_action.triggered.connect(self.save_all_files)
        file_menu.addAction(save_all_action)

        file_menu.addSeparator()
        
        close_tab_action = QAction('Close Tab', self)
        close_tab_action.setShortcut('Ctrl+W')
        close_tab_action.triggered.connect(self.close_current_tab_action)
        file_menu.addAction(close_tab_action)
        
        close_window_action = QAction('Close Window', self)
        close_window_action.setShortcut('Ctrl+Shift+W')
        close_window_action.triggered.connect(self.close_window)
        file_menu.addAction(close_window_action)

        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close) # self.close handles the exit logic
        file_menu.addAction(exit_action)

        # --- Edit Menu ---
        self.edit_menu = menubar.addMenu('&Edit')
        self.undo_action = self.edit_menu.addAction('Undo', self.undo, 'Ctrl+Z')
        self.edit_menu.addSeparator()
        self.cut_action = self.edit_menu.addAction('Cut', self.cut, 'Ctrl+X')
        self.copy_action = self.edit_menu.addAction('Copy', self.copy, 'Ctrl+C')
        self.paste_action = self.edit_menu.addAction('Paste', self.paste, 'Ctrl+V')
        self.delete_action = self.edit_menu.addAction('Delete', self.delete, 'Del')
        self.edit_menu.addSeparator()
        self.find_action = self.edit_menu.addAction('Find...', self.show_find_dialog, 'Ctrl+F')
        self.find_next_action = self.edit_menu.addAction('Find Next', self.find_next, 'F3')
        self.find_prev_action = self.edit_menu.addAction('Find Previous', self.find_prev, 'Shift+F3')
        
        self.update_edit_menu() # Initial state

        # --- View Menu ---
        view_menu = menubar.addMenu('&View')
        view_menu.addAction('Zoom In', self.zoom_in, 'Ctrl++')
        view_menu.addAction('Zoom Out', self.zoom_out, 'Ctrl+-')
        view_menu.addAction('Default Zoom', self.default_zoom, 'Ctrl+0')

    def update_edit_menu(self):
        editor = self.current_editor()
        has_selection = bool(editor and editor.textCursor().hasSelection())
        self.cut_action.setEnabled(has_selection)
        self.copy_action.setEnabled(has_selection)
        self.delete_action.setEnabled(has_selection)
        self.paste_action.setEnabled(QApplication.clipboard().mimeData().hasText())

    def current_editor(self):
        return self.tab_widget.currentWidget()

    def new_tab(self, file_path=None, content=''):
        editor = QTextEdit()
        editor.setAcceptRichText(False)
        editor.setText(content)
        editor.copyAvailable.connect(self.update_edit_menu)
        
        index = self.tab_widget.addTab(editor, "Untitled")
        self.tab_widget.setCurrentIndex(index)
        
        if file_path:
            self.set_tab_file_path(index, file_path)
        else:
            editor.setProperty("file_path", None)
        return editor

    def set_tab_file_path(self, index, file_path):
        editor = self.tab_widget.widget(index)
        editor.setProperty("file_path", file_path)
        self.tab_widget.setTabText(index, os.path.basename(file_path))
        self.add_to_recent_files(file_path)

    def new_window(self):
        # The logic in __main__ handles creating new windows
        QApplication.instance().new_window()

    def open_file(self, file_path=None):
        if not file_path:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "",
                                                       "Text Files (*.txt *.md);;All Files (*)", options=options)
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.widget(i).property("file_path") == file_path:
                        self.tab_widget.setCurrentIndex(i)
                        return

                editor = self.current_editor()
                if editor and not editor.toPlainText() and not editor.property("file_path"):
                     editor.setText(content)
                     self.set_tab_file_path(self.tab_widget.currentIndex(), file_path)
                else:
                    self.new_tab(file_path=file_path, content=content)
                
                self.add_to_recent_files(file_path)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {e}")

    def save_file(self, index=None):
        if index is None:
            index = self.tab_widget.currentIndex()
        editor = self.tab_widget.widget(index)
        if not editor: return False
            
        file_path = editor.property("file_path")
        if file_path is None:
            return self.save_as_file(index)
        else:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(editor.toPlainText())
                editor.document().setModified(False)
                self.add_to_recent_files(file_path)
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file: {e}")
                return False

    def save_as_file(self, index=None):
        if index is None:
            index = self.tab_widget.currentIndex()
        editor = self.tab_widget.widget(index)
        if not editor: return False

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File As", "",
                                                   "Text Files (*.txt *.md);;All Files (*)", options=options)
        if file_path:
            self.set_tab_file_path(index, file_path)
            return self.save_file(index)
        return False
        
    def save_all_files(self):
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if editor.document().isModified():
                self.save_file(i)

    def close_current_tab_action(self):
        self.close_tab(self.tab_widget.currentIndex())

    def close_tab(self, index):
        editor = self.tab_widget.widget(index)
        if self.maybe_save(editor):
            self.tab_widget.removeTab(index)
            if self.tab_widget.count() == 0:
                self.close() # Close window if last tab is closed
        else:
            return False # Save was cancelled
        return True

    def close_window(self):
        self.is_closing_window = True
        self.close()

    def maybe_save(self, editor):
        if not editor or not editor.document().isModified():
            return True
        
        file_name = self.tab_widget.tabText(self.tab_widget.indexOf(editor))
        ret = QMessageBox.warning(self, "Application",
                                     f"The document '{file_name}' has been modified.\nDo you want to save your changes?",
                                     QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

        if ret == QMessageBox.Save:
            return self.save_file(self.tab_widget.indexOf(editor))
        elif ret == QMessageBox.Cancel:
            return False
        return True

    # --- Edit Actions ---
    def undo(self):
        if self.current_editor(): self.current_editor().undo()
    def cut(self):
        if self.current_editor(): self.current_editor().cut()
    def copy(self):
        if self.current_editor(): self.current_editor().copy()
    def paste(self):
        if self.current_editor(): self.current_editor().paste()
    def delete(self):
        if self.current_editor(): self.current_editor().textCursor().removeSelectedText()

    # --- View Actions ---
    def zoom_in(self):
        if self.current_editor(): self.current_editor().zoomIn(2)
    def zoom_out(self):
        if self.current_editor(): self.current_editor().zoomOut(2)
    def default_zoom(self):
        if self.current_editor():
            font = self.current_editor().font()
            font.setPointSize(QApplication.font().pointSize())
            self.current_editor().setFont(font)

    # --- Find Functionality ---
    def show_find_dialog(self):
        if not self.find_dialog:
            self.find_dialog = FindDialog(self)
        self.find_dialog.show()
        self.find_dialog.activateWindow()

    def find_text(self, text, find_next=False, backward=False):
        self.last_search = text
        editor = self.current_editor()
        if not editor: return

        flags = QTextDocument.FindFlags()
        if backward:
            flags |= QTextDocument.FindBackward

        if not find_next:
            # Move cursor to beginning to start search from the top
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            editor.setTextCursor(cursor)

        found = editor.find(text, flags)
        if not found:
            QMessageBox.information(self, "Find", f"Cannot find '{text}'")

    def find_next(self):
        if self.last_search:
            self.find_text(self.last_search, find_next=True)

    def find_prev(self):
        if self.last_search:
            self.find_text(self.last_search, find_next=True, backward=True)

    # --- Recent Files ---
    def get_recent_files(self):
        settings = QSettings()
        return settings.value("recentFiles", [], type=list)

    def add_to_recent_files(self, file_path):
        settings = QSettings()
        recent_files = self.get_recent_files()
        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        settings.setValue("recentFiles", recent_files[:10]) # Store last 10
        self.update_recent_files_menu()

    def update_recent_files_menu(self):
        self.recent_menu.clear()
        recent_files = self.get_recent_files()
        for file_path in recent_files:
            action = QAction(os.path.basename(file_path), self)
            action.setData(file_path)
            action.triggered.connect(self.open_recent_file)
            self.recent_menu.addAction(action)
        self.recent_menu.addSeparator()
        clear_action = QAction("Clear List", self)
        clear_action.triggered.connect(self.clear_recent_files)
        self.recent_menu.addAction(clear_action)

    def open_recent_file(self):
        action = self.sender()
        if action:
            self.open_file(action.data())
            
    def clear_recent_files(self):
        settings = QSettings()
        settings.remove("recentFiles")
        self.update_recent_files_menu()

    # --- Session Management ---
    def save_session(self):
        session_data = []
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            file_path = editor.property("file_path")
            # Save unsaved content only if it's not empty
            if not file_path and editor.toPlainText():
                 session_data.append({"file_path": None, "content": editor.toPlainText()})
            elif file_path:
                 session_data.append({"file_path": file_path})

        settings = QSettings()
        settings.setValue("session", json.dumps(session_data))
        settings.setValue("geometry", self.saveGeometry())

    def restore_session(self):
        settings = QSettings()
        
        # Restore geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        session_data_json = settings.value("session")
        if not session_data_json:
            self.new_tab()
            return
            
        try:
            session_data = json.loads(session_data_json)
            if not session_data: # If session was empty
                self.new_tab()
                return

            for item in session_data:
                if item.get("file_path"):
                    self.open_file(item["file_path"])
                elif "content" in item:
                    self.new_tab(content=item["content"])
        except (json.JSONDecodeError, TypeError):
            self.new_tab() # Start fresh if session data is corrupt

    def closeEvent(self, event):
        if self.is_closing_window:
            self.save_session()
            # Don't check for saving changes, just save state and close
            event.accept()
            return

        # This is a full exit (Ctrl+Q or red X button)
        for i in range(self.tab_widget.count() - 1, -1, -1):
            if not self.close_tab(i):
                event.ignore() # A save was cancelled
                return
        
        # Clear session on proper exit
        settings = QSettings()
        settings.remove("session")
        settings.remove("geometry")
        
        event.accept()


class Application(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setOrganizationName("GeminiCLI")
        self.setApplicationName("PyQtNotepad")
        self.windows = []
        self.new_window(restore=True) # Start with one window

    def new_window(self, restore=False):
        notepad = Notepad(restore=restore)
        self.windows.append(notepad)
        notepad.show()

if __name__ == '__main__':
    app = Application(sys.argv)
    sys.exit(app.exec_())