# BeatBlast: Real-Time Stream Processing & Data Lake Engineering

This project demonstrates a robust, end-to-end **Real-Time Data Engineering** pipeline for **BeatBlast**, a digital music streaming platform. It covers the entire lifecycle of big data—from high-velocity data simulation to stateful stream processing and optimized data lake storage.

---

## 📌 Project Objective
The goal was to build a system capable of processing near real-time user interaction events (playing, skipping, and liking songs) to derive actionable business insights. Using **Apache Spark Structured Streaming**, the pipeline identifies trending content and monitors platform engagement while persisting data in a highly organized, partitioned format.

---

## 🛠️ Tech Stack
* **Language:** Python
* **Distributed Computing:** Apache Spark (PySpark)
* **Streaming API:** Spark Structured Streaming
* **Data Formats:** JSON (Source), Snappy-Compressed Parquet (Sink)
* **Storage Architecture:** Partitioned Data Lake
* **Environment:** Google Colab / Spark Cluster

**[👉 View the Full Technical Report here](./REPORT.md)**

**[👉 View the Full Structured Streaming Script (PDF)](./Structured%20Streaming%20script.pdf)**

---




## 🏗️ Data Pipeline Architecture



### 1. Real-Time Data Simulation (Producer)
A Python-based simulator mimics a live production environment by generating a continuous stream of JSON events.
* **Event Types:** `songPlay`, `songSkip`, `songLike`, and `appOpen`.
* **Metadata:** Captures `userId`, `sessionId`, `platform`, `country`, and high-precision `eventTimestamp`.

### 2. Stream Processing Engine
The PySpark application reads the JSON stream from the landing zone with a strictly enforced schema.
* **Timestamp Conversion:** Transforms string-based ISO timestamps into Spark `TimestampType` for accurate event-time operations.
* **Watermarking:** A **10-minute watermark** is applied to handle late-arriving data while managing system memory efficiently.

### 3. Windowed Aggregations
* **Popular Songs:** Uses a **5-minute tumbling window** to calculate the number of plays per song.
* **Active Sessions:** Employs a **10-minute sliding window** (sliding every 5 minutes) to count distinct active sessions by platform.

---
## 💻 Core Streaming Logic
The pipeline utilizes Spark's `readStream` to ingest JSON events and `writeStream` to persist data in a partitioned Parquet format.

```python
# Core logic from the Structured Streaming script
query = (
    processed_df
    .writeStream
    .format("parquet")
    .option("path", "/content/beatblast_datalake/song_plays")
    .option("checkpointLocation", "/content/checkpoints/song_plays")
    .partitionBy("year", "month", "day", "country")
    .outputMode("append")
    .start()
)

``` 
## 📂 Data Lake Design & Partitioning
To facilitate high-performance analytics, the `songPlay` event stream is written to a simulated Data Lake in **Parquet** format.

**Partitioning Strategy:** `/year/month/day/country/`

* **Optimization:** This hierarchy enables **partition pruning**, ensuring the compute engine (like Spark or Presto) only reads relevant files rather than scanning the entire dataset.
* **Scalability:** Columnar storage (Parquet) provides superior compression and faster read speeds for analytical workloads.

---

## 🧠 Technical Justifications

* **Structured Streaming vs. DStreams:** Structured Streaming was chosen for its declarative API, superior "exactly-once" guarantees, and seamless integration with the Spark SQL engine.
* **Watermarking Logic:** A 10-minute threshold provides a realistic buffer for network latency without allowing the state store to grow indefinitely.
* **Handling Late Data:** For data arriving outside the watermark, the strategy involves using append-only modes combined with scheduled batch-reprocessing jobs to ensure historical data integrity.

---

## 🚀 Key Results & Output

### Real-Time Aggregation Sample (Popular Songs)
| Window Start | Window End | songId | play_count |
| :--- | :--- | :--- | :--- |
| 2025-07-18 22:50:00 | 2025-07-18 23:00:00 | song_002 | 13 |
| 2025-07-18 22:50:00 | 2025-07-18 23:00:00 | song_001 | 12 |

### Storage Structure Result
```text
/beatblast_datalake/song_plays/
 └── year=2025/
     └── month=07/
         └── day=18/
             ├── country=CA/
             ├── country=GB/
             ├── country=IN/
             └── country=US/
```

## 📂 Project Resources

To explore the technical depth of this project, please refer to the following resources:

* **Main Implementation:** [BeatBlast Streaming Pipeline (Notebook)](./BeatBlast_Streaming_Pipeline.ipynb)
* **Data Generation:** [Event Simulator Script (Python)](./simulator.py)
* **Technical Deep-Dive:** [Project Analysis & Report (Markdown)](./REPORT.md)
* **Original Documentation:** [Academic Report (PDF)](./BeatBlast%20Analysis%20and%20report.pdf)
* **Core Script Reference:** [Structured Streaming Logic (PDF)](./Structured%20Streaming%20script.pdf)
* **Environment Setup:** [Requirements File](./requirements.txt)
  

## 👤 Author
Tejashwini Saravanan [LinkedIn](https://www.linkedin.com/in/tejashwinisaravanan/)
