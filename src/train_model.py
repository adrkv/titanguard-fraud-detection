import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score
import os

# Configuration
DATA_PATH = "data/training_dataset.parquet"
MODEL_NAME = "TitanGuardFraudModel"
# CHANGED: Incremented to v3 to bypass the "UNIQUE constraint" DB error
EXPERIMENT_NAME = "fraud_detection_v3"

# 1. Setup MLflow Tracking
mlflow.set_tracking_uri("http://localhost:5001")

# 2. Setup Artifact Location
local_mlruns_path = os.path.abspath("mlruns")
artifact_uri = f"file://{local_mlruns_path}"

# --- ROBUST EXPERIMENT SETUP ---
try:
    # Try to fetch existing experiment
    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    
    if experiment:
        print(f"ℹ️  Using existing experiment '{EXPERIMENT_NAME}' (ID: {experiment.experiment_id})")
        experiment_id = experiment.experiment_id
    else:
        # If not found, create it with the CORRECT local path
        print(f"🆕 Creating new experiment '{EXPERIMENT_NAME}'...")
        print(f"📂 Artifact Location: {artifact_uri}")
        experiment_id = mlflow.create_experiment(
            EXPERIMENT_NAME, 
            artifact_location=artifact_uri
        )
        
    # Set it as active
    mlflow.set_experiment(experiment_id=experiment_id)
    
except Exception as e:
    print(f"⚠️  Experiment setup warning: {e}")
    print("➡️  Falling back to default experiment...")
    # Just proceed without a specific experiment if all else fails
    
# 4. Load Data
print("🧠 Loading data...")
if not os.path.exists(DATA_PATH):
    print("❌ Data not found! Run generate_dataset.py first.")
    exit()

df = pd.read_parquet(DATA_PATH)

features = ["txn_count_1h", "avg_spend_1h", "distance_from_home", "txn_hour"]
X = df[features]
y = df['is_fraud']

# 5. Train
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"💪 Training Isolation Forest on {len(X_train)} records...")
model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
model.fit(X_train)

# 6. Evaluate
print("📊 Validating model...")
preds = model.predict(X_test)
binary_preds = [1 if x == -1 else 0 for x in preds]

precision = precision_score(y_test, binary_preds, zero_division=0)
recall = recall_score(y_test, binary_preds, zero_division=0)
f1 = f1_score(y_test, binary_preds, zero_division=0)

print(f"   Precision: {precision:.2f} | Recall: {recall:.2f} | F1: {f1:.2f}")

# 7. Log
print("📝 Logging model to MLflow...")
with mlflow.start_run() as run:
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        registered_model_name=MODEL_NAME
    )
    mlflow.log_metric("precision", precision)
    mlflow.log_metric("recall", recall)
    mlflow.log_metric("f1_score", f1)

print(f"✅ Success! Model registered as '{MODEL_NAME}'.")