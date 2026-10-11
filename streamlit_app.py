import datetime as dt
import math
import os

import requests
import streamlit as st

# FastAPI endpoint (start it first with `python app.py`)
API_URL = os.getenv("ETA_API_URL", "http://127.0.0.1:8000/predict")

# illustrative routes: restaurant lat, lon, delivery lat, lon
SAMPLES = {
    "Mumbai": (19.1136, 72.8697, 19.1176, 72.9047),
    "Bengaluru": (12.9716, 77.5946, 12.9352, 77.6245),
    "Pune": (18.5204, 73.8567, 18.5590, 73.7868),
    "Delhi": (28.6139, 77.2090, 28.5355, 77.2100),
    "Hyderabad": (17.4401, 78.3489, 17.4326, 78.4071),
}
ROUTE_KEYS = ["r_lat", "r_lon", "d_lat", "d_lon"]

st.set_page_config(page_title="ETA Predictor", layout="wide")


# ---------- helpers ----------
def haversine_km(lat1, lon1, lat2, lon2):
    """Same formula as the backend: absolute coordinates, earth radius 6371 km."""
    lat1, lon1, lat2, lon2 = (math.radians(abs(v)) for v in (lat1, lon1, lat2, lon2))
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def distance_band(km):
    # same bins the backend uses to create "distance_type"
    for limit, name in ((5, "short"), (10, "medium"), (15, "long"), (25, "very long")):
        if km < limit:
            return name
    return None


def minutes_of(t: dt.time) -> int:
    return t.hour * 60 + t.minute


def apply_sample():
    choice = st.session_state["sample"]
    if choice in SAMPLES:
        for key, value in zip(ROUTE_KEYS, SAMPLES[choice]):
            st.session_state[key] = value


# ---------- defaults (set once per session) ----------
if "order_date" not in st.session_state:
    now = dt.datetime.now()
    order_min = max(now.hour * 60 + now.minute, 60)  # 00:00-00:59 orders cannot be scored
    st.session_state["order_date"] = now.date()
    st.session_state["order_time"] = dt.time(order_min // 60, order_min % 60)
    st.session_state["pickup_time"] = dt.time((order_min + 10) // 60 % 24, (order_min + 10) % 60)
    for key, value in zip(ROUTE_KEYS, SAMPLES["Mumbai"]):
        st.session_state[key] = value
    st.session_state["sample"] = "Mumbai"

st.title("ETA Predictor")
st.caption("Estimate food delivery time from the order, the rider and the route.")

form_col, result_col = st.columns([2, 1], gap="large")

with form_col:
    st.subheader("Order")
    c1, c2, c3 = st.columns(3)
    order_date = c1.date_input("Order date", key="order_date")
    order_time = c2.time_input("Order placed at", key="order_time", step=60)
    pickup_time = c3.time_input("Picked up at", key="pickup_time", step=60)
    prep_min = (minutes_of(pickup_time) - minutes_of(order_time)) % 1440
    c3.caption(f"{prep_min} min after the order was placed")

    c1, c2, c3, c4 = st.columns(4)
    type_of_order = c1.selectbox("Type of order", ["Snack", "Meal", "Drinks", "Buffet"], index=1)
    weather = c2.selectbox("Weather", ["Sunny", "Cloudy", "Fog", "Windy", "Stormy", "Sandstorms"])
    traffic = c3.selectbox("Road traffic", ["Low", "Medium", "High", "Jam"], index=1)
    # "Metropolitian" is the spelling used in the dataset the model was trained on
    city = c4.selectbox("City type", ["Metropolitian", "Urban", "Semi-Urban"], index=1,
                        format_func=lambda v: "Metropolitan" if v == "Metropolitian" else v)
    festival = st.radio("Festival day", ["No", "Yes"], horizontal=True)

    st.subheader("Rider")
    c1, c2, c3, c4, c5 = st.columns(5)
    age = c1.number_input("Age", min_value=18, max_value=70, value=30, step=1)
    rating = c2.number_input("Rating (1-5)", min_value=1.0, max_value=5.0, value=4.6, step=0.1)
    vehicle = c3.selectbox("Vehicle", ["motorcycle", "scooter", "electric_scooter", "bicycle"],
                           format_func=lambda v: v.replace("_", " ").capitalize())
    vehicle_condition = c4.selectbox("Vehicle condition (0-3)", [0, 1, 2, 3], index=2)
    multiple = c5.selectbox("Multiple deliveries (0-3)", [0, 1, 2, 3], index=1,
                            help="Orders carried on the same trip")

    st.subheader("Route")
    st.selectbox("Sample route", ["Custom", *SAMPLES], key="sample", on_change=apply_sample)
    c1, c2, c3, c4 = st.columns(4)
    r_lat = c1.number_input("Restaurant latitude", key="r_lat", format="%.4f", step=0.001)
    r_lon = c2.number_input("Restaurant longitude", key="r_lon", format="%.4f", step=0.001)
    d_lat = c3.number_input("Delivery latitude", key="d_lat", format="%.4f", step=0.001)
    d_lon = c4.number_input("Delivery longitude", key="d_lon", format="%.4f", step=0.001)

    km = haversine_km(r_lat, r_lon, d_lat, d_lon)
    band = distance_band(km)
    if band:
        st.info(f"Straight-line distance: **{km:.1f} km** ({band})")
    else:
        st.warning(f"Straight-line distance: {km:.1f} km. The model only supports routes under 25 km.")

    predict = st.button("Predict delivery time", type="primary")


def validate():
    errors = []
    if minutes_of(order_time) < 60:
        errors.append("Orders placed between 00:00 and 00:59 are not supported.")
    if prep_min > 120:
        errors.append("Pickup is more than 2 hours after the order. Check the times.")
    for label, value, limit in (("Restaurant latitude", r_lat, 90), ("Restaurant longitude", r_lon, 180),
                                ("Delivery latitude", d_lat, 90), ("Delivery longitude", d_lon, 180)):
        if abs(value) < 1 or abs(value) > limit:
            errors.append(f"{label} must be between 1 and {limit}.")
    if not errors and km >= 25:
        errors.append("The route must be under 25 km.")
    return errors


def build_payload():
    return {
        "ID": f"st-{dt.datetime.now().timestamp():.0f}",
        "Delivery_person_ID": "WEBRES00DEL00",  # only used to derive a city name the model drops
        "Delivery_person_Age": str(int(age)),
        "Delivery_person_Ratings": str(round(rating, 1)),
        "Restaurant_latitude": r_lat,
        "Restaurant_longitude": r_lon,
        "Delivery_location_latitude": d_lat,
        "Delivery_location_longitude": d_lon,
        "Order_Date": order_date.strftime("%d-%m-%Y"),
        "Time_Orderd": order_time.strftime("%H:%M:00"),
        "Time_Order_picked": pickup_time.strftime("%H:%M:00"),
        "Weatherconditions": f"conditions {weather}",
        "Road_traffic_density": traffic,
        "Vehicle_condition": int(vehicle_condition),
        "Type_of_order": type_of_order,
        "Type_of_vehicle": vehicle,
        "multiple_deliveries": str(multiple),
        "Festival": festival,
        "City": city,
    }


def error_text(response):
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        return "; ".join(f"{e['loc'][-1]}: {e['msg']}" for e in detail)
    return f"The server returned status {response.status_code}."


with result_col:
    st.subheader("Estimated delivery time")
    if not predict:
        st.write("Fill in the details and press **Predict delivery time**.")
    else:
        problems = validate()
        if problems:
            for problem in problems:
                st.error(problem)
        else:
            try:
                with st.spinner("Predicting..."):
                    response = requests.post(API_URL, json=build_payload(), timeout=30)
                    st.write("API status:", response.status_code)
                    st.write("API response:", response.text)
            except requests.RequestException:
                st.error(f"Could not reach the API at {API_URL}. Start it with `python app.py` and try again.")
            else:
                # result = response.json() if response.ok else None
                # if not response.ok:
                #     st.error(error_text(response))
                # elif not isinstance(result, (int, float)):
                #     st.error("The server returned an unexpected response.")
                # else:
                #     st.metric("Predicted delivery time", f"{result:.1f} min")
                
                if not response.ok:
                    st.error(error_text(response))
                else:
                    try:
                        data = response.json()
                        result = data["prediction"] if isinstance(data, dict) else data
                        result = float(result)

                        st.metric(
                            label="Predicted delivery time",
                            value=f"{result:.1f} minutes"
                        )

                        st.success("Delivery time predicted successfully!")

                        st.table({
                            "Detail": [
                                "Estimated delivery time",
                                "Distance",
                                "Pickup after order",
                                "Weather",
                                "Road traffic",
                                "Vehicle"
                            ],
                            "Value": [
                                f"{result:.1f} minutes",
                                f"{km:.1f} km",
                                f"{prep_min} minutes",
                                weather,
                                traffic,
                                vehicle.replace("_", " ").capitalize()
                            ]
                        })

                    except (ValueError, TypeError, KeyError):
                        st.error("The API returned an invalid prediction format.")

                    st.table({
                        "Distance": f"{km:.1f} km",
                        "Pickup after order": f"{prep_min} min",
                        "Weather / traffic": f"{weather} / {traffic}",
                        "Vehicle": vehicle.replace("_", " ").capitalize(),
                    })