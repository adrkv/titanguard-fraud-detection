import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# Configuration
NUM_ROWS = 10000
FRAUD_RATE = 0.05  # 5% of data will be anomalies
OUTPUT_PATH = "data/training_dataset.parquet"

print(f"🚀 Generating {NUM_ROWS} transactions (Sophisticated 4-Feature Mode)...")

# 1. Generate Normal Transactions (95%)
# Pattern: Local, Daytime, Low Spend
n_normal = int(NUM_ROWS * (1 - FRAUD_RATE))
normal_data = pd.DataFrame({
    "txn_count_1h": np.random.randint(1, 5, size=n_normal),
    "avg_spend_1h": np.random.uniform(10, 100, size=n_normal),
    "distance_from_home": np.random.uniform(0.5, 20, size=n_normal), # < 20km
    "txn_hour": np.random.randint(8, 22, size=n_normal),             # 8am - 10pm
    "is_fraud": 0
})

# 2. Generate Sophisticated Fraud (5%)
# Pattern: International, Nighttime, High Frequency, "Medium" Spend
n_fraud = NUM_ROWS - n_normal
fraud_data = pd.DataFrame({
    "txn_count_1h": np.random.randint(40, 60, size=n_fraud),
    "avg_spend_1h": np.random.uniform(200, 450, size=n_fraud),       # Harder to catch!
    "distance_from_home": np.random.uniform(2000, 8000, size=n_fraud), # International
    "txn_hour": np.random.randint(2, 4, size=n_fraud),               # 2am - 4am
    "is_fraud": 1
})

# 3. Combine and Shuffle
df = pd.concat([normal_data, fraud_data]).sample(frac=1).reset_index(drop=True)
df["timestamp"] = [datetime.utcnow() - timedelta(minutes=x) for x in range(NUM_ROWS)]

# 4. Save
os.makedirs("data", exist_ok=True)
df.to_parquet(OUTPUT_PATH)

print(f"✅ Success! Saved {len(df)} records to {OUTPUT_PATH}")
print(df.head())