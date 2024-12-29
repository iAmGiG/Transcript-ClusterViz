import os
from PyQt6.QtCore import QThread, pyqtSignal
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px


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

    def __init__(self, density_df, gap_threshold, file_path, file_type, current_df=None):
        super().__init__()
        self.density_df = density_df
        self.gap_threshold = gap_threshold
        self.file_path = file_path
        self.file_type = file_type
        self.current_df = current_df  # Add current_df to access cluster information

    def run(self):
        try:
            if not self.file_path:
                raise ValueError("No file path provided for export.")

            # Add cluster information if available
            if self.current_df is not None and "cluster_id" in self.current_df.columns:
                self.density_df = pd.merge(
                    self.density_df,
                    self.current_df[["bin_index", "cluster_id"]
                                    ].drop_duplicates(),
                    on="bin_index",
                    how="left"
                )
                color_discrete_map = {
                    cluster_id: f"rgba({50 + cluster_id * 20 % 255}, {80 + cluster_id * 30 % 255}, {120 + cluster_id * 40 % 255}, 0.8)"
                    for cluster_id in self.density_df["cluster_id"].unique() if pd.notnull(cluster_id)
                }
            else:
                color_discrete_map = {}

            # Create figure with full styling
            fig = px.bar(
                self.density_df,
                x="time_minutes",
                y="words_per_bin",
                color="cluster_id" if "cluster_id" in self.density_df.columns else None,
                color_discrete_map=color_discrete_map,
                text="words_per_bin",
                labels={
                    "time_minutes": "Time (minutes)",
                    "words_per_bin": "Words per Minute",
                    "cluster_id": "Cluster ID"
                },
                title=f"Word Density Over Time (Gap Threshold: {self.gap_threshold}s)"
            )

            # Update layout
            fig.update_layout(
                template="plotly_dark",
                plot_bgcolor="rgba(15,15,15,1)",
                paper_bgcolor="rgba(15,15,15,1)",
                font=dict(color="white"),
                title_font_color="white",
                height=600,
                margin=dict(t=50, b=50, l=50, r=50)
            )

            # Update axes
            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                color="white"
            )
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                color="white"
            )

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

            # Export with explicit format and scale
            fig.write_image(
                self.file_path,
                format=self.file_type,
                scale=2,  # Higher resolution
                engine="kaleido"  # Explicitly specify the rendering engine
            )

            self.finished.emit(f"Export successful: {self.file_path}")

        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            print(f"DEBUG: {error_msg}")  # Debug print
            self.finished.emit(error_msg)
