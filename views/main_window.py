# transcript_clusterviz/views/main_window.py

import os

from PyQt6.QtWidgets import (
    QMainWindow, QTextEdit, QVBoxLayout, QWidget,
    QPushButton, QApplication, QFileDialog, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView  # For embedding Plotly HTML

from controllers.parse_controller import ParseController


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcript ClusterViz - Prototype")
        self.setAcceptDrops(True)

        # Controller with default bin_size=60s, gap_threshold=5s
        self.parse_controller = ParseController(gap_threshold=5.0, bin_size=60)

        # UI elements
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)

        self.cluster_button = QPushButton("Perform Time-Based Clustering")
        self.cluster_button.clicked.connect(self.handle_clustering)

        self.density_button = QPushButton("Plot Density Chart")
        self.density_button.clicked.connect(self.handle_density)

        self.open_file_button = QPushButton("Open SRT File")
        self.open_file_button.clicked.connect(self.handle_open_file)

        # A QWebEngineView for showing the Plotly chart
        self.web_view = QWebEngineView()

        # Layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.open_file_button)
        button_layout.addWidget(self.cluster_button)
        button_layout.addWidget(self.density_button)

        container = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.text_display)
        main_layout.addWidget(self.web_view)
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.current_filepath = None

    def handle_open_file(self):
        """
        Let user pick an SRT file via file dialog.
        """
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("SRT files (*.srt)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.handle_srt_file(selected_files[0])

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                if filepath.lower().endswith(".srt"):
                    self.handle_srt_file(filepath)
                else:
                    self.text_display.append("Not an .srt file: " + filepath)

    def handle_srt_file(self, filepath):
        if not os.path.exists(filepath):
            self.text_display.append(f"File not found: {filepath}")
            return

        self.current_filepath = filepath
        df = self.parse_controller.parse_srt_file(filepath)
        self.text_display.clear()
        self.text_display.append(f"Loaded SRT file: {filepath}\n")
        preview = df.head(5).to_string(index=False)
        self.text_display.append(preview)

    def handle_clustering(self):
        """
        Uses the parse controller to cluster the currently loaded subtitles,
        then shows a small preview of the result (including cluster_ids).
        """
        if self.parse_controller.current_df is None:
            self.text_display.append(
                "No data to cluster. Please load an SRT file first.")
            return

        clustered_df = self.parse_controller.cluster_by_time()
        self.text_display.append("\n--- Time-Based Clustering Results ---\n")
        preview = clustered_df.head(5).to_string(index=False)
        self.text_display.append(preview)
        unique_clusters = clustered_df["cluster_id"].nunique()
        self.text_display.append(f"\nTotal clusters found: {unique_clusters}")

    def handle_density(self):
        """
        Calculate and plot the words-per-bin chart in the embedded QWebEngineView.
        """
        if self.parse_controller.current_df is None:
            self.text_display.append(
                "No data to plot. Please load an SRT file first.")
            return

        # Calculate density
        density_df = self.parse_controller.calculate_density()
        # Create Plotly figure HTML
        chart_html = self.parse_controller.plot_density_chart(density_df)

        # Load the HTML into the QWebEngineView
        self.web_view.setHtml(chart_html)
        self.text_display.append("\n--- Density Chart Updated ---\n")
