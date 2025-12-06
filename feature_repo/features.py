from datetime import timedelta
from feast import Entity, Field, FeatureView, PushSource, FileSource
from feast.data_format import ParquetFormat  # <--- FIXED IMPORT PATH
from feast.types import Int64, Float32

# 1. Define a "Dummy" Batch Source
batch_source = FileSource(
    file_format=ParquetFormat(),
    path="data/transactions.parquet",
    timestamp_field="timestamp",
    created_timestamp_column="created_timestamp",
)

# 2. The Entity (User)
user = Entity(name="user_id", join_keys=["user_id"])

# 3. The Source (Stream)
source = PushSource(
    name="transactions_stream",
    batch_source=batch_source,
)

# 4. The Features
stats_view = FeatureView(
    name="user_stats",
    entities=[user],
    ttl=timedelta(days=1),
    schema=[
        Field(name="txn_count_1h", dtype=Int64),
        Field(name="avg_spend_1h", dtype=Float32),
    ],
    online=True,
    source=source,
)