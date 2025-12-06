from feast import FeatureStore
import pandas as pd
from datetime import datetime

# 1. Connect
store = FeatureStore(repo_path="feature_repo")

print("--- 1. Defining Data ---")
# Force the exact data types Feast expects
event_data = pd.DataFrame({
    "user_id": ["user_criminal"],
    "txn_count_1h": [50],
    "avg_spend_1h": [9999.99],
    "timestamp": [pd.Timestamp.utcnow()],
    "created_timestamp": [pd.Timestamp.utcnow()]
})

# Cast to specific types to ensure match
event_data["txn_count_1h"] = event_data["txn_count_1h"].astype("int64")
event_data["avg_spend_1h"] = event_data["avg_spend_1h"].astype("float32")

print(event_data)

print("\n--- 2. Pushing to Online Store ---")
try:
    store.push("transactions_stream", event_data)
    print("✅ Push succeeded.")
except Exception as e:
    print(f"❌ Push failed: {e}")

print("\n--- 3. Reading from Online Store ---")
try:
    features = store.get_online_features(
        features=[
            "user_stats:txn_count_1h", 
            "user_stats:avg_spend_1h"
        ],
        entity_rows=[{"user_id": "user_criminal"}]
    ).to_dict()
    
    print("🔍 Result from Database:")
    print(features)
    
    val = features["user_stats:avg_spend_1h"][0]
    if val is not None and val > 500:
        print("\n🎉 SUCCESS! Data was found and is valid.")
    else:
        print("\n⚠️ FAILURE. Data was NOT found (Result is None or 0).")
        
except Exception as e:
    print(f"❌ Read failed: {e}")