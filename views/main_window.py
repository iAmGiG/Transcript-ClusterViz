# transcript_clusterviz/views/main_window.py

import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget,
    QPushButton, QFileDialog, QHBoxLayout,
    QSizePolicy, QSlider, QLabel, QMessageBox, QTabWidget, QStatusBar,
    QTableWidget, QTableWidgetItem
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from utils.export_worker import ExportWorker, ChartExportWorker
from controllers.parse_controller import ParseController


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcript ClusterViz - Prototype")
        self.setAcceptDrops(True)

        # Controller with default bin_size=60s, gap_threshold=5s
        self.parse_controller = ParseController(gap_threshold=5.0, bin_size=60)

        # Create main toolbar with file operations
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout()
        self.open_file_button = QPushButton("Open SRT File")
        self.open_file_button.clicked.connect(self.handle_open_file)
        toolbar_layout.addWidget(self.open_file_button)
        toolbar_widget.setLayout(toolbar_layout)

        # Tabs for clustering and density
        self.tabs = QTabWidget()
        self.clustering_tab = QWidget()
        self.density_tab = QWidget()

        # Clustering Tab
        self.cluster_button = QPushButton("Perform Time-Based Clustering")
        self.cluster_button.clicked.connect(self.handle_clustering)
        self.cluster_table = QTableWidget()
        # Number of columns: index, start, end, text, cluster_id
        self.cluster_table.setColumnCount(5)
        self.cluster_table.setHorizontalHeaderLabels(
            ["Index", "Start", "End", "Text", "Cluster ID"])
        self.cluster_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.cluster_table.setVerticalScrollMode(
            QTableWidget.ScrollMode.ScrollPerPixel)
        self.cluster_table.setHorizontalScrollMode(
            QTableWidget.ScrollMode.ScrollPerPixel)
        self.cluster_table.resizeColumnsToContents()
        self.cluster_table.resizeRowsToContents()
        self.export_clusters_button = QPushButton("Export Clusters")
        self.export_clusters_button.clicked.connect(
            self.handle_export_clusters)

        cluster_layout = QVBoxLayout()
        cluster_layout.addWidget(self.cluster_table)
        cluster_layout.addWidget(self.cluster_button)
        cluster_layout.addWidget(self.export_clusters_button)
        self.clustering_tab.setLayout(cluster_layout)

        # Gap threshold slider
        threshold_container = QWidget()
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Time Gap Threshold (seconds):")
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(1, 300)  # Range: 1s to 20s
        self.threshold_slider.setValue(5)  # Default value
        self.threshold_slider.valueChanged.connect(
            self.handle_threshold_change)
        self.threshold_value_label = QLabel("5")

        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_value_label)
        threshold_container.setLayout(threshold_layout)

        # Insert below the clustering button
        cluster_layout.insertWidget(1, threshold_container)

        # Density Tab
        density_controls = QWidget()
        density_controls_layout = QHBoxLayout()

        # Add density button
        self.density_button = QPushButton("Plot Density Chart")
        self.export_chart_button = QPushButton("Export Chart")
        self.export_chart_button.clicked.connect(self.handle_export_chart)
        self.density_button.clicked.connect(self.handle_density)
        density_controls_layout.addWidget(self.density_button)
        density_controls_layout.addWidget(self.export_chart_button)

        # Add bin size slider
        slider_container = QWidget()
        slider_layout = QHBoxLayout()
        slider_label = QLabel("Bin Size (seconds):")
        self.bin_slider = QSlider(Qt.Orientation.Horizontal)
        self.bin_slider.setRange(10, 300)  # Bin size range: 10s to 5m
        self.bin_slider.setValue(60)  # Default bin size
        self.bin_slider.valueChanged.connect(self.handle_bin_size_change)

        # Add value label that updates with slider
        self.bin_size_value_label = QLabel("60")

        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.bin_slider)
        slider_layout.addWidget(self.bin_size_value_label)
        slider_container.setLayout(slider_layout)
        density_controls_layout.addWidget(slider_container)

        density_controls.setLayout(density_controls_layout)

        # Web view for the plot
        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(400)
        self.web_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Combine all density elements
        density_layout = QVBoxLayout()
        density_layout.addWidget(density_controls)
        density_layout.addWidget(self.web_view)
        self.density_tab.setLayout(density_layout)

        # Add tabs
        self.tabs.addTab(self.clustering_tab, "Clustering")
        self.tabs.addTab(self.density_tab, "Density Chart")

        # Status bar for updates
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Main layout
        container = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(toolbar_widget)
        main_layout.addWidget(self.tabs)
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Set initial window size but allow resizing
        self.resize(800, 800)
        self.current_filepath = None

    def show_error(self, message):
        error_dialog = QMessageBox(self)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(message)
        error_dialog.setIcon(QMessageBox.Icon.Warning)
        error_dialog.exec()

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
        """
        Handles loading an SRT file and displaying the preview in the clustering tab.
        """
        if not os.path.exists(filepath):
            self.status_bar.showMessage(f"File not found: {filepath}")
            return

        self.current_filepath = filepath
        df = self.parse_controller.parse_srt_file(filepath)

        # Clear previous table data
        self.cluster_table.setRowCount(0)

        # Display first 5 rows in the table as a preview
        for i, row in df.head(5).iterrows():
            self.cluster_table.insertRow(i)
            self.cluster_table.setItem(
                i, 0, QTableWidgetItem(str(row["index"])))
            self.cluster_table.setItem(
                i, 1, QTableWidgetItem(f"{row['start_seconds']:.2f}"))
            self.cluster_table.setItem(
                i, 2, QTableWidgetItem(f"{row['end_seconds']:.2f}"))
            self.cluster_table.setItem(i, 3, QTableWidgetItem(row["text"]))
            # Placeholder for cluster_id
            self.cluster_table.setItem(i, 4, QTableWidgetItem("N/A"))

        self.status_bar.showMessage(f"Loaded: {filepath}", 5000)

    def handle_clustering(self):
        """
        Handles clustering and updates the clustering tab with a table.
        """
        if self.parse_controller.current_df is None:
            self.status_bar.showMessage(
                "No data to cluster. Please load an SRT file first.")
            return

        clustered_df = self.parse_controller.cluster_by_time()

        # Clear previous results
        self.cluster_table.setRowCount(0)

        # Populate the table
        for i, row in clustered_df.iterrows():
            self.cluster_table.insertRow(i)
            self.cluster_table.setItem(
                i, 0, QTableWidgetItem(str(row["index"])))
            self.cluster_table.setItem(
                i, 1, QTableWidgetItem(f"{row['start_seconds']:.2f}"))
            self.cluster_table.setItem(
                i, 2, QTableWidgetItem(f"{row['end_seconds']:.2f}"))
            self.cluster_table.setItem(i, 3, QTableWidgetItem(row["text"]))
            self.cluster_table.setItem(
                i, 4, QTableWidgetItem(str(row["cluster_id"])))

        unique_clusters = clustered_df["cluster_id"].nunique()
        self.status_bar.showMessage(
            f"Clustering completed: {unique_clusters} clusters found", 5000)

    def handle_density(self):
        """
        Handles density chart plotting and updates the density tab.
        """
        if self.parse_controller.current_df is None:
            self.status_bar.showMessage(
                "No data to plot. Please load an SRT file first.")
            return

        # Ensure clustering is updated before plotting
        if "cluster_id" not in self.parse_controller.current_df.columns:
            print("DEBUG: Recalculating clustering as 'cluster_id' is missing.")
            self.parse_controller.current_df = self.parse_controller.cluster_by_time()

        try:
            # Calculate density and plot
            density_df = self.parse_controller.calculate_density()
            chart_html = self.parse_controller.plot_density_chart(density_df)
            self.web_view.setHtml(chart_html)
            self.status_bar.showMessage(
                "Density chart updated with clustering", 5000)
        except Exception as e:
            print(f"DEBUG: Error occurred: {str(e)}")
            self.status_bar.showMessage(
                f"Error creating density chart: {str(e)}")

    def handle_bin_size_change(self, value):
        """
        Updates the bin size in the controller and refreshes the density plot
        """
        self.bin_size_value_label.setText(str(value))  # Update the label
        self.parse_controller.bin_size = value

        if self.parse_controller.current_df is not None and self.tabs.currentWidget() == self.density_tab:
            self.handle_density()  # Recalculate density with new bin size
            self.status_bar.showMessage(
                f"Updated bin size to {value} seconds", 3000)

    def handle_threshold_change(self, value):
        """
        Updates the gap_threshold in ParseController and refreshes clustering results.
        """
        self.threshold_value_label.setText(str(value))  # Update label
        self.parse_controller.gap_threshold = value  # Update threshold

        # Re-run clustering if data is loaded
        if self.parse_controller.current_df is not None:
            clustered_df = self.parse_controller.cluster_by_time()
            self.parse_controller.current_df = clustered_df  # Ensure `current_df` is updated

            # Clear and repopulate the table with updated clustering
            self.cluster_table.setRowCount(0)
            for i, row in clustered_df.iterrows():
                self.cluster_table.insertRow(i)
                self.cluster_table.setItem(
                    i, 0, QTableWidgetItem(str(row["index"])))
                self.cluster_table.setItem(
                    i, 1, QTableWidgetItem(f"{row['start_seconds']:.2f}"))
                self.cluster_table.setItem(
                    i, 2, QTableWidgetItem(f"{row['end_seconds']:.2f}"))
                self.cluster_table.setItem(i, 3, QTableWidgetItem(row["text"]))
                self.cluster_table.setItem(
                    i, 4, QTableWidgetItem(str(row["cluster_id"])))

            unique_clusters = clustered_df["cluster_id"].nunique()
            self.status_bar.showMessage(
                f"Updated clustering with gap threshold: {value}s", 3000)

    def handle_export_clusters(self):
        """
        Exports clustering results in various formats using threading.
        """
        if self.parse_controller.current_df is None or "cluster_id" not in self.parse_controller.current_df.columns:
            self.status_bar.showMessage(
                "No clustering data available to export.")
            return

        # Open file dialog to select save location and file type
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self,
            "Save Clusters As",
            "",
            "PNG Files (*.png);;PDF Files (*.pdf);;CSV Files (*.csv);;Excel Files (*.xlsx)"
        )

        if not file_path:
            self.status_bar.showMessage("Export canceled.")
            return

        # Determine file type
        file_type = file_path.split(".")[-1].lower()
        if file_type not in ["png", "pdf", "csv", "xlsx"]:
            self.status_bar.showMessage("Unsupported file format.")
            return

        # Prepare data and metadata
        df = self.parse_controller.current_df[[
            "index", "start_seconds", "end_seconds", "text", "cluster_id"]]
        gap_threshold = self.parse_controller.gap_threshold
        num_clusters = df["cluster_id"].nunique()

        # Start export in a separate thread
        self.export_thread = ExportWorker(
            df, file_path, file_type, gap_threshold, num_clusters)
        self.export_thread.finished.connect(self.on_export_finished)
        self.export_thread.start()

        self.status_bar.showMessage("Exporting...")

    def on_chart_export_finished(self, message):
        """
        Separate handler for chart export completion
        """
        print(f"DEBUG: Chart export thread finished with message: {message}")
        self.status_bar.showMessage(message)
        if "failed" in message.lower():
            self.show_error(message)

    def handle_export_chart(self):
        """
        Exports the density chart as an image or PDF using Plotly.
        """
        if self.parse_controller.current_df is None:
            self.status_bar.showMessage("No data available to export.")
            return

        # Open file dialog to select save location and file type
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self,
            "Save Density Chart As",
            "",
            # Removed JPEG as it's less reliable
            "PNG Files (*.png);;PDF Files (*.pdf)"
        )

        if not file_path:
            self.status_bar.showMessage("Export canceled.")
            return

        # Determine file type
        file_type = file_path.split(".")[-1].lower()
        if file_type not in ["png", "pdf"]:
            self.status_bar.showMessage("Unsupported file format.")
            return

        try:
            # Clean up any existing export thread
            if hasattr(self, 'chart_export_thread'):
                try:
                    self.chart_export_thread.stop()
                    self.chart_export_thread.wait()
                except:
                    pass

            # Prepare density data and start export thread
            density_df = self.parse_controller.calculate_density()

            # Create new thread instance
            self.chart_export_thread = ChartExportWorker(
                density_df,
                self.parse_controller.gap_threshold,
                file_path,
                file_type,
                current_df=self.parse_controller.current_df
            )

            # Connect signals
            self.chart_export_thread.progress.connect(self.on_export_progress)
            self.chart_export_thread.finished.connect(
                self.on_chart_export_finished)

            # Start the thread
            self.chart_export_thread.start()

            print(f"DEBUG: Chart export thread started for {file_path}")
            self.status_bar.showMessage("Starting chart export...")

        except Exception as e:
            error_msg = f"Failed to start export: {str(e)}"
            print(f"DEBUG: {error_msg}")
            self.status_bar.showMessage(error_msg)
            self.show_error(error_msg)

    def on_export_progress(self, message):
        """Handle progress updates from the export thread"""
        print(f"DEBUG: Export progress - {message}")
        self.status_bar.showMessage(message)

    def on_chart_export_finished(self, message):
        """Handle completion of chart export"""
        print(f"DEBUG: Chart export finished - {message}")
        self.status_bar.showMessage(message)

        # Clean up the thread
        if hasattr(self, 'chart_export_thread'):
            self.chart_export_thread.deleteLater()
            del self.chart_export_thread

        if "failed" in message.lower():
            self.show_error(message)
