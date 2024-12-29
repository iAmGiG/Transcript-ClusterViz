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
    progress = pyqtSignal(str)

    def __init__(self, density_df, gap_threshold, file_path, file_type, current_df=None):
        super().__init__()
        # Create deep copies to isolate data
        self.density_df = density_df.copy(deep=True)
        self.gap_threshold = gap_threshold
        self.file_path = file_path
        self.file_type = file_type
        self.current_df = current_df.copy(
            deep=True) if current_df is not None else None
        self.is_running = True

    def run(self):
        try:
            self.progress.emit("Starting export...")

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.file_path) if os.path.dirname(
                self.file_path) else '.', exist_ok=True)

            # Create basic figure without clustering
            fig = px.bar(
                self.density_df,
                x='time_minutes',
                y='words_per_bin',
                labels={
                    'time_minutes': 'Time (minutes)',
                    'words_per_bin': 'Words per Minute',
                },
                title=f'Word Density Over Time (Gap Threshold: {self.gap_threshold}s)'
            )

            # Update layout
            fig.update_layout(
                template='plotly_dark',
                plot_bgcolor='rgba(15,15,15,1)',
                paper_bgcolor='rgba(15,15,15,1)',
                font=dict(color='white'),
                title_font_color='white',
                height=600,
                width=1200
            )

            self.progress.emit("Writing image...")

            # Write image directly
            fig.write_image(
                self.file_path,
                format=self.file_type,
                engine='kaleido',
                scale=2
            )

            self.progress.emit("Cleaning up...")
            # Force cleanup
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
            self.is_running = False
