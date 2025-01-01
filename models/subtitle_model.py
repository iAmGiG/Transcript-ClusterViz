# transcript_clusterviz/models/subtitle_model.py
from dataclasses import dataclass


@dataclass
class SubtitleSegment:
    index: int
    start_seconds: float
    end_seconds: float
    text: str
