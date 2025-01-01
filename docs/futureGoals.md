# UPDATED_GOALS.md

## 1. Project Overview

Transcript ClusterViz is a Python-based tool that analyzes and visualizes conversational timelines from subtitle files (e.g., `.srt`). The primary focus is to **group short subtitle segments into meaningful clusters based on time gaps**, then **generate simple, interactive visualizations** (timelines or bubble charts).

## 2. Key Goals

1. **Parsing & Preprocessing**
   - Use the `srt` Python library to parse `.srt` files.
   - Clean up extraneous tags (like `[Music]`, `[Laughter]`, etc.) and optionally normalize text.

2. **Time-Based Clustering**
   - Implement a **configurable time gap** (default 5 seconds) to decide when a new cluster begins.
   - **Snap** cluster boundaries to the nearest subtitle end to avoid mid-segment splits.
   - Store metadata (start time, end time, duration, concatenated text, etc.) for each cluster.

3. **Visualization**
   - Employ **Plotly** to generate interactive timelines or bubble charts.
   - On the timeline: display clusters along a single time axis.
   - Include hover-over text showing each cluster’s content or summary.

4. **Data Output & Organization**
   - Export cluster data to **JSON** (for programmatic use) and **CSV** (for quick manual review).
   - Keep it lightweight to facilitate easy iteration.

5. **Scalability & Extensibility**
   - Ensure the architecture supports large transcripts without prohibitive runtime.
   - Plan for future ML-based enhancements (topic analysis, speaker diarization, sentiment clustering).

## 3. Future Enhancements (Post-Prototype)

- **Semantic Clustering**: Add NLP or ML-driven clustering logic to refine large clusters based on topic or sentiment.
- **Speaker Diarization**: Integrate audio-based methods to differentiate speakers and handle overlaps.
- **Advanced Summaries**: Generate short summaries for each cluster using summarization models (e.g., T5, BART).
- **Web-Based Interaction**: Extend the tool with frameworks like Dash for a more robust user interface.
