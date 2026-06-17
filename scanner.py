import json
import asyncio
import aiohttp
import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime, timedelta

# --- CONSTANTS ---
GAMMA_URL = "https://gamma-api.polymarket.com/events/slug"
CLOB_URL = "https://clob.polymarket.com"
DEFAULT_CONCURRENCY = 20
STORAGE_FILE = "storage_config.json"  # File lưu trữ dữ liệu trên Server

# Danh sách thành phố tích hợp đầy đủ Lat/Lon để gọi Open-Meteo API
CITIES_DATA = [
    {"key": "seattle", "name": "Seattle", "polymarketCity": "seattle", "marketType": "highest", "status": "active", "lat": 47.6062, "lon": -122.3321},
    {"key": "losangeles", "name": "Los Angeles", "polymarketCity": "los-angeles", "marketType": "highest", "status": "active", "lat": 34.0522, "lon": -118.2437},
    {"key": "sanfrancisco", "name": "San Francisco", "polymarketCity": "san-francisco", "marketType": "highest", "status": "active", "lat": 37.7749, "lon": -122.4194},
    {"key": "denver", "name": "Denver", "polymarketCity": "denver", "marketType": "highest", "status": "active", "lat": 39.7392, "lon": -104.9903},
    {"key": "chicago", "name": "Chicago", "polymarketCity": "chicago", "marketType": "highest", "status": "active", "lat": 41.8781, "lon": -87.6298},
    {"key": "dallas", "name": "Dallas", "polymarketCity": "dallas", "marketType": "highest", "status": "active", "lat": 32.7767, "lon": -96.7970},
    {"key": "austin", "name": "Austin", "polymarketCity": "austin", "marketType": "highest", "status": "active", "lat": 30.2672, "lon": -97.7431},
    {"key": "houston", "name": "Houston", "polymarketCity": "houston", "marketType": "highest", "status": "active", "lat": 29.7604, "lon": -95.3698},
    {"key": "mexicocity", "name": "Mexico City", "polymarketCity": "mexico-city", "marketType": "highest", "status": "active", "lat": 19.4326, "lon": -99.1332},
    {"key": "panamacity", "name": "Panama City", "polymarketCity": "panama-city", "marketType": "highest", "status": "active", "lat": 8.9824, "lon": -79.5199},
    {"key": "miami", "name": "Miami", "polymarketCity": "miami", "marketType": ["highest", "lowest"], "status": "active", "lat": 25.7617, "lon": -80.1918},
    {"key": "atlanta", "name": "Atlanta", "polymarketCity": "atlanta", "marketType": "highest", "status": "active", "lat": 33.7490, "lon": -84.3880},
    {"key": "nyc", "name": "New York", "polymarketCity": "nyc", "marketType": ["highest", "lowest"], "status": "active", "lat": 40.7128, "lon": -74.0060},
    {"key": "toronto", "name": "Toronto", "polymarketCity": "toronto", "marketType": "highest", "status": "active", "lat": 43.6532, "lon": -79.3832},
    {"key": "buenosaires", "name": "Buenos Aires", "polymarketCity": "buenos-aires", "marketType": "highest", "status": "active", "lat": -34.6037, "lon": -58.3816},
    {"key": "saopaulo", "name": "São Paulo", "polymarketCity": "sao-paulo", "marketType": "highest", "status": "active", "lat": -23.5505, "lon": -46.6333},
    {"key": "london", "name": "London", "polymarketCity": "london", "marketType": ["highest", "lowest"], "status": "active", "lat": 51.5074, "lon": -0.1278},
    {"key": "lagos", "name": "Lagos", "polymarketCity": "lagos", "marketType": "highest", "status": "active", "lat": 6.5244, "lon": 3.3792},
    {"key": "amsterdam", "name": "Amsterdam", "polymarketCity": "amsterdam", "marketType": "highest", "status": "active", "lat": 52.3676, "lon": 4.9041},
    {"key": "paris", "name": "Paris", "polymarketCity": "paris", "marketType": ["highest", "lowest"], "status": "active", "lat": 48.8566, "lon": 2.3522},
    {"key": "munich", "name": "Munich", "polymarketCity": "munich", "marketType": "highest", "status": "active", "lat": 48.1351, "lon": 11.5820},
    {"key": "milan", "name": "Milan", "polymarketCity": "milan", "marketType": "highest", "status": "active", "lat": 45.4642, "lon": 9.1900},
    {"key": "madrid", "name": "Madrid", "polymarketCity": "madrid", "marketType": "highest", "status": "active", "lat": 40.4168, "lon": -3.7038},
    {"key": "warsaw", "name": "Warsaw", "polymarketCity": "warsaw", "marketType": "highest", "status": "active", "lat": 52.2297, "lon": 21.0122},
    {"key": "helsinki", "name": "Helsinki", "polymarketCity": "helsinki", "marketType": "highest", "status": "active", "lat": 60.1699, "lon": 24.9384},
    {"key": "capetown", "name": "Cape Town", "polymarketCity": "cape-town", "marketType": "highest", "status": "active", "lat": -33.9249, "lon": 18.4241},
    {"key": "telaviv", "name": "Tel Aviv", "polymarketCity": "tel-aviv", "marketType": "highest", "status": "active", "lat": 32.0853, "lon": 34.7818},
    {"key": "moscow", "name": "Moscow", "polymarketCity": "moscow", "marketType": "highest", "status": "active", "lat": 55.7558, "lon": 37.6173},
    {"key": "istanbul", "name": "Istanbul", "polymarketCity": "istanbul", "marketType": "highest", "status": "active", "lat": 41.0082, "lon": 28.9784},
    {"key": "ankara", "name": "Ankara", "polymarketCity": "ankara", "marketType": "highest", "status": "active", "lat": 39.9334, "lon": 32.8597},
    {"key": "jeddah", "name": "Jeddah", "polymarketCity": "jeddah", "marketType": "highest", "status": "active", "lat": 21.5433, "lon": 39.1728},
    {"key": "karachi", "name": "Karachi", "polymarketCity": "karachi", "marketType": "highest", "status": "active", "lat": 24.8607, "lon": 67.0011},
    {"key": "lucknow", "name": "Lucknow", "polymarketCity": "lucknow", "marketType": "highest", "status": "active", "lat": 26.8467, "lon": 80.9462},
    {"key": "kualalumpur", "name": "Kuala Lumpur", "polymarketCity": "kuala-lumpur", "marketType": "highest", "status": "active", "lat": 3.1390, "lon": 101.6869},
    {"key": "jakarta", "name": "Jakarta", "polymarketCity": "jakarta", "marketType": "highest", "status": "active", "lat": -6.2088, "lon": 106.8456},
    {"key": "singapore", "name": "Singapore", "polymarketCity": "singapore", "marketType": "highest", "status": "active", "lat": 1.3521, "lon": 103.8198},
    {"key": "hongkong", "name": "Hong Kong", "polymarketCity": "hong-kong", "marketType": ["highest", "lowest"], "status": "active", "lat": 22.3193, "lon": 114.1694},
    {"key": "beijing", "name": "Beijing", "polymarketCity": "beijing", "marketType": "highest", "status": "active", "lat": 39.9042, "lon": 116.4074},
    {"key": "chengdu", "name": "Chengdu", "polymarketCity": "chengdu", "marketType": "highest", "status": "active", "lat": 30.5728, "lon": 104.0668},
    {"key": "chongqing", "name": "Chongqing", "polymarketCity": "chongqing", "marketType": "highest", "status": "active", "lat": 29.5630, "lon": 106.5516},
    {"key": "shanghai", "name": "Shanghai", "polymarketCity": "shanghai", "marketType": ["highest", "lowest"], "status": "active", "lat": 31.2304, "lon": 121.4737},
    {"key": "shenzhen", "name": "Shenzhen", "polymarketCity": "shenzhen", "marketType": "highest", "status": "active", "lat": 22.5431, "lon": 114.0579},
    {"key": "taipei", "name": "Taipei", "polymarketCity": "taipei", "marketType": "highest", "status": "active", "lat": 25.0330, "lon": 121.5654},
    {"key": "qingdao", "name": "Qingdao", "polymarketCity": "qingdao", "marketType": "highest", "status": "active", "lat": 36.0671, "lon": 120.3826},
    {"key": "wuhan", "name": "Wuhan", "polymarketCity": "wuhan", "marketType": "highest", "status": "active", "lat": 30.5928, "lon": 114.3055},
    {"key": "guangzhou", "name": "Guangzhou", "polymarketCity": "guangzhou", "marketType": "highest", "status": "active", "lat": 23.1291, "lon": 113.2644},
    {"key": "manila", "name": "Manila", "polymarketCity": "manila", "marketType": "highest", "status": "active", "lat": 14.5995, "lon": 120.9842},
    {"key": "seoul", "name": "Seoul", "polymarketCity": "seoul", "marketType": ["highest", "lowest"], "status": "active", "lat": 37.5665, "lon": 126.9780},
    {"key": "busan", "name": "Busan", "polymarketCity": "busan", "marketType": "highest", "status": "active", "lat": 35.1796, "lon": 129.0756},
    {"key": "tokyo", "name": "Tokyo", "polymarketCity": "tokyo", "marketType": ["highest", "lowest"], "status": "active", "lat": 35.6762, "lon": 139.6503},
    {"key": "wellington", "name": "Wellington", "polymarketCity": "wellington", "marketType": "highest", "status": "active", "lat": -41.2865, "lon": 174.7762}
]

# --- TỰ ĐỘNG GÁN 3 MODEL TỐI ƯU NHẤT THEO KHU VỰC CỦA THÀNH PHỐ ---
for city in CITIES_DATA:
    name = city["name"]
    if name in ["Seattle", "Los Angeles", "San Francisco", "Denver", "Chicago", "Dallas", "Austin", "Houston", "Miami", "Atlanta", "New York", "Mexico City", "Panama City", "Buenos Aires", "São Paulo", "Lagos", "Cape Town"]:
        city["models"] = ["ECMWF", "ICON", "GFS"]
    elif name == "Toronto":
        city["models"] = ["ECMWF", "GEM", "ICON"]
    elif name == "Wellington":
        city["models"] = ["ECMWF", "ACCESS-G", "ICON"]
    else:
        city["models"] = ["ECMWF", "ICON", "UKMO"]

# --- ĐỊNH NGHĨA MÀU SẮC NEON GLOW CHO TỪNG MODEL ---
MODEL_STYLES = {
    "ECMWF": {"color": "#bf5af2", "bg": "#251733", "border": "#bf5af2"},    # Tím
    "ICON": {"color": "#30b0c7", "bg": "#12272e", "border": "#30b0c7"},     # Cyan
    "GFS": {"color": "#ff453a", "bg": "#331311", "border": "#ff453a"},      # Đỏ
    "UKMO": {"color": "#ff375f", "bg": "#33121a", "border": "#ff375f"},     # Hồng đậm
    "GEM": {"color": "#0a84ff", "bg": "#112033", "border": "#0a84ff"},      # Xanh Dương
    "ACCESS-G": {"color": "#30d158", "bg": "#132e18", "border": "#30d158"}  # Xanh Lá
}

DEFAULT_FAVORITE_CITIES = [
    "Tokyo", "Seoul", "Busan", "Singapore", "Shanghai", "Wuhan", "Chengdu", 
    "Chongqing", "Beijing", "Kuala Lumpur", "Taipei", "Manila", 
    "Guangzhou", "Lucknow", "Karachi", "Jeddah", "Tel Aviv", 
    "Amsterdam", "Cape Town", "Munich", "Paris", "Milan", "Warsaw", "Madrid", 
    "London", "Ankara", "Helsinki", "Istanbul", "Moscow", "Wellington"
]

MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

DEFAULT_CONFIG = {
    "min_p_yes": 80.0,
    "max_p_yes": 99.5,
    "min_p_no": 90.0,
    "max_p_no": 99.5,
    "filter_yes": False,
    "filter_no": True,
    "gap_filter_enabled": True,
    "gap_value": 4,
    "gap_direction": "Both",
    "selected_dates": ["Today", "Tomorrow", "Day After Tomorrow"],
    "selected_cities": DEFAULT_FAVORITE_CITIES,
    "excluded_cities": ["Lagos", "Shenzhen", "Hong Kong", "Jakarta", "Qingdao"],
    "ordered_markets": [],
    "checked_markets": []
}

# --- JSON PERSISTENCE HELPERS ---
def load_stored_data():
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "config": DEFAULT_CONFIG.copy(),
        "ordered_markets": [],
        "checked_markets": []
    }

def save_stored_data():
    data_to_save = {
        "config": st.session_state.current_config,
        "ordered_markets": st.session_state.ordered_markets,
        "checked_markets": st.session_state.checked_markets
    }
    try:
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Lỗi ghi file cấu hình: {e}")

# --- CALLBACK FUNCTIONS ---
def toggle_ordered_status(event_title):
    if event_title in st.session_state.ordered_markets:
        st.session_state.ordered_markets.remove(event_title)
    else:
        st.session_state.ordered_markets.append(event_title)
        if event_title in st.session_state.checked_markets:
            st.session_state.checked_markets.remove(event_title)
    save_stored_data()

def toggle_checked_status(event_title):
    if event_title in st.session_state.checked_markets:
        st.session_state.checked_markets.remove(event_title)
    else:
        st.session_state.checked_markets.append(event_title)
        if event_title in st.session_state.ordered_markets:
            st.session_state.ordered_markets.remove(event_title)
    save_stored_data()

def clear_all_flags():
    st.session_state.ordered_markets = []
    st.session_state.checked_markets = []
    save_stored_data()

# --- HELPER FUNCTIONS ---
def parse_val(title):
    if not title: return None
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", title)
    if not nums: return None
    if len(nums) >= 2:
        return (float(nums[0]) + float(nums[1])) / 2
    return float(nums[0])

def get_target_dates(selected_date_labels):
    dates = []
    now = datetime.now()
    label_map = {"Today": 0, "Tomorrow": 1, "Day After Tomorrow": 2}
    if isinstance(selected_date_labels, str):
        selected_date_labels = ["Today", "Tomorrow", "Day After Tomorrow"] if selected_date_labels == "All Days" else [selected_date_labels]
    for label in selected_date_labels:
        if label in label_map:
            d = now + timedelta(days=label_map[label])
            dates.append({
                "slug": f"{MONTH_NAMES[d.month-1]}-{d.day}-{d.year}",
                "display": d.strftime("%d/%m/%Y")
            })
    return dates

async def fetch_model_temperatures(session, lat, lon, date_display_str, market_type):
    """Gọi Open-Meteo API để lấy dữ liệu dự báo nhiệt độ của các mô hình cốt lõi"""
    try:
        date_obj = datetime.strptime(date_display_str, "%d/%m/%Y")
        date_iso = date_obj.strftime("%Y-%m-%d")
        suffix = "max" if market_type == "highest" else "min"
        
        # Ép Open-Meteo trả về đúng các trường dữ liệu theo từng model bằng cách ghép suffix
        daily_params = [
            f"temperature_2m_{suffix}_ecmwf_ifs",
            f"temperature_2m_{suffix}_gfs_seamless",
            f"temperature_2m_{suffix}_icon_seamless",
            f"temperature_2m_{suffix}_gem_global",
            f"temperature_2m_{suffix}_access_g",
            f"temperature_2m_{suffix}_ukmo_seamless"  # Thêm UKMO cho các thị trường EU/Asia
        ]
        daily_str = ",".join(daily_params)
        
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&daily={daily_str}"
            f"&temperature_unit=fahrenheit"
            f"&start_date={date_iso}&end_date={date_iso}&timezone=auto"
        )
        
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            
        daily_data = data.get("daily", {})
        
        # Trả về mapping chuẩn khớp với cấu hình MODEL_STYLES trên giao diện
        return {
            "ECMWF": daily_data.get(f"temperature_2m_{suffix}_ecmwf_ifs", [None])[0],
            "GFS": daily_data.get(f"temperature_2m_{suffix}_gfs_seamless", [None])[0],
            "ICON": daily_data.get(f"temperature_2m_{suffix}_icon_seamless", [None])[0],
            "GEM": daily_data.get(f"temperature_2m_{suffix}_gem_global", [None])[0],
            "ACCESS-G": daily_data.get(f"temperature_2m_{suffix}_access_g", [None])[0],
            "UKMO": daily_data.get(f"temperature_2m_{suffix}_ukmo_seamless", [None])[0], # Map thêm dòng này
        }
    except Exception:
        return None

async def check_event(session, semaphore, city, date_info, m_type, min_p_yes, max_p_yes, min_p_no, max_p_no, filter_yes, filter_no, gap_filter_enabled, gap_value, gap_direction, matches_list, filtered_cities, error_cities):
    async with semaphore:
        slug = f"{m_type}-temperature-in-{city['polymarketCity']}-on-{date_info['slug']}"
        try:
            async with session.get(f"{GAMMA_URL}/{slug}") as resp:
                if resp.status != 200: 
                    error_cities.append(city["name"])
                    return
                event = await resp.json()
            markets = event.get("markets", [])
            if not markets: 
                error_cities.append(city["name"])
                return
            
            book_reqs = []
            market_map = {}
            for m in markets:
                tokens = json.loads(m.get("clobTokenIds", "[]"))
                if len(tokens) < 2: continue
                yes_id, no_id = tokens[0], tokens[1]
                book_reqs.extend([{"token_id": yes_id}, {"token_id": no_id}])
                market_map[yes_id] = {"m": m, "side": "YES", "other": no_id, "event": event}
                market_map[no_id] = {"m": m, "side": "NO", "other": yes_id, "event": event}
            
            if not book_reqs: 
                error_cities.append(city["name"])
                return
            
            async with session.post(f"{CLOB_URL}/books", json=book_reqs) as books_resp:
                if books_resp.status != 200: 
                    error_cities.append(city["name"])
                    return
                books_data = await books_resp.json()
            
            books = {b["asset_id"]: b for b in books_data}
            sorted_markets = sorted(markets, key=lambda m: parse_val(m.get("groupItemTitle") or m.get("question")) or 0)

            highest_idx = -1
            if gap_filter_enabled:
                max_yes_found = -1.0
                for i, m in enumerate(sorted_markets):
                    tokens = json.loads(m.get("clobTokenIds", "[]"))
                    if len(tokens) < 2: continue
                    y_id = tokens[0]
                    y_book = books.get(y_id, {})
                    y_asks = y_book.get("asks", [])
                    if not y_asks: continue
                    y_p = float(min(y_asks, key=lambda x: float(x["price"]))["price"])
                    if y_p > max_yes_found:
                        max_yes_found = y_p
                        highest_idx = i
            
            event_has_match = False
            temp_matches = []
            for yes_id, info in market_map.items():
                if info["side"] != "YES": continue
                m = info["m"]
                no_id = info["other"]
                evt = info["event"]
                
                yes_book = books.get(yes_id, {})
                no_book = books.get(no_id, {})
                y_asks = yes_book.get("asks", [])
                n_asks = no_book.get("asks", [])
                
                yes_price = float(min(y_asks, key=lambda x: float(x["price"]))["price"]) if y_asks else 1.0
                no_price = float(min(n_asks, key=lambda x: float(x["price"]))["price"]) if n_asks else 1.0
                y_depth = float(min(y_asks, key=lambda x: float(x["price"]))["size"]) if y_asks else 0.0
                n_depth = float(min(n_asks, key=lambda x: float(x["price"]))["size"]) if n_asks else 0.0
                
                spread = (yes_price + no_price) * 100 - 100
                is_match = False
                matched_price = 100.0
                
                if filter_yes and (min_p_yes/100) <= yes_price <= (max_p_yes/100):
                    is_match = True
                    matched_price = min(matched_price, yes_price * 100)
                
                if filter_no and (min_p_no/100) <= no_price <= (max_p_no/100):
                    pass_gap = True
                    if gap_filter_enabled and highest_idx != -1:
                        current_idx = -1
                        for idx, sm in enumerate(sorted_markets):
                            if sm['id'] == m['id']:
                                current_idx = idx
                                break
                        if current_idx != -1:
                            diff = current_idx - highest_idx
                            effective_dir = gap_direction
                            if m_type == "lowest":
                                if gap_direction == "Up": effective_dir = "Down"
                                elif gap_direction == "Down": effective_dir = "Up"
                            
                            if effective_dir == "Both":
                                if abs(diff) <= gap_value: pass_gap = False
                            elif effective_dir == "Up":
                                if diff <= gap_value: pass_gap = False
                            elif effective_dir == "Down":
                                if diff >= -gap_value: pass_gap = False
                    
                    if pass_gap:
                        is_match = True
                        matched_price = min(matched_price, no_price * 100)

                if is_match:
                    event_has_match = True
                    temp_matches.append({
                        "City": city["name"], "Date": date_info["display"], "Type": "Highest" if m_type == "highest" else "Lowest",
                        "Market": m.get("groupItemTitle") or m.get("question"), "YES": yes_price * 100, "NO": no_price * 100,
                        "YES_Depth": y_depth, "NO_Depth": n_depth, "Spread": spread, "MatchedPrice": matched_price,
                        "Link": f"https://polymarket.com/event/{evt['slug']}/{m['slug']}",
                        "EventTitle": f"{m_type.capitalize()} temperature in {city['name']} on {date_info['display']}?"
                    })
            
            if event_has_match:
                weather_data = await fetch_model_temperatures(session, city["lat"], city["lon"], date_info["display"], m_type)
                for item in temp_matches:
                    item["ModelForecasts"] = weather_data
                    matches_list.append(item)
            else:
                filtered_cities.append(city["name"])

        except Exception:
            error_cities.append(city["name"])

async def run_scan(min_p_yes, max_p_yes, min_p_no, max_p_no, filter_yes, filter_no, gap_filter_enabled, gap_value, gap_direction, selected_cities, excluded_cities, selected_dates):
    cities_to_scan = [c for c in CITIES_DATA if c.get("status") == "active"]
    if excluded_cities:
        cities_to_scan = [c for c in cities_to_scan if c["name"] not in excluded_cities]
    if selected_cities:
        cities_to_scan = [c for c in cities_to_scan if c["name"] in selected_cities]
        
    dates = get_target_dates(selected_dates)
    matches_list = []
    filtered_cities = []
    error_cities = []
    semaphore = asyncio.Semaphore(DEFAULT_CONCURRENCY)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for city in cities_to_scan:
            m_types = city.get("marketType")
            if not isinstance(m_types, list): m_types = [m_types]
            for d in dates:
                for mt in m_types:
                    tasks.append(check_event(session, semaphore, city, d, mt, min_p_yes, max_p_yes, min_p_no, max_p_no, filter_yes, filter_no, gap_filter_enabled, gap_value, gap_direction, matches_list, filtered_cities, error_cities))
        await asyncio.gather(*tasks)
    return matches_list, list(set(filtered_cities)), list(set(error_cities))

# --- STREAMLIT UI ---
st.set_page_config(page_title="PolyWeather Market Finder", page_icon="🎯", layout="wide")

if "config_loaded" not in st.session_state:
    stored_data = load_stored_data()
    st.session_state.current_config = stored_data["config"]
    st.session_state.selected_cities = st.session_state.current_config.get("selected_cities", DEFAULT_FAVORITE_CITIES)
    st.session_state.excluded_cities = st.session_state.current_config.get("excluded_cities", [])
    st.session_state.ordered_markets = stored_data["ordered_markets"]
    st.session_state.checked_markets = stored_data["checked_markets"]
    st.session_state.scan_results = None
    st.session_state.config_loaded = True

config = st.session_state.current_config

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stApp { background-color: #0e1117; }
    header { background-color: #161b22 !important; border-bottom: 1px solid #30363d; }
    .filter-box { background-color: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 20px; }
    .result-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
    .city-header { color: #e6edf3; font-size: 1.1rem; font-weight: bold; margin-bottom: 10px; display: flex; justify-content: space-between; }
    .event-box { border-top: 1px solid #30363d; padding-top: 10px; margin-top: 10px; }
    .market-row { display: flex; align-items: center; justify-content: space-between; padding: 10px; }
    .price-btn-yes { background-color: #0d4429; color: #3fb950; padding: 4px 12px; border-radius: 4px; font-weight: bold; min-width: 80px; text-align: center; }
    .price-btn-no { background-color: #490e15; color: #f85149; padding: 4px 12px; border-radius: 4px; font-weight: bold; min-width: 80px; text-align: center; }
    .spread-box { background-color: #21262d; color: #8b949e; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #30363d; }
    .depth-text { color: #8b949e; font-size: 0.7rem; margin-top: 2px; }
    .open-link { background-color: #238636; color: white !important; padding: 4px 12px; border-radius: 4px; text-decoration: none; font-size: 0.9rem; }
    .open-link:hover { background-color: #2ea043; }
    .back-to-top { position: fixed; bottom: 70px; right: 20px; background-color: #1f6feb; color: white !important; padding: 10px 15px; border-radius: 50px; text-decoration: none; font-weight: bold; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
</style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    all_city_names = sorted([c["name"] for c in CITIES_DATA])
    
    st.session_state.selected_cities = [c for c in st.session_state.selected_cities if c not in st.session_state.excluded_cities]

    exclude_options = [c for c in all_city_names if c not in st.session_state.selected_cities]
    excluded_cities = st.multiselect("EXCLUDE CITIES (BLACKLIST)", exclude_options, default=[c for c in st.session_state.excluded_cities if c in exclude_options])
    st.session_state.excluded_cities = excluded_cities
    
    preset_col1, preset_col2, preset_col3, preset_col4 = st.columns([1.5, 1.5, 1, 1.5])
    with preset_col1:
        if st.button("Morning Cities", use_container_width=True): 
            st.session_state.selected_cities = [c for c in DEFAULT_FAVORITE_CITIES if c not in st.session_state.excluded_cities]
            st.session_state.current_config["selected_cities"] = st.session_state.selected_cities
            save_stored_data()
            st.rerun()
    with preset_col2:
        if st.button("Evening Cities", use_container_width=True):
            morning_set = set(DEFAULT_FAVORITE_CITIES)
            st.session_state.selected_cities = [c["name"] for c in CITIES_DATA if c["name"] not in morning_set and c["name"] not in st.session_state.excluded_cities]
            st.session_state.current_config["selected_cities"] = st.session_state.selected_cities
            save_stored_data()
            st.rerun()
    with preset_col3:
        if st.button("Clear All", use_container_width=True): 
            st.session_state.selected_cities = []
            st.session_state.current_config["selected_cities"] = []
            save_stored_data()
            st.rerun()
    with preset_col4:
        st.button("🧹 Reset Bộ Nhớ (Check/Order)", use_container_width=True, on_click=clear_all_flags, help="Xóa sạch cờ đã vào lệnh và cờ đã check để làm chu kỳ mới")
    
    city_names = [c for c in all_city_names if c not in st.session_state.excluded_cities]
    selected_cities = st.multiselect("SELECT CITIES TO SCAN", city_names, default=[c for c in st.session_state.selected_cities if c in city_names])
    st.session_state.selected_cities = selected_cities
    
    c1, c2 = st.columns([1, 1])
    saved_dates = config.get("selected_dates", ["Today", "Tomorrow", "Day After Tomorrow"])
    
    with c1: selected_dates = st.multiselect("SELECT DATES", ["Today", "Tomorrow", "Day After Tomorrow"], default=saved_dates)
    with c2: st.markdown("<p style='color:#8b949e; font-size:0.9rem; margin-top:28px'>Markets are scanned for all types (Highest & Lowest).</p>", unsafe_allow_html=True)

    y_head_col, y_in_col1, y_in_col2 = st.columns([1, 2, 2])
    with y_head_col:
        st.markdown("<p style='font-weight: 600; color: #3fb950; margin-bottom: 5px;'>SCAN YES</p>", unsafe_allow_html=True)
        filter_yes = st.checkbox("Yes", value=config.get("filter_yes", True), label_visibility="collapsed", key="chk_yes")
    with y_in_col1:
        st.markdown("<p style='font-weight: 600; color: #3fb950; margin-bottom: 5px;'>MIN YES (¢)</p>", unsafe_allow_html=True)
        min_p_yes = st.number_input("MIN YES", min_value=0.0, max_value=100.0, value=config.get("min_p_yes", 80.0), step=0.1, format="%.1f", label_visibility="collapsed")
    with y_in_col2:
        st.markdown("<p style='font-weight: 600; color: #3fb950; margin-bottom: 5px;'>MAX YES (¢)</p>", unsafe_allow_html=True)
        max_p_yes = st.number_input("MAX YES", min_value=0.0, max_value=100.0, value=config.get("max_p_yes", 99.9), step=0.1, format="%.1f", label_visibility="collapsed")

    n_head_col, n_in_col1, n_in_col2, n_gap_col = st.columns([1, 1.5, 1.5, 1.0])
    with n_head_col:
        st.markdown("<p style='font-weight: 600; color: #f85149; margin-bottom: 5px;'>SCAN NO</p>", unsafe_allow_html=True)
        filter_no = st.checkbox("No", value=config.get("filter_no", True), label_visibility="collapsed", key="chk_no")
    with n_in_col1:
        st.markdown("<p style='font-weight: 600; color: #f85149; margin-bottom: 5px;'>MIN NO (¢)</p>", unsafe_allow_html=True)
        min_p_no = st.number_input("MIN NO", min_value=0.0, max_value=100.0, value=config.get("min_p_no", 98.0), step=0.1, format="%.1f", label_visibility="collapsed")
    with n_in_col2:
        st.markdown("<p style='font-weight: 600; color: #f85149; margin-bottom: 5px;'>MAX NO (¢)</p>", unsafe_allow_html=True)
        max_p_no = st.number_input("MAX NO", min_value=0.0, max_value=100.0, value=config.get("max_p_no", 99.9), step=0.1, format="%.1f", label_visibility="collapsed")
    with n_gap_col:
        st.markdown("<p style='font-weight: 600; color: #f85149; margin-bottom: 5px;'>GAP FILTER</p>", unsafe_allow_html=True)
        gc1, gc2, gc3 = st.columns([0.5, 1, 1.5])
        with gc1:
            gap_filter_enabled = st.checkbox("", value=config.get("gap_filter_enabled", False), key="chk_gap")
        with gc2:
            gap_value = st.number_input("Gap", min_value=1, max_value=10, value=config.get("gap_value", 3), step=1, label_visibility="collapsed")
        with gc3:
            gap_direction = st.selectbox("Dir", ["Both", "Up", "Down"], index=["Both", "Up", "Down"].index(config.get("gap_direction", "Both")), label_visibility="collapsed")
        st.markdown(f"<p style='color:#8b949e; font-size:0.7rem; margin-top:-10px'>(Skip {gap_value} {gap_direction})</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    col_msg, col_btn = st.columns([2, 1])
    with col_msg: st.markdown("<p style='color:#8b949e; font-size:0.9rem; margin-top:10px'>Settings apply to the current active session.</p>", unsafe_allow_html=True)
    with col_btn: search_clicked = st.button("Search Markets", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if search_clicked:
    current_config = {
        "min_p_yes": min_p_yes, "max_p_yes": max_p_yes, "min_p_no": min_p_no, "max_p_no": max_p_no, 
        "filter_yes": filter_yes, "filter_no": filter_no, "gap_filter_enabled": gap_filter_enabled, 
        "gap_value": gap_value, "gap_direction": gap_direction, "selected_dates": selected_dates, 
        "selected_cities": selected_cities, "excluded_cities": excluded_cities
    }
    st.session_state.current_config = current_config
    save_stored_data()

    with st.spinner("Finding markets..."):
        res, filt, err = asyncio.run(run_scan(min_p_yes, max_p_yes, min_p_no, max_p_no, filter_yes, filter_no, gap_filter_enabled, gap_value, gap_direction, selected_cities, excluded_cities, selected_dates))
        st.session_state.scan_results = {
            "matches": res,
            "filtered": filt,
            "errors": err
        }

if st.session_state.scan_results is not None:
    scan_data = st.session_state.scan_results
    results = scan_data["matches"]
    filtered_raw = scan_data["filtered"]
    errors_raw = scan_data["errors"]
    
    actual_scanned_list = [c["name"] for c in CITIES_DATA if c.get("status") == "active" and c["name"] not in excluded_cities]
    if selected_cities:
        actual_scanned_list = [c for c in actual_scanned_list if c in selected_cities]
        
    total_scanned_cities = len(actual_scanned_list)

    df = pd.DataFrame(results) if results else pd.DataFrame()
    sorted_cities = df.groupby('City')['MatchedPrice'].min().sort_values(ascending=True).index if not df.empty else []
    matched_cities_count = len(sorted_cities)

    no_match_at_all = [c for c in actual_scanned_list if c not in sorted_cities]
    filtered_list = [c for c in no_match_at_all if c in filtered_raw]
    error_list = [c for c in no_match_at_all if c not in filtered_list]

    # --- HÀNG TIÊU ĐỀ & TIÊU CHÍ PHÂN LOẠI BADGES (NẰM NGANG) ---
    col_title, col_badges = st.columns([1.2, 3])
    with col_title:
        badge_color = "#1f6feb" if matched_cities_count > 0 else "#f85149"
        st.markdown(f"### Search Results <span style='background:{badge_color}; padding:2px 10px; border-radius:10px; font-size:0.8rem'>{matched_cities_count}/{total_scanned_cities} Cities</span>", unsafe_allow_html=True)
        
    with col_badges:
        badges_html = ""
        if filtered_list:
            badges_html += f"<span style='color: #e3b341; font-size: 0.85rem; font-weight: bold; margin-right: 5px;'>🟡 FILTERED OUT:</span>"
            for city in sorted(filtered_list):
                badges_html += f"<span style='background-color: #3a2d0c; color: #e3b341; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-right: 6px; border: 1px solid #e3b341; display: inline-block; margin-bottom: 4px;'>{city}</span>"
        
        if error_list:
            if filtered_list: badges_html += "<span style='margin-right: 15px;'></span>"
            badges_html += f"<span style='color: #f85149; font-size: 0.85rem; font-weight: bold; margin-right: 5px;'>🔴 NO MARKET / API ERROR:</span>"
            for city in sorted(error_list):
                badges_html += f"<span style='background-color: #490e15; color: #f85149; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-right: 6px; border: 1px solid #f85149; display: inline-block; margin-bottom: 4px;'>{city}</span>"
        
        if not filtered_list and not error_list:
            badges_html = "<span style='color: #3fb950; font-size: 0.85rem; font-style: italic; font-weight: bold;'>✅ All selected cities matched perfectly!</span>"
            
        st.markdown(f"<div style='margin-top: 10px;'>{badges_html}</div>", unsafe_allow_html=True)

    # --- KẾT QUẢ KÈO ĐẠT TIÊU CHUẨN (HIỂN THỊ FULL WIDTH) ---
    if not df.empty:
        for city_name in sorted_cities:
            city_results = df[df['City'] == city_name].sort_values(by="MatchedPrice", ascending=True)
            with st.container():
                
                # --- LẤY BADGES 3 MODEL KHUYẾN NGHỊ (NEON GLOW TÊN THÀNH PHỐ) ---
                city_info = next((c for c in CITIES_DATA if c["name"] == city_name), None)
                model_badges = ""
                if city_info and "models" in city_info:
                    for m in city_info["models"]:
                        style = MODEL_STYLES.get(m, {"color": "#8b949e", "bg": "#21262d", "border": "#30363d"})
                        color = style["color"]
                        bg = style["bg"]
                        border = style["border"]
                        model_badges += f"<span style='background-color: {bg}; color: {color}; border: 1px solid {border}; padding: 3px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: bold; margin-left: 8px; display: inline-block; box-shadow: 0 0 4px {border}40;'>{m}</span>"
                
                st.markdown(f"""<div class="result-card"><div class="city-header"><span>{city_name}{model_badges}</span></div>""", unsafe_allow_html=True)
                
                for event_title in city_results['EventTitle'].unique():
                    event_markets = city_results[city_results['EventTitle'] == event_title]
                    
                    is_ordered = event_title in st.session_state.ordered_markets
                    is_checked = event_title in st.session_state.checked_markets
                    
                    if is_ordered:
                        title_color = "#3fb950"
                        badge = " &nbsp; <span style='background-color:#14472c; color:#3fb950; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight:bold;'>🟢 ĐÃ VÀO LỆNH</span>"
                        row_bg = "background-color: #0d2a1a; border: 1px solid #3fb950; border-radius: 8px; opacity: 1.0;"
                    elif is_checked:
                        title_color = "#e3b341"
                        badge = " &nbsp; <span style='background-color:#3a2d0c; color:#e3b341; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight:bold;'>🟡 ĐÃ CHECK (THEO DÕI)</span>"
                        row_bg = "background-color: #211b0a; border: 1px solid #e3b341; border-radius: 8px; opacity: 1.0;"
                    else:
                        title_color = "#e6edf3"
                        badge = ""
                        row_bg = "border-bottom: 1px solid #21262d; opacity: 1.0;"
                    
                    title_col, check_btn_col, order_btn_col = st.columns([4, 1, 1])
                    with title_col:
                        st.markdown(f"<div style='color:{title_color}; font-size:0.95rem; margin-bottom:10px; margin-top: 5px; font-weight: bold;'>{event_title}{badge}</div>", unsafe_allow_html=True)
                    
                    with check_btn_col:
                        chk_text = "Bỏ Check" if is_checked else "Đã Check ✔"
                        st.button(chk_text, key=f"chk_{event_title}", on_click=toggle_checked_status, args=(event_title,), use_container_width=True)
                        
                    with order_btn_col:
                        btn_text = "Hủy cờ lệnh" if is_ordered else "Vào lệnh 🚀"
                        st.button(btn_text, key=f"btn_{event_title}", on_click=toggle_ordered_status, args=(event_title,), use_container_width=True)
                    
                    row = event_markets.iloc[0]
                    
                    # --- XỬ LÝ ĐƯỜNG DỰ BÁO NHIỆT ĐỘ LIVE TỪ OPEN-METEO ---
                    forecasts_str = ""
                    if "ModelForecasts" in row and isinstance(row["ModelForecasts"], dict):
                        f_items = []
                        relevant_models = city_info["models"] if city_info else ["ECMWF", "ICON", "GFS"]
                        for m in relevant_models:
                            val = row["ModelForecasts"].get(m)
                            if val is not None:
                                style = MODEL_STYLES.get(m, {"color": "#8b949e"})
                                f_items.append(f"<span style='color:{style['color']}; font-weight:bold;'>{m}: {val:.1f}°F</span>")
                        if f_items:
                            forecasts_str = f"<div style='font-size:0.82rem; margin-top:6px; color:#8b949e; background-color:#1c2128; padding:4px 8px; border-radius:4px; display:inline-block; border:1px solid #30363d;'>🔮 Live Forecasts: {' &nbsp;|&nbsp; '.join(f_items)}</div>"

                    # --- [FIXED] TRIỆT TIÊU TOÀN BỘ INDENTATION TRONG MULTI-LINE HTML ĐỂ TRÁNH LỖI MARKDOWN PARSING ---
                    st.markdown(f"""<div class="market-row" style="{row_bg}">
<div style="flex:2; color:#e6edf3">
<div style="font-weight:500;">{row['Market']} <span style="color:#8b949e; font-size:0.7rem; margin-left:10px">(Best Price)</span></div>
{forecasts_str}
</div>
<div style="flex:2; display:flex; gap:15px; justify-content:center; align-items:center">
<div style="text-align:center">
<div class="price-btn-yes">Yes {row['YES']:.1f}¢</div>
<div class="depth-text">${row['YES_Depth']:,.0f}</div>
</div>
<div class="spread-box">Spread {row['Spread']:.1f}¢</div>
<div style="text-align:center">
<div class="price-btn-no">No {row['NO']:.1f}¢</div>
<div class="depth-text">${row['NO_Depth']:,.0f}</div>
</div>
</div>
<div style="flex:1; text-align:right">
<a href="{row['Link']}" target="_blank" class="open-link">Open</a>
</div>
</div>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("No markets match your criteria.")

    st.markdown('<a href="#top" class="back-to-top">↑ Back to Top</a>', unsafe_allow_html=True)
else:
    st.info("Select cities and filters, then click 'Search Markets' to begin.")
