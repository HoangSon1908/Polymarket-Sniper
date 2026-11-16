import asyncio
import json
import os
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import aiohttp
import pandas as pd
import streamlit as st

# --- CONSTANTS ---
CONFIG_FILE = "config.json"
GAMMA_URL = "https://gamma-api.polymarket.com/events/slug"
CLOB_URL = "https://clob.polymarket.com"
DEFAULT_CONCURRENCY = 25
BOOK_BATCH_SIZE = 150
VN_TZ = timezone(timedelta(hours=7))

CITIES_DATA = [
    {"key": "seattle", "name": "Seattle", "polymarketCity": "seattle", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "losangeles", "name": "Los Angeles", "polymarketCity": "los-angeles", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "sanfrancisco", "name": "San Francisco", "polymarketCity": "san-francisco", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "denver", "name": "Denver", "polymarketCity": "denver", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "chicago", "name": "Chicago", "polymarketCity": "chicago", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "dallas", "name": "Dallas", "polymarketCity": "dallas", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "austin", "name": "Austin", "polymarketCity": "austin", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "houston", "name": "Houston", "polymarketCity": "houston", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "mexicocity", "name": "Mexico City", "polymarketCity": "mexico-city", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "panamacity", "name": "Panama City", "polymarketCity": "panama-city", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "miami", "name": "Miami", "polymarketCity": "miami", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "atlanta", "name": "Atlanta", "polymarketCity": "atlanta", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "nyc", "name": "New York", "polymarketCity": "nyc", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "toronto", "name": "Toronto", "polymarketCity": "toronto", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "buenosaires", "name": "Buenos Aires", "polymarketCity": "buenos-aires", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "saopaulo", "name": "São Paulo", "polymarketCity": "sao-paulo", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "london", "name": "London", "polymarketCity": "london", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "lagos", "name": "Lagos", "polymarketCity": "lagos", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "amsterdam", "name": "Amsterdam", "polymarketCity": "amsterdam", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "paris", "name": "Paris", "polymarketCity": "paris", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "munich", "name": "Munich", "polymarketCity": "munich", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "milan", "name": "Milan", "polymarketCity": "milan", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "madrid", "name": "Madrid", "polymarketCity": "madrid", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "warsaw", "name": "Warsaw", "polymarketCity": "warsaw", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "helsinki", "name": "Helsinki", "polymarketCity": "helsinki", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "capetown", "name": "Cape Town", "polymarketCity": "cape-town", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "telaviv", "name": "Tel Aviv", "polymarketCity": "tel-aviv", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "moscow", "name": "Moscow", "polymarketCity": "moscow", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "istanbul", "name": "Istanbul", "polymarketCity": "istanbul", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "ankara", "name": "Ankara", "polymarketCity": "ankara", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "jeddah", "name": "Jeddah", "polymarketCity": "jeddah", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "karachi", "name": "Karachi", "polymarketCity": "karachi", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "lucknow", "name": "Lucknow", "polymarketCity": "lucknow", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "kualalumpur", "name": "Kuala Lumpur", "polymarketCity": "kuala-lumpur", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "jakarta", "name": "Jakarta", "polymarketCity": "jakarta", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "singapore", "name": "Singapore", "polymarketCity": "singapore", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "hongkong", "name": "Hong Kong", "polymarketCity": "hong-kong", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "beijing", "name": "Beijing", "polymarketCity": "beijing", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "chengdu", "name": "Chengdu", "polymarketCity": "chengdu", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "chongqing", "name": "Chongqing", "polymarketCity": "chongqing", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "shanghai", "name": "Shanghai", "polymarketCity": "shanghai", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "shenzhen", "name": "Shenzhen", "polymarketCity": "shenzhen", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "taipei", "name": "Taipei", "polymarketCity": "taipei", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "qingdao", "name": "Qingdao", "polymarketCity": "qingdao", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "wuhan", "name": "Wuhan", "polymarketCity": "wuhan", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "guangzhou", "name": "Guangzhou", "polymarketCity": "guangzhou", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "manila", "name": "Manila", "polymarketCity": "manila", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "seoul", "name": "Seoul", "polymarketCity": "seoul", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "busan", "name": "Busan", "polymarketCity": "busan", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "tokyo", "name": "Tokyo", "polymarketCity": "tokyo", "marketType": ["highest", "lowest"], "status": "active"},
    {"key": "wellington", "name": "Wellington", "polymarketCity": "wellington", "marketType": ["highest", "lowest"], "status": "active"},
]

DEFAULT_FAVORITE_CITIES = [
    "Tokyo", "Busan", "Singapore", "Shanghai", "Wuhan", "Chengdu", "Chongqing",
    "Beijing", "Kuala Lumpur", "Manila", "Guangzhou", "Lucknow", "Karachi",
    "Jeddah", "Tel Aviv", "Amsterdam", "Cape Town", "Paris", "Milan", "Warsaw",
    "Madrid", "London", "Ankara", "Helsinki", "Istanbul", "Moscow", "Wellington",
    "Taipei", "Shenzhen", "Munich", "Seoul",
]

MONTH_NAMES = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]

DEFAULT_CONFIG = {
    "scan_highest": True,
    "h_filter_no": True,
    "h_min_p_no": 80.0,
    "h_max_p_no": 99.9,
    "h_gap_filter_enabled": True,
    "h_gap_top_k": 2,
    "h_gap_value": 4,
    "scan_lowest": True,
    "l_filter_no": True,
    "l_min_p_no": 80.0,
    "l_max_p_no": 99.9,
    "l_gap_filter_enabled": True,
    "l_gap_top_k": 1,
    "l_gap_value": 3,
    "selected_dates": ["Yesterday", "Today"],
    "selected_cities": DEFAULT_FAVORITE_CITIES,
    "excluded_cities": ["Lagos", "Hong Kong", "Jakarta", "Qingdao", "Denver"],
    "ordered_markets": [],
    "checked_markets": [],
}


# ==========================================
# OOP CLASS: QUẢN LÝ CẤU HÌNH VÀ STATE
# ==========================================
class ConfigManager:
    """Quản lý việc nạp, lưu, sao lưu file cấu hình và cập nhật trạng thái session"""

    @staticmethod
    def load_saved_config() -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    cfg = DEFAULT_CONFIG.copy()
                    cfg.update(saved)
                    return cfg
            except Exception:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    @staticmethod
    def save_config_to_file(cfg: dict):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"Lỗi khi lưu cấu hình: {e}")

    @classmethod
    def toggle_ordered_status(cls, event_title: str):
        if event_title in st.session_state.ordered_markets:
            st.session_state.ordered_markets.remove(event_title)
        else:
            st.session_state.ordered_markets.append(event_title)
            if event_title in st.session_state.checked_markets:
                st.session_state.checked_markets.remove(event_title)
        cls._sync_flags()

    @classmethod
    def toggle_checked_status(cls, event_title: str):
        if event_title in st.session_state.checked_markets:
            st.session_state.checked_markets.remove(event_title)
        else:
            st.session_state.checked_markets.append(event_title)
            if event_title in st.session_state.ordered_markets:
                st.session_state.ordered_markets.remove(event_title)
        cls._sync_flags()

    @classmethod
    def clear_all_flags(cls):
        st.session_state.ordered_markets = []
        st.session_state.checked_markets = []
        cls._sync_flags()

    @classmethod
    def _sync_flags(cls):
        if "current_config" in st.session_state:
            st.session_state.current_config["ordered_markets"] = st.session_state.ordered_markets
            st.session_state.current_config["checked_markets"] = st.session_state.checked_markets
            cls.save_config_to_file(st.session_state.current_config)


# ==========================================
# OOP CLASS: QUẢN LÝ MÚI GIỜ & RESOLVE (TỰ ĐỘNG DST)
# ==========================================
class CityTimeManager:
    """Quản lý múi giờ IANA (tự động giờ mùa hè DST) và đếm ngược đến 23:59:59 địa phương"""

    CITY_TIMEZONES = {
        # Châu Á & Trung Đông
        "Tokyo": "Asia/Tokyo",
        "Seoul": "Asia/Seoul",
        "Busan": "Asia/Seoul",
        "Beijing": "Asia/Shanghai",
        "Chengdu": "Asia/Shanghai",
        "Chongqing": "Asia/Shanghai",
        "Shanghai": "Asia/Shanghai",
        "Shenzhen": "Asia/Shanghai",
        "Guangzhou": "Asia/Shanghai",
        "Wuhan": "Asia/Shanghai",
        "Qingdao": "Asia/Shanghai",
        "Hong Kong": "Asia/Hong_Kong",
        "Taipei": "Asia/Taipei",
        "Kuala Lumpur": "Asia/Kuala_Lumpur",
        "Singapore": "Asia/Singapore",
        "Manila": "Asia/Manila",
        "Jakarta": "Asia/Jakarta",
        "Lucknow": "Asia/Kolkata",
        "Karachi": "Asia/Karachi",
        "Jeddah": "Asia/Riyadh",
        "Tel Aviv": "Asia/Jerusalem",
        # Châu Âu & Châu Phi
        "Moscow": "Europe/Moscow",
        "Istanbul": "Europe/Istanbul",
        "Ankara": "Europe/Istanbul",
        "Helsinki": "Europe/Helsinki",
        "Warsaw": "Europe/Warsaw",
        "Munich": "Europe/Berlin",
        "Amsterdam": "Europe/Amsterdam",
        "Paris": "Europe/Paris",
        "Milan": "Europe/Rome",
        "Madrid": "Europe/Madrid",
        "London": "Europe/London",
        "Cape Town": "Africa/Johannesburg",
        "Lagos": "Africa/Lagos",
        # Châu Mỹ & Châu Đại Dương
        "Toronto": "America/Toronto",
        "New York": "America/New_York",
        "Miami": "America/New_York",
        "Atlanta": "America/New_York",
        "Chicago": "America/Chicago",
        "Dallas": "America/Chicago",
        "Austin": "America/Chicago",
        "Houston": "America/Chicago",
        "Mexico City": "America/Mexico_City",
        "Panama City": "America/Panama",
        "Denver": "America/Denver",
        "Los Angeles": "America/Los_Angeles",
        "San Francisco": "America/Los_Angeles",
        "Seattle": "America/Los_Angeles",
        "Buenos Aires": "America/Argentina/Buenos_Aires",
        "São Paulo": "America/Sao_Paulo",
        "Wellington": "Pacific/Auckland",
    }

    @classmethod
    def get_resolve_info(cls, city_name: str, date_str: str):
        tz_name = cls.CITY_TIMEZONES.get(city_name)
        if not tz_name:
            return float("inf"), ""
        try:
            tz = ZoneInfo(tz_name)
            city_now = datetime.now(tz)
            target_date = datetime.strptime(date_str, "%d/%m/%Y")
            resolve_time = datetime(
                target_date.year, target_date.month, target_date.day, 23, 59, 59, tzinfo=tz
            )
            total_seconds = (resolve_time - city_now).total_seconds()
            if total_seconds <= 0:
                return float("inf"), "Đã hết hạn"

            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            display_str = f"còn {hours}h {minutes:02d}m" if hours > 0 else f"còn {minutes}m"
            return total_seconds, display_str
        except Exception:
            return float("inf"), ""

    @classmethod
    def get_seconds_until_resolve(cls, city_name: str, date_str: str) -> float:
        secs, _ = cls.get_resolve_info(city_name, date_str)
        return secs

    @classmethod
    def get_hours_until_resolve(cls, city_name: str, date_str: str) -> str:
        _, disp = cls.get_resolve_info(city_name, date_str)
        return disp


# ==========================================
# OOP CLASS: QUÉT VÀ PHÂN TÍCH POLYMARKET (2-PHASE BATCH)
# ==========================================
class MarketScanner:
    """Kéo sự kiện theo lô song song, gộp batch CLOB /books và lọc cơ hội"""

    @staticmethod
    def parse_val(title: str) -> float:
        if not title:
            return 0.0
        text = str(title).lower()
        text = re.sub(
            r"(january|february|march|april|may|june|july|august|september|october|november|december|\b\d{4}\b)",
            "",
            text,
        )
        m_below = re.search(
            r"([-+]?\d+(?:\.\d+)?)\s*(?:°f|f|°c|c)?\s*(?:or\s*below|or\s*lower|or\s*less)", text
        )
        if m_below:
            return float(m_below.group(1)) - 0.5

        m_above = re.search(
            r"([-+]?\d+(?:\.\d+)?)\s*(?:°f|f|°c|c)?\s*(?:or\s*higher|or\s*above|or\s*more)", text
        )
        if m_above:
            return float(m_above.group(1)) + 0.5

        m_range = re.search(r"([-+]?\d+(?:\.\d+)?)\s*(?:-|to)\s*([-+]?\d+(?:\.\d+)?)", text)
        if m_range:
            return (float(m_range.group(1)) + float(m_range.group(2))) / 2.0

        nums = re.findall(r"[-+]?\d+(?:\.\d+)?", text)
        return float(nums[-1]) if nums else 0.0

    @staticmethod
    def get_target_dates(selected_date_labels) -> list:
        dates = []
        # Cố định múi giờ Việt Nam (GMT+7) để tránh lệch ngày sau 00:00 sáng VN
        now_vn = datetime.now(VN_TZ)
        label_map = {
            "Yesterday": -1,
            "Today": 0,
            "Tomorrow": 1,
            "Day After Tomorrow": 2,
        }
        if isinstance(selected_date_labels, str):
            selected_date_labels = (
                ["Yesterday", "Today", "Tomorrow", "Day After Tomorrow"]
                if selected_date_labels == "All Days"
                else [selected_date_labels]
            )
        for label in selected_date_labels:
            if label in label_map:
                d = now_vn + timedelta(days=label_map[label])
                dates.append(
                    {
                        "slug": f"{MONTH_NAMES[d.month - 1]}-{d.day}-{d.year}",
                        "display": d.strftime("%d/%m/%Y"),
                    }
                )
        return dates

    @staticmethod
    def get_bracket_prob(m: dict, books: dict) -> float:
        try:
            tokens = json.loads(m.get("clobTokenIds", "[]"))
            if len(tokens) >= 2:
                yes_id, no_id = tokens[0], tokens[1]
                yes_book = books.get(yes_id, {})
                no_book = books.get(no_id, {})

                y_bids = yes_book.get("bids", [])
                y_asks = yes_book.get("asks", [])
                n_bids = no_book.get("bids", [])
                n_asks = no_book.get("asks", [])

                if not y_bids and not y_asks and not n_bids and not n_asks:
                    return -1.0

                if y_bids:
                    valid_bids = [float(b["price"]) for b in y_bids if "price" in b]
                    if valid_bids:
                        return max(valid_bids) * 100.0

                if n_asks:
                    valid_n_asks = [float(a["price"]) for a in n_asks if "price" in a]
                    if valid_n_asks:
                        return (1.0 - min(valid_n_asks)) * 100.0

                vol = float(m.get("volume", 0) or 0)
                if y_asks and (vol > 0 or n_bids):
                    valid_y_asks = [float(a["price"]) for a in y_asks if "price" in a]
                    if valid_y_asks:
                        return min(valid_y_asks) * 100.0
        except Exception:
            pass

        vol = float(m.get("volume", 0) or 0)
        if vol > 0:
            try:
                raw_op = m.get("outcomePrices")
                if raw_op:
                    prices = json.loads(raw_op) if isinstance(raw_op, str) else raw_op
                    if prices and len(prices) > 0:
                        return float(prices[0]) * 100.0
            except Exception:
                pass
        return -1.0

    @classmethod
    async def _fetch_gamma_event(cls, session, semaphore, city, date_info, m_type, type_cfg):
        slug = f"{m_type}-temperature-in-{city['polymarketCity']}-on-{date_info['slug']}"
        async with semaphore:
            try:
                async with session.get(f"{GAMMA_URL}/{slug}") as resp:
                    if resp.status != 200:
                        return {"status": "error", "city": city["name"]}
                    event = await resp.json()
                markets = event.get("markets", [])
                if not markets:
                    return {"status": "error", "city": city["name"]}
                return {
                    "status": "ok",
                    "city": city["name"],
                    "date_info": date_info,
                    "m_type": m_type,
                    "type_cfg": type_cfg,
                    "event": event,
                    "markets": markets,
                }
            except Exception:
                return {"status": "error", "city": city["name"]}

    @classmethod
    async def _fetch_books_batch(cls, session, semaphore, token_ids: list) -> dict:
        if not token_ids:
            return {}
        unique_ids = list(dict.fromkeys(token_ids))
        chunks = [unique_ids[i : i + BOOK_BATCH_SIZE] for i in range(0, len(unique_ids), BOOK_BATCH_SIZE)]
        books_map = {}

        async def fetch_chunk(chunk):
            payload = [{"token_id": tid} for tid in chunk]
            async with semaphore:
                try:
                    async with session.post(f"{CLOB_URL}/books", json=payload) as resp:
                        if resp.status != 200:
                            return []
                        return await resp.json()
                except Exception:
                    return []

        results = await asyncio.gather(*(fetch_chunk(c) for c in chunks))
        for res_list in results:
            if isinstance(res_list, list):
                for b in res_list:
                    if isinstance(b, dict) and "asset_id" in b:
                        books_map[b["asset_id"]] = b
        return books_map

    @classmethod
    def _evaluate_event(cls, evt_pack: dict, books: dict, matches_list: list) -> bool:
        city_name = evt_pack["city"]
        date_info = evt_pack["date_info"]
        m_type = evt_pack["m_type"]
        type_cfg = evt_pack["type_cfg"]
        event = evt_pack["event"]
        raw_markets = evt_pack["markets"]

        # Loại bỏ các bracket đã đóng / hết hiệu lực
        markets = [m for m in raw_markets if not m.get("closed", False)]
        if not markets:
            return False

        sorted_markets = sorted(
            markets, key=lambda m: cls.parse_val(m.get("groupItemTitle") or m.get("question"))
        )

        top_bracket_indices = []
        if type_cfg.get("gap_filter_enabled", False):
            candidates = []
            for i, m in enumerate(sorted_markets):
                prob = cls.get_bracket_prob(m, books)
                if prob >= 0:
                    candidates.append((i, prob))
            candidates.sort(key=lambda x: x[1], reverse=True)
            top_k = int(type_cfg.get("gap_top_k", 2))
            top_bracket_indices = [item[0] for item in candidates[:top_k]]

        event_has_match = False
        min_limit = float(type_cfg["min_p_no"])
        max_limit = float(type_cfg["max_p_no"])
        gap_enabled = type_cfg.get("gap_filter_enabled", True)
        gap_distance = int(type_cfg.get("gap_value", 4))

        for current_idx, m in enumerate(sorted_markets):
            try:
                tokens = json.loads(m.get("clobTokenIds", "[]"))
            except Exception:
                continue
            if len(tokens) < 2:
                continue
            no_id = tokens[1]
            no_book = books.get(no_id, {})

            # 1. Phân tích sổ lệnh Bid (NO)
            n_bids = no_book.get("bids", [])
            valid_bids = []
            for b in n_bids:
                if "price" in b:
                    p_dec = float(b["price"])
                    sz = float(b.get("size", 0))
                    if p_dec > 0 and sz > 0:
                        valid_bids.append((p_dec, sz))

            best_no_bid = max((p for p, _ in valid_bids), default=None)
            best_bid_cents = round(best_no_bid * 100.0, 2) if best_no_bid is not None else 0.0
            # Tổng thanh khoản $ USD nằm trong vùng [min_limit, max_limit]
            bid_depth_usdc = sum(
                p * sz for p, sz in valid_bids if min_limit <= round(p * 100.0, 2) <= max_limit
            )

            # 2. Phân tích sổ lệnh Ask (NO)
            n_asks = no_book.get("asks", [])
            valid_asks = []
            for a in n_asks:
                if "price" in a:
                    p_dec = float(a["price"])
                    sz = float(a.get("size", 0))
                    if p_dec > 0 and sz > 0:
                        valid_asks.append((p_dec, sz))

            best_no_ask = min((p for p, _ in valid_asks), default=None)
            best_ask_cents = round(best_no_ask * 100.0, 2) if best_no_ask is not None else None
            # Tổng thanh khoản $ USD có thể khớp ngay dưới trần max_limit
            ask_depth_usdc = sum(
                p * sz for p, sz in valid_asks if min_limit <= round(p * 100.0, 2) <= max_limit
            )

            if best_no_ask is not None and best_no_bid is not None:
                spread_val = round((best_no_ask - best_no_bid) * 100.0, 1)
                spread_str = f"Spread {spread_val:.1f}¢"
            else:
                spread_str = "Spread —"

            # 3. Kiểm tra Gap Filter
            if gap_enabled and top_bracket_indices:
                if any(abs(current_idx - ref_idx) <= gap_distance for ref_idx in top_bracket_indices):
                    continue

            # 4. Kiểm tra điều kiện giá (Tách độc lập BUY NOW và PLACE LIMIT)
            is_match = False
            matched_price = 100.0
            target_type = "LIMIT_BID"

            if type_cfg.get("filter_no", True):
                # Nhánh 1: Có người bán NO ngay trong dải [min_limit, max_limit] -> Khớp ngay bất kể Bid
                if best_ask_cents is not None and (min_limit <= best_ask_cents <= max_limit):
                    is_match = True
                    matched_price = best_ask_cents - 0.0001
                    target_type = "MARKET_BUY"
                # Nhánh 2: Chưa có Ask rẻ -> Kê Limit nếu Bid hiện tại nằm trong [min_limit, max_limit)
                elif best_no_bid is not None and (min_limit <= best_bid_cents < max_limit):
                    is_match = True
                    matched_price = best_bid_cents
                    target_type = "LIMIT_BID"

            if is_match:
                event_has_match = True
                matches_list.append(
                    {
                        "City": city_name,
                        "Date": date_info["display"],
                        "Type": "Highest" if m_type == "highest" else "Lowest",
                        "Market": m.get("groupItemTitle") or m.get("question"),
                        "NO_Bid_Display": f"{best_bid_cents:.1f}¢" if best_no_bid is not None else "Trống",
                        "NO_Bid_Depth": bid_depth_usdc,
                        "NO_Ask_Display": f"{best_ask_cents:.1f}¢" if best_ask_cents is not None else "Trống",
                        "NO_Ask_Depth": ask_depth_usdc,
                        "Spread_Display": spread_str,
                        "MatchedPrice": matched_price,
                        "TargetType": target_type,
                        "Link": f"https://polymarket.com/event/{event['slug']}/{m['slug']}",
                        "EventTitle": f"{m_type.capitalize()} temperature in {city_name} on {date_info['display']}?",
                    }
                )

        return event_has_match

    @classmethod
    async def run_scan(cls, highest_cfg, lowest_cfg, selected_cities, excluded_cities, selected_dates):
        cities_to_scan = [c for c in CITIES_DATA if c.get("status") == "active"]
        if excluded_cities:
            cities_to_scan = [c for c in cities_to_scan if c["name"] not in excluded_cities]
        if selected_cities:
            cities_to_scan = [c for c in cities_to_scan if c["name"] in selected_cities]

        dates = cls.get_target_dates(selected_dates)
        semaphore = asyncio.Semaphore(DEFAULT_CONCURRENCY)
        timeout = aiohttp.ClientTimeout(total=15)
        connector = aiohttp.TCPConnector(limit=DEFAULT_CONCURRENCY)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Pha 1: Kéo toàn bộ sự kiện từ Gamma API
            gamma_tasks = []
            for city in cities_to_scan:
                m_types = city.get("marketType", ["highest", "lowest"])
                if not isinstance(m_types, list):
                    m_types = [m_types]
                for d in dates:
                    if highest_cfg["enabled"] and "highest" in m_types:
                        gamma_tasks.append(
                            cls._fetch_gamma_event(session, semaphore, city, d, "highest", highest_cfg)
                        )
                    if lowest_cfg["enabled"] and "lowest" in m_types:
                        gamma_tasks.append(
                            cls._fetch_gamma_event(session, semaphore, city, d, "lowest", lowest_cfg)
                        )

            gamma_results = await asyncio.gather(*gamma_tasks)

            # Pha 2: Gom toàn bộ token_id & gọi batch CLOB /books
            ok_events = []
            all_token_ids = []
            city_ok_counts = {}
            city_err_counts = {}

            for res in gamma_results:
                c_name = res["city"]
                if res["status"] != "ok":
                    city_err_counts[c_name] = city_err_counts.get(c_name, 0) + 1
                    continue
                city_ok_counts[c_name] = city_ok_counts.get(c_name, 0) + 1
                ok_events.append(res)
                for m in res["markets"]:
                    if m.get("closed", False):
                        continue
                    try:
                        tokens = json.loads(m.get("clobTokenIds", "[]"))
                        if len(tokens) >= 2:
                            all_token_ids.extend([tokens[0], tokens[1]])
                    except Exception:
                        continue

            books_map = await cls._fetch_books_batch(session, semaphore, all_token_ids)

        matches_list = []
        matched_cities = set()
        for evt_pack in ok_events:
            if cls._evaluate_event(evt_pack, books_map, matches_list):
                matched_cities.add(evt_pack["city"])

        # Chỉ xếp vào lỗi nếu thành phố không tải được bất kỳ sự kiện hợp lệ nào
        error_cities = [
            c["name"]
            for c in cities_to_scan
            if c["name"] not in matched_cities and city_ok_counts.get(c["name"], 0) == 0
        ]
        filtered_cities = [
            c["name"]
            for c in cities_to_scan
            if c["name"] not in matched_cities and c["name"] not in error_cities
        ]

        return matches_list, filtered_cities, error_cities


# ==========================================
# STREAMLIT UI
# ==========================================
st.set_page_config(page_title="PolyWeather Limit Hunter", page_icon="🎯", layout="wide")
st.markdown("<div id='top'></div>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    .filter-box {
        background-color: #190d14;
        border: 1px solid #3d1b2b;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }
    .type-panel {
        background-color: #21111a;
        border: 1px solid #4a2335;
        border-radius: 10px;
        padding: 12px 15px;
    }
    .result-card {
        background-color: #190d14;
        border: 1px solid #3d1b2b;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 14px;
    }
    .city-header {
        font-size: 1.15rem;
        font-weight: 800;
        color: #f472b6;
        border-bottom: 1px solid #3d1b2b;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "config_loaded" not in st.session_state:
    st.session_state.current_config = ConfigManager.load_saved_config()
    st.session_state.selected_cities = st.session_state.current_config.get(
        "selected_cities", DEFAULT_FAVORITE_CITIES
    )
    st.session_state.excluded_cities = st.session_state.current_config.get(
        "excluded_cities", DEFAULT_CONFIG.get("excluded_cities", [])
    )
    st.session_state.ordered_markets = st.session_state.current_config.get("ordered_markets", [])
    st.session_state.checked_markets = st.session_state.current_config.get("checked_markets", [])
    st.session_state.scan_results = None
    st.session_state.config_loaded = True

config = st.session_state.current_config

with st.container():
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    all_city_names = sorted([c["name"] for c in CITIES_DATA])

    st.session_state.selected_cities = [
        c for c in st.session_state.selected_cities if c not in st.session_state.excluded_cities
    ]

    exclude_options = [c for c in all_city_names if c not in st.session_state.selected_cities]
    excluded_cities = st.multiselect(
        "EXCLUDE CITIES (BLACKLIST)",
        exclude_options,
        default=[c for c in st.session_state.excluded_cities if c in exclude_options],
    )
    st.session_state.excluded_cities = excluded_cities

    preset_col1, preset_col2, preset_col3, preset_col4, preset_col5 = st.columns([1.2, 1.2, 0.9, 1.5, 1.2])
    with preset_col1:
        if st.button("Morning Cities", use_container_width=True):
            st.session_state.selected_cities = [
                c for c in DEFAULT_FAVORITE_CITIES if c not in st.session_state.excluded_cities
            ]
            st.session_state.current_config["selected_cities"] = st.session_state.selected_cities
            ConfigManager.save_config_to_file(st.session_state.current_config)
            st.rerun()
    with preset_col2:
        if st.button("Evening Cities", use_container_width=True):
            morning_set = set(DEFAULT_FAVORITE_CITIES)
            st.session_state.selected_cities = [
                c["name"]
                for c in CITIES_DATA
                if c["name"] not in morning_set and c["name"] not in st.session_state.excluded_cities
            ]
            st.session_state.current_config["selected_cities"] = st.session_state.selected_cities
            ConfigManager.save_config_to_file(st.session_state.current_config)
            st.rerun()
    with preset_col3:
        if st.button("Clear All", use_container_width=True):
            st.session_state.selected_cities = []
            st.session_state.current_config["selected_cities"] = []
            ConfigManager.save_config_to_file(st.session_state.current_config)
            st.rerun()
    with preset_col4:
        st.button(
            "🧹 Reset Memory",
            use_container_width=True,
            on_click=ConfigManager.clear_all_flags,
            help="Xóa cờ đánh dấu Checked và Ordered cho chu kỳ mới.",
        )
    with preset_col5:
        if st.button("🔄 Reset Defaults", use_container_width=True, help="Khôi phục toàn bộ cài đặt gốc"):
            st.session_state.current_config = DEFAULT_CONFIG.copy()
            st.session_state.selected_cities = DEFAULT_CONFIG["selected_cities"].copy()
            st.session_state.excluded_cities = DEFAULT_CONFIG["excluded_cities"].copy()
            st.session_state.ordered_markets = []
            st.session_state.checked_markets = []
            for k in [
                "chk_scan_highest", "chk_h_no", "num_h_min_no", "num_h_max_no",
                "chk_h_gap", "num_h_top_k", "num_h_gap",
                "chk_scan_lowest", "chk_l_no", "num_l_min_no", "num_l_max_no",
                "chk_l_gap", "num_l_top_k", "num_l_gap",
            ]:
                if k in st.session_state:
                    del st.session_state[k]
            ConfigManager.save_config_to_file(DEFAULT_CONFIG)
            st.toast("Đã khôi phục cài đặt mặc định!", icon="🔄")
            st.rerun()

    city_names = [c for c in all_city_names if c not in st.session_state.excluded_cities]
    selected_cities = st.multiselect(
        "SELECT CITIES TO SCAN",
        city_names,
        default=[c for c in st.session_state.selected_cities if c in city_names],
    )
    st.session_state.selected_cities = selected_cities

    date_options = ["Yesterday", "Today", "Tomorrow", "Day After Tomorrow"]
    saved_dates = config.get("selected_dates", ["Yesterday", "Today"])
    valid_saved_dates = [d for d in saved_dates if d in date_options]
    selected_dates = st.multiselect("SELECT DATES", date_options, default=valid_saved_dates)

    st.markdown("<hr style='border: 1px solid #3d1b2b; margin: 15px 0;'>", unsafe_allow_html=True)

    col_high, col_low = st.columns(2)

    # 1. BẢNG HIGHEST
    with col_high:
        st.markdown('<div class="type-panel">', unsafe_allow_html=True)
        scan_highest = st.checkbox(
            "🔥 SCAN HIGHEST MARKETS", value=config.get("scan_highest", True), key="chk_scan_highest"
        )
        st.markdown(
            "<p style='font-weight: 600; color: #f85149; font-size: 0.85rem; margin-top: 5px; margin-bottom: 2px;'>HIGHEST NO PRICE (MIN BID - MAX THRESHOLD)</p>",
            unsafe_allow_html=True,
        )
        h_no1, h_no2, h_no3 = st.columns([0.6, 1.2, 1.2])
        with h_no1:
            h_filter_no = st.checkbox(
                "Limit",
                value=config.get("h_filter_no", True),
                label_visibility="collapsed",
                key="chk_h_no",
                disabled=not scan_highest,
            )
        with h_no2:
            h_min_p_no = st.number_input(
                "MIN BID",
                min_value=0.0,
                max_value=100.0,
                value=float(config.get("h_min_p_no", 80.0)),
                step=0.1,
                format="%.1f",
                label_visibility="collapsed",
                key="num_h_min_no",
                disabled=not scan_highest,
            )
        with h_no3:
            h_max_p_no = st.number_input(
                "MAX",
                min_value=0.0,
                max_value=100.0,
                value=float(config.get("h_max_p_no", 99.9)),
                step=0.1,
                format="%.1f",
                help="Ask <= mức này khớp ngay | Trống mức này thì kê Limit",
                label_visibility="collapsed",
                key="num_h_max_no",
                disabled=not scan_highest,
            )
        st.markdown(
            f"<p style='color:#9d8590; font-size:0.7rem; margin-top:-8px'>(Ask ≤ {h_max_p_no:.1f}¢: Mua luôn | Bid ≥ {h_min_p_no:.1f}¢: Kê Limit)</p>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<p style='font-weight: 600; color: #e3b341; font-size: 0.85rem; margin-top: 10px; margin-bottom: 2px;'>HIGHEST GAP FILTER</p>",
            unsafe_allow_html=True,
        )
        h_g1, h_g2, h_g3 = st.columns([0.6, 1.2, 1.2])
        with h_g1:
            h_gap_filter_enabled = st.checkbox(
                "", value=config.get("h_gap_filter_enabled", True), key="chk_h_gap", disabled=not scan_highest
            )
        with h_g2:
            h_gap_top_k = st.number_input(
                "Top K",
                min_value=1,
                max_value=5,
                value=int(config.get("h_gap_top_k", 2)),
                step=1,
                label_visibility="collapsed",
                key="num_h_top_k",
                disabled=not scan_highest,
            )
        with h_g3:
            h_gap_value = st.number_input(
                "Gap",
                min_value=1,
                max_value=10,
                value=int(config.get("h_gap_value", 4)),
                step=1,
                label_visibility="collapsed",
                key="num_h_gap",
                disabled=not scan_highest,
            )
        st.markdown(
            f"<p style='color:#9d8590; font-size:0.7rem; margin-top:-8px'>(Né ±{h_gap_value} ô từ Top {h_gap_top_k} cao nhất)</p>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # 2. BẢNG LOWEST
    with col_low:
        st.markdown('<div class="type-panel">', unsafe_allow_html=True)
        scan_lowest = st.checkbox(
            "❄️ SCAN LOWEST MARKETS", value=config.get("scan_lowest", True), key="chk_scan_lowest"
        )
        st.markdown(
            "<p style='font-weight: 600; color: #f85149; font-size: 0.85rem; margin-top: 5px; margin-bottom: 2px;'>LOWEST NO PRICE (MIN BID - MAX THRESHOLD)</p>",
            unsafe_allow_html=True,
        )
        l_no1, l_no2, l_no3 = st.columns([0.6, 1.2, 1.2])
        with l_no1:
            l_filter_no = st.checkbox(
                "Limit",
                value=config.get("l_filter_no", True),
                label_visibility="collapsed",
                key="chk_l_no",
                disabled=not scan_lowest,
            )
        with l_no2:
            l_min_p_no = st.number_input(
                "MIN BID",
                min_value=0.0,
                max_value=100.0,
                value=float(config.get("l_min_p_no", 80.0)),
                step=0.1,
                format="%.1f",
                label_visibility="collapsed",
                key="num_l_min_no",
                disabled=not scan_lowest,
            )
        with l_no3:
            l_max_p_no = st.number_input(
                "MAX",
                min_value=0.0,
                max_value=100.0,
                value=float(config.get("l_max_p_no", 99.9)),
                step=0.1,
                format="%.1f",
                help="Ask <= mức này khớp ngay | Trống mức này thì kê Limit",
                label_visibility="collapsed",
                key="num_l_max_no",
                disabled=not scan_lowest,
            )
        st.markdown(
            f"<p style='color:#9d8590; font-size:0.7rem; margin-top:-8px'>(Ask ≤ {l_max_p_no:.1f}¢: Mua luôn | Bid ≥ {l_min_p_no:.1f}¢: Kê Limit)</p>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<p style='font-weight: 600; color: #e3b341; font-size: 0.85rem; margin-top: 10px; margin-bottom: 2px;'>LOWEST GAP FILTER</p>",
            unsafe_allow_html=True,
        )
        l_g1, l_g2, l_g3 = st.columns([0.6, 1.2, 1.2])
        with l_g1:
            l_gap_filter_enabled = st.checkbox(
                "", value=config.get("l_gap_filter_enabled", True), key="chk_l_gap", disabled=not scan_lowest
            )
        with l_g2:
            l_gap_top_k = st.number_input(
                "Top K",
                min_value=1,
                max_value=5,
                value=int(config.get("l_gap_top_k", 1)),
                step=1,
                label_visibility="collapsed",
                key="num_l_top_k",
                disabled=not scan_lowest,
            )
        with l_g3:
            l_gap_value = st.number_input(
                "Gap",
                min_value=1,
                max_value=10,
                value=int(config.get("l_gap_value", 3)),
                step=1,
                label_visibility="collapsed",
                key="num_l_gap",
                disabled=not scan_lowest,
            )
        st.markdown(
            f"<p style='color:#9d8590; font-size:0.7rem; margin-top:-8px'>(Né ±{l_gap_value} ô từ Top {l_gap_top_k} cao nhất)</p>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    col_msg, col_toggle, col_save, col_btn = st.columns([2.0, 1.2, 1.0, 1.1])
    with col_msg:
        st.markdown(
            "<p style='color:#9d8590; font-size:0.9rem; margin-top:10px'>🚀 <b>Hunter Mode:</b> Tự động gộp <b>⚡ Mua ngay</b> & <b>🎯 Kê Limit</b> (Thanh khoản tính theo USD trong vùng lọc).</p>",
            unsafe_allow_html=True,
        )
    with col_toggle:
        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
        only_buy_now = st.toggle(
            "⚡ Chỉ kèo vào luôn", value=False, help="Chỉ hiển thị các kèo khớp ngay (Market Buy)"
        )
    with col_save:
        if st.button("💾 Lưu Cài Đặt", use_container_width=True):
            current_config = {
                "scan_highest": scan_highest,
                "h_filter_no": h_filter_no,
                "h_min_p_no": h_min_p_no,
                "h_max_p_no": h_max_p_no,
                "h_gap_filter_enabled": h_gap_filter_enabled,
                "h_gap_top_k": h_gap_top_k,
                "h_gap_value": h_gap_value,
                "scan_lowest": scan_lowest,
                "l_filter_no": l_filter_no,
                "l_min_p_no": l_min_p_no,
                "l_max_p_no": l_max_p_no,
                "l_gap_filter_enabled": l_gap_filter_enabled,
                "l_gap_top_k": l_gap_top_k,
                "l_gap_value": l_gap_value,
                "selected_dates": selected_dates,
                "selected_cities": selected_cities,
                "excluded_cities": excluded_cities,
                "ordered_markets": st.session_state.ordered_markets,
                "checked_markets": st.session_state.checked_markets,
            }
            st.session_state.current_config = current_config
            ConfigManager.save_config_to_file(current_config)
            st.toast("✅ Đã lưu thông số thành công!", icon="💾")
    with col_btn:
        search_clicked = st.button("Search Markets", type="primary", use_container_width=True)

    # Sao lưu / Khôi phục nhanh config.json (chống mất cờ khi Streamlit Cloud ngủ đông)
    with st.expander("📦 Sao lưu / Khôi phục cấu hình & danh sách Ordered (config.json)", expanded=False):
        b_col1, b_col2 = st.columns([1, 2])
        with b_col1:
            cfg_json_bytes = json.dumps(
                st.session_state.current_config, ensure_ascii=False, indent=2
            ).encode("utf-8")
            st.download_button(
                "📥 Tải config.json",
                data=cfg_json_bytes,
                file_name="polyweather_config.json",
                mime="application/json",
                use_container_width=True,
            )
        with b_col2:
            uploaded_cfg = st.file_uploader(
                "Nạp lại file config.json", type=["json"], label_visibility="collapsed"
            )
            if uploaded_cfg is not None:
                try:
                    loaded = json.load(uploaded_cfg)
                    merged = DEFAULT_CONFIG.copy()
                    merged.update(loaded)
                    st.session_state.current_config = merged
                    st.session_state.selected_cities = merged.get("selected_cities", DEFAULT_FAVORITE_CITIES)
                    st.session_state.excluded_cities = merged.get("excluded_cities", [])
                    st.session_state.ordered_markets = merged.get("ordered_markets", [])
                    st.session_state.checked_markets = merged.get("checked_markets", [])
                    ConfigManager.save_config_to_file(merged)
                    st.toast("✅ Đã khôi phục cấu hình từ file!", icon="📦")
                    st.rerun()
                except Exception as e:
                    st.error(f"File JSON không hợp lệ: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

if search_clicked:
    if not scan_highest and not scan_lowest:
        st.warning("Please check at least one market type to scan (Highest or Lowest).")
    else:
        current_config = {
            "scan_highest": scan_highest,
            "h_filter_no": h_filter_no,
            "h_min_p_no": h_min_p_no,
            "h_max_p_no": h_max_p_no,
            "h_gap_filter_enabled": h_gap_filter_enabled,
            "h_gap_top_k": h_gap_top_k,
            "h_gap_value": h_gap_value,
            "scan_lowest": scan_lowest,
            "l_filter_no": l_filter_no,
            "l_min_p_no": l_min_p_no,
            "l_max_p_no": l_max_p_no,
            "l_gap_filter_enabled": l_gap_filter_enabled,
            "l_gap_top_k": l_gap_top_k,
            "l_gap_value": l_gap_value,
            "selected_dates": selected_dates,
            "selected_cities": selected_cities,
            "excluded_cities": excluded_cities,
            "ordered_markets": st.session_state.ordered_markets,
            "checked_markets": st.session_state.checked_markets,
        }
        st.session_state.current_config = current_config
        ConfigManager.save_config_to_file(current_config)

        highest_cfg = {
            "enabled": scan_highest,
            "filter_no": h_filter_no,
            "min_p_no": h_min_p_no,
            "max_p_no": h_max_p_no,
            "gap_filter_enabled": h_gap_filter_enabled,
            "gap_top_k": h_gap_top_k,
            "gap_value": h_gap_value,
        }
        lowest_cfg = {
            "enabled": scan_lowest,
            "filter_no": l_filter_no,
            "min_p_no": l_min_p_no,
            "max_p_no": l_max_p_no,
            "gap_filter_enabled": l_gap_filter_enabled,
            "gap_top_k": l_gap_top_k,
            "gap_value": l_gap_value,
        }

        with st.spinner("Hunting Opportunities (Batch CLOB Mode)..."):
            res, filt, err = asyncio.run(
                MarketScanner.run_scan(
                    highest_cfg, lowest_cfg, selected_cities, excluded_cities, selected_dates
                )
            )
            st.session_state.scan_results = {
                "matches": res,
                "filtered": filt,
                "errors": err,
                "scan_time_vn": datetime.now(VN_TZ).strftime("%H:%M:%S %d/%m/%Y (GMT+7)"),
            }

if st.session_state.scan_results is not None:
    scan_data = st.session_state.scan_results
    results = scan_data["matches"]
    filtered_raw = scan_data["filtered"]
    errors_raw = scan_data["errors"]
    scan_time_vn = scan_data.get("scan_time_vn", "")

    actual_scanned_list = [
        c["name"]
        for c in CITIES_DATA
        if c.get("status") == "active" and c["name"] not in excluded_cities
    ]
    if selected_cities:
        actual_scanned_list = [c for c in actual_scanned_list if c in selected_cities]

    total_scanned_cities = len(actual_scanned_list)
    df = pd.DataFrame(results) if results else pd.DataFrame()

    if only_buy_now and not df.empty:
        df = df[df["TargetType"] == "MARKET_BUY"]

    if not df.empty:
        df["SecondsUntilResolve"] = df.apply(
            lambda r: CityTimeManager.get_seconds_until_resolve(r["City"], r["Date"]), axis=1
        )
        df["TimeLeftDisplay"] = df.apply(
            lambda r: CityTimeManager.get_hours_until_resolve(r["City"], r["Date"]), axis=1
        )
        df["Priority"] = df["TargetType"].apply(lambda x: 0 if x == "MARKET_BUY" else 1)
        df = df.sort_values(
            by=["SecondsUntilResolve", "Priority", "MatchedPrice"], ascending=[True, True, True]
        )

    sorted_cities = (
        df.groupby("City")
        .agg({"SecondsUntilResolve": "min", "MatchedPrice": "min"})
        .sort_values(by=["SecondsUntilResolve", "MatchedPrice"], ascending=[True, True])
        .index
        if not df.empty
        else []
    )
    matched_cities_count = len(sorted_cities)

    no_match_at_all = [c for c in actual_scanned_list if c not in sorted_cities]
    error_list = [c for c in no_match_at_all if c in errors_raw]
    filtered_list = [c for c in no_match_at_all if c not in error_list]

    col_title, col_badges = st.columns([1.6, 2.6])
    with col_title:
        badge_color = "#ec4899" if matched_cities_count > 0 else "#f85149"
        buy_now_cnt = len(df[df["TargetType"] == "MARKET_BUY"]) if not df.empty else 0
        limit_cnt = len(df[df["TargetType"] == "LIMIT_BID"]) if not df.empty else 0

        st.markdown(
            f"### Hunt Results <span style='background:{badge_color}; padding:2px 10px; border-radius:10px; font-size:0.8rem'>{matched_cities_count}/{total_scanned_cities} Cities</span> "
            f"<span style='background:#0d4429; color:#3fb950; padding:2px 8px; border-radius:8px; font-size:0.75rem'>⚡ {buy_now_cnt} Buy</span> "
            f"<span style='background:#3a2d0c; color:#e3b341; padding:2px 8px; border-radius:8px; font-size:0.75rem'>🎯 {limit_cnt} Limit</span>",
            unsafe_allow_html=True,
        )
        if scan_time_vn:
            st.caption(f"Cập nhật lúc: **{scan_time_vn}**")

        if st.session_state.ordered_markets:
            ordered_summary = []
            for item in st.session_state.ordered_markets:
                match = re.search(r"(Highest|Lowest) temperature in ([a-zA-Z\s]+) on", item)
                if match:
                    ordered_summary.append(f"{match.group(2)} ({match.group(1)[:4].upper()})")
                else:
                    ordered_summary.append(item[:15] + "...")
            st.markdown(
                f"<p style='color:#3fb950; font-size:0.85rem; margin-top:4px; margin-bottom:0px;'><b>🟢 Ordered:</b> {', '.join(ordered_summary)}</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<p style='color:#9d8590; font-size:0.85rem; margin-top:4px; margin-bottom:0px;'><b>🟢 Ordered:</b> None</p>",
                unsafe_allow_html=True,
            )

    with col_badges:
        badges_html = ""
        if filtered_list:
            badges_html += "<span style='color: #e3b341; font-size: 0.85rem; font-weight: bold; margin-right: 5px;'>🟡 FILTERED OUT:</span>"
            for city in sorted(filtered_list):
                badges_html += f"<span style='background-color: #3a2d0c; color: #e3b341; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-right: 6px; border: 1px solid #e3b341; display: inline-block; margin-bottom: 4px;'>{city}</span>"

        if error_list:
            if filtered_list:
                badges_html += "<span style='margin-right: 15px;'></span>"
            badges_html += "<span style='color: #f85149; font-size: 0.85rem; font-weight: bold; margin-right: 5px;'>🔴 NO MARKET / API ERROR:</span>"
            for city in sorted(error_list):
                badges_html += f"<span style='background-color: #490e15; color: #f85149; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-right: 6px; border: 1px solid #f85149; display: inline-block; margin-bottom: 4px;'>{city}</span>"

        if not filtered_list and not error_list:
            badges_html = "<span style='color: #ec4899; font-size: 0.85rem; font-style: italic; font-weight: bold;'>✅ All selected cities matched perfectly!</span>"

        st.markdown(f"<div style='margin-top: 10px;'>{badges_html}</div>", unsafe_allow_html=True)

    if not df.empty:
        for city_name in sorted_cities:
            city_results = df[df["City"] == city_name].sort_values(
                by=["SecondsUntilResolve", "Priority", "MatchedPrice"], ascending=[True, True, True]
            )
            with st.container():
                st.markdown(
                    f"""<div class="result-card"><div class="city-header"><span>{city_name}</span></div>""",
                    unsafe_allow_html=True,
                )

                for event_title in city_results["EventTitle"].unique():
                    event_markets = city_results[city_results["EventTitle"] == event_title]
                    time_left_str = event_markets.iloc[0]["TimeLeftDisplay"]

                    if time_left_str:
                        if "hết hạn" in time_left_str:
                            time_tag = f" &nbsp; <span style='background-color:#490e15; color:#f85149; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; font-weight:bold; border:1px solid #f85149;'>⏳ {time_left_str}</span>"
                        else:
                            time_tag = f" &nbsp; <span style='background-color:#26161f; color:#f472b6; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; font-weight:bold; border:1px solid #4a2335;'>⏳ {time_left_str}</span>"
                    else:
                        time_tag = ""

                    is_ordered = event_title in st.session_state.ordered_markets
                    is_checked = event_title in st.session_state.checked_markets

                    if is_ordered:
                        title_color = "#3fb950"
                        badge = " &nbsp; <span style='background-color:#14472c; color:#3fb950; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight:bold;'>🟢 ORDERED</span>"
                        row_bg = "background-color: #0d2a1a; border: 1px solid #3fb950; border-radius: 8px; margin-bottom: 6px;"
                    elif is_checked:
                        title_color = "#e3b341"
                        badge = " &nbsp; <span style='background-color:#3a2d0c; color:#e3b341; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight:bold;'>🟡 CHECKED (MONITORING)</span>"
                        row_bg = "background-color: #211b0a; border: 1px solid #e3b341; border-radius: 8px; margin-bottom: 6px;"
                    else:
                        title_color = "#e6edf3"
                        badge = ""
                        row_bg = "border-bottom: 1px solid #4a2335; margin-bottom: 4px;"

                    title_col, check_btn_col, order_btn_col = st.columns([4, 1, 1])
                    with title_col:
                        st.markdown(
                            f"<div style='color:{title_color}; font-size:0.95rem; margin-bottom:8px; margin-top: 5px; font-weight: bold;'>{event_title}{time_tag}{badge}</div>",
                            unsafe_allow_html=True,
                        )
                    with check_btn_col:
                        chk_text = "Uncheck" if is_checked else "Checked ✔"
                        st.button(
                            chk_text,
                            key=f"chk_{event_title}",
                            on_click=ConfigManager.toggle_checked_status,
                            args=(event_title,),
                            use_container_width=True,
                        )
                    with order_btn_col:
                        btn_text = "Cancel Order" if is_ordered else "Order 🚀"
                        st.button(
                            btn_text,
                            key=f"btn_{event_title}",
                            on_click=ConfigManager.toggle_ordered_status,
                            args=(event_title,),
                            use_container_width=True,
                        )

                    # Gom toàn bộ bracket của Event vào 1 iframe duy nhất để tăng tốc render
                    rows_markup = []
                    for idx_r, (_, row) in enumerate(event_markets.iterrows()):
                        safe_id = re.sub(
                            r"[^a-zA-Z0-9]",
                            "",
                            f"{row['Market']}_{row['City']}_{row['TargetType']}_{idx_r}",
                        )
                        target_tag = (
                            "<span style='background-color:#0d4429; color:#3fb950; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:bold; margin-left:8px; border:1px solid #3fb950;'>⚡ BUY NOW (ASK)</span>"
                            if row.get("TargetType") == "MARKET_BUY"
                            else "<span style='background-color:#3a2d0c; color:#e3b341; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:bold; margin-left:8px; border:1px solid #e3b341;'>🎯 PLACE LIMIT</span>"
                        )
                        rows_markup.append(
                            f"""
                            <div class="market-row" style="{row_bg}">
                                <div style="flex:2; color:#e6edf3; font-weight: 500; padding-right:10px;">
                                    {row['Market']} {target_tag}
                                </div>
                                <div style="flex:2; display:flex; gap:15px; justify-content:center; align-items:center">
                                    <div style="text-align:center">
                                        <div class="price-btn-bid">No Bid {row['NO_Bid_Display']}</div>
                                        <div class="depth-text">${row['NO_Bid_Depth']:,.0f}</div>
                                    </div>
                                    <div class="spread-box">{row['Spread_Display']}</div>
                                    <div style="text-align:center">
                                        <div class="price-btn-ask">No Ask {row['NO_Ask_Display']}</div>
                                        <div class="depth-text">${row['NO_Ask_Depth']:,.0f}</div>
                                    </div>
                                </div>
                                <div style="flex:1; text-align:right">
                                    <textarea id="txt_{safe_id}" style="position:absolute; left:-9999px;">{row['Link']}</textarea>
                                    <button onclick="copyLink('{safe_id}', this)" class="copy-link">Copy Link</button>
                                </div>
                            </div>
                            """
                        )

                    combined_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <style>
                        body {{
                            background-color: transparent;
                            margin: 0;
                            padding: 0;
                            color: #e6edf3;
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                            overflow: hidden;
                        }}
                        .market-row {{
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                            padding: 10px;
                            font-size: 0.9rem;
                            box-sizing: border-box;
                            height: 68px;
                        }}
                        .price-btn-bid {{ background-color: #0d4429; color: #3fb950; padding: 4px 12px; border-radius: 4px; font-weight: bold; min-width: 95px; text-align: center; }}
                        .price-btn-ask {{ background-color: #490e15; color: #f85149; padding: 4px 12px; border-radius: 4px; font-weight: bold; min-width: 95px; text-align: center; }}
                        .spread-box {{ background-color: #26161f; color: #f472b6; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #4a2335; text-align: center; min-width: 85px; }}
                        .depth-text {{ color: #9d8590; font-size: 0.7rem; margin-top: 2px; text-align: center; }}
                        .copy-link {{ background-color: #ec4899; color: white !important; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 0.9rem; border: none; cursor: pointer; font-weight: bold; box-shadow: 0 2px 8px rgba(236,72,153,0.3); transition: all 0.2s ease; }}
                        .copy-link:hover {{ background-color: #f43f5e; }}
                    </style>
                    </head>
                    <body>
                    {''.join(rows_markup)}
                    <script>
                    function copyLink(safeId, btn) {{
                        var copyText = document.getElementById("txt_" + safeId);
                        copyText.select();
                        copyText.setSelectionRange(0, 99999);
                        try {{
                            var successful = document.execCommand('copy');
                            if (successful) {{
                                btn.innerText = "Copied!";
                                btn.style.backgroundColor = "#ffb7c5";
                                btn.style.color = "#4a1525";
                                setTimeout(function() {{
                                    btn.innerText = "Copy Link";
                                    btn.style.backgroundColor = "#ec4899";
                                    btn.style.color = "white";
                                }}, 2000);
                            }}
                        }} catch (err) {{}}
                    }}
                    </script>
                    </body>
                    </html>
                    """
                    st.components.v1.html(combined_html, height=len(event_markets) * 74)

                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("No markets match your criteria.")

st.markdown("[↑ Back to Top](#top)")
