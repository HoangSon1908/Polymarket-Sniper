import json
import asyncio
import aiohttp
import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta

# --- CONSTANTS ---
GAMMA_URL = "https://gamma-api.polymarket.com/events/slug"
CLOB_URL = "https://clob.polymarket.com"
DEFAULT_CONCURRENCY = 20

CITIES_DATA = [
    {"key": "seattle", "name": "Seattle", "polymarketCity": "seattle", "marketType": "highest", "status": "active"},
    {"key": "losangeles", "name": "Los Angeles", "polymarketCity": "los-angeles", "marketType": "highest", "status": "active"},
    {"key": "sanfrancisco", "name": "San Francisco", "polymarketCity": "san-francisco", "marketType": "highest", "status": "active"},
    {"key": "denver", "name": "Denver", "polymarketCity": "denver", "marketType": "highest", "status": "active"},
    {"key": "chicago", "name": "Chicago", "polymarketCity": "chicago", "marketType": "highest", "status": "active"},
    {"key": "dallas", "name": "Dallas", "polymarketCity": "dallas", "marketType": "highest", "status": "active"},
    {"key": "austin", "name": "Austin", "polymarketCity": "austin", "marketType": "highest", "status": "active"},
    {"key": "houston", "name": "Houston", "polymarketCity": "houston", "marketType": "highest", "status": "active"},
    {"key": "mexicocity", "name": "Mexico City", "polymarketCity": "mexico-city", "marketType": "highest", "status": "active"},
    {"key": "panamacity", "name": "Panama City", "polymarketCity": "panama-city", "marketType": "highest", "status": "active"},
    {"key": "miami", "name": "Miami", "polymarketCity": "miami", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "atlanta", "name": "Atlanta", "polymarketCity": "atlanta", "marketType": "highest", "status": "active"},
    {"key": "nyc", "name": "New York", "polymarketCity": "nyc", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "toronto", "name": "Toronto", "polymarketCity": "toronto", "marketType": "highest", "status": "active"},
    {"key": "buenosaires", "name": "Buenos Aires", "polymarketCity": "buenos-aires", "marketType": "highest", "status": "active"},
    {"key": "saopaulo", "name": "São Paulo", "polymarketCity": "sao-paulo", "marketType": "highest", "status": "active"},
    {"key": "london", "name": "London", "polymarketCity": "london", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "lagos", "name": "Lagos", "polymarketCity": "lagos", "marketType": "highest", "status": "active"},
    {"key": "amsterdam", "name": "Amsterdam", "polymarketCity": "amsterdam", "marketType": "highest", "status": "active"},
    {"key": "paris", "name": "Paris", "polymarketCity": "paris", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "munich", "name": "Munich", "polymarketCity": "munich", "marketType": "highest", "status": "active"},
    {"key": "milan", "name": "Milan", "polymarketCity": "milan", "marketType": "highest", "status": "active"},
    {"key": "madrid", "name": "Madrid", "polymarketCity": "madrid", "marketType": "highest", "status": "active"},
    {"key": "warsaw", "name": "Warsaw", "polymarketCity": "warsaw", "marketType": "highest", "status": "active"},
    {"key": "helsinki", "name": "Helsinki", "polymarketCity": "helsinki", "marketType": "highest", "status": "active"},
    {"key": "capetown", "name": "Cape Town", "polymarketCity": "cape-town", "marketType": "highest", "status": "active"},
    {"key": "telaviv", "name": "Tel Aviv", "polymarketCity": "tel-aviv", "marketType": "highest", "status": "active"},
    {"key": "moscow", "name": "Moscow", "polymarketCity": "moscow", "marketType": "highest", "status": "active"},
    {"key": "istanbul", "name": "Istanbul", "polymarketCity": "istanbul", "marketType": "highest", "status": "active"},
    {"key": "ankara", "name": "Ankara", "polymarketCity": "ankara", "marketType": "highest", "status": "active"},
    {"key": "jeddah", "name": "Jeddah", "polymarketCity": "jeddah", "marketType": "highest", "status": "active"},
    {"key": "karachi", "name": "Karachi", "polymarketCity": "karachi", "marketType": "highest", "status": "active"},
    {"key": "lucknow", "name": "Lucknow", "polymarketCity": "lucknow", "marketType": "highest", "status": "active"},
    {"key": "kualalumpur", "name": "Kuala Lumpur", "polymarketCity": "kuala-lumpur", "marketType": "highest", "status": "active"},
    {"key": "jakarta", "name": "Jakarta", "polymarketCity": "jakarta", "marketType": "highest", "status": "active"},
    {"key": "singapore", "name": "Singapore", "polymarketCity": "singapore", "marketType": "highest", "status": "active"},
    {"key": "hongkong", "name": "Hong Kong", "polymarketCity": "hong-kong", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "beijing", "name": "Beijing", "polymarketCity": "beijing", "marketType": "highest", "status": "active"},
    {"key": "chengdu", "name": "Chengdu", "polymarketCity": "chengdu", "marketType": "highest", "status": "active"},
    {"key": "chongqing", "name": "Chongqing", "polymarketCity": "chongqing", "marketType": "highest", "status": "active"},
    {"key": "shanghai", "name": "Shanghai", "polymarketCity": "shanghai", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "shenzhen", "name": "Shenzhen", "polymarketCity": "shenzhen", "marketType": "highest", "status": "active"},
    {"key": "taipei", "name": "Taipei", "polymarketCity": "taipei", "marketType": "highest", "status": "active"},
    {"key": "qingdao", "name": "Qingdao", "polymarketCity": "qingdao", "marketType": "highest", "status": "active"},
    {"key": "wuhan", "name": "Wuhan", "polymarketCity": "wuhan", "marketType": "highest", "status": "active"},
    {"key": "guangzhou", "name": "Guangzhou", "polymarketCity": "guangzhou", "marketType": "highest", "status": "active"},
    {"key": "manila", "name": "Manila", "polymarketCity": "manila", "marketType": "highest", "status": "active"},
    {"key": "seoul", "name": "Seoul", "polymarketCity": "seoul", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "busan", "name": "Busan", "polymarketCity": "busan", "marketType": "highest", "status": "active"},
    {"key": "tokyo", "name": "Tokyo", "polymarketCity": "tokyo", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "wellington", "name": "Wellington", "polymarketCity": "wellington", "marketType": "highest", "status": "active"}
]

DEFAULT_FAVORITE_CITIES = [
    "Tokyo", "Seoul", "Busan", "Singapore", "Shanghai", "Wuhan", "Chengdu", 
    "Chongqing", "Beijing", "Kuala Lumpur", "Taipei", "Qingdao", "Manila", 
    "Guangzhou", "Lucknow", "Karachi", "Jeddah", "Tel Aviv", 
    "Amsterdam", "Cape Town", "Munich", "Paris", "Milan", "Warsaw", "Madrid", 
    "London", "Ankara", "Helsinki", "Istanbul", "Moscow"
]

MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

DEFAULT_CONFIG = {
    "min_p_yes": 80.0,
    "max_p_yes": 99.7,
    "min_p_no": 98.0,
    "max_p_no": 99.7,
    "filter_yes": True,
    "filter_no": True,
    "gap_filter_enabled": True,
    "gap_value": 3,
    "gap_direction": "Both",
    "selected_dates": ["Today", "Tomorrow", "Day After Tomorrow"],
    "selected_cities": DEFAULT_FAVORITE_CITIES,
    "excluded_cities": ["Lagos", "Shenzhen", "Hong Kong", "Jakarta"],
    "ordered_markets": [],
    "checked_markets": []
}

# --- CALLBACK FUNCTIONS ---
def toggle_ordered_status(event_title):
    if event_title in st.session_state.ordered_markets:
        st.session_state.ordered_markets.remove(event_title)
    else:
        st.session_state.ordered_markets.append(event_title)
        if event_title in st.session_state.checked_markets:
            st.session_state.checked_markets.remove(event_title)

def toggle_checked_status(event_title):
    if event_title in st.session_state.checked_markets:
        st.session_state.checked_markets.remove(event_title)
    else:
        st.session_state.checked_markets.append(event_title)
        if event_title in st.session_state.ordered_markets:
            st.session_state.ordered_markets.remove(event_title)

def clear_all_flags():
    st.session_state.ordered_markets = []
    st.session_state.checked_markets = []

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

async def check_event(session, semaphore, city, date_info, m_type, min_p_yes, max_p_yes, min_p_no, max_p_no, filter_yes, filter_no, gap_filter_enabled, gap_value, gap_direction, matches_list):
    async with semaphore:
        slug = f"{m_type}-temperature-in-{city['polymarketCity']}-on-{date_info['slug']}"
        try:
            async with session.get(f"{GAMMA_URL}/{slug}") as resp:
                if resp.status != 200: return
                event = await resp.json()
            markets = event.get("markets", [])
            if not markets: return
            
            book_reqs = []
            market_map = {}
            for m in markets:
                tokens = json.loads(m.get("clobTokenIds", "[]"))
                if len(tokens) < 2: continue
                yes_id, no_id = tokens[0], tokens[1]
                book_reqs.extend([{"token_id": yes_id}, {"token_id": no_id}])
                market_map[yes_id] = {"m": m, "side": "YES", "other": no_id, "event": event}
                market_map[no_id] = {"m": m, "side": "NO", "other": yes_id, "event": event}
            
            if not book_reqs: return
            
            async with session.post(f"{CLOB_URL}/books", json=book_reqs) as books_resp:
                if books_resp.status != 200: return
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
                    matches_list.append({
                        "City": city["name"],
                        "Date": date_info["display"],
                        "Type": "Highest" if m_type == "highest" else "Lowest",
                        "Market": m.get("groupItemTitle") or m.get("question"),
                        "YES": yes_price * 100,
                        "NO": no_price * 100,
                        "YES_Depth": y_depth,
                        "NO_Depth": n_depth,
                        "Spread": spread,
                        "MatchedPrice": matched_price,
                        "Link": f"https://polymarket.com/event/{evt['slug']}/{m['slug']}",
                        "EventTitle": f"{m_type.capitalize()} temperature in {city['name']} on {date_info['display']}?"
                    })
        except Exception:
            pass

async def run_scan(min_p_yes, max_p_yes, min_p_no, max_p_no, filter_yes, filter_no, gap_filter_enabled, gap_value, gap_direction, selected_cities, excluded_cities, selected_dates):
    cities_to_scan = [c for c in CITIES_DATA if c.get("status") == "active"]
    if excluded_cities:
        cities_to_scan = [c for c in cities_to_scan if c["name"] not in excluded_cities]
    if selected_cities:
        cities_to_scan = [c for c in cities_to_scan if c["name"] in selected_cities]
        
    dates = get_target_dates(selected_dates)
    matches_list = []
    semaphore = asyncio.Semaphore(DEFAULT_CONCURRENCY)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for city in cities_to_scan:
            m_types = city.get("marketType")
            if not isinstance(m_types, list): m_types = [m_types]
            for d in dates:
                for mt in m_types:
                    tasks.append(check_event(session, semaphore, city, d, mt, min_p_yes, max_p_yes, min_p_no, max_p_no, filter_yes, filter_no, gap_filter_enabled, gap_value, gap_direction, matches_list))
        await asyncio.gather(*tasks)
    return matches_list

# --- STREAMLIT UI ---
st.set_page_config(page_title="PolyWeather Market Finder", page_icon="🎯", layout="wide")

if "config_loaded" not in st.session_state:
    st.session_state.current_config = DEFAULT_CONFIG.copy()
    st.session_state.selected_cities = st.session_state.current_config["selected_cities"]
    st.session_state.excluded_cities = st.session_state.current_config["excluded_cities"]
    st.session_state.ordered_markets = st.session_state.current_config["ordered_markets"]
    st.session_state.checked_markets = st.session_state.current_config["checked_markets"]
    st.session_state.scan_results = None
    st.session_state.config_loaded = True

config = st.session_state.current_config

st.markdown("""
<div id="top"></div>
<style>
    .main { background-color: #0e1117; }
    .stApp { background-color: #0e1117; }
    header { background-color: #161b22 !important; border-bottom: 1px solid #30363d; }
    .filter-box { background-color: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 20px; }
    .result-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
    .city-header { color: #e6edf3; font-size: 1.1rem; font-weight: bold; margin-bottom: 10px; display: flex; justify-content: space-between; }
    .event-box { border-top: 1px solid #30363d; padding-top: 10px; margin-top: 10px; }
    .market-row { display: flex; align-items: center; justify-content: space-between; padding: 10px; transition: all 0.2s; }
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
            st.rerun()
    with preset_col2:
        if st.button("Evening Cities", use_container_width=True):
            morning_set = set(DEFAULT_FAVORITE_CITIES)
            st.session_state.selected_cities = [c["name"] for c in CITIES_DATA if c["name"] not in morning_set and c["name"] not in st.session_state.excluded_cities]
            st.rerun()
    with preset_col3:
        if st.button("Clear All", use_container_width=True): 
            st.session_state.selected_cities = []
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
        "selected_cities": selected_cities, "excluded_cities": excluded_cities,
        "ordered_markets": st.session_state.ordered_markets, "checked_markets": st.session_state.checked_markets
    }
    st.session_state.current_config = current_config

    with st.spinner("Finding markets..."):
        st.session_state.scan_results = asyncio.run(run_scan(min_p_yes, max_p_yes, min_p_no, max_p_no, filter_yes, filter_no, gap_filter_enabled, gap_value, gap_direction, selected_cities, excluded_cities, selected_dates))

if st.session_state.scan_results is not None:
    results = st.session_state.scan_results
    total_scanned_cities = len(selected_cities) if selected_cities else len([c for c in CITIES_DATA if c.get("status") == "active" and c["name"] not in excluded_cities])
    
    if results:
        df = pd.DataFrame(results)
        city_min_prices = df.groupby('City')['MatchedPrice'].min()
        sorted_cities = city_min_prices.sort_values(ascending=True).index
        matched_cities_count = len(sorted_cities)
        
        st.markdown(f"### Search Results <span style='background:#1f6feb; padding:2px 10px; border-radius:10px; font-size:0.8rem'>{matched_cities_count}/{total_scanned_cities} Cities</span>", unsafe_allow_html=True)
        
        for city_name in sorted_cities:
            city_results = df[df['City'] == city_name].sort_values(by="MatchedPrice", ascending=True)
            with st.container():
                st.markdown(f"""<div class="result-card"><div class="city-header"><span>{city_name}</span></div>""", unsafe_allow_html=True)
                
                for event_title in city_results['EventTitle'].unique():
                    event_markets = city_results[city_results['EventTitle'] == event_title]
                    
                    is_ordered = event_title in st.session_state.ordered_markets
                    is_checked = event_title in st.session_state.checked_markets
                    
                    # --- THIẾT LẬP HỆ MÀU MỚI (MÀU SẮC RÕ RÀNG, OPACITY LUÔN LÀ 1.0) ---
                    if is_ordered:
                        title_color = "#3fb950"  # Xanh lục
                        badge = " &nbsp; <span style='background-color:#14472c; color:#3fb950; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight:bold;'>🟢 ĐÃ VÀO LỆNH</span>"
                        row_bg = "background-color: #0d2a1a; border: 1px solid #3fb950; border-radius: 8px; opacity: 1.0;"
                    elif is_checked:
                        title_color = "#e3b341"  # Vàng hổ phách
                        badge = " &nbsp; <span style='background-color:#3a2d0c; color:#e3b341; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight:bold;'>🟡 ĐÃ CHECK (THEO DÕI)</span>"
                        row_bg = "background-color: #211b0a; border: 1px solid #e3b341; border-radius: 8px; opacity: 1.0;"
                    else:
                        title_color = "#ffffff"  # Trắng (Chưa gắn cờ)
                        badge = ""
                        row_bg = "background-color: #161b22; border: 1px solid #ffffff; border-radius: 8px; opacity: 1.0;"
                    
                    # Layout nút bấm
                    title_col, check_btn_col, order_btn_col = st.columns([4, 1, 1])
                    with title_col:
                        st.markdown(f"<div style='color:{title_color}; font-size:0.95rem; margin-bottom:10px; margin-top: 5px; font-weight: bold;'>{event_title}{badge}</div>", unsafe_allow_html=True)
                    
                    with check_btn_col:
                        chk_text = "Bỏ Theo Dõi" if is_checked else "Đã Check 🟡"
                        st.button(chk_text, key=f"chk_{event_title}", on_click=toggle_checked_status, args=(event_title,), use_container_width=True)
                        
                    with order_btn_col:
                        btn_text = "Hủy cờ lệnh" if is_ordered else "Vào lệnh 🚀"
                        st.button(btn_text, key=f"btn_{event_title}", on_click=toggle_ordered_status, args=(event_title,), use_container_width=True)
                    
                    row = event_markets.iloc[0]
                    st.markdown(f"""
                    <div class="market-row" style="{row_bg}">
                        <div style="flex:2; color:#e6edf3">{row['Market']} <span style="color:#8b949e; font-size:0.7rem; margin-left:10px">(Best Price)</span></div>
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
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<a href="#top" class="back-to-top">↑ Back to Top</a>', unsafe_allow_html=True)
    else:
        st.markdown(f"### Search Results <span style='background:#f85149; padding:2px 10px; border-radius:10px; font-size:0.8rem'>0/{total_scanned_cities} Cities</span>", unsafe_allow_html=True)
        st.warning("No markets match your criteria.")
else:
    st.info("Select cities and filters, then click 'Search Markets' to begin.")
