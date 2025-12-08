import pandas as pd
import mlflow.pyfunc
from fastapi import FastAPI
from pydantic import BaseModel
from feast import FeatureStore
import time

# Config
MLFLOW_URI = "http://localhost:5001"
MODEL_NAME = "TitanGuardFraudModel"

app = FastAPI()
store = FeatureStore(repo_path="feature_repo")
mlflow.set_tracking_uri(MLFLOW_URI)

# Global Model State
current_model = None
current_version = "0"
last_check_time = 0

def get_latest_model():
    global current_model, current_version, last_check_time
    if time.time() - last_check_time < 10: return current_model, current_version

    client = mlflow.tracking.MlflowClient()
    try:
        latest = client.get_latest_versions(MODEL_NAME, stages=["None"])[0]
        if latest.version != current_version:
            print(f"🚀 Upgrading to v{latest.version}...")
            model_uri = f"models:/{MODEL_NAME}/{latest.version}"
            current_model = mlflow.pyfunc.load_model(model_uri)
            current_version = latest.version
        last_check_time = time.time()
    except: 
        if current_model is None:
             try: current_model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}/1")
             except: pass
    return current_model, current_version

# --- UPDATE: Accept 4 Features ---
class Transaction(BaseModel):
    user_id: str
    distance_from_home: float
    txn_hour: int

@app.post("/check")
def check_fraud(txn: Transaction):
    model, version = get_latest_model()
    
    # 1. Get History from Feast (Spend / Count)
    features = store.get_online_features(
        features=["user_stats:txn_count_1h", "user_stats:avg_spend_1h"],
        entity_rows=[{"user_id": txn.user_id}]
    ).to_dict()
    
    txn_count = features.get("txn_count_1h", [0])[0] or 0
    avg_spend = features.get("avg_spend_1h", [0.0])[0] or 0.0

    # 2. Combine with Live Context
    input_df = pd.DataFrame({
        "txn_count_1h": [txn_count],
        "avg_spend_1h": [avg_spend],
        "distance_from_home": [txn.distance_from_home],
        "txn_hour": [txn.txn_hour]
    })
    
    # 3. Predict
    prediction = 1
    if model:
        prediction = model.predict(input_df)[0]
    
    is_fraud = prediction == -1
    
    return {
        "user_id": txn.user_id,
        "status": "BLOCKED" if is_fraud else "APPROVED", 
        "reason": "AI Context Anomaly" if is_fraud else "Normal",
        "model_version": version,
        "live_features": {
            "txn_count": txn_count,
            "avg_spend": avg_spend,
            "distance": txn.distance_from_home,
            "hour": txn.txn_hour
        }
    }