import streamlit as st
import pandas as pd
from binance.client import Client
import plotly.express as px
import requests

st.set_page_config(page_title="Binance Spot Momentum", layout="wide", page_icon="⚡")
st.title("⚡ ماسح زخم السيولة الحقيقية (Volume Delta) - Binance Spot")

STABLECOINS = {
    "USDC", "BUSD", "FDUSD", "TUSD", "DAI", "USDP", "EUR", "GBP", 
    "AEUR", "EURI", "USDS", "WBTC", "WEETH", "USDE"
}

# حل مشكلة الحظر الجغرافي للسيرفرات الأمريكية بطلب البيانات المباشرة
@st.cache_resource
def init_binance_client():
    try:
        # المحاولة الأولى باستخدام TLD vision
        return Client(tld='vision')
    except Exception:
        # المحاولة الثانية بدون ping أولي
        c = Client()
        c.API_URL = 'https://api1.binance.com/api'
        return c

client = init_binance_client()

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

@st.cache_data(ttl=3600)
def get_all_spot_symbols():
    try:
        info = client.get_exchange_info()
        symbols = []
        for s in info['symbols']:
            if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING' and s['isSpotTradingAllowed']:
                if s['baseAsset'] not in STABLECOINS:
                    symbols.append(s['symbol'])
        return symbols
    except Exception:
        # حل بديل مباشر عبر API المباشر في حال تعذر المكتبة
        res = requests.get("https://api.binance.com/api/v3/exchangeInfo").json()
        symbols = []
        for s in res['symbols']:
            if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING' and s['isSpotTradingAllowed']:
                if s['baseAsset'] not in STABLECOINS:
                    symbols.append(s['symbol'])
        return symbols

fast_timeframes = {
    "1m":  {"interval": Client.KLINE_INTERVAL_1MINUTE,  "limit": 30},
    "5m":  {"interval": Client.KLINE_INTERVAL_5MINUTE,  "limit": 24},
    "15m": {"interval": Client.KLINE_INTERVAL_15MINUTE, "limit": 20}
}

@st.cache_data(ttl=30)
def run_full_spot_screener(symbols_list, min_volume_filter):
    screener_data = []

    for symbol in symbols_list:
        try:
            klines_1m = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=30)
            q_vol_1m = [float(k[7]) for k in klines_1m]
            if sum(q_vol_1m) < min_volume_filter:
                continue

            ratios, volumes, deltas = {}, {}, {}
            current_price = float(klines_1m[-1][4])

            for tf_name, tf_params in fast_timeframes.items():
                klines = klines_1m if tf_name == "1m" else client.get_klines(symbol=symbol, interval=tf_params["interval"], limit=tf_params["limit"])
                quote_volumes = [float(k[7]) for k in klines]
                curr_q_vol = quote_volumes[-1]
                avg_q_vol = sum(quote_volumes[:-1]) / len(quote_volumes[:-1]) if len(quote_volumes) > 1 else 1.0
                
                vol_ratio = (curr_q_vol / avg_q_vol) if avg_q_vol > 0 else 1.0
                ratios[tf_name] = vol_ratio
                volumes[tf_name] = curr_q_vol

                buy_vol_quote = float(klines[-1][10])
                deltas[tf_name] = buy_vol_quote - (curr_q_vol - buy_vol_quote)

            is_bullish = deltas["1m"] > 0 and deltas["5m"] > 0
            raw_score = (ratios["1m"] * 0.5) + (ratios["5m"] * 0.3) + (ratios["15m"] * 0.2)
            momentum_score = raw_score * 1.5 if is_bullish else raw_score * 0.2

            screener_data.append({
                "رابط الشارت": f"https://www.tradingview.com/chart/?symbol=BINANCE:{symbol}",
                "العملة": symbol,
                "درجة الزخم": round(momentum_score, 2),
                "نوع السيولة": "🟢 شراء حقيقي" if is_bullish else "🔴 بيع/تصريف",
                "Delta 1m ($)": round(deltas["1m"], 2),
                "Delta 5m ($)": round(deltas["5m"], 2),
                "السعر الحالي": current_price,
                "إجمالي السيولة ($)": round(sum(volumes.values()), 2)
            })
        except Exception:
            continue

    df = pd.DataFrame(screener_data)
    return df.sort_values(by="درجة الزخم", ascending=False) if not df.empty else df

st.sidebar.header("⚙️ الإعدادات والتنبيهات")
all_symbols = get_all_spot_symbols()
st.sidebar.success(f"تم تحميل {len(all_symbols)} عملة سبوت")

bot_token = st.sidebar.text_input("Bot Token", type="password")
chat_id = st.sidebar.text_input("Chat ID")
min_vol = st.sidebar.number_input("حد أدنى للسيولة ($)", value=5000, step=1000)

if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()

df_screener = run_full_spot_screener(all_symbols, min_vol)

if not df_screener.empty:
    df_screener = df_screener[df_screener["نوع السيولة"] == "🟢 شراء حقيقي"]

tab1, tab2 = st.tabs(["🔥 أعلى 20 عملة زخماً", "📊 كل العملات"])

with tab1:
    if not df_screener.empty:
        top_20 = df_screener.head(20)
        if st.button("📲 إرسال Top 5 لـ Telegram"):
            top_5 = top_20.head(5)
            msg = "🚀 *أعلى 5 عملات بها زخم شراء حقيقي*\n\n"
            for _, r in top_5.iterrows():
                msg += f"• *{r['العملة']}* | زخم: `{r['درجة الزخم']}x` | [📈 الشارت]({r['رابط الشارت']})\n"
            send_telegram_msg(bot_token, chat_id, msg)

        st.plotly_chart(px.bar(top_20, x="العملة", y="درجة الزخم", color="Delta 1m ($)", title="الزخم وصافي الشراء"), use_container_width=True)
        st.dataframe(top_20, column_config={"رابط الشارت": st.column_config.LinkColumn("الشارت", display_text="📈 فتح")}, hide_index=True, use_container_width=True)

with tab2:
    if not df_screener.empty:
        st.dataframe(df_screener, column_config={"رابط الشارت": st.column_config.LinkColumn("الشارت", display_text="📈 فتح")}, hide_index=True, use_container_width=True)
