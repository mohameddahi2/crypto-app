import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="Binance Spot Momentum", layout="wide", page_icon="⚡")
st.title("⚡ ماسح زخم السيولة الحقيقية (Volume Delta) - Binance Spot")

STABLECOINS = {
    "USDC", "BUSD", "FDUSD", "TUSD", "DAI", "USDP", "EUR", "GBP", 
    "AEUR", "EURI", "USDS", "WBTC", "WEETH", "USDE"
}

# استخدام الخوادم العامة البديلة المتاحة للسيرفرات الأمريكية
BASE_URLS = [
    "https://data-api.binance.vision/api/v3",
    "https://api.binance.com/api/v3",
    "https://api1.binance.com/api/v3",
    "https://api3.binance.com/api/v3"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

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
        return False, "يرجى إدخال Bot Token و Chat ID في الشريط الجانبي."
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=5)
        return (True, "تم الإرسال بنجاح!") if res.status_code == 200 else (False, res.text)
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

@st.cache_data(ttl=30)
def run_full_spot_screener(symbols_list, min_volume_filter):
    screener_data = []

    tickers = fetch_binance_data("ticker/24hr")
    if not tickers:
        return pd.DataFrame()
    
    # فلترة سريعة لأعلى العملات في السيولة خلال 24 ساعة
    ticker_dict = {t['symbol']: float(t['quoteVolume']) for t in tickers if 'quoteVolume' in t}
    valid_symbols = [s for s in symbols_list if s in ticker_dict and ticker_dict[s] >= min_volume_filter]
    
    # رتب العملات وافحص أعلى 60 عملة سيولة لسرعة الاستجابة
    sorted_symbols = sorted(valid_symbols, key=lambda x: ticker_dict[x], reverse=True)[:60]

    for symbol in sorted_symbols:
        try:
            klines_1m = fetch_binance_data(f"klines?symbol={symbol}&interval=1m&limit=15")
            if not klines_1m or len(klines_1m) < 2:
                continue

            q_vol_1m = [float(k[7]) for k in klines_1m]
            curr_q_vol = q_vol_1m[-1]
            avg_q_vol = sum(q_vol_1m[:-1]) / len(q_vol_1m[:-1]) if len(q_vol_1m) > 1 else 1.0

            vol_ratio = (curr_q_vol / avg_q_vol) if avg_q_vol > 0 else 1.0
            
            # حساب Volume Delta (شراء حقيقي)
            buy_vol_quote = float(klines_1m[-1][10])
            delta_1m = buy_vol_quote - (curr_q_vol - buy_vol_quote)
            current_price = float(klines_1m[-1][4])

            is_bullish = delta_1m > 0
            momentum_score = vol_ratio * (1.5 if is_bullish else 0.3)

            screener_data.append({
                "رابط الشارت": f"https://www.tradingview.com/chart/?symbol=BINANCE:{symbol}",
                "العملة": symbol,
                "درجة الزخم": round(momentum_score, 2),
                "نوع السيولة": "🟢 شراء حقيقي" if is_bullish else "🔴 بيع/تصريف",
                "Delta 1m ($)": round(delta_1m, 2),
                "السعر الحالي": current_price,
                "سيولة الدقيقة الحالية ($)": round(curr_q_vol, 2)
            })
        except Exception:
            continue

    df = pd.DataFrame(screener_data)
    return df.sort_values(by="درجة الزخم", ascending=False) if not df.empty else df

st.sidebar.header("⚙️ الإعدادات والتنبيهات")
all_symbols = get_all_spot_symbols()

if all_symbols:
    st.sidebar.success(f"تم تحميل {len(all_symbols)} عملة سبوت")
else:
    st.sidebar.error("جاري إعادة المحاولة مع سيرفرات Binance Vision...")

bot_token = st.sidebar.text_input("Bot Token", type="password")
chat_id = st.sidebar.text_input("Chat ID")
min_vol = st.sidebar.number_input("حد أدنى لسيولة 24 ساعة ($)", value=1000000, step=500000)

if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()

df_screener = run_full_spot_screener(all_symbols, min_vol)

tab1, tab2 = st.tabs(["🔥 أعلى العملات زخماً", "📊 كل العملات"])

with tab1:
    if not df_screener.empty:
        bullish_df = df_screener[df_screener["نوع السيولة"] == "🟢 شراء حقيقي"]
        if not bullish_df.empty:
            top_20 = bullish_df.head(20)
            if st.button("📲 إرسال Top 5 لـ Telegram"):
                top_5 = top_20.head(5)
                msg = "🚀 *أعلى 5 عملات بها زخم شراء حقيقي*\n\n"
                for _, r in top_5.iterrows():
                    msg += f"• *{r['العملة']}* | زخم: `{r['درجة الزخم']}x` | [📈 الشارت]({r['رابط الشارت']})\n"
                send_telegram_msg(bot_token, chat_id, msg)

            st.plotly_chart(px.bar(top_20, x="العملة", y="درجة الزخم", color="Delta 1m ($)", title="الزخم وصافي الشراء"), use_container_width=True)
            st.dataframe(top_20, column_config={"رابط الشارت": st.column_config.LinkColumn("الشارت", display_text="📈 فتح")}, hide_index=True, use_container_width=True)
        else:
            st.info("لا توجد عملات بـ Delta موجب في هذه اللحظة.")
    else:
        st.warning("جاري تحميل البيانات، اضغط '🔄 تحديث البيانات' إن لم تظهر خلال ثوانٍ.")

with tab2:
    if not df_screener.empty:
        st.dataframe(df_screener, column_config={"رابط الشارت": st.column_config.LinkColumn("الشارت", display_text="📈 فتح")}, hide_index=True, use_container_width=True)
