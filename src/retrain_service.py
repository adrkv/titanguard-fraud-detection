import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score
import time
import os

# Config
DATA_PATH = "data/training_dataset.parquet"
MLFLOW_URI = "http://localhost:5001"
MODEL_NAME = "TitanGuardFraudModel"
# CHANGED: Must match the training script
EXPERIMENT_NAME = "fraud_detection_v3"

# Force Absolute Path for Artifacts
local_mlruns_path = os.path.abspath("mlruns")
artifact_uri = f"file://{local_mlruns_path}"

mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment(EXPERIMENT_NAME)

print("🤖 Retraining Service Active...")

while True:
    print("\n--- ⏳ Starting Retraining Cycle ---")
    
    try:
        df = pd.read_parquet(DATA_PATH)
    except:
        print("Waiting for data...")
        time.sleep(10)
        continue

    # 1. Simulate new data arrival
    new_normal = pd.DataFrame({
        "txn_count_1h": np.random.randint(1, 5, size=190),
        "avg_spend_1h": np.random.uniform(10, 100, size=190),
        "distance_from_home": np.random.uniform(1, 50, size=190),
        "txn_hour": np.random.randint(8, 22, size=190),
        "is_fraud": 0,
        "timestamp": pd.Timestamp.now()
    })
    
    new_anomalies = pd.DataFrame({
        "txn_count_1h": np.random.randint(40, 60, size=10),
        "avg_spend_1h": np.random.uniform(200, 450, size=10),
        "distance_from_home": np.random.uniform(2000, 8000, size=10),
        "txn_hour": np.random.randint(2, 4, size=10),
        "is_fraud": 1,
        "timestamp": pd.Timestamp.now()
    })
    
    df = pd.concat([df, new_normal, new_anomalies])
    if len(df) > 20000: df = df.tail(20000)
    df.to_parquet(DATA_PATH)
    
    # 2. Train/Test Split
    features = ["txn_count_1h", "avg_spend_1h", "distance_from_home", "txn_hour"]
    X = df[features]
    y = df['is_fraud']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=int(time.time()))
    
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=int(time.time()))
    model.fit(X_train)
    
    # 3. Evaluate
    preds = model.predict(X_test)
    binary_preds = [1 if x == -1 else 0 for x in preds]
    
    precision = precision_score(y_test, binary_preds, zero_division=0)
    recall = recall_score(y_test, binary_preds, zero_division=0)
    f1 = f1_score(y_test, binary_preds, zero_division=0)
    
    print(f"   📊 Precision: {precision:.2f} | Recall: {recall:.2f} | F1: {f1:.2f}")

    # 4. Log
    with mlflow.start_run() as run:
        mlflow.sklearn.log_model(model, "model", registered_model_name=MODEL_NAME)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1_score", f1)
    
    print("✅ Model Updated. Sleeping...")
    time.sleep(60)