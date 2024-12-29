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
        # Create deep copies to isolate data
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
        """Handle case where export takes too long"""
        if self.is_running:
            self.is_running = False
            self.finished.emit("Export timed out - operation cancelled")
            self.terminate()  # Force thread termination

    def run(self):
        try:
            # Start timeout timer
            # Convert to milliseconds
            self.timer.start(self.timeout_seconds * 1000)

            self.progress.emit("Starting export...")

            # Create figure - simplified version with minimal dependencies
            import plotly.graph_objects as go
            fig = go.Figure()

            # Add trace directly using graph_objects for more control
            fig.add_trace(go.Bar(
                x=self.density_df['time_minutes'],
                y=self.density_df['words_per_bin'],
                name='Word Density'
            ))

            # Update layout with minimal styling
            fig.update_layout(
                title=f'Word Density Over Time (Gap Threshold: {self.gap_threshold}s)',
                xaxis_title='Time (minutes)',
                yaxis_title='Words per Minute',
                template='plotly_dark',
                width=1200,
                height=800
            )

            self.progress.emit("Writing image...")

            # Use lower-level pio functionality
            import plotly.io as pio
            pio.kaleido.scope.mathjax = None

            # Write image with explicit timeout
            with open(self.file_path, 'wb') as f:
                img_bytes = pio.to_image(
                    fig,
                    format=self.file_type,
                    scale=2,
                    validate=False  # Skip validation for speed
                )
                f.write(img_bytes)

            # Stop timeout timer
            self.timer.stop()

            if self.is_running:  # Check if we haven't been cancelled
                self.progress.emit("Cleanup...")
                fig.data = []
                fig = None
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
        self.wait(1000)  # Wait up to 1 second for natural completion
        if self.isRunning():
            self.terminate()
            self.wait()  # Wait for termination to complete
