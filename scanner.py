import os
import json
import asyncio
import aiohttp
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CONSTANTS ---
GAMMA_URL = "https://gamma-api.polymarket.com/events/slug"
CLOB_URL = "https://clob.polymarket.com"
DEFAULT_CONCURRENCY = 20
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "user_config.json")

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
    "Guangzhou", "Jakarta", "Lucknow", "Karachi", "Jeddah", "Tel Aviv", 
    "Amsterdam", "Cape Town", "Munich", "Paris", "Milan", "Warsaw", "Madrid", "London"
]

MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

# --- CONFIG MANAGEMENT ---

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "min_p": 97.0,
        "max_p": 99.5,
        "max_spread": 100.0,
        "market_type": "All Types",
        "selected_dates": ["Today", "Tomorrow", "Day After Tomorrow"],
        "selected_cities": DEFAULT_FAVORITE_CITIES
    }

def save_config(config_data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f)

# --- HELPER FUNCTIONS ---

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

async def check_event(session, semaphore, city, date_info, m_type, min_price, max_price, max_spread, matches_list):
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
                
                # Spread Calculation
                spread = (yes_price + no_price) * 100 - 100
                
                is_match = False
                matched_price = 100.0
                
                if (min_price/100) <= yes_price <= (max_price/100):
                    is_match = True
                    matched_price = min(matched_price, yes_price * 100)
                if (min_price/100) <= no_price <= (max_price/100):
                    is_match = True
                    matched_price = min(matched_price, no_price * 100)

                if is_match and spread <= max_spread:
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

async def run_scan(min_price, max_price, max_spread, selected_cities, selected_dates, selected_type):
    cities_to_scan = [c for c in CITIES_DATA if c.get("status") == "active"]
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
            if selected_type == "Highest": m_types = [t for t in m_types if t == "highest"]
            elif selected_type == "Lowest": m_types = [t for t in m_types if t == "lowest"]
            for d in dates:
                for mt in m_types:
                    tasks.append(check_event(session, semaphore, city, d, mt, min_price, max_price, max_spread, matches_list))
        await asyncio.gather(*tasks)
    return matches_list

# --- STREAMLIT UI ---
st.set_page_config(page_title="PolyWeather Market Finder", page_icon="🎯", layout="wide")
config = load_config()

st.markdown("""
<div id="top"></div>
<style>
    .main { background-color: #0e1117; }
    .stApp { background-color: #0e1117; }
    header { background-color: #161b22 !important; border-bottom: 1px solid #30363d; }
    .top-bar { background-color: #161b22; padding: 10px 20px; margin: -6rem -5rem 2rem -5rem; border-bottom: 1px solid #30363d; }
    .top-bar h2 { color: white; margin: 0; font-size: 1.2rem; font-weight: 600; }
    .filter-box { background-color: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 20px; }
    .result-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
    .city-header { color: #e6edf3; font-size: 1.1rem; font-weight: bold; margin-bottom: 10px; display: flex; justify-content: space-between; }
    .event-box { border-top: 1px solid #30363d; padding-top: 10px; margin-top: 10px; }
    .market-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #21262d; }
    .market-row:last-child { border-bottom: none; }
    .price-btn-yes { background-color: #0d4429; color: #3fb950; padding: 4px 12px; border-radius: 4px; font-weight: bold; min-width: 80px; text-align: center; }
    .price-btn-no { background-color: #490e15; color: #f85149; padding: 4px 12px; border-radius: 4px; font-weight: bold; min-width: 80px; text-align: center; }
    .spread-box { background-color: #21262d; color: #8b949e; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #30363d; }
    .depth-text { color: #8b949e; font-size: 0.7rem; margin-top: 2px; }
    .open-link { background-color: #238636; color: white !important; padding: 4px 12px; border-radius: 4px; text-decoration: none; font-size: 0.9rem; }
    .open-link:hover { background-color: #2ea043; }
    .back-to-top { position: fixed; bottom: 20px; right: 20px; background-color: #1f6feb; color: white !important; padding: 10px 15px; border-radius: 50px; text-decoration: none; font-weight: bold; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
</style>
<div class="top-bar">
    <h2>PolyWeather Market Finder</h2>
</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    city_names = sorted([c["name"] for c in CITIES_DATA])
    preset_col1, preset_col2 = st.columns([1, 5])
    with preset_col1:
        if st.button("Default Favorites"): st.session_state.selected_cities = DEFAULT_FAVORITE_CITIES
        if st.button("Clear All"): st.session_state.selected_cities = []
    if "selected_cities" not in st.session_state: st.session_state.selected_cities = config.get("selected_cities", DEFAULT_FAVORITE_CITIES)
    selected_cities = st.multiselect("SELECT CITIES", city_names, default=st.session_state.selected_cities)
    
    c1, c2, c3, c4, c5 = st.columns([1.5, 1.5, 1, 1, 1])
    type_idx = ["All Types", "Highest", "Lowest"].index(config.get("market_type", "All Types"))
    saved_dates = config.get("selected_dates", ["Today", "Tomorrow", "Day After Tomorrow"])
    if isinstance(saved_dates, str): saved_dates = ["Today", "Tomorrow", "Day After Tomorrow"]
    
    with c1: selected_type = st.selectbox("MARKET TYPE", ["All Types", "Highest", "Lowest"], index=type_idx)
    with c2: selected_dates = st.multiselect("SELECT DATES", ["Today", "Tomorrow", "Day After Tomorrow"], default=saved_dates)
    with c3: min_p = st.number_input("MIN PRICE (¢)", min_value=0.0, max_value=100.0, value=config.get("min_p", 97.0), step=0.1, format="%.1f")
    with c4: max_p = st.number_input("MAX PRICE (¢)", min_value=0.0, max_value=100.0, value=config.get("max_p", 99.5), step=0.1, format="%.1f")
    with c5: max_spread = st.number_input("MAX SPREAD (¢)", min_value=0.0, max_value=100.0, value=config.get("max_spread", 100.0), step=0.1, format="%.1f")
    
    st.markdown("---")
    col_msg, col_btn = st.columns([2, 1])
    with col_msg: st.markdown("<p style='color:#8b949e; font-size:0.9rem; margin-top:10px'>Settings are saved automatically when you search.</p>", unsafe_allow_html=True)
    with col_btn: search_clicked = st.button("Search Markets", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if search_clicked:
    current_config = {"min_p": min_p, "max_p": max_p, "max_spread": max_spread, "market_type": selected_type, "selected_dates": selected_dates, "selected_cities": selected_cities}
    save_config(current_config)

    with st.spinner("Finding markets..."):
        results = asyncio.run(run_scan(min_p, max_p, max_spread, selected_cities, selected_dates, selected_type))
    
    st.markdown(f"### Search Results <span style='background:#1f6feb; padding:2px 10px; border-radius:10px; font-size:0.8rem'>{len(results)}</span>", unsafe_allow_html=True)
    if results:
        df = pd.DataFrame(results)
        city_min_prices = df.groupby('City')['MatchedPrice'].min()
        sorted_cities = city_min_prices.sort_values(ascending=True).index
        for city_name in sorted_cities:
            city_results = df[df['City'] == city_name].sort_values(by="MatchedPrice", ascending=True)
            with st.container():
                st.markdown(f"""<div class="result-card"><div class="city-header"><span>{city_name}</span><span style="background:#21262d; padding:2px 8px; border-radius:10px; font-size:0.7rem">{len(city_results)} events</span></div>""", unsafe_allow_html=True)
                for event_title in city_results['EventTitle'].unique():
                    event_markets = city_results[city_results['EventTitle'] == event_title]
                    st.markdown(f"<div class='event-box'><div style='color:#8b949e; font-size:0.9rem; margin-bottom:10px'>{event_title}</div>", unsafe_allow_html=True)
                    for _, row in event_markets.iterrows():
                        st.markdown(f"""
                        <div class="market-row">
                            <div style="flex:2; color:#e6edf3">{row['Market']}</div>
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
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<a href="#top" class="back-to-top">↑ Back to Top</a>', unsafe_allow_html=True)
    else: st.warning("No markets match your criteria.")
else:
    st.info("Select cities and filters, then click 'Search Markets' to begin.")
