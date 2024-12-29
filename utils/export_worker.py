import os
from PyQt6.QtCore import QThread, pyqtSignal
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
    progress = pyqtSignal(str)  # Add progress signal

    def __init__(self, density_df, gap_threshold, file_path, file_type, current_df=None):
        super().__init__()
        self.density_df = density_df.copy()  # Create a copy of the data
        self.gap_threshold = gap_threshold
        self.file_path = file_path
        self.file_type = file_type
        self.current_df = current_df.copy() if current_df is not None else None
        self.is_running = True

    def stop(self):
        self.is_running = False
        self.wait()  # Wait for the thread to finish

    def cleanup(self):
        """Clean up resources"""
        self.density_df = None
        self.current_df = None
        gc.collect()  # Force garbage collection

    def run(self):
        try:
            if not self.is_running:
                return

            self.progress.emit("Starting export process...")

            if not self.file_path:
                raise ValueError("No file path provided for export.")

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.file_path) if os.path.dirname(
                self.file_path) else '.', exist_ok=True)

            # Add cluster information if available
            if self.current_df is not None and "cluster_id" in self.current_df.columns:
                self.progress.emit("Processing cluster information...")
                try:
                    self.density_df = pd.merge(
                        self.density_df,
                        self.current_df[["bin_index",
                                         "cluster_id"]].drop_duplicates(),
                        on="bin_index",
                        how="left"
                    )
                except Exception as e:
                    print(f"DEBUG: Merge failed - {str(e)}")

            if not self.is_running:
                return

            self.progress.emit("Creating figure...")

            # Set up the renderer
            pio.kaleido.scope.mathjax = None
            pio.kaleido.scope.default_format = self.file_type

            # Create figure with minimal styling first
            fig = px.bar(
                self.density_df,
                x="time_minutes",
                y="words_per_bin",
                title=f"Word Density Over Time (Gap Threshold: {self.gap_threshold}s)"
            )

            if not self.is_running:
                return

            self.progress.emit("Writing image...")

            # Write image with maximum compatibility settings
            write_image(
                fig,
                self.file_path,
                format=self.file_type,
                engine='kaleido',
                width=1200,
                height=800,
                scale=1
            )

            # Clean up
            fig.data = []
            fig = None
            self.cleanup()

            self.progress.emit("Export completed.")
            self.finished.emit(f"Export successful: {self.file_path}")

        except Exception as e:
            import traceback
            error_msg = f"Export failed: {str(e)}\n{traceback.format_exc()}"
            print(f"DEBUG: {error_msg}")
            self.finished.emit(error_msg)
        finally:
            self.cleanup()
            self.is_running = False
