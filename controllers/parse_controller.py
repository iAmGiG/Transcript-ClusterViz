# transcript_clusterviz/controllers/parse_controller.py

from core.parse_srt import SRTParser


class ParseController:
    def __init__(self):
        self.parser = SRTParser()

    def parse_srt_file(self, filepath: str):
        """
        Delegates to the SRTParser and returns the parsed results.
        """
        return self.parser.parse_file(filepath)
