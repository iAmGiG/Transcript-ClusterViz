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
        Creates a Plotly figure for words-per-bin vs. time_bin, returning an HTML string.
        """
        # Convert bin_index to minutes for better readability
        density_df['time_minutes'] = density_df['bin_index'] * \
            (self.bin_size / 60)

        # Create figure
        fig = px.bar(
            density_df,
            x='time_minutes',
            y='words_per_bin',
            labels={
                'time_minutes': 'Time (minutes)',
                'words_per_bin': 'Words per Minute'
            },
            title='Word Density Over Time'
        )

        # Update layout with dark theme
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(15,15,15,1)',  # Darker background
            paper_bgcolor='rgba(15,15,15,1)',  # Darker background
            font=dict(color='white'),  # White text
            title_font_color='white',  # White title
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )

        # Update axes
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            color='white'  # Axis labels in white
        )
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            color='white'  # Axis labels in white
        )

        # Update bar colors
        fig.update_traces(marker_color='rgb(99,110,250)')  # A nice blue color

        return fig.to_html(
            full_html=False,
            include_plotlyjs='cdn',
            config={
                'responsive': True,
                'displayModeBar': False  # Hide the modebar
            }
        )

    def handle_density(self):
        """
        Calculate and plot the words-per-bin chart in the embedded QWebEngineView.
        """
        if self.parse_controller.current_df is None:
            self.text_display.append(
                "No data to plot. Please load an SRT file first.")
            return

        print("DEBUG: Starting density chart handling")  # Debug print

        try:
            # Calculate density
            density_df = self.parse_controller.calculate_density()
            print("DEBUG: Density calculation completed")  # Debug print

            # Create Plotly figure HTML
            chart_html = self.parse_controller.plot_density_chart(density_df)
            print("DEBUG: Chart HTML generated")  # Debug print

            # Load the HTML into the QWebEngineView
            self.web_view.setHtml(chart_html)
            print("DEBUG: HTML set to QWebEngineView")  # Debug print

            self.text_display.append("\n--- Density Chart Updated ---\n")
        except Exception as e:
            print(f"DEBUG: Error occurred: {str(e)}")  # Debug print
            self.text_display.append(
                f"\nError creating density chart: {str(e)}\n")
