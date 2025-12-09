# PeakWhale™ Orca | Enterprise Fraud Defense Platform

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Live%20Dashboard-red)
![MLflow](https://img.shields.io/badge/MLflow-Model%20Tracking-orange)
![Feast](https://img.shields.io/badge/Feast-Feature%20Store-green)
![Kafka](https://img.shields.io/badge/Redpanda-Event%20Streaming-black)

**PeakWhale™** Orca is a high-velocity, event-driven fraud defense engine engineered to detect and block anomalies with sub-50ms latency. By leveraging an unsupervised Isolation Forest model within a distributed streaming architecture, the system achieves 96% precision in identifying complex transaction vectors, executing blocking decisions in real-time before settlement occurs..

## 🚀 Key Features

* **Real-Time Ingestion**: Utilizing **Redpanda (Kafka)** and **Feast** to ingest and process transaction streams with sub-second latency.
* **Unsupervised AI**: Powered by an **Isolation Forest** model that detects anomalies without needing pre-labeled fraud data.
* **Deep Ocean UI**: A custom-engineered, dark-mode **Streamlit** dashboard optimized for Security Operations Centers (SOC).
* **Auto-Retraining Pipeline**: A background service that continuously retrains the model on new data, logs performance to **MLflow**, and hot-swaps the model in the API without downtime.
* **Snapshot Inspection**: "Freeze-frame" functionality allows analysts to inspect specific time windows without losing data continuity.

## 🧠 AI Logic

The model analyzes **Spend Amount**, **Transaction Velocity**, **Location Distance**, and **Time of Day** to instantly approve or block transactions.

## 🛠️ Architecture

```mermaid
graph LR
    A[Producer] -->|JSON Stream| B(Redpanda/Kafka)
    B -->|Stream| C(Feast Feature Store)
    B -->|Context| D(FastAPI Model Server)
    C -->|Historical Stats| D
    D -->|Prediction| E[Dashboard]
    F[Retraining Service] -->|New Model| G(MLflow Registry)
    G -->|Load Model| D
