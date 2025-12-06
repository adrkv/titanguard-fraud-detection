# TitanGuard: Real-Time Fraud Detection Pipeline 🛡️

TitanGuard is an end-to-end MLOps pipeline designed to detect fraudulent credit card transactions in real-time. 

Built with a modern streaming architecture, it processes live transaction events, manages features using a Feature Store, and serves decisions via a low-latency API.

> **Current Status:** This project currently implements the **Data Engineering & Infrastructure layer** using deterministic logic (Rules-Based). The integration of a Machine Learning model (XGBoost/Isolation Forest) is the next phase on the roadmap.

## 🏗️ Architecture

The system mimics a production-grade event-driven architecture, optimized for Apple Silicon (M1/M2/M3) hardware.

```mermaid
graph LR
    A["Producer Script"] -- "Stream Events" --> B["Redpanda (Kafka)"]
    A -- "Push Features" --> C["Feast Feature Store"]
    C -- "Store Stats" --> D[("Redis")]
    E["Client / Web"] -- "POST Request" --> F["FastAPI Server"]
    F -- "Fetch Features < 5ms" --> C
    F -- "Return Verdict" --> E