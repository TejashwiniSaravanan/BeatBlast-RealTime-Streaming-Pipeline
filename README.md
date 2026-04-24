# BeatBlast: Real-Time Streaming Pipeline with PySpark

An end-to-end data engineering pipeline that simulates, ingests, processes, and stores real-time user interaction events for a music streaming platform. Built with Apache Spark Structured Streaming, partitioned Parquet storage, and a custom Python event simulator.

---

## Overview

Most data engineering projects in academic settings work with static files. This one doesn't. BeatBlast is designed around a core question: what does it actually take to process streaming data in real time, the way platforms like Spotify or Netflix do it in production?

The answer involves more than just reading a CSV and running aggregations. It requires a live data source, schema enforcement on arrival, event-time windowing to handle late-arriving records, stateful aggregations that update continuously, and a storage layer designed for downstream analytics queries. This project implements all of that - from the Python simulator generating the raw events to the partitioned Parquet data lake at the other end.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| Distributed Computing | Apache Spark 3.x, PySpark |
| Streaming API | Spark Structured Streaming |
| Data Source Format | JSON |
| Storage Format | Snappy-Compressed Parquet |
| Storage Architecture | Partitioned Data Lake |
| Environment | Google Colab |

---

## How the Pipeline Works

### Step 1 - Event simulation

Rather than using a pre-existing static dataset, I wrote a Python simulator (`simulator.py`) that generates a continuous stream of JSON events mimicking real user behavior on a music platform. Each event captures the action type (`songPlay`, `songSkip`, `songLike`, `appOpen`), along with `userId`, `sessionId`, `platform`, `country`, and a high-precision ISO `eventTimestamp`.

This design decision matters. A static file cannot test whether your streaming logic handles late arrivals, out-of-order events, or burst traffic. A live simulator can.

### Step 2 - Schema enforcement on ingestion

The stream is read using `readStream` with a strictly defined schema applied at ingestion time rather than inferred after the fact. On streaming data, schema inference is unreliable - a single malformed event can corrupt the type mapping for the entire stream. Enforcing the schema explicitly means the pipeline fails fast and loud on bad data rather than silently producing wrong results downstream.

```python
event_schema = StructType([
    StructField("eventType", StringType(), True),
    StructField("eventTimestamp", StringType(), True),
    StructField("songId", StringType(), True),
    StructField("userId", StringType(), True),
    StructField("sessionId", StringType(), True),
    StructField("platform", StringType(), True),
    StructField("country", StringType(), True)
])
```

### Step 3 - Timestamp conversion and watermarking

The raw `eventTimestamp` arrives as a string in ISO format. Before any time-based aggregations can run, it is cast to Spark's native `TimestampType`. A 10-minute watermark is then applied to the stream.

The watermark serves a specific purpose: it tells Spark how long to hold state in memory waiting for late-arriving events. Ten minutes was chosen as a realistic buffer for network latency without allowing the state store to grow unbounded. Events arriving more than 10 minutes past the current watermark threshold are dropped - a deliberate trade-off between completeness and memory efficiency.

```python
processed_df = raw_df.withColumn(
    "eventTimestamp", col("eventTimestamp").cast(TimestampType())
).withWatermark("eventTimestamp", "10 minutes")
```

### Step 4 - Windowed aggregations

Two separate aggregations run continuously on the stream.

**Popular songs** use a 5-minute tumbling window to count plays per song within each non-overlapping 5-minute interval. This gives a real-time view of what is trending right now.

```python
popular_songs = (
    song_plays_df
    .withWatermark("eventTimestamp", "10 minutes")
    .groupBy(window("eventTimestamp", "5 minutes"), "songId")
    .count()
)
```

**Active sessions** use a 10-minute sliding window that advances every 5 minutes, counting distinct active sessions by platform. The overlap is intentional - sliding windows smooth out burst effects that tumbling windows can artificially amplify.

The choice between Spark Structured Streaming and the older DStream API was deliberate. Structured Streaming offers a declarative SQL-like API, exactly-once processing guarantees, and native event-time support with watermarking. DStreams process on arrival time, not event time, which means late data silently goes into the wrong window.

### Step 5 - Partitioned Parquet data lake

The `songPlay` event stream is written to a simulated data lake using `writeStream` in append mode, partitioned by `year`, `month`, `day`, and `country`.

```python
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

The partition order is not arbitrary. Analysts and downstream query engines almost always filter first by date range, then by geography. Ordering partitions from broadest (year) to narrowest (country) enables partition pruning - when a query asks for "all plays from the US in July 2025," Spark skips every other partition entirely and reads only the relevant folders. On a dataset with months or years of data, this reduces I/O costs dramatically.

Parquet's columnar storage format compounds this advantage. Analytical queries that only touch a few columns - say, `songId` and `play_count` - read only those columns from disk rather than loading entire rows. Combined with Snappy compression, the storage footprint is roughly 3x smaller than equivalent CSV files.

A checkpoint location is also configured, which allows the streaming query to resume exactly where it left off if it is interrupted, without reprocessing or losing events.

---

## Pipeline Output

**Real-time popular songs aggregation (5-minute tumbling window)**

| Window Start | Window End | songId | play_count |
|---|---|---|---|
| 2025-07-18 22:50:00 | 2025-07-18 23:00:00 | song_002 | 13 |
| 2025-07-18 22:50:00 | 2025-07-18 23:00:00 | song_001 | 12 |

**Data lake storage structure after pipeline run**

```
/beatblast_datalake/song_plays/
 └── year=2025/
     └── month=07/
         └── day=18/
             ├── country=CA/
             ├── country=GB/
             ├── country=IN/
             └── country=US/
```

Each leaf folder contains Parquet files that can be queried independently by any Spark, Presto, or Athena job without touching the rest of the lake.

---

## Repository Structure

```
BeatBlast-RealTime-Streaming-Pipeline/
│
├── BeatBlast_Streaming_Pipeline.ipynb    # Full pipeline implementation
├── simulator.py                          # Python event generator (live data source)
├── requirements.txt                      # Environment dependencies
├── REPORT.md                             # Technical deep-dive and design justifications
├── BeatBlast Analysis and report.pdf     # Full academic report
├── Structured Streaming script.pdf       # Core streaming logic reference
└── README.md
```

---

## Design Decisions and Trade-offs

**Why a custom simulator instead of a static dataset?** Static files cannot reproduce the conditions that make streaming hard - late arrivals, out-of-order events, and variable throughput. A simulator that continuously writes to the landing zone creates the actual conditions the pipeline needs to handle.

**Why a 10-minute watermark?** A shorter watermark reduces memory usage but drops more late events. A longer watermark handles more late data but holds more state in memory. Ten minutes reflects a realistic network latency budget for a consumer streaming platform.

**Why append mode instead of complete or update?** Append mode only writes new rows to the sink, which is correct for immutable event logs like play events. Complete mode rewrites the entire result set on every trigger - fine for small aggregations, unusable at scale. Update mode writes only changed rows but is not supported by all sink types including Parquet.

**Handling data outside the watermark.** Events that arrive after the watermark threshold are dropped from windowed aggregations. In a production environment, these would be captured by a dead-letter queue and reprocessed by a scheduled batch job to backfill the data lake without affecting the real-time stream.

---

## Limitations and What I Would Do Next

Running on a single Google Colab instance demonstrates the logic correctly but does not test horizontal scaling. A proper stress test would run the simulator at 10,000+ events per second across a multi-node Spark cluster to validate watermark and checkpoint behavior under real throughput.

The current pipeline has no schema evolution strategy. If the event structure changes - adding a new field like `deviceType` - the pipeline would need to be restarted and historical data migrated. Apache Avro or schema registry integration would solve this in production.

I would also add a monitoring layer: streaming query metrics exposed to a dashboard showing records processed per second, watermark lag, and state store size. Without visibility into those metrics, a streaming pipeline in production is effectively running blind.

---

## Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Run the event simulator (generates live JSON events)
python simulator.py

# Open and run the notebook
# BeatBlast_Streaming_Pipeline.ipynb
```

---

## Tools

Apache Spark 3.x, PySpark, Spark Structured Streaming, Python, Google Colab, Parquet, Snappy Compression

---

## About Me

**Tejashwini Saravanan** - Master's student in Data Analytics specializing in scalable data pipelines and real-time stream processing.

[LinkedIn](https://www.linkedin.com/in/tejashwinisaravanan/) · [GitHub](https://github.com/TejashwiniSaravanan)

---

*Course: ISM6362 Big Data and Cloud-Based Tools - Seattle Pacific University*
