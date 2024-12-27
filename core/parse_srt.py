# transcript_clusterviz/core/parse_srt.py

import srt
from datetime import timedelta


class SRTParser:
    """
    A class responsible for parsing .srt files into a structured format.
    """

    def __init__(self, placeholders=None):
        """
        :param placeholders: Optional list of placeholder strings to remove from subtitle text.
        """
        if placeholders is None:
            placeholders = ["[Music]", "[Laughter]", "[Applause]", "foreign"]
        self.placeholders = placeholders

    def clean_subtitle_text(self, text: str) -> str:
        """
        Remove unwanted placeholders or tags from subtitle text.
        """
        for ph in self.placeholders:
            text = text.replace(ph, "")
        # Basic whitespace cleanup
        return text.strip()

    def parse_file(self, filepath: str):
        """
        Parses an .srt file and returns a list of dictionaries.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            srt_data = f.read()

        subtitles = list(srt.parse(srt_data))
        parsed_results = []

        for index, sub in enumerate(subtitles, start=1):
            cleaned_text = self.clean_subtitle_text(sub.content)
            parsed_results.append({
                "index": index,
                "start_seconds": sub.start.total_seconds(),
                "end_seconds": sub.end.total_seconds(),
                "text": cleaned_text
            })

        return parsed_results
