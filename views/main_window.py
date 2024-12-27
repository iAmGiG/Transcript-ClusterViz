# transcript_clusterviz/views/main_window.py

import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

from controllers.parse_controller import ParseController


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcript ClusterViz - Prototype")
        self.setAcceptDrops(True)  # Enable drag & drop

        # Controller
        self.parse_controller = ParseController()

        # Simple UI - just a text widget to show output
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)

        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.text_display)
        container.setLayout(layout)
        self.setCentralWidget(container)

    def dragEnterEvent(self, event):
        """
        Called when a user drags a file into the main window.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Called when a user drops the file.
        """
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                if filepath.lower().endswith(".srt"):
                    self.handle_srt_file(filepath)
                else:
                    self.text_display.append("Not an .srt file: " + filepath)

    def handle_srt_file(self, filepath):
        """
        Call the controller to parse the dropped .srt file, then display results.
        """
        if not os.path.exists(filepath):
            self.text_display.append("File not found: " + filepath)
            return

        parsed_data = self.parse_controller.parse_srt_file(filepath)

        # Display some info
        self.text_display.clear()
        self.text_display.append(f"Parsed SRT file: {filepath}\n")
        for item in parsed_data[:5]:
            self.text_display.append(
                f"Index: {item['index']}, Start: {item['start_seconds']}, "
                f"End: {item['end_seconds']}, Text: {item['text']}"
            )
        self.text_display.append("...\n(Showing first 5 entries)")
