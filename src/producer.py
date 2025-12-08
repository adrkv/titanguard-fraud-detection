import json
import time
import random
import pandas as pd
from kafka import KafkaProducer
from feast import FeatureStore

producer = KafkaProducer(
    bootstrap_servers='localhost:19092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
store = FeatureStore(repo_path="feature_repo")

print("🚀 Starting PeakWhale Traffic Stream...")
print("Context: 🟢 Normal (Day/Local) | 🔴 Criminal (Night/International)")

while True:
    is_criminal = random.random() < 0.2

    if is_criminal:
        # 😈 The Sophisticated Criminal
        # High Frequency, "Medium" Spend, but Suspicious Context
        user_id = "user_criminal"
        fake_count = random.randint(40, 60)
        fake_avg_spend = round(random.uniform(200, 450), 2)
        
        # Context Anomalies
        distance_from_home = round(random.uniform(2000, 8000), 2) # International
        txn_hour = random.randint(2, 4)             # 3 AM
        
        log_icon = "🔴 CRIMINAL"
    else:
        # 🟢 Normal User
        user_id = f"user_{random.randint(1, 5)}"
        fake_count = random.randint(1, 5)
        fake_avg_spend = round(random.uniform(10, 100), 2)
        
        distance_from_home = round(random.uniform(1, 50), 2) # Local
        txn_hour = random.randint(8, 22) # Daytime
        
        log_icon = "🟢 Normal  "

    # Feast stores History (Count/Spend)
    event_data = {
        "user_id": [user_id],
        "txn_count_1h": [fake_count],
        "avg_spend_1h": [fake_avg_spend],
        "timestamp": [pd.Timestamp.utcnow()],
        "created_timestamp": [pd.Timestamp.utcnow()]
    }
    
    # Redpanda sends Context (Distance/Hour)
    payload = {
        "user_id": user_id, 
        "amount": fake_avg_spend,
        "distance_km": distance_from_home,
        "hour": txn_hour
    }
    producer.send('transactions', payload)
    
    store.push("transactions_stream", pd.DataFrame(event_data))
    
    print(f"{log_icon} | {user_id}: ${fake_avg_spend} @ {txn_hour}:00 ({distance_from_home}km away)")
    
    time.sleep(1.0)