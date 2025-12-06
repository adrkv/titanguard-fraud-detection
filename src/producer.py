import json
import time
import random
import pandas as pd
from kafka import KafkaProducer
from feast import FeatureStore

# 1. Connect to Redpanda
producer = KafkaProducer(
    bootstrap_servers='localhost:19092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# 2. Connect to Feast
store = FeatureStore(repo_path="feature_repo")

print("🚀 Starting Hybrid Traffic Stream (UTC Mode)...")
print("green = Good User | red = Criminal")

while True:
    # --- PROBABILITY LOGIC ---
    # Generate a random number between 0 and 1
    # If it's less than 0.2 (20%), be a criminal. Otherwise, be normal.
    is_criminal = random.random() < 0.2

    if is_criminal:
        # 😈 The Bad Guy
        user_id = "user_criminal"
        fake_count = random.randint(30, 60)
        fake_avg_spend = round(random.uniform(501, 2000), 2) # Always above $500
        log_icon = "🔴 CRIMINAL"
    else:
        # 🟢 The Good Guys (User 1 to 5)
        user_id = f"user_{random.randint(1, 5)}"
        fake_count = random.randint(1, 10)
        fake_avg_spend = round(random.uniform(5, 450), 2) # Always below $500
        log_icon = "🟢 Normal  "

    # Create the payload (Using UTC as required)
    event_data = {
        "user_id": [user_id],
        "txn_count_1h": [fake_count],
        "avg_spend_1h": [fake_avg_spend],
        "timestamp": [pd.Timestamp.utcnow()],
        "created_timestamp": [pd.Timestamp.utcnow()]
    }
    
    # 3. Send to Redpanda
    producer.send('transactions', {"user_id": user_id, "amount": fake_avg_spend})
    
    # 4. Push to Feast
    try:
        store.push("transactions_stream", pd.DataFrame(event_data))
        print(f"{log_icon} | {user_id}: Count={fake_count}, Spend=${fake_avg_spend}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Run a bit slower so you can read the logs (1 second delay)
    time.sleep(1.0)