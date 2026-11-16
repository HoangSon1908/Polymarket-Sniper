import time
from datetime import datetime, timedelta, timezone
import numpy as np
import requests
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Polymarket Copy Signal Scanner",
    page_icon="⚡",
    layout="wide",
)

POSITIONS_URL = "https://data-api.polymarket.com/v2/positions"
CLOB_BOOKS_URL = "https://clob.polymarket.com/books"
DEFAULT_WALLET = "0xc9bfc7986767173b4f1c3fc9b2c6b255fc7381c0"
VN_TZ = timezone(timedelta(hours=7))


def fetch_positions_v2(wallet: str, status_val: str) -> list[dict]:
    """Kéo vị thế theo chuẩn Polymarket Data API v2 (lọc status + phân trang cursor)."""
    rows = []
    params = {
        "user": wallet.strip(),
        "status": status_val,
        "limit": 500,
    }

    for _ in range(50):
        res = requests.get(POSITIONS_URL, params=params, timeout=15)
        if res.status_code == 429:
            time.sleep(2.0)
            continue
        res.raise_for_status()
        payload = res.json()

        batch = payload.get("data") or []
        rows.extend(batch)

        pagination = payload.get("pagination") or {}
        next_cursor = pagination.get("next_cursor")
        has_more = pagination.get("has_more", False)

        if not next_cursor or not has_more:
            break

        # API v2 dùng cursor-only, giữ nguyên user & status và không truyền offset
        params = {
            "user": wallet.strip(),
            "status": status_val,
            "cursor": next_cursor,
        }

    return rows


def fetch_clob_books(token_ids: list[str]) -> dict[str, dict]:
    """Lấy sổ lệnh thực tế (Best Ask & thanh khoản) từ CLOB API theo lô token_id."""
    unique_ids = [t for t in dict.fromkeys(token_ids) if t and str(t).strip()]
    books_map: dict[str, dict] = {}
    if not unique_ids:
        return books_map

    for i in range(0, len(unique_ids), 100):
        chunk = [{"token_id": tid} for tid in unique_ids[i : i + 100]]
        for _ in range(3):
            try:
                res = requests.post(CLOB_BOOKS_URL, json=chunk, timeout=10)
                if res.status_code == 429:
                    time.sleep(1.5)
                    continue
                if res.status_code == 200:
                    for b in res.json():
                        asset_id = str(b.get("asset_id", ""))
                        if asset_id:
                            books_map[asset_id] = b
                break
            except Exception:
                time.sleep(0.5)

    return books_map


def parse_ask_metrics(book: dict, max_limit_dec: float) -> tuple[float | None, float]:
    """Trả về (best_ask_price, tổng_USDC_khả_dụng_tại_hoặc_dưới_giá_trần)."""
    asks = book.get("asks") or []
    valid_asks = []
    for a in asks:
        try:
            p = float(a.get("price", 0))
            s = float(a.get("size", 0))
            if p > 0 and s > 0:
                valid_asks.append((p, s))
        except Exception:
            continue

    if not valid_asks:
        return None, 0.0

    best_ask = min(p for p, _ in valid_asks)
    avail_usdc = sum(p * s for p, s in valid_asks if p <= max_limit_dec + 1e-6)
    return best_ask, avail_usdc


def format_time_ago(epoch_val) -> str:
    if pd.isna(epoch_val) or not epoch_val:
        return "N/A"
    try:
        dt = datetime.fromtimestamp(float(epoch_val), tz=timezone.utc)
        diff_min = (datetime.now(timezone.utc) - dt).total_seconds() / 60.0
        if diff_min < 0:
            return "Vừa xong"
        if diff_min < 60:
            return f"{int(diff_min)} phút trước"
        if diff_min < 1440:
            return f"{diff_min / 60:.1f} giờ trước"
        return f"{diff_min / 1440:.1f} ngày trước"
    except Exception:
        return "N/A"


def evaluate_positions(
    raw_open: list[dict],
    books_map: dict[str, dict],
    multiplier: float,
    min_user_bet: float,
    max_user_cap: float,
    max_slippage_cents: float,
    drop_warn_cents: float,
    block_50_60: bool,
    detect_hedge: bool,
    max_fav_prob: float,
    blocked_keywords: list[str],
) -> pd.DataFrame:
    if not raw_open:
        return pd.DataFrame()

    df = pd.DataFrame(raw_open)

    def get_col(candidates: list[str], default=None) -> pd.Series:
        for c in candidates:
            if c in df.columns:
                return df[c]
        return pd.Series([default] * len(df), index=df.index)

    df["condition_id"] = get_col(["condition_id"], default="").astype(str)
    df["token_id"] = get_col(["token_id", "asset", "asset_id"], default="").astype(str)
    df["title"] = get_col(["title", "question"], default="N/A").astype(str)
    df["outcome"] = get_col(["outcome"], default="").astype(str)
    df["avg_price"] = pd.to_numeric(get_col(["avg_price"]), errors="coerce").fillna(0.0)
    df["entry_cost_usdc"] = pd.to_numeric(get_col(["entry_cost_usdc"]), errors="coerce").fillna(0.0)
    df["current_size"] = pd.to_numeric(get_col(["current_size"]), errors="coerce").fillna(0.0)
    df["current_value"] = pd.to_numeric(get_col(["current_value"]), errors="coerce").fillna(0.0)

    # Khóa định danh duy nhất cho từng vị thế để lưu trạng thái Đã vào lệnh
    df["pos_key"] = np.where(
        df["token_id"].str.strip() != "",
        df["token_id"].str.strip(),
        df["condition_id"].str.strip() + "_" + df["outcome"].str.strip(),
    )

    # Chuẩn API v2: total_pnl = realized_pnl + unrealized_pnl
    realized_s = pd.to_numeric(get_col(["realized_pnl"]), errors="coerce").fillna(0.0)
    unrealized_s = pd.to_numeric(get_col(["unrealized_pnl"]), errors="coerce")
    df["total_pnl"] = realized_s + unrealized_s.fillna(df["current_value"] - df["entry_cost_usdc"])

    # Giá tham chiếu từ /v2/positions (dùng làm fallback khi sổ lệnh không có Ask)
    raw_cur_p = pd.to_numeric(get_col(["current_price"]), errors="coerce")
    implied_cur_p = np.where(df["current_size"] > 0, df["current_value"] / df["current_size"], df["avg_price"])
    df["ref_price"] = raw_cur_p.where(raw_cur_p.notna() & (raw_cur_p > 0), implied_cur_p).fillna(df["avg_price"])

    # Quy tắc 1 & 3: Nhân hệ số, không làm tròn lên, khóa trần max_user_cap
    df["raw_user_bet"] = df["entry_cost_usdc"] * multiplier
    df["final_user_bet"] = df["raw_user_bet"].clip(upper=max_user_cap).round(2)

    # Quy tắc 4: Tính giá trần tối đa & đối chiếu Best Ask thực tế trên CLOB
    max_slip_dec = max_slippage_cents / 100.0
    df["max_limit_dec"] = (df["avg_price"] + max_slip_dec).clip(upper=0.99)
    df["max_limit_cents"] = df["max_limit_dec"] * 100.0

    exec_prices = []
    avail_liqs = []
    has_live_ask = []

    for _, r in df.iterrows():
        book = books_map.get(r["token_id"].strip(), {})
        best_ask, avail_usdc = parse_ask_metrics(book, r["max_limit_dec"])
        if best_ask is not None:
            exec_prices.append(best_ask)
            avail_liqs.append(avail_usdc)
            has_live_ask.append(True)
        else:
            exec_prices.append(r["ref_price"])
            avail_liqs.append(0.0)
            has_live_ask.append(False)

    df["exec_price"] = exec_prices
    df["avail_liq_usdc"] = avail_liqs
    df["has_live_ask"] = has_live_ask
    df["slippage_cents"] = (df["exec_price"] - df["avg_price"]) * 100.0

    # Phát hiện các thị trường ví gốc đang ôm từ 2 cửa trở lên (Hedge 2 đầu)
    active_pos = df[(df["condition_id"].str.strip() != "") & (df["current_size"] > 0)]
    outcome_counts = active_pos.groupby("condition_id")["outcome"].nunique()
    hedged_cids = set(outcome_counts[outcome_counts >= 2].index)

    last_ts = pd.to_numeric(get_col(["last_event_at", "updated_at", "timestamp"]), errors="coerce")
    df["last_buy_ago"] = last_ts.apply(format_time_ago)

    slug_col = get_col(["event_slug", "slug"], default="")
    df["url"] = slug_col.apply(
        lambda s: f"https://polymarket.com/event/{s}" if pd.notna(s) and str(s).strip() else ""
    )

    statuses = []
    reasons = []
    action_notes = []

    for _, r in df.iterrows():
        p = r["avg_price"]
        ref_p = r["ref_price"]
        raw_bet = r["raw_user_bet"]
        user_bet = r["final_user_bet"]
        slip_c = r["slippage_cents"]
        liq = r["avail_liq_usdc"]
        live_ask = r["has_live_ask"]
        title_lower = r["title"].lower()

        if ref_p <= 0.02 or ref_p >= 0.98:
            statuses.append("REJECTED")
            reasons.append(f"Kèo đã ngã ngũ/sát giờ đóng (Giá {ref_p*100:.1f}¢)")
            action_notes.append("")
            continue

        # Kiểm tra Hedge 2 đầu trước khi vào tiền
        if detect_hedge and r["condition_id"] in hedged_cids:
            statuses.append("HEDGED")
            reasons.append("Ví gốc đang giữ cả 2 cửa trên trận này")
            action_notes.append("🛑 Bỏ qua (Ví đang Hedge)")
            continue

        # Quy tắc 2 (Giải đấu): Tách riêng giải đấu chặn sang Mục 4
        matched_kw = next((kw for kw in blocked_keywords if kw in title_lower), None)
        if matched_kw:
            statuses.append("BLOCKED_LEAGUE")
            sub_notes = ["Đạt vốn >=$4k" if raw_bet >= min_user_bet else "Dưới vốn <$4k"]
            if (block_50_60 and 0.50 <= p < 0.60) or (p > max_fav_prob / 100.0):
                sub_notes.append("Sai dải giá")
            else:
                sub_notes.append("Đúng dải giá")
            reasons.append(f"[{matched_kw.upper()}] " + " • ".join(sub_notes))
            action_notes.append("Không vào tiền")
            continue

        # Quy tắc 1: Ngưỡng kích hoạt tối thiểu
        if raw_bet < min_user_bet:
            min_whale_req = min_user_bet / multiplier if multiplier > 0 else 0
            statuses.append("REJECTED")
            reasons.append(f"Vốn ví gốc ${r['entry_cost_usdc']:,.0f} < ${min_whale_req:,.0f} (Lệnh bạn ${raw_bet:.2f})")
            action_notes.append("")
            continue

        # Quy tắc 2 (Xác suất): Cấm 50–60% và >85%
        if block_50_60 and (0.50 <= p < 0.60):
            statuses.append("REJECTED")
            reasons.append(f"Dải cấm 50%–60% (Giá ví gốc {p*100:.1f}¢)")
            action_notes.append("")
            continue

        if p > (max_fav_prob / 100.0):
            statuses.append("REJECTED")
            reasons.append(f"Dải cấm >{max_fav_prob:.0f}% (Biên lãi mỏng: {p*100:.1f}¢)")
            action_notes.append("")
            continue

        # Quy tắc 4: Kiểm soát trượt giá tăng quá trần (dựa trên Best Ask thực tế)
        if slip_c > max_slippage_cents:
            statuses.append("SLIPPAGE_WARN")
            reasons.append(f"Ask thực tế vượt trần (+{slip_c:.1f}¢ > +{max_slippage_cents:.1f}¢)")
            action_notes.append("Chỉ đặt Limit ở Giá trần")
            continue

        statuses.append("VALID")
        reasons.append("Đạt đủ quy tắc")

        notes = []
        if slip_c < -abs(drop_warn_cents):
            notes.append(f"⚠️ Tụt >{drop_warn_cents:.0f}¢ (CHECK LIVE!)")

        if not live_ask:
            notes.append("📋 Trống Ask (Kê Limit)")
        elif liq < user_bet:
            notes.append(f"💧 Ask mỏng (${liq:.2f}/${user_bet:.2f})")
        elif not notes:
            notes.append("✅ Khớp ngay (Check Pre-match)")

        action_notes.append(" | ".join(notes))

    df["signal_group"] = statuses
    df["reason"] = reasons
    df["action_note"] = action_notes
    return df


# Khởi tạo bộ nhớ các kèo đã đánh dấu vào lệnh trong phiên
if "entered_ids" not in st.session_state:
    st.session_state["entered_ids"] = set()

# ======================== SIDEBAR CẤU HÌNH ========================
with st.sidebar:
    st.header("⚙️ Tham số 5 Quy Tắc")
    wallet_input = st.text_input(
        "Địa chỉ ví mục tiêu",
        value=DEFAULT_WALLET,
        help="Ví chuyên CS2, gom lệnh pre-match trước 11–13h.",
    )

    multiplier = st.number_input(
        "Hệ số nhân quy mô (QT 5)",
        min_value=0.00001,
        max_value=1.0,
        value=0.00025,
        step=0.00005,
        format="%.5f",
        help="Giữ cố định 0.00025 suốt tháng đầu tiên trên vốn $100–$120.",
    )

    col_s1, col_s2 = st.columns(2)
    min_user_bet = col_s1.number_input(
        "Lệnh tối thiểu ($) (QT 1)",
        min_value=0.1,
        value=1.00,
        step=0.5,
        help="Tương đương vốn ví gốc >= $4,000. Không làm tròn lên.",
    )
    max_user_cap = col_s2.number_input(
        "Trần tối đa ($) (QT 3)",
        min_value=1.0,
        value=10.00,
        step=1.0,
        help="Khóa rủi ro tối đa $10/kèo (tương đương $40,000 ví gốc).",
    )

    max_slippage_cents = st.slider(
        "Trượt giá Ask tối đa (cent) (QT 4)",
        min_value=0.5,
        max_value=10.0,
        value=2.5,
        step=0.5,
        help="So sánh Best Ask thực tế trên CLOB với giá trung bình ví gốc.",
    )

    drop_warn_cents = st.slider(
        "Cảnh báo giá tụt sâu trên (cent) (QT 4)",
        min_value=2.0,
        max_value=15.0,
        value=5.0,
        step=1.0,
        help="Tự gắn cờ cảnh báo kiểm tra trận đã đánh Live chưa nếu giá tụt sâu.",
    )

    block_50_60 = st.checkbox("Chặn dải lỗ 50% – 60% (QT 2)", value=True)
    detect_hedge = st.checkbox("Chặn kèo ví gốc Hedge 2 đầu", value=True)
    max_fav_prob = st.slider("Chặn kèo chắc ăn trên (%) (QT 2)", min_value=70, max_value=99, value=85, step=5)

    blocked_kw_input = st.text_input(
        "Từ khóa giải chặn — Bảng riêng (QT 2)",
        value="CCT Europe",
        help="Tách riêng các trận thuộc giải này sang Mục 4 để theo dõi, không vào tiền.",
    )
    blocked_keywords = [k.strip().lower() for k in blocked_kw_input.split(",") if k.strip()]

    st.divider()
    st.caption(
        f"**Ngưỡng ví gốc:** Từ **${min_user_bet / multiplier:,.0f}** "
        f"đến **${max_user_cap / multiplier:,.0f}** (đạt trần ${max_user_cap:.0f})."
    )
    if st.session_state["entered_ids"]:
        if st.button(f"🧹 Xóa dấu Đã vào ({len(st.session_state['entered_ids'])})", use_container_width=True):
            st.session_state["entered_ids"] = set()
            st.rerun()

# ======================== MAIN UI ========================
st.title("⚡ Trạm Quét Lệnh Copy-Trade CS2")

with st.expander("📋 Bảng Tóm Tắt 5 Quy Tắc & Cảnh Báo Thủ Công (Bấm để xem/thu gọn)", expanded=False):
    rule_col1, rule_col2 = st.columns(2)
    with rule_col1:
        st.markdown(
            "**🤖 Tool đã tự động lọc 100%:**\n"
            "* **QT 1 (Ngưỡng vào):** Chỉ lấy kèo ví gốc `>= $4,000` (bạn vào `>= $1.00`, không làm tròn lên).\n"
            "* **QT 2 (Dải giá & Giải):** Chỉ lấy `< 50%` hoặc `60% – 85%`; chặn `50%–60%`, `> 85%`, kèo Hedge 2 đầu và tách riêng **`CCT Europe`**.\n"
            "* **QT 3 (Trần rủi ro):** Khóa tối đa **`$10.00/kèo`** (`min(Vốn ví × 0.00025, $10)`).\n"
            "* **QT 4 (Trượt giá CLOB):** Đối soát trực tiếp **Best Ask** & **Thanh khoản** trên sổ lệnh; chặn Ask cao hơn ví gốc quá **`+2.5¢`**."
        )
    with rule_col2:
        st.warning(
            "**⚠️ 3 việc BẮT BUỘC tự kiểm tra (Tool không tự chặn được):**\n"
            "1. **Không vào kèo Live (QT 4):** Mở link Polymarket kiểm tra trận chưa bắt đầu thi đấu (đặc biệt khi thấy cờ `⚠️ Tụt >5¢`).\n"
            "2. **Giữ tới đáo hạn (QT 4):** Khớp xong giữ nguyên tới hết trận để bấm **Redeem**, không bán non giữa trận.\n"
            "3. **Kỷ luật vốn $100–$120 (QT 5):** Giữ nguyên hệ số `0.00025` suốt tháng đầu; khi tổng ví vượt **`$150`**, rút lãi dôi ra đưa vốn về **`$100–$120`**."
        )

top_col1, top_col2 = st.columns([1.2, 3])
with top_col1:
    scan_clicked = st.button("🔍 QUÉT LỆNH HỢP LỆ NGAY", type="primary", use_container_width=True)

if "scan_data" not in st.session_state or scan_clicked:
    with st.spinner("Đang quét vị thế API v2 & đối soát sổ lệnh CLOB thực tế..."):
        try:
            open_rows = fetch_positions_v2(wallet_input, "OPEN")
            redeem_rows = fetch_positions_v2(wallet_input, "REDEEMABLE")
            token_list = [
                str(r.get("token_id") or r.get("asset") or r.get("asset_id") or "")
                for r in open_rows
            ]
            books_map = fetch_clob_books(token_list)
            now_vn_str = datetime.now(VN_TZ).strftime("%H:%M:%S %d/%m/%Y (GMT+7)")
            st.session_state["scan_data"] = (open_rows, redeem_rows, books_map, now_vn_str)
        except Exception as e:
            st.error(f"Lỗi gọi API Polymarket: {e}")
            st.stop()

open_rows, redeem_rows, books_map, last_scan_str = st.session_state["scan_data"]
top_col2.caption(
    f"Cập nhật lần cuối: **{last_scan_str}** | "
    f"Vị thế đang mở: **{len(open_rows)}** | "
    f"Sổ lệnh CLOB đã đối soát: **{len(books_map)}** token"
)

evaluated_df = evaluate_positions(
    open_rows,
    books_map=books_map,
    multiplier=multiplier,
    min_user_bet=min_user_bet,
    max_user_cap=max_user_cap,
    max_slippage_cents=max_slippage_cents,
    drop_warn_cents=float(drop_warn_cents),
    block_50_60=block_50_60,
    detect_hedge=detect_hedge,
    max_fav_prob=float(max_fav_prob),
    blocked_keywords=blocked_keywords,
)

if evaluated_df.empty:
    st.info("Hiện tại ví mục tiêu không có vị thế nào đang mở (`OPEN`).")
    st.stop()

valid_df = evaluated_df[evaluated_df["signal_group"] == "VALID"].sort_values("final_user_bet", ascending=False).copy()
slip_df = evaluated_df[evaluated_df["signal_group"] == "SLIPPAGE_WARN"].sort_values("final_user_bet", ascending=False).copy()
hedged_df = evaluated_df[evaluated_df["signal_group"] == "HEDGED"].sort_values(["condition_id", "entry_cost_usdc"], ascending=[True, False]).copy()
blocked_df = evaluated_df[evaluated_df["signal_group"] == "BLOCKED_LEAGUE"].sort_values("entry_cost_usdc", ascending=False).copy()
rej_df = evaluated_df[evaluated_df["signal_group"] == "REJECTED"].sort_values("entry_cost_usdc", ascending=False).copy()

# Tính tổng vốn còn lại cần vào (loại trừ các kèo đã tick Đã vào)
pending_valid_df = valid_df[~valid_df["pos_key"].isin(st.session_state["entered_ids"])]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(
    "🟢 Kèo hợp lệ cần vào",
    f"{len(pending_valid_df)}/{len(valid_df)} kèo",
    f"Vốn cần thêm: ${pending_valid_df['final_user_bet'].sum():.2f}",
)
m2.metric("🟡 Quá trượt giá Ask", f"{len(slip_df)} kèo", "Chờ giá hồi về trần")
m3.metric("⚠️ Ví Hedge 2 đầu", f"{len(hedged_df)} vị thế", "Chặn tránh lệch kèo")
m4.metric("🚫 Giải chặn riêng", f"{len(blocked_df)} kèo", blocked_kw_input or "Trống")
m5.metric("💰 Chờ Redeem", f"{len(redeem_rows)} kèo", "Nhắc bấm Claim")

st.divider()

# --- MỤC 1: KÈO HỢP LỆ ---
st.subheader(f"🟢 1. Danh sách Kèo Hợp Lệ — Vào Lệnh Ngay ({len(valid_df)})")
if valid_df.empty:
    st.info("Chưa có kèo nào đạt đủ điều kiện ở thời điểm hiện tại. Hãy quay lại quét trước giờ các trận CS2 diễn ra.")
else:
    st.caption("Tick vào cột **Đã vào** sau khi khớp lệnh trên Polymarket để tránh vào trùng ở các lần quét sau.")
    valid_df["entered"] = valid_df["pos_key"].isin(st.session_state["entered_ids"])
    disp_valid = valid_df[
        [
            "entered",
            "title",
            "outcome",
            "final_user_bet",
            "action_note",
            "avg_price",
            "exec_price",
            "slippage_cents",
            "max_limit_cents",
            "avail_liq_usdc",
            "entry_cost_usdc",
            "last_buy_ago",
            "url",
        ]
    ].copy()
    disp_valid["avg_price"] = disp_valid["avg_price"] * 100.0
    disp_valid["exec_price"] = disp_valid["exec_price"] * 100.0

    edited_valid = st.data_editor(
        disp_valid,
        use_container_width=True,
        hide_index=True,
        key="editor_valid_signals",
        disabled=[c for c in disp_valid.columns if c != "entered"],
        column_config={
            "entered": st.column_config.CheckboxColumn("✅ Đã vào", default=False),
            "title": st.column_config.TextColumn("Trận đấu (Market)", width="large"),
            "outcome": st.column_config.TextColumn("Cửa chọn"),
            "final_user_bet": st.column_config.NumberColumn("💵 Tiền bạn vào ($)", format="$%.2f"),
            "action_note": st.column_config.TextColumn("Cảnh báo thao tác", width="medium"),
            "avg_price": st.column_config.NumberColumn("Giá ví gốc", format="%.1f¢"),
            "exec_price": st.column_config.NumberColumn("Giá Ask thực", format="%.1f¢"),
            "slippage_cents": st.column_config.NumberColumn("Trượt thực", format="%+.1f¢"),
            "max_limit_cents": st.column_config.NumberColumn("🛑 Giá trần", format="%.1f¢"),
            "avail_liq_usdc": st.column_config.NumberColumn("Thanh khoản Ask", format="$%.2f"),
            "entry_cost_usdc": st.column_config.NumberColumn("Vốn ví gốc ($)", format="$%,.0f"),
            "last_buy_ago": st.column_config.TextColumn("Lệnh cuối"),
            "url": st.column_config.LinkColumn("Đặt lệnh", display_text="Mở Polymarket"),
        },
    )

    # Đồng bộ trạng thái checkbox Đã vào (an toàn kể cả khi người dùng sort bảng)
    checked_valid_keys = set(valid_df.loc[edited_valid.index[edited_valid["entered"]], "pos_key"])
    unchecked_valid_keys = set(valid_df.loc[edited_valid.index[~edited_valid["entered"]], "pos_key"])
    new_entered = (st.session_state["entered_ids"] | checked_valid_keys) - unchecked_valid_keys
    if new_entered != st.session_state["entered_ids"]:
        st.session_state["entered_ids"] = new_entered
        st.rerun()

# --- MỤC 2: KÈO QUÁ TRƯỢT GIÁ ASK ---
if not slip_df.empty:
    st.subheader(f"🟡 2. Kèo Đạt Điều Kiện Nhưng Quá Trượt Giá Ask ({len(slip_df)})")
    st.caption("Giá Ask trên sổ lệnh đang cao hơn trần cho phép; chỉ đặt lệnh Limit ở cột **Giá trần** nếu trận chưa đá Live.")
    slip_df["entered"] = slip_df["pos_key"].isin(st.session_state["entered_ids"])
    disp_slip = slip_df[
        [
            "entered",
            "title",
            "outcome",
            "final_user_bet",
            "avg_price",
            "exec_price",
            "slippage_cents",
            "max_limit_cents",
            "entry_cost_usdc",
            "last_buy_ago",
            "url",
        ]
    ].copy()
    disp_slip["avg_price"] = disp_slip["avg_price"] * 100.0
    disp_slip["exec_price"] = disp_slip["exec_price"] * 100.0

    edited_slip = st.data_editor(
        disp_slip,
        use_container_width=True,
        hide_index=True,
        key="editor_slip_signals",
        disabled=[c for c in disp_slip.columns if c != "entered"],
        column_config={
            "entered": st.column_config.CheckboxColumn("✅ Đã kê Limit", default=False),
            "title": st.column_config.TextColumn("Trận đấu (Market)", width="large"),
            "outcome": st.column_config.TextColumn("Cửa chọn"),
            "final_user_bet": st.column_config.NumberColumn("💵 Tiền bạn vào ($)", format="$%.2f"),
            "avg_price": st.column_config.NumberColumn("Giá ví gốc", format="%.1f¢"),
            "exec_price": st.column_config.NumberColumn("Giá Ask thực", format="%.1f¢"),
            "slippage_cents": st.column_config.NumberColumn("Trượt thực", format="%+.1f¢"),
            "max_limit_cents": st.column_config.NumberColumn("🛑 Giá trần", format="%.1f¢"),
            "entry_cost_usdc": st.column_config.NumberColumn("Vốn ví gốc ($)", format="$%,.0f"),
            "last_buy_ago": st.column_config.TextColumn("Lệnh cuối"),
            "url": st.column_config.LinkColumn("Xem kèo", display_text="Mở Polymarket"),
        },
    )

    checked_slip_keys = set(slip_df.loc[edited_slip.index[edited_slip["entered"]], "pos_key"])
    unchecked_slip_keys = set(slip_df.loc[edited_slip.index[~edited_slip["entered"]], "pos_key"])
    new_entered_slip = (st.session_state["entered_ids"] | checked_slip_keys) - unchecked_slip_keys
    if new_entered_slip != st.session_state["entered_ids"]:
        st.session_state["entered_ids"] = new_entered_slip
        st.rerun()

# --- MỤC 3: CẢNH BÁO KÈO VÍ GỐC ĐANG HEDGE 2 ĐẦU ---
if not hedged_df.empty:
    st.subheader(f"⚠️ 3. Cảnh Báo: Ví Gốc Đang Hedge 2 Đầu ({len(hedged_df)} vị thế)")
    st.caption("Ví mục tiêu đang mua cả 2 cửa trên cùng thị trường — hệ thống tự động khóa không copy để tránh lệch kèo.")
    disp_hedged = hedged_df[
        ["title", "outcome", "entry_cost_usdc", "final_user_bet", "avg_price", "exec_price", "total_pnl", "last_buy_ago", "url"]
    ].copy()
    disp_hedged["avg_price"] = disp_hedged["avg_price"] * 100.0
    disp_hedged["exec_price"] = disp_hedged["exec_price"] * 100.0

    st.dataframe(
        disp_hedged,
        use_container_width=True,
        hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("Trận đấu (Đang Hedge)", width="large"),
            "outcome": st.column_config.TextColumn("Cửa giữ"),
            "entry_cost_usdc": st.column_config.NumberColumn("Vốn ví gốc ($)", format="$%,.0f"),
            "final_user_bet": st.column_config.NumberColumn("Quy đổi ($)", format="$%.2f"),
            "avg_price": st.column_config.NumberColumn("Giá ví gốc", format="%.1f¢"),
            "exec_price": st.column_config.NumberColumn("Giá hiện tại", format="%.1f¢"),
            "total_pnl": st.column_config.NumberColumn("PnL tạm tính ví ($)", format="$%+,.2f"),
            "last_buy_ago": st.column_config.TextColumn("Lệnh cuối"),
            "url": st.column_config.LinkColumn("Xem kèo", display_text="Mở Polymarket"),
        },
    )

# --- MỤC 4: BẢNG THEO DÕI RIÊNG GIẢI ĐẤU CHẶN (CCT EUROPE) ---
st.subheader(f"🚫 4. Bảng Theo Dõi Riêng: Giải Đấu Chặn ({len(blocked_df)})")
if blocked_df.empty:
    st.caption("Hiện tại ví gốc không có vị thế đang mở nào thuộc danh sách giải chặn.")
else:
    st.caption("Bảng này chỉ để theo dõi phong độ của ví ở giải chặn (hệ thống tự động chặn không vào tiền).")
    disp_blocked = blocked_df[
        ["title", "outcome", "reason", "entry_cost_usdc", "final_user_bet", "avg_price", "exec_price", "total_pnl", "last_buy_ago", "url"]
    ].copy()
    disp_blocked["avg_price"] = disp_blocked["avg_price"] * 100.0
    disp_blocked["exec_price"] = disp_blocked["exec_price"] * 100.0

    st.dataframe(
        disp_blocked,
        use_container_width=True,
        hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("Trận đấu (Giải chặn)", width="large"),
            "outcome": st.column_config.TextColumn("Cửa chọn"),
            "reason": st.column_config.TextColumn("Trạng thái điều kiện", width="medium"),
            "entry_cost_usdc": st.column_config.NumberColumn("Vốn ví gốc ($)", format="$%,.0f"),
            "final_user_bet": st.column_config.NumberColumn("Quy đổi ($)", format="$%.2f"),
            "avg_price": st.column_config.NumberColumn("Giá ví gốc", format="%.1f¢"),
            "exec_price": st.column_config.NumberColumn("Giá hiện tại", format="%.1f¢"),
            "total_pnl": st.column_config.NumberColumn("PnL tạm tính ví ($)", format="$%+,.2f"),
            "last_buy_ago": st.column_config.TextColumn("Lệnh cuối"),
            "url": st.column_config.LinkColumn("Xem kèo", display_text="Mở Polymarket"),
        },
    )

# --- MỤC 5: CÁC VỊ THẾ BỊ LOẠI KHÁC & REDEEMABLE ---
with st.expander(f"⚪ Xem {len(rej_df)} vị thế bị loại do vốn nhỏ hoặc sai dải giá"):
    disp_rej = rej_df[["reason", "title", "outcome", "avg_price", "entry_cost_usdc", "raw_user_bet", "last_buy_ago"]].copy()
    disp_rej["avg_price"] = disp_rej["avg_price"] * 100.0
    st.dataframe(
        disp_rej,
        use_container_width=True,
        hide_index=True,
        column_config={
            "reason": st.column_config.TextColumn("Lý do loại", width="medium"),
            "title": st.column_config.TextColumn("Trận đấu", width="large"),
            "outcome": st.column_config.TextColumn("Cửa"),
            "avg_price": st.column_config.NumberColumn("Giá ví gốc", format="%.1f¢"),
            "entry_cost_usdc": st.column_config.NumberColumn("Vốn ví gốc ($)", format="$%,.2f"),
            "raw_user_bet": st.column_config.NumberColumn("Quy đổi x0.00025", format="$%.2f"),
            "last_buy_ago": st.column_config.TextColumn("Lệnh cuối"),
        },
    )

if redeem_rows:
    with st.expander(f"💰 Xem {len(redeem_rows)} kèo của ví vừa thắng chờ Redeem — Nhắc bạn bấm Claim"):
        red_df = pd.DataFrame(redeem_rows)
        r_pnl = pd.to_numeric(red_df.get("realized_pnl", 0), errors="coerce").fillna(0.0)
        u_pnl = pd.to_numeric(red_df.get("unrealized_pnl", 0), errors="coerce").fillna(0.0)
        red_df["total_pnl"] = r_pnl + u_pnl
        cols_r = [c for c in ["title", "outcome", "avg_price", "total_pnl"] if c in red_df.columns]
        if cols_r:
            st.dataframe(red_df[cols_r], use_container_width=True, hide_index=True)
