import streamlit as st
import pydeck as pdk
import firebase_admin
from firebase_admin import credentials, db
import time

# -----------------------------
# FIREBASE CONFIG
# -----------------------------
firebase_url = "YOUR_REALTIME_DB_URL"

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceKey.json")
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

dustbin_ref = db.reference("dustbins")

# -----------------------------
# UI DESIGN
# -----------------------------
st.set_page_config(page_title="BINOVA", page_icon="🗑️", layout="wide")

st.markdown("""
<style>
body { background: linear-gradient(135deg, #6EE7B7, #3B82F6); }
.title { font-size: 42px; color: white; text-align: center; font-weight: bold; }
.subtitle { font-size: 20px; color: #E0F2FE; text-align: center; }
.bin-card {
    background: white; padding: 18px; border-radius: 16px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.2); margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">BINOVA – Smart Dustbin Worker App</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Live Monitoring • Map View • Cleaning Updates</div>', unsafe_allow_html=True)

# -----------------------------
# FETCH DUSTBIN DATA
# -----------------------------
def get_dustbins():
    data = dustbin_ref.get()
    if data: return data
    return {}

def mark_cleaned(bin_id):
    dustbin_ref.child(bin_id).update({
        "fill_level": 0,
        "status": "cleaned",
        "alert": False
    })

# -----------------------------
# LIVE MAP
# -----------------------------
st.header("🌍 Live Map of All Dustbins")

bins = get_dustbins()
map_data = []

for bin_id, bin_data in bins.items():
    # Color logic
    if bin_data["fill_level"] >= 80:
        color = [255, 0, 0]      # full
    elif bin_data["fill_level"] >= 50:
        color = [255, 165, 0]    # mid
    else:
        color = [0, 255, 0]      # normal

    map_data.append({
        "name": bin_id,
        "lat": bin_data["latitude"],
        "lon": bin_data["longitude"],
        "color": color,
    })

layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_data,
    get_position='[lon, lat]',
    get_color='color',
    get_radius=40,
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=list(bins.values())[0]["latitude"] if bins else 12.97,
    longitude=list(bins.values())[0]["longitude"] if bins else 77.59,
    zoom=12,
)

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"text": "Dustbin: {name}"}
))

# -----------------------------
# BIN STATUS + ACTIONS
# -----------------------------
st.header("🗑️ Dustbin Status & Actions")

for bin_id, bin_data in bins.items():
    st.markdown('<div class="bin-card">', unsafe_allow_html=True)

    st.subheader(f"📌 {bin_id}")
    st.write(f"Location: **({bin_data['latitude']}, {bin_data['longitude']})**")
    st.write(f"Fill Level: **{bin_data['fill_level']}%**")
    st.write(f"Status: **{bin_data['status']}**")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button(f"✔ Mark {bin_id} Cleaned"):
            mark_cleaned(bin_id)
            st.success(f"{bin_id} marked cleaned!")
            time.sleep(1)
            st.rerun()

    with col2:
        if bin_data["fill_level"] >= 80:
            st.error("⚠ FULL – Clean ASAP!")
        elif bin_data["fill_level"] >= 50:
            st.warning("⛔ Filling up")
        else:
            st.success("🟢 Normal")

    st.markdown('</div>', unsafe_allow_html=True)

st.info("🔄 Auto-refresh every 60 seconds.")
