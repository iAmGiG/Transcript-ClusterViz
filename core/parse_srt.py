# transcript_clusterviz/core/parse_srt.py

import srt
import pandas as pd


class SRTParser:
    """
    A class responsible for parsing .srt files into a Pandas DataFrame.
    """

    def __init__(self, placeholders=None):
        if placeholders is None:
            placeholders = ["[Music]", "[Laughter]", "[Applause]", "foreign"]
        self.placeholders = placeholders

    def clean_subtitle_text(self, text: str) -> str:
        for ph in self.placeholders:
            text = text.replace(ph, "")
        return text.strip()

    def parse_file(self, filepath: str) -> pd.DataFrame:
        """
        Parses an .srt file into a Pandas DataFrame with columns:
        ['index', 'start_seconds', 'end_seconds', 'text', 'word_count'].
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            srt_data = f.read()

        subtitles = list(srt.parse(srt_data))
        records = []

        for idx, sub in enumerate(subtitles, start=1):
            cleaned_text = self.clean_subtitle_text(sub.content)
            word_count = len(cleaned_text.split()) if cleaned_text else 0

            records.append({
                "index": idx,
                "start_seconds": sub.start.total_seconds(),
                "end_seconds": sub.end.total_seconds(),
                "text": cleaned_text,
                "word_count": word_count
            })

        df = pd.DataFrame(records)
        return df
