import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time

# إعدادات الصفحة والتصميم
st.set_page_config(
    page_title="Binance Spot Momentum Terminal",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# إضافة CSS مخصص لتحسين مظهر الواجهة
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e222d; padding: 15px; border-radius: 10px; border: 1px solid #2a2e39; }
    div[data-testid="stSidebarNav"] { background-color: #131722; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e222d; border-radius: 6px; padding: 8px 16px; color: #d1d4dc; }
    .stTabs [aria-selected="true"] { background-color: #2962ff !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ منصة رصد الزخم والسيولة - Binance Spot")

STABLECOINS = {
    "USDC", "BUSD", "FDUSD", "TUSD", "DAI", "USDP", "EUR", "GBP", 
    "AEUR", "EURI", "USDS", "WBTC", "WEETH", "USDE"
}

BASE_URLS = [
    "https://data-api.binance.vision/api/v3",
    "https://api.binance.com/api/v3",
    "https://api1.binance.com/api/v3",
    "https://api3.binance.com/api/v3"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# --- الشريط الجانبي ---
st.sidebar.header("⚙️ إعدادات الماسح")
auto_refresh = st.sidebar.checkbox("تفعيل التحديث التلقائي", value=True)
refresh_interval = st.sidebar.slider("معدل التحديث (ثواني)", min_value=10, max_value=120, value=30, step=5)
min_vol = st.sidebar.number_input("حد أدنى لسيولة 24h ($)", value=1000000, step=500000)

st.sidebar.markdown("---")
st.sidebar.header("💬 إعدادات التليجرام")
bot_token = st.sidebar.text_input("Bot Token", type="password")
chat_id = st.sidebar.text_input("Chat ID")

def fetch_binance_data(endpoint):
    for base in BASE_URLS:
        try:
            url = f"{base}/{endpoint}"
            res = requests.get(url, headers=HEADERS, timeout=4)
            if res.status_code == 200:
                return res.json()
        except Exception:
            continue
    return None

def send_telegram_msg(token, chat_id, message):
    if not token or not chat_id:
        return False, "يرجى إدخال البيانات"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        res = requests.post(url, json=payload, timeout=5)
        return (True, "تم الإرسال!") if res.status_code == 200 else (False, res.text)
    except Exception as e:
        return False, str(e)

@st.cache_data(ttl=1800)
def get_all_spot_symbols():
    data = fetch_binance_data("exchangeInfo")
    if not data or 'symbols' not in data:
        return []
    
    symbols = []
    for s in data['symbols']:
        if s.get('quoteAsset') == 'USDT' and s.get('status') == 'TRADING' and s.get('isSpotTradingAllowed', True):
            base = s.get('baseAsset')
            if base not in STABLECOINS:
                symbols.append(s['symbol'])
    return symbols

fast_timeframes = {
    "1m":  {"interval": "1m",  "limit": 15},
    "5m":  {"interval": "5m",  "limit": 12},
    "15m": {"interval": "15m", "limit": 8}
}

def run_full_spot_screener(symbols_list, min_volume_filter):
    screener_data = []

    tickers = fetch_binance_data("ticker/24hr")
    if not tickers:
        return pd.DataFrame()
    
    ticker_dict = {t['symbol']: float(t['quoteVolume']) for t in tickers if 'quoteVolume' in t}
    valid_symbols = [s for s in symbols_list if s in ticker_dict and ticker_dict[s] >= min_volume_filter]
    sorted_symbols = sorted(valid_symbols, key=lambda x: ticker_dict[x], reverse=True)[:50]

    for symbol in sorted_symbols:
        try:
            ratios, deltas = {}, {}
            current_price = 0.0

            for tf_name, tf_params in fast_timeframes.items():
                klines = fetch_binance_data(f"klines?symbol={symbol}&interval={tf_params['interval']}&limit={tf_params['limit']}")
                if not klines or len(klines) < 2:
                    continue

                quote_volumes = [float(k[7]) for k in klines]
                curr_q_vol = quote_volumes[-1]
                avg_q_vol = sum(quote_volumes[:-1]) / len(quote_volumes[:-1]) if len(quote_volumes) > 1 else 1.0

                ratios[tf_name] = (curr_q_vol / avg_q_vol) if avg_q_vol > 0 else 1.0

                buy_vol_quote = float(klines[-1][10])
                deltas[tf_name] = buy_vol_quote - (curr_q_vol - buy_vol_quote)
                current_price = float(klines[-1][4])

            if "1m" not in deltas or "5m" not in deltas or "15m" not in deltas:
                continue

            is_bullish = deltas["1m"] > 0 and deltas["5m"] > 0
            raw_score = (ratios["1m"] * 0.5) + (ratios["5m"] * 0.3) + (ratios["15m"] * 0.2)
            momentum_score = raw_score * (1.5 if is_bullish else 0.3)

            screener_data.append({
                "الرمز": symbol,
                "الزخم المركب": round(momentum_score, 2),
                "الحالة": "🟢 شراء" if is_bullish else "🔴 بيع",
                "Delta 1m ($)": round(deltas["1m"], 2),
                "Delta 5m ($)": round(deltas["5m"], 2),
                "Delta 15m ($)": round(deltas["15m"], 2),
                "زخم 1m": f"{round(ratios['1m'], 1)}x",
                "زخم 5m": f"{round(ratios['5m'], 1)}x",
                "زخم 15m": f"{round(ratios['15m'], 1)}x",
                "السعر": current_price,
                "الشارت": f"https://www.tradingview.com/chart/?symbol=BINANCE:{symbol}"
            })
        except Exception:
            continue

    df = pd.DataFrame(screener_data)
    return df.sort_values(by="الزخم المركب", ascending=False) if not df.empty else df

all_symbols = get_all_spot_symbols()
df_screener = run_full_spot_screener(all_symbols, min_vol)

if not df_screener.empty:
    bullish_df = df_screener[df_screener["الحالة"] == "🟢 شراء"]
    
    # 1. كروت المؤشرات العلوية (KPI Metrics)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("إجمالي العملات المفحوصة", len(df_screener))
    col2.metric("فرص الشراء الحالية", len(bullish_df))
    
    top_coin = bullish_df.iloc[0]["الرمز"] if not bullish_df.empty else "N/A"
    top_score = bullish_df.iloc[0]["الزخم المركب"] if not bullish_df.empty else 0
    col3.metric("أعلى عملة زخماً", top_coin, f"{top_score}x")
    col4.metric("حالة النظام", "نشط ⚡", f"تحديث كل {refresh_interval}s")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. التبويبات المنسقة
    tab1, tab2, tab3 = st.tabs(["🔥 أقوى الفرص (Live Terminal)", "📊 الرسم البياني للزخم", "📋 الجدول الكامل"])

    with tab1:
        if not bullish_df.empty:
            top_15 = bullish_df.head(15)
            
            if st.button("📲 إرسال Top 5 لـ Telegram"):
                top_5 = top_15.head(5)
                msg = "🚀 *أعلى 5 عملات بها زخم شراء حقيقي*\n\n"
                for _, r in top_5.iterrows():
                    msg += f"• *{r['الرمز']}* | زخم: `{r['الزخم المركب']}x` | Delta 5m: `${r['Delta 5m ($)']}` | [📈 فتح الشارت]({r['الشارت']})\n"
                send_telegram_msg(bot_token, chat_id, msg)

            st.dataframe(
                top_15,
                column_config={
                    "الشارت": st.column_config.LinkColumn("الشارت", display_text="📈 Opening Chart"),
                    "الزخم المركب": st.column_config.ProgressColumn("مؤشر الزخم", format="%.2f", min_value=0, max_value=float(df_screener["الزخم المركب"].max())),
                    "Delta 5m ($)": st.column_config.NumberColumn("Delta 5m", format="$%.2f")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("لا توجد عملات بزخم إيجابي حالياً.")

    with tab2:
        if not bullish_df.empty:
            fig = px.bar(
                bullish_df.head(15), 
                x="الرمز", 
                y="الزخم المركب", 
                color="Delta 5m ($)",
                color_continuous_scale="G10",
                title="مقارنة الزخم للعملات الأعلى إيجابية"
            )
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.dataframe(df_screener, hide_index=True, use_container_width=True)

else:
    st.info("جاري الاتصال والتحليل...")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
