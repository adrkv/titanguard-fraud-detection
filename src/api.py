from fastapi import FastAPI
from pydantic import BaseModel
from feast import FeatureStore

app = FastAPI()

# Connect to our existing Feature Store
store = FeatureStore(repo_path="feature_repo")

class Transaction(BaseModel):
    user_id: str

@app.post("/check")
def check_fraud(txn: Transaction):
    # 1. Ask Feast/Redis for stats
    # Note: We request them using the "Full Name" (View:Feature)
    features = store.get_online_features(
        features=[
            "user_stats:txn_count_1h", 
            "user_stats:avg_spend_1h"
        ],
        entity_rows=[{"user_id": txn.user_id}]
    ).to_dict()
    
    # --- THE FIX: Use Short Names for Lookup ---
    # Feast 0.33 returns the keys without the view prefix
    
    # 1. Get Count (Look for 'txn_count_1h', not 'user_stats:txn_count_1h')
    count_list = features.get("txn_count_1h", [0])
    if count_list is None or len(count_list) == 0 or count_list[0] is None:
        txn_count = 0
    else:
        txn_count = count_list[0]

    # 2. Get Spend (Look for 'avg_spend_1h')
    spend_list = features.get("avg_spend_1h", [0.0])
    if spend_list is None or len(spend_list) == 0 or spend_list[0] is None:
        avg_spend = 0.0
    else:
        avg_spend = spend_list[0]
    
    # 3. The Logic
    is_fraud = avg_spend > 500
    
    return {
        "user_id": txn.user_id,
        "status": "BLOCKED" if is_fraud else "APPROVED", 
        "reason": "High spending detected" if is_fraud else "Normal behavior",
        "live_features": {
            "txn_count_1h": txn_count,
            "avg_spend_1h": avg_spend
        }
    }