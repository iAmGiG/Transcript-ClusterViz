import pytest
from core.parse_srt import SRTParser

def test_parse_file():
    parser = SRTParser()
    df = parser.parse_file("sampleStream.srt")
    assert not df.empty
    assert 'word_count' in df.columns
