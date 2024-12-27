# transcript_clusterviz/controllers/parse_controller.py

import pandas as pd
from core.parse_srt import SRTParser
import plotly.express as px


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

        # Binning logic: integer division of start_seconds by bin_size
        df["bin_index"] = (df["start_seconds"] // self.bin_size).astype(int)
        grouped = df.groupby("bin_index")["word_count"].sum().reset_index()
        grouped.rename(columns={"word_count": "words_per_bin"}, inplace=True)
        return grouped

    def plot_density_chart(self, density_df: pd.DataFrame):
        """
        Creates a Plotly figure for words-per-bin vs. time_bin, returning an HTML string.
        """
        fig = px.bar(
            density_df,
            x="bin_index",
            y="words_per_bin",
            labels={"bin_index": "Time Bin", "words_per_bin": "Total Words"},
            title="Words Per Time Bin"
        )
        # Convert figure to HTML for embedding
        return fig.to_html(full_html=False)
