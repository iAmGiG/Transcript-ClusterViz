# CURRENT_PIPELINE.md

## 1. Parsing & Ingest

1. **Input**: `.srt` file containing subtitle segments.
2. **Tool**: `srt` Python library.
3. **Output Data**:
   - Start Time (datetime or seconds)
   - End Time
   - Text

## 2. Cleanup & Filtering

1. **Noise Removal**: Strip or transform markers like `[Music]`, `[Laughter]`, or foreign-language tags.
2. **Text Normalization** (optional):
   - Lowercase text.
   - Remove extraneous punctuation or bracketed text.

## 3. Time-Based Clustering

1. **Adjustable Gap**:
   - Compare the next subtitle’s start time to the current subtitle’s end time.
   - If `time_gap > threshold` (default 5s), start a **new cluster**; otherwise, continue the **current cluster**.
2. **Snap to Nearest End**:
   - Ensure the cluster’s end time is the last included subtitle’s actual end timestamp.
3. **Cluster Metadata**:
   - `cluster_id`
   - `start_time`, `end_time` (snapped)
   - `duration = end_time - start_time`
   - `concatenated_text`
   - `subtitle_count` (number of subtitles in the cluster)

## 4. Data Output

1. **JSON File**:
   - Contains all cluster metadata, enabling programmatic downstream usage.
2. **CSV File**:
   - Summarizes cluster info in a table (one row per cluster).

## 5. Visualization

1. **Plotly Timeline**:
   - **X-axis**: Time (seconds or datetime).
   - **Y-axis**: Single lane or cluster IDs.
   - **Hover Tooltips**: Show cluster text snippet or full text.
2. **Bubble Chart** (optional):
   - **Bubble X**: Midpoint of cluster time.
   - **Bubble Size**: Duration or subtitle count.
   - **Bubble Color**: Differentiates clusters.

## 6. Next Steps & Feedback Loop

1. **Tune Threshold**:
   - Gather feedback on whether the default 5s gap is appropriate.
   - Adjust cluster sizing if certain conversations are merged/split incorrectly.
2. **Prototype Review**:
   - Examine output JSON/CSV and the Plotly visualizations for clarity and performance.
3. **Future Add-Ons**:
   - Integrate ML for sub-clustering (topic/sentiment).
   - Implement speaker diarization and advanced summarizations once the prototype is validated.
