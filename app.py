import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time

st.set_page_config(
    page_title="Binance Spot Terminal",
    layout="wide",
    page_icon="⚡"
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e222d; padding: 12px; border-radius: 8px; border: 1px solid #2a2e39; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e222d; border-radius: 6px; padding: 8px 16px; color: #d1d4dc; }
    .stTabs [aria-selected="true"] { background-color: #2962ff !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ ماسح السيولة والزخم السريع - Binance Spot")

STABLECOINS = {
    "USDC", "BUSD", "FDUSD", "TUSD", "DAI", "USDP", "EUR", "GBP", 
    "AEUR", "EURI", "USDS", "WBTC", "WEETH", "USDE"
}

BASE_URLS = [
    "https://data-api.binance.vision/api/v3",
    "https://api.binance.com/api/v3",
    "https://api1.binance.com/api/v3"
]

HEADERS = {"User-Agent": "Mozilla/5.0"}

# --- الشريط الجانبي ---
st.sidebar.header("⚙️ خيارات الفلترة")
auto_refresh = st.sidebar.checkbox("تفعيل التحديث التلقائي", value=True)
refresh_interval = st.sidebar.slider("معدل التحديث (ثواني)", min_value=10, max_value=60, value=20, step=5)

min_vol = st.sidebar.number_input("حد أدنى لسيولة 24 ساعة ($)", value=200000, step=100000)
show_only_bullish = st.sidebar.checkbox("عرض الشراء الحقيقي فقط (🟢)", value=False)

st.sidebar.markdown("---")
st.sidebar.header("💬 التنبيهات (اختياري)")
bot_token = st.sidebar.text_input("Bot Token", type="password")
chat_id = st.sidebar.text_input("Chat ID")

def fetch_binance_data(endpoint):
    for base in BASE_URLS:
        try:
            res = requests.get(f"{base}/{endpoint}", headers=HEADERS, timeout=3)
            if res.status_code == 200:
                return res.json()
        except Exception:
            continue
    return None

def send_telegram_msg(token, chat_id, message):
    if not token or not chat_id:
        return False, "يرجى إدخال البيانات"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=4)
        return (True, "تم الإرسال!") if res.status_code == 200 else (False, res.text)
    except Exception as e:
        return False, str(e)

@st.cache_data(ttl=1800)
def get_all_spot_symbols():
    data = fetch_binance_data("exchangeInfo")
    if not data or 'symbols' not in data:
        return []
    return [
        s['symbol'] for s in data['symbols'] 
        if s.get('quoteAsset') == 'USDT' 
        and s.get('status') == 'TRADING' 
        and s.get('isSpotTradingAllowed', True)
        and s.get('baseAsset') not in STABLECOINS
    ]

fast_timeframes = {
    "1m":  {"interval": "1m",  "limit": 10},
    "5m":  {"interval": "5m",  "limit": 10},
    "15m": {"interval": "15m", "limit": 6}
}

def run_screener(symbols_list, min_volume):
    tickers = fetch_binance_data("ticker/24hr")
    if not tickers:
        return pd.DataFrame()
    
    ticker_dict = {t['symbol']: float(t['quoteVolume']) for t in tickers if 'quoteVolume' in t}
    valid_symbols = [s for s in symbols_list if s in ticker_dict and ticker_dict[s] >= min_volume]
    sorted_symbols = sorted(valid_symbols, key=lambda x: ticker_dict[x], reverse=True)[:35]

    screener_data = []

    for symbol in sorted_symbols:
        try:
            ratios, deltas = {}, {}
            price = 0.0

            for tf_name, tf_params in fast_timeframes.items():
                klines = fetch_binance_data(f"klines?symbol={symbol}&interval={tf_params['interval']}&limit={tf_params['limit']}")
                if not klines or len(klines) < 2:
                    continue

                quote_vols = [float(k[7]) for k in klines]
                curr_vol = quote_vols[-1]
                avg_vol = sum(quote_vols[:-1]) / len(quote_vols[:-1]) if len(quote_vols) > 1 else 1.0

                ratios[tf_name] = (curr_vol / avg_vol) if avg_vol > 0 else 1.0
                buy_vol = float(klines[-1][10])
                deltas[tf_name] = buy_vol - (curr_vol - buy_vol)
                price = float(klines[-1][4])

            if "1m" not in deltas or "5m" not in deltas:
                continue

            is_bullish = deltas["1m"] > 0 and deltas["5m"] > 0
            score = (ratios.get("1m", 1) * 0.5) + (ratios.get("5m", 1) * 0.3) + (ratios.get("15m", 1) * 0.2)

            screener_data.append({
                "الرمز": symbol,
                "السيولة": "🟢 شراء" if is_bullish else "🔴 بيع",
                "الزخم": float(round(score, 2)),
                "Delta 1m ($)": float(round(deltas.get("1m", 0), 2)),
                "Delta 5m ($)": float(round(deltas.get("5m", 0), 2)),
                "Delta 15m ($)": float(round(deltas.get("15m", 0), 2)),
                "زخم 1m": f"{round(ratios.get('1m', 1), 1)}x",
                "زخم 5m": f"{round(ratios.get('5m', 1), 1)}x",
                "زخم 15m": f"{round(ratios.get('15m', 1), 1)}x",
                "السعر": price,
                "الشارت": f"https://www.tradingview.com/chart/?symbol=BINANCE:{symbol}"
            })
        except Exception:
            continue

    df = pd.DataFrame(screener_data)
    return df.sort_values(by="الزخم", ascending=False) if not df.empty else df

symbols = get_all_spot_symbols()
df = run_screener(symbols, min_vol)

if not df.empty:
    df_display = df[df["السيولة"] == "🟢 شراء"] if show_only_bullish else df

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("إجمالي العملات المفحوصة", len(df))
    c2.metric("فرص الشراء الإيجابي", len(df[df["السيولة"] == "🟢 شراء"]))
    
    top_coin = df_display.iloc[0]["الرمز"] if not df_display.empty else "N/A"
    top_score = df_display.iloc[0]["الزخم"] if not df_display.empty else 0
    c3.metric("أعلى عملة زخماً", top_coin, f"{top_score}x")
    c4.metric("التحديث", "تلقائي ⚡", f"كل {refresh_interval}s")

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔥 الجدول الرئيسي", "📊 رسم الزخم البياني", "📋 كافة البيانات"])

    with tab1:
        if not df_display.empty:
            top_15 = df_display.head(15)
            
            if st.button("📲 إرسال Top 5 لـ Telegram"):
                top_5 = top_15.head(5)
                msg = "🚀 *أعلى 5 عملات بها زخم شراء حقيقي*\n\n"
                for _, r in top_5.iterrows():
                    msg += f"• *{r['الرمز']}* | زخم: `{r['الزخم']}x` | Delta 5m: `${r['Delta 5m ($)']}` | [📈 الشارت]({r['الشارت']})\n"
                send_telegram_msg(bot_token, chat_id, msg)

            st.dataframe(
                top_15,
                column_config={
                    "الشارت": st.column_config.LinkColumn("الشارت", display_text="📈 فتح"),
                    "الزخم": st.column_config.NumberColumn("مؤشر الزخم", format="%.2f"),
                    "السعر": st.column_config.NumberColumn("السعر الحالي", format="$%.4f")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.warning("لا توجد عملات تطابق شرط الشراء الحقيقي حالياً. قم بإلغاء اختيار 'عرض الشراء الحقيقي فقط' من الشريط الجانبي.")

    with tab2:
        if not df_display.empty:
            try:
                # رسم بياني أمن مع حماية متكاملة ضد أخطاء الألوان
                chart_data = df_display.head(15).copy()
                fig = px.bar(
                    chart_data, 
                    x="الرمز", 
                    y="الزخم", 
                    color="Delta 5m ($)",
                    color_continuous_scale="Viridis",
                    title="مقارنة الزخم لأعلى العملات حركة"
                )
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.info("جاري تحديث الرسم البياني...")
        else:
            st.info("لا توجد بيانات كافية لرسم المخطط البياني حالياً.")

    with tab3:
        st.dataframe(df, hide_index=True, use_container_width=True)

else:
    st.info("جاري فحص وجلب البيانات من بينانس...")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
