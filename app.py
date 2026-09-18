import streamlit as st
import streamlit.components.v1 as components

# إعدادات الصفحة لتكون بعرض الشاشة بالكامل
st.set_page_config(
    page_title="Binance Liquidity & CVD Monitor",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# إخفاء الهيدر والقوائم الافتراضية لـ Streamlit لمظهر أكثر احترافية
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding: 0rem !important;}
    </style>
""", unsafe_allow_html=True)

# كود الواجهة الكامل بالـ HTML & JavaScript
html_code = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Liquidity Monitor</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        :root {
            --bg-primary: #121418;
            --bg-secondary: #1e2329;
            --text-main: #eaecef;
            --green: #0ecb81;
            --red: #f6465d;
            --gold: #f0b90b;
            --border: #2b313a;
        }

        body {
            background-color: var(--bg-primary);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 15px;
            box-sizing: border-box;
        }

        .header-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
            justify-content: space-between;
            background: var(--bg-secondary);
            padding: 12px 20px;
            border-radius: 8px;
            border: 1px solid var(--border);
            margin-bottom: 15px;
        }

        .controls {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }

        select, input, button {
            background: var(--bg-primary);
            color: var(--text-main);
            border: 1px solid var(--border);
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.9rem;
            outline: none;
        }

        button {
            background: var(--gold);
            color: #000;
            font-weight: bold;
            cursor: pointer;
            border: none;
        }

        button:hover { opacity: 0.9; }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }

        .stat-card {
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid var(--border);
            text-align: center;
        }

        .stat-title { font-size: 0.85rem; color: #848e9c; margin-bottom: 5px; }
        .stat-value { font-size: 1.2rem; font-weight: bold; }
        .green { color: var(--green); }
        .red { color: var(--red); }

        .charts-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }

        @media (max-width: 900px) {
            .charts-container { grid-template-columns: 1fr; }
        }

        .chart-box {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 10px;
            border: 1px solid var(--border);
            height: 380px;
        }

        .signal-box {
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid var(--border);
            margin-top: 15px;
        }

        .high-prob { border-right: 4px solid var(--green); }
        .med-prob { border-right: 4px solid var(--gold); }
    </style>
</head>
<body>

    <div class="header-bar">
        <div class="controls">
            <label>اختر العملة:</label>
            <select id="symbolSelect" onchange="changeSymbol()">
                <option value="BTCUSDT">BTC/USDT</option>
                <option value="ETHUSDT">ETH/USDT</option>
                <option value="SOLUSDT">SOL/USDT</option>
                <option value="DASHUSDT">DASH/USDT</option>
            </select>
        </div>

        <div class="controls">
            <input type="text" id="tgToken" placeholder="Telegram Bot Token">
            <input type="text" id="tgChatId" placeholder="Telegram Chat ID">
            <button onclick="testTelegram()">اختبار التنبيه</button>
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-title">السعر الحالي</div>
            <div class="stat-value" id="currentPrice">-</div>
        </div>
        <div class="stat-card">
            <div class="stat-title">تراكمي السيولة (CVD)</div>
            <div class="stat-value" id="cvdValue">0.00</div>
        </div>
        <div class="stat-card">
            <div class="stat-title">أكبر حائط شراء (Bid Wall)</div>
            <div class="stat-value green" id="maxBidWall">-</div>
        </div>
        <div class="stat-card">
            <div class="stat-title">أكبر حائط بيع (Ask Wall)</div>
            <div class="stat-value red" id="maxAskWall">-</div>
        </div>
    </div>

    <div class="charts-container">
        <div class="chart-box" id="depthChart"></div>
        <div class="chart-box" id="cvdChart"></div>
    </div>

    <div id="signalContainer"></div>

    <script>
        let currentSymbol = 'BTCUSDT';
        let depthWs = null;
        let tradeWs = null;
        
        let cvdData = [];
        let cvdLabels = [];
        let cumulativeCVD = 0;
        let lastPrice = 0;
        let maxBid = { price: 0, qty: 0 };
        let maxAsk = { price: 0, qty: 0 };
        let lastAlertSignal = '';
        let lastChartUpdate = Date.now();

        function initCharts() {
            const darkLayout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#eaecef' },
                margin: { t: 30, r: 20, l: 40, b: 40 },
                xaxis: { gridcolor: '#2b313a' },
                yaxis: { gridcolor: '#2b313a' }
            };

            Plotly.newPlot('depthChart', [
                { name: 'Bids', x: [], y: [], fill: 'tozeroy', type: 'scatter', mode: 'lines', line: { color: '#0ecb81' } },
                { name: 'Asks', x: [], y: [], fill: 'tozeroy', type: 'scatter', mode: 'lines', line: { color: '#f6465d' } }
            ], { ...darkLayout, title: 'عمق السيولة (Depth Chart)' });

            Plotly.newPlot('cvdChart', [
                { name: 'CVD', x: [], y: [], type: 'scatter', mode: 'lines', line: { color: '#f0b90b', width: 2 } }
            ], { ...darkLayout, title: 'تراكمي حجم التداول (CVD)' });
        }

        function connectWebSockets() {
            const symbolLower = currentSymbol.toLowerCase();

            if (depthWs) depthWs.close();
            if (tradeWs) tradeWs.close();

            // 1. Depth Stream
            depthWs = new WebSocket(`wss://stream.binance.com:9443/ws/${symbolLower}@depth20@100ms`);
            depthWs.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateDepthChart(data.bids, data.asks);
            };

            // 2. Trade Stream
            tradeWs = new WebSocket(`wss://stream.binance.com:9443/ws/${symbolLower}@trade`);
            tradeWs.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateTradeCVD(data);
            };
        }

        function updateDepthChart(bidsRaw, asksRaw) {
            let bidsX = [], bidsY = [], cumBid = 0, highestBid = { price: 0, qty: 0 };
            bidsRaw.forEach(item => {
                const price = parseFloat(item[0]), qty = parseFloat(item[1]);
                cumBid += qty;
                bidsX.push(price); bidsY.push(cumBid);
                if (qty > highestBid.qty) highestBid = { price, qty };
            });

            let asksX = [], asksY = [], cumAsk = 0, highestAsk = { price: 0, qty: 0 };
            asksRaw.forEach(item => {
                const price = parseFloat(item[0]), qty = parseFloat(item[1]);
                cumAsk += qty;
                asksX.push(price); asksY.push(cumAsk);
                if (qty > highestAsk.qty) highestAsk = { price, qty };
            });

            maxBid = highestBid;
            maxAsk = highestAsk;

            document.getElementById('maxBidWall').innerText = `${maxBid.price.toFixed(2)} (${maxBid.qty.toFixed(1)})`;
            document.getElementById('maxAskWall').innerText = `${maxAsk.price.toFixed(2)} (${maxAsk.qty.toFixed(1)})`;

            Plotly.restyle('depthChart', { x: [bidsX, asksX], y: [bidsY, asksY] });
            evaluateSignals();
        }

        function updateTradeCVD(trade) {
            const price = parseFloat(trade.p);
            const qty = parseFloat(trade.q);
            const isBuyerMaker = trade.m; 

            const volume = isBuyerMaker ? -qty : qty;
            cumulativeCVD += volume;

            document.getElementById('currentPrice').innerText = price.toFixed(2);
            const cvdEl = document.getElementById('cvdValue');
            cvdEl.innerText = cumulativeCVD.toFixed(2);
            cvdEl.className = `stat-value ${cumulativeCVD >= 0 ? 'green' : 'red'}`;

            cvdData.push(cumulativeCVD);
            cvdLabels.push(new Date(trade.T).toLocaleTimeString());

            if (cvdData.length > 100) {
                cvdData.shift();
                cvdLabels.shift();
            }

            const now = Date.now();
            if (now - lastChartUpdate > 300) {
                Plotly.restyle('cvdChart', { x: [cvdLabels], y: [cvdData] });
                lastChartUpdate = now;
            }
        }

        function evaluateSignals() {
            if (cvdData.length < 20 || maxBid.price === 0) return;

            let score = 0;
            let reasons = [];

            if (maxBid.qty > 30) {
                score += 50;
                reasons.push(`رصد جدار سيولة شرائية ضخمة عند ${maxBid.price}`);
            }

            const recentCVD = cvdData[cvdData.length - 1];
            const oldCVD = cvdData[Math.max(0, cvdData.length - 20)];
            if (recentCVD > oldCVD) {
                score += 45;
                reasons.push("تراكم سيولة شرائية متزايدة (CVD Bullish Flow)");
            }

            const container = document.getElementById('signalContainer');

            if (score >= 90) {
                const entry = maxBid.price;
                const stopLoss = (entry * 0.995).toFixed(2);
                const takeProfit = (entry * 1.015).toFixed(2);

                container.innerHTML = `
                    <div class="signal-box high-prob">
                        <div style="color: var(--green); font-weight: bold; margin-bottom: 8px;">🔥 إشارة فرصة عالية التوافق (${score}%)</div>
                        <ul style="margin: 0; padding-right: 20px;">${reasons.map(r => `<li>${r}</li>`).join('')}</ul>
                        <div style="margin-top: 10px; font-size: 0.9rem;">
                            <b>دخول:</b> ${entry} | <b>وقف:</b> ${stopLoss} | <b>هدف:</b> ${takeProfit}
                        </div>
                    </div>
                `;

                triggerTelegramAlert(currentSymbol, score, entry, stopLoss, takeProfit, reasons);
            }
        }

        async function triggerTelegramAlert(symbol, score, entry, sl, tp, reasons) {
            const token = document.getElementById('tgToken').value.trim();
            const chatId = document.getElementById('tgChatId').value.trim();

            if (!token || !chatId) return;

            const signalKey = `${symbol}_${entry}_${score}`;
            if (lastAlertSignal === signalKey) return;

            lastAlertSignal = signalKey;

            const msg = `🚀 *تنبيه سيولة جديد (${symbol})*%0A%0A` +
                `🎯 *التوافق:* ${score}%%0A` +
                `📍 *الدخول:* \`${entry}\`%0A` +
                `🛑 *الوقف:* \`${sl}\`%0A` +
                `🎯 *الهدف:* \`${tp}\`%0A%0A` +
                `📋 *الأسباب:*%0A` + reasons.map(r => `- ${r}`).join('%0A');

            try {
                await fetch(`https://api.telegram.org/bot${token}/sendMessage?chat_id=${chatId}&text=${msg}&parse_mode=Markdown`);
            } catch (e) {
                console.error("Telegram error:", e);
            }
        }

        async function testTelegram() {
            const token = document.getElementById('tgToken').value.trim();
            const chatId = document.getElementById('tgChatId').value.trim();

            if (!token || !chatId) {
                alert("يرجى إدخال Bot Token و Chat ID أولاً.");
                return;
            }

            try {
                const res = await fetch(`https://api.telegram.org/bot${token}/sendMessage?chat_id=${chatId}&text=✅ اختبار الاتصال بنجاح!`);
                const data = await res.json();
                if (data.ok) alert("✅ تم الإرسال بنجاح!");
                else alert("❌ فشل الإرسال: " + data.description);
            } catch (err) {
                alert("حدث خطأ أثناء الاتصال بـ Telegram.");
            }
        }

        function changeSymbol() {
            currentSymbol = document.getElementById('symbolSelect').value;
            cvdData = [];
            cvdLabels = [];
            cumulativeCVD = 0;
            connectWebSockets();
        }

        window.onload = () => {
            initCharts();
            connectWebSockets();
        };
    </script>
</body>
</html>
"""

# عرض تطبيق الـ HTML المدمج بأداء عالي داخل Streamlit
components.html(html_code, height=920, scrolling=True)
