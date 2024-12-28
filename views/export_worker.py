from PyQt6.QtCore import QThread, pyqtSignal
import pandas as pd
import matplotlib.pyplot as plt


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
