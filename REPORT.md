# BeatBlast: Stream Processing Analysis & Report

**Author:** Tejashwini Saravanan  
**Course:** ISM6362 Big Data and Cloud-Based Tools  
**Date:** July 19, 2025  

[👉 Click here to view the original PDF Report](./BeatBlast%20Analysis%20and%20report.pdf)
---

## 1. Project Objective
The goal of this project was to simulate a real-time event stream for a music platform (BeatBlast) and build a processing pipeline using **Apache Spark Structured Streaming**. The system handles high-velocity JSON data, performs windowed aggregations, and persists results into a partitioned Data Lake for long-term analytics.

---

## 2. Technical Justifications

### Why a 10-minute watermark?
I chose a **10-minute watermark** to provide a realistic buffer for late-arriving data. This ensures the system can account for minor network latencies while still being able to clear old state from memory to maintain high performance.

### Partitioning Strategy: `year/month/day/country`
* **Why these columns?** Analytics teams most frequently filter data by date and geographic region.
* **Why this order?** Partitioning from broadest (Year) to narrowest (Country) allows Spark to perform **partition pruning**, skipping irrelevant folders and drastically reducing I/O costs.

### Structured Streaming vs. DStreams
Structured Streaming was preferred over the older DStream API because it offers:
* **Declarative API:** Easier to write and more optimized.
* **Exactly-once Guarantees:** Ensures no data is lost or duplicated.
* **Event-time handling:** Built-in support for watermarking and late-arriving data.

---

## 3. Real-Time Results & Output

### Popular Songs (5-Minute Tumbling Window)
| Window Start | Window End | songId | play_count |
| :--- | :--- | :--- | :--- |
| 2025-07-18 22:50:00 | 2025-07-18 23:00:00 | song_002 | 13 |
| 2025-07-18 22:50:00 | 2025-07-18 23:00:00 | song_001 | 12 |

### Data Lake Storage Structure
```text
/beatblast_datalake/song_plays/
 └── year=2025/
     └── month=07/
         └── day=18/
             ├── country=CA/
             ├── country=GB/
             ├── country=IN/
             └── country=US/
