# transcript_clusterviz/controllers/parse_controller.py

import pandas as pd
from core.parse_srt import SRTParser
import plotly.express as px
import plotly.io as pio

pio.templates.default = "plotly_dark"


class ParseController:
    def __init__(self, gap_threshold=5.0, bin_size=60):
        """
        :param gap_threshold: Float in seconds for time-based clustering
        :param bin_size: Number of seconds per bin (e.g., 60s = 1 minute)
        """
        self.parser = SRTParser()
        self.gap_threshold = gap_threshold
        self.bin_size = bin_size
        self.current_df = None

    def parse_srt_file(self, filepath: str) -> pd.DataFrame:
        """
        Parse the SRT file into a DataFrame and store it internally.
        """
        self.current_df = self.parser.parse_file(filepath)
        return self.current_df

    def cluster_by_time(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Perform time-based clustering on the DataFrame, assigning cluster IDs.
        """
        if df is None:
            df = self.current_df
        if df is None or df.empty:
            raise ValueError("No subtitle data available for clustering.")

        df = df.sort_values("start_seconds").reset_index(drop=True)
        df["prev_end"] = df["end_seconds"].shift(1)
        df["prev_end"].fillna(df["start_seconds"], inplace=True)
        df["gap"] = df["start_seconds"] - df["prev_end"]

        cluster_id = 0
        cluster_ids = []
        for i, row in df.iterrows():
            if i == 0:
                cluster_ids.append(cluster_id)
                continue
            if row["gap"] > self.gap_threshold:
                cluster_id += 1
            cluster_ids.append(cluster_id)

        df["cluster_id"] = cluster_ids
        df.drop(columns=["prev_end", "gap"], inplace=True)

        print("DEBUG: Clustering completed. Cluster IDs assigned.")
        # Debug print
        print(df[["start_seconds", "end_seconds", "cluster_id"]].head())

        return df

    def calculate_density(self, df: pd.DataFrame = None):
        """
        Groups subtitles by time bins (in seconds) and computes total word_count per bin.
        Returns a DataFrame with columns ['time_bin', 'words_per_bin'].
        """
        if df is None:
            df = self.current_df
        if df is None or df.empty:
            raise ValueError(
                "No subtitle data available for density calculation.")

        print("DEBUG: Starting density calculation")  # Debug print
        print(f"DEBUG: DataFrame shape: {df.shape}")  # Debug print

        # Binning logic: integer division of start_seconds by bin_size
        df["bin_index"] = (df["start_seconds"] // self.bin_size).astype(int)
        grouped = df.groupby("bin_index")["word_count"].sum().reset_index()
        grouped.rename(columns={"word_count": "words_per_bin"}, inplace=True)

        # Debug print
        print(f"DEBUG: Density calculation result shape: {grouped.shape}")
        print("DEBUG: First few rows of density data:")  # Debug print
        print(grouped.head())  # Debug print

        return grouped

    def plot_density_chart(self, density_df: pd.DataFrame):
        """
        Creates a Plotly figure for words-per-bin vs. time_bin, with cluster visualization.
        """
        # Convert bin_index to minutes for better readability
        density_df['time_minutes'] = density_df['bin_index'] * \
            (self.bin_size / 60)

        # Add cluster information
        if self.current_df is not None and "cluster_id" in self.current_df.columns:
            # Map clusters to density data for coloring
            density_df = pd.merge(
                density_df,
                self.current_df[["bin_index", "cluster_id"]].drop_duplicates(),
                on="bin_index",
                how="left"
            )
            color_discrete_map = {
                cluster_id: f"rgba({50 + cluster_id * 20 % 255}, {80 + cluster_id * 30 % 255}, {120 + cluster_id * 40 % 255}, 0.8)"
                for cluster_id in density_df["cluster_id"].unique() if pd.notnull(cluster_id)
            }
        else:
            color_discrete_map = {}

        # Create figure
        fig = px.bar(
            density_df,
            x='time_minutes',
            y='words_per_bin',
            color='cluster_id',
            color_discrete_map=color_discrete_map,
            text='words_per_bin',  # Adds text to bars
            labels={
                'time_minutes': 'Time (minutes)',
                'words_per_bin': 'Words per Minute',
                'cluster_id': 'Cluster ID'
            },
            title='Word Density Over Time with Clustering'
        )

        # Update layout
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(15,15,15,1)',
            paper_bgcolor='rgba(15,15,15,1)',
            font=dict(color='white'),
            title_font_color='white',
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )

        # Update axes
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            color='white'
        )
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            color='white'
        )

        return fig.to_html(
            full_html=False,
            include_plotlyjs='cdn',
            config={
                'responsive': True,
                'displayModeBar': False
            }
        )
