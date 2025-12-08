import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import mlflow
import threading
from datetime import datetime
from collections import deque

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000/check"
MLFLOW_URI = "http://localhost:5001"
USERS_TO_MONITOR = [f"user_{i}" for i in range(1, 6)] + ["user_criminal"]

mlflow.set_tracking_uri(MLFLOW_URI)

st.set_page_config(
    page_title="PeakWhale™",
    page_icon="🐋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (Deep Ocean Theme) ---
st.markdown("""
<style>
    /* 1. Main Background */
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    
    /* 2. Sidebar */
    [data-testid="stSidebar"] { background-color: #1E293B; border-right: 1px solid #334155; }
    
    /* 3. Text Colors */
    h1, h2, h3, h4, h5, h6, p, label, div, span { color: #F8FAFC !important; }
    .stMetricLabel { color: #94A3B8 !important; }
    div[data-testid="stMetricValue"] { color: #38BDF8 !important; }
    
    /* 4. Tables */
    .stDataFrame { border: 1px solid #334155; }
    [data-testid="stTable"] { background-color: #1E293B; }
    
    /* 5. Spacing */
    .block-container { padding-top: 2rem; padding-bottom: 5rem; }
    
    /* 6. Hide Header/Footer */
    header[data-testid="stHeader"] { display: none; }
    footer { display: none; }
    
    /* 7. Button Styling */
    div.stButton > button {
        background-color: #38BDF8;
        color: #0F172A;
        font-weight: bold;
        border: none;
        width: 100%;
        padding: 0.6rem;
        border-radius: 5px;
    }
    div.stButton > button:hover {
        background-color: #0EA5E9;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# --- GLOBAL SHARED STATE (Thread-Safe) ---
@st.cache_resource
def get_shared_state():
    return {
        "buffer": deque(maxlen=10000), 
        "model_version": "v1"
    }

# --- HELPER FUNCTIONS ---
def get_mlflow_metrics():
    try:
        client = mlflow.tracking.MlflowClient()
        versions = client.get_latest_versions("TitanGuardFraudModel", stages=["None"])
        if not versions: return {}, "v1"
        latest = versions[0]
        run = client.get_run(latest.run_id)
        return run.data.metrics, latest.version
    except: return {}, "Unknown"

def generate_explanation(data):
    f = data['live_features']
    r = []
    if f['avg_spend'] > 200: r.append(f"High Spend (${f['avg_spend']:.0f})")
    if f['txn_count'] > 20: r.append(f"High Velocity ({f['txn_count']}/hr)")
    if f['distance'] > 500: r.append(f"Location ({f['distance']:.0f}km)")
    if f['hour'] < 5: r.append(f"Time ({f['hour']} AM)")
    return " + ".join(r) if r else "Normal Pattern"

# --- BACKGROUND WORKER ---
def background_data_fetcher(shared_state):
    while True:
        try:
            for uid in USERS_TO_MONITOR:
                try:
                    dist, hr = (2500.0, 3) if uid == "user_criminal" else (5.0, 14)
                    payload = {"user_id": uid, "distance_from_home": dist, "txn_hour": hr}
                    res = requests.post(API_URL, json=payload, timeout=0.1)
                    
                    if res.status_code == 200:
                        d = res.json()
                        ver = d.get("model_version", "1")
                        shared_state["model_version"] = ver
                        
                        if d['live_features']['avg_spend'] > 0:
                            status = "BLOCKED" if d["status"] == "BLOCKED" else "APPROVED"
                            shared_state["buffer"].append({
                                "Timestamp": pd.Timestamp.now(),
                                "User": d["user_id"],
                                "Amount": d['live_features']['avg_spend'],
                                "Status": status,
                                "Risk Factors": generate_explanation(d),
                                "Model": ver,
                                "Distance": dist,
                                "Hour": hr
                            })
                except:
                    pass
        except Exception:
            pass
        time.sleep(1)

if "thread_started" not in st.session_state:
    state = get_shared_state()
    t = threading.Thread(target=background_data_fetcher, args=(state,), daemon=True)
    t.start()
    st.session_state.thread_started = True

# --- UI STATE ---
if "inspect_mode" not in st.session_state:
    st.session_state.inspect_mode = False
if "snapshot_df" not in st.session_state:
    st.session_state.snapshot_df = pd.DataFrame()
if "snapshot_time" not in st.session_state:
    st.session_state.snapshot_time = ""

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("PeakWhale™ 🐋")
    st.caption("Enterprise Fraud Defense")
    st.markdown("---")
    
    metrics, ver = get_mlflow_metrics()
    c1, c2 = st.columns(2)
    c1.metric("Precision", f"{float(metrics.get('precision', 0)):.2f}")
    c2.metric("Recall", f"{float(metrics.get('recall', 0)):.2f}")
    st.metric("F1 Score", f"{float(metrics.get('f1_score', 0)):.2f}")
    
    global_state = get_shared_state()
    st.caption(f"Model: v{global_state['model_version']}")

# --- 3. MAIN DASHBOARD ---
st.markdown("### Live Dashboard")
st.caption("AI analyses spend amount, transaction velocity, location distance, and time of day to approve or block transactions.")

# --- THE GHOST KILLER: MASTER CONTAINER ---
dashboard_placeholder = st.empty()

with dashboard_placeholder.container():
    # A. FETCH DATA
    global_state = get_shared_state()
    live_df = pd.DataFrame(list(global_state["buffer"]))

    # B. CALCULATE AND SHOW KPIS ONLY IF DATA EXISTS
    if not live_df.empty:
        total_scanned = len(live_df)
        threats_blocked = len(live_df[live_df["Status"] == "BLOCKED"])
        capital_preserved = live_df[live_df["Status"] == "BLOCKED"]['Amount'].sum()

        # C. LIVE KPIS (Dulls when Inspect Mode is active)
        opacity = 0.3 if st.session_state.inspect_mode else 1.0
        st.markdown(f'<div style="opacity: {opacity}; transition: opacity 0.3s;">', unsafe_allow_html=True)
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Scanned", f"{total_scanned:,}")
        k2.metric("Threats Blocked", f"{threats_blocked:,}")
        k3.metric("Capital Preserved", f"${capital_preserved:,.2f}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

        # D. DYNAMIC VIEW SWITCHER
        if st.session_state.inspect_mode:
            # === INSPECT VIEW ===
            
            # 1. Controls
            if st.button("Go Back"):
                st.session_state.inspect_mode = False
                st.session_state.snapshot_df = pd.DataFrame()
                st.rerun()

            # 2. Data
            display_df = st.session_state.snapshot_df
            st.markdown(f"**Snapshot taken at:** {st.session_state.snapshot_time}")
            
            # 3. Chart
            fig = px.scatter(
                display_df, 
                x="Timestamp", y="Amount", color="Status",
                color_discrete_map={"BLOCKED": "#EF4444", "APPROVED": "#38BDF8"},
                height=400, hover_data=["User", "Risk Factors"],
                template="plotly_dark", title="Anomaly Detection Log"
            )
            fig.update_layout(
                plot_bgcolor="#0F172A", paper_bgcolor="#0F172A", font=dict(color="#F8FAFC"),
                xaxis=dict(rangeslider=dict(visible=True), type="date")
            )
            st.plotly_chart(fig, use_container_width=True)

            # 4. Table
            st.markdown("#### Transaction Log")
            sorted_df = display_df.sort_values("Timestamp", ascending=False).reset_index(drop=True)
            
            event = st.dataframe(
                sorted_df, use_container_width=True, hide_index=True,
                column_order=("Timestamp", "User", "Status", "Amount", "Risk Factors"),
                column_config={
                    "Timestamp": st.column_config.DatetimeColumn(format="H:mm:ss"),
                    "Amount": st.column_config.NumberColumn(format="$%.2f"),
                    "Status": st.column_config.TextColumn(width="small"),
                },
                selection_mode="single-row", on_select="rerun", height=300
            )

            # 5. Details
            if event.selection.rows:
                index = event.selection.rows[0]
                selected_row = sorted_df.iloc[index]
                with st.container():
                    st.markdown("---")
                    st.subheader("Transaction Details")
                    c1, c2, c3 = st.columns(3)
                    c1.info(f"**User:** {selected_row['User']}")
                    if selected_row['Status'] == "BLOCKED":
                        c2.error(f"**Risk:** {selected_row['Risk Factors']}") 
                    else:
                        c2.success(f"**Risk:** {selected_row['Risk Factors']}")
                    c3.metric("Amount", f"${selected_row['Amount']:.2f}")

        else:
            # === LIVE VIEW ===
            # The button is fully visible here
            if st.button("View Transaction Logs"):
                st.session_state.inspect_mode = True
                st.session_state.snapshot_df = live_df.copy()
                st.session_state.snapshot_time = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
                st.rerun()
    else:
        # If no data yet, show NOTHING (Blank Screen below Header)
        pass

# --- 4. REFRESH LOOP ---
if not st.session_state.inspect_mode:
    time.sleep(1)
    st.rerun()