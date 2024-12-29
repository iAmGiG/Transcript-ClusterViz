import os
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
import pandas as pd
import plotly.express as px
import plotly.io as pio
from plotly.io import write_image
import gc


class ExportWorker(QThread):
    finished = pyqtSignal(str)  # Signal to indicate export completion

    def __init__(self, df, file_path, file_type, gap_threshold, num_clusters):
        super().__init__()
        self.df = df
        self.file_path = file_path
        self.file_type = file_type
        self.gap_threshold = gap_threshold
        self.num_clusters = num_clusters

    def run(self):
        try:
            if self.file_type == "png" or self.file_type == "pdf":
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.axis('tight')
                ax.axis('off')

                # Create a table
                data = self.df.values.tolist()
                column_labels = self.df.columns.tolist()
                table = ax.table(
                    cellText=data, colLabels=column_labels, loc='center')
                table.auto_set_font_size(False)
                table.set_fontsize(8)
                table.auto_set_column_width(col=range(len(column_labels)))

                # Add metadata as a title
                ax.set_title(f"Clustering Results\nTime Gap Threshold: {self.gap_threshold}s, Total Clusters: {self.num_clusters}",
                             fontsize=12, pad=20)

                # Save the image
                plt.savefig(self.file_path, format=self.file_type,
                            bbox_inches="tight")
                plt.close(fig)

            elif self.file_type == "csv":
                self.df.to_csv(self.file_path, index=False)
            elif self.file_type == "xlsx":
                self.df.to_excel(self.file_path, index=False)

            self.finished.emit(f"Export successful: {self.file_path}")
        except Exception as e:
            self.finished.emit(f"Export failed: {str(e)}")


class ChartExportWorker(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, density_df, gap_threshold, file_path, file_type, current_df=None, timeout_seconds=30):
        super().__init__()
        self.density_df = density_df.copy(deep=True)
        self.gap_threshold = gap_threshold
        self.file_path = file_path
        self.file_type = file_type
        self.current_df = current_df.copy(
            deep=True) if current_df is not None else None
        self.is_running = True

        # Add timeout handling
        self.timeout_seconds = timeout_seconds
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.handle_timeout)

    def handle_timeout(self):
        if self.is_running:
            self.is_running = False
            self.finished.emit("Export timed out - operation cancelled")
            self.terminate()

    def run(self):
        try:
            self.timer.start(self.timeout_seconds * 1000)

            self.progress.emit("Starting export...")

            # Use matplotlib instead of plotly
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend

            # Create figure and axis
            fig, ax = plt.subplots(figsize=(12, 8))

            # Create bar plot
            ax.bar(self.density_df['time_minutes'],
                   self.density_df['words_per_bin'],
                   color='steelblue')

            # Set labels and title
            ax.set_xlabel('Time (minutes)')
            ax.set_ylabel('Words per Minute')
            ax.set_title(
                f'Word Density Over Time\nGap Threshold: {self.gap_threshold}s')

            # Style the plot
            ax.grid(True, alpha=0.3)
            fig.set_facecolor('#1f1f1f')
            ax.set_facecolor('#1f1f1f')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            for spine in ax.spines.values():
                spine.set_color('white')

            self.progress.emit("Writing image...")

            # Save the plot
            plt.savefig(
                self.file_path,
                format=self.file_type,
                bbox_inches='tight',
                facecolor=fig.get_facecolor(),
                edgecolor='none',
                pad_inches=0.1,
                dpi=300
            )

            # Cleanup
            plt.close(fig)
            self.timer.stop()

            if self.is_running:
                self.progress.emit("Cleanup...")
                self.density_df = None
                self.current_df = None

                import gc
                gc.collect()

                self.finished.emit(f"Export successful: {self.file_path}")

        except Exception as e:
            import traceback
            error_msg = f"Export failed: {str(e)}\n{traceback.format_exc()}"
            print(f"DEBUG: {error_msg}")
            self.finished.emit(error_msg)

        finally:
            self.timer.stop()
            self.is_running = False

    def cleanup(self):
        """External cleanup method"""
        self.timer.stop()
        self.is_running = False
        self.wait(1000)
        if self.isRunning():
            self.terminate()
            self.wait()
