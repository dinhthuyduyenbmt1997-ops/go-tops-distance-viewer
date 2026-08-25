from pathlib import Path
import time
import requests
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

APP_DIR = Path(__file__).resolve().parent
MASTER_PATH = APP_DIR / "data" / "our_store_master_go_tops.csv"
OSRM_ROUTE_BASE = "https://router.project-osrm.org/route/v1/driving"
HEADERS = {
    "User-Agent": "GO-TOPS-Distance-Viewer/1.0 (internal store distance viewer)"
}

st.set_page_config(
    page_title="GO! + TOPS Distance Viewer",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1180px;}
div[data-testid="stMetricValue"] {font-size: 2.05rem;}
.viewer-note {
    padding: .8rem 1rem; border-radius: .6rem;
    background: rgba(120,120,120,.08); margin-top:.35rem;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_master():
    df = pd.read_csv(MASTER_PATH)
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df = df[df["Latitude"].notna() & df["Longitude"].notna()].copy()
    df["StoreID"] = pd.to_numeric(df["StoreID"], errors="coerce").astype("Int64")
    df["Label"] = df.apply(
        lambda r: f"{r['Brand']} | {r['Store']} | ID {int(r['StoreID'])}",
        axis=1,
    )
    return df.reset_index(drop=True)


@st.cache_data(ttl=60 * 60 * 24 * 7, show_spinner=False)
def route_between(lat1, lon1, lat2, lon2):
    coords = f"{float(lon1):.7f},{float(lat1):.7f};{float(lon2):.7f},{float(lat2):.7f}"
    url = f"{OSRM_ROUTE_BASE}/{coords}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
        "alternatives": "true",
    }

    last_error = None
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=45)
            if r.status_code in {429, 502, 503, 504}:
                last_error = RuntimeError(f"Routing server HTTP {r.status_code}")
                time.sleep(1.2 + attempt)
                continue
            r.raise_for_status()
            data = r.json()
            routes = data.get("routes") or []
            if not routes:
                return None

            # Use shortest distance among alternatives returned by OSRM.
            best = min(routes, key=lambda x: float(x.get("distance", 10**18)))
            return {
                "distance_km": float(best["distance"]) / 1000.0,
                "duration_min": float(best["duration"]) / 60.0,
                "geometry": (best.get("geometry") or {}).get("coordinates") or [],
                "alternatives": len(routes),
            }
        except Exception as exc:
            last_error = exc
            time.sleep(1.0 + attempt)

    raise RuntimeError(str(last_error) if last_error else "Không lấy được tuyến đường.")


def route_map(origin, destination, route):
    m = folium.Map(
        location=[
            (float(origin["Latitude"]) + float(destination["Latitude"])) / 2,
            (float(origin["Longitude"]) + float(destination["Longitude"])) / 2,
        ],
        zoom_start=12,
        control_scale=True,
    )

    folium.Marker(
        [float(origin["Latitude"]), float(origin["Longitude"])],
        tooltip=f"Điểm đi: {origin['Store']}",
        popup=f"<b>{origin['Brand']} — {origin['Store']}</b><br>StoreID {int(origin['StoreID'])}",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(m)

    folium.Marker(
        [float(destination["Latitude"]), float(destination["Longitude"])],
        tooltip=f"Điểm đến: {destination['Store']}",
        popup=f"<b>{destination['Brand']} — {destination['Store']}</b><br>StoreID {int(destination['StoreID'])}",
        icon=folium.Icon(color="red", icon="stop"),
    ).add_to(m)

    coords = route.get("geometry") or []
    if coords:
        latlon = [(lat, lon) for lon, lat in coords]
        folium.PolyLine(
            latlon,
            weight=6,
            opacity=0.85,
            tooltip=f"{route['distance_km']:.1f} km",
        ).add_to(m)
        bounds = [
            [min(x[0] for x in latlon), min(x[1] for x in latlon)],
            [max(x[0] for x in latlon), max(x[1] for x in latlon)],
        ]
        m.fit_bounds(bounds, padding=(35, 35))

    return m


master = load_master()

st.title("Tra khoảng cách GO! + TOPS")
st.caption(
    "Chọn 2 store bất kỳ trong master. Không cần upload file hay nhập địa chỉ."
)

c1, c2 = st.columns(2)

labels = master["Label"].tolist()
default_origin = next(
    (i for i, x in enumerate(labels) if "GO! Truong Chinh" in x or "GO! Trường Chinh" in x),
    0,
)
default_destination = next(
    (i for i, x in enumerate(labels) if "Tops Au Co" in x or "TOPS Au Co" in x or "Tops Âu Cơ" in x),
    1 if len(labels) > 1 else 0,
)

with c1:
    origin_label = st.selectbox(
        "Điểm đi",
        labels,
        index=default_origin,
        key="origin",
    )

with c2:
    destination_label = st.selectbox(
        "Điểm đến",
        labels,
        index=default_destination,
        key="destination",
    )

origin = master.loc[master["Label"] == origin_label].iloc[0]
destination = master.loc[master["Label"] == destination_label].iloc[0]

if origin_label == destination_label:
    st.info("Điểm đi và điểm đến đang là cùng một store.")
else:
    try:
        with st.spinner("Đang tính tuyến đường lái xe..."):
            route = route_between(
                origin["Latitude"], origin["Longitude"],
                destination["Latitude"], destination["Longitude"],
            )

        if not route:
            st.warning("Không tìm được tuyến đường lái xe giữa hai store này.")
        else:
            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("Quãng đường lái xe", f"{route['distance_km']:.1f} km")
            m2.metric("Thời gian ước tính", f"{route['duration_min']:.0f} phút")
            m3.metric("Store master", "GO! + TOPS")

            st.markdown(
                f"""
                <div class="viewer-note">
                <b>{origin['Store']}</b> → <b>{destination['Store']}</b><br>
                {origin['Province']} → {destination['Province']}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st_folium(
                route_map(origin, destination, route),
                height=560,
                use_container_width=True,
                key=f"route_{int(origin['StoreID'])}_{int(destination['StoreID'])}",
            )

            st.caption(
                "Khoảng cách/thời gian dùng OSRM + OpenStreetMap. "
                "Số liệu có thể khác Google Maps do dữ liệu đường và thuật toán routing khác nhau."
            )
    except Exception as exc:
        st.error(
            "Không kết nối được dịch vụ routing công cộng lúc này. "
            f"Chi tiết: {exc}"
        )

with st.expander("Danh sách store trong master"):
    st.dataframe(
        master[["StoreID", "Brand", "Store", "Province", "Ward / Commune"]],
        use_container_width=True,
        hide_index=True,
    )
