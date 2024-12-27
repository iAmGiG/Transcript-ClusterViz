# Transcript ClusterViz

Transcript ClusterViz is a Python-based tool for analyzing and visualizing conversational timelines extracted from subtitle files. The tool clusters short subtitle segments into meaningful groups and generates intuitive visualizations such as interactive timelines and bubble charts.

## **Pipeline Overview**

### **1. Input Stage**

- **Supported Formats:**
  - `.srt` (initial support)
  - `.vtt`, `.sbv`, and plain `.txt` (planned future support).
- **Input Requirements:**
  - Subtitles or transcripts with timestamped segments.
  - Designed for subtitle structures where each line typically represents 3-4 seconds of spoken content.

### **2. Parsing and Preprocessing**

- **Subtitle Parsing:**
  - Use the `srt` library to extract text, start times, and end times from `.srt` files.
- **Preprocessing:**
  - Normalize text (e.g., lowercase, punctuation cleanup).
  - Remove non-verbal annotations if necessary (e.g., [laughs], [music]).

### **3. Clustering Logic**

- **Time-Based Clustering:**
  - Group segments based on gaps between timestamps.
  - Configurable time threshold (default: 5 seconds).
- **Semantic Clustering (Future Feature):**
  - Use NLP techniques to combine segments with similar topics or themes.
  - Leverage tools like `spaCy` or `KeyBERT` for keyword extraction and similarity analysis.

### **4. Data Organization**

- **Cluster Data Structure:**
  - Store clustered segments with metadata:
    - Start time, end time, combined duration.
    - Text content of all segments in the cluster.
  - Format output for easy integration into visualizations.
- **Output Formats:**
  - JSON: For programmatic access and further processing.
  - CSV: For manual review and archival purposes.

### **5. Visualization**

- **Timeline and Bubble Charts:**
  - **X-Axis:** Time (in seconds or minutes).
  - **Y-Axis:** Cluster index or group identifier.
  - **Bubble Size:** Duration of the cluster or number of merged segments.
- **Interactivity:**
  - Hover over a bubble to view combined text for the cluster.
  - Option to zoom into specific time ranges.

### **6. Extensibility**

- **Modular Design:**
  - Parsing, clustering, and visualization components are independent.
  - Can easily integrate additional file formats or new clustering algorithms.
- **Future Enhancements:**
  - Speaker diarization for separating speakers.
  - Summarization tools for generating concise overviews of clustered content.

## **Project Goals**

- Simplify the process of analyzing and visualizing transcript data.
- Provide intuitive tools for identifying key conversational events in long-form content.
- Build a flexible framework that supports future extensions like diarization and advanced text analysis.

## **Contributing**

Contributions are welcome! For ideas, bug reports, or feature requests, please open an issue or submit a pull request. Planned enhancements include:

- Support for additional file formats (.vtt, .sbv).
- Improved clustering using text similarity and topic modeling.
- Integration with speaker diarization frameworks.

## **License**

This project is licensed under the MIT License.
