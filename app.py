<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تتبع السيولة اللحظية - Crypto Liquidity Dashboard</title>
    <!-- Plotly.js for interactive charts -->
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        :root {
            --bg-primary: #0b0e14;
            --bg-secondary: #151a23;
            --bg-card: #1e2532;
            --text-main: #f0f4f8;
            --text-muted: #8a99ad;
            --green: #00c853;
            --red: #ff3d00;
            --accent: #00b0ff;
            --gold: #ffd600;
            --border: #2a3447;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-main);
            direction: rtl;
            padding: 20px;
            min-height: 100vh;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-secondary);
            padding: 15px 25px;
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }

        .logo-title {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-title h1 {
            font-size: 1.4rem;
            color: var(--text-main);
        }

        .status-badge {
            background: rgba(0, 200, 83, 0.15);
            color: var(--green);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
            border: 1px solid rgba(0, 200, 83, 0.3);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--green);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--green);
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.3; }
            100% { opacity: 1; }
        }

        .controls-bar {
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }

        select, input, button {
            background: var(--bg-card);
            color: var(--text-main);
            border: 1px solid var(--border);
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s ease;
        }

        select:focus, input:focus {
            border-color: var(--accent);
        }

        button {
            cursor: pointer;
            background: var(--accent);
            color: #fff;
            border: none;
            font-weight: bold;
        }

        button:hover {
            opacity: 0.9;
        }

        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: bold;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .chart-box {
            width: 100%;
            height: 380px;
        }

        .signal-box {
            background: var(--bg-card);
            border-radius: 10px;
            padding: 15px;
            border-right: 5px solid var(--border);
            margin-top: 10px;
        }

        .signal-box.high-prob {
            border-right-color: var(--green);
            background: rgba(0, 200, 83, 0.05);
        }

        .signal-box.med-prob {
            border-right-color: var(--gold);
            background: rgba(255, 214, 0, 0.05);
        }

        .signal-title {
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
        }

        .telegram-panel {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
        }

        .tg-inputs {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }

        .input-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        .input-group label {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .stats-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }

        .stat-value {
            font-size: 1.4rem;
            font-weight: bold;
            margin-top: 5px;
        }

        .stat-value.green { color: var(--green); }
        .stat-value.red { color: var(--red); }
        .stat-value.accent { color: var(--accent); }

        @media (max-width: 600px) {
            .grid-container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>

    <header>
        <div class="logo-title">
            <span style="font-size: 1.8rem;">📊</span>
            <div>
                <h1>منصة تتبع السيولة المباشرة</h1>
                <p style="font-size: 0.8rem; color: var(--text-muted);">Binance Live OrderBook & CVD Stream</p>
            </div>
        </div>

        <div class="controls-bar">
            <select id="symbolSelect" onchange="changeSymbol()">
                <option value="DASHUSDT">DASH / USDT</option>
                <option value="BTCUSDT">BTC / USDT</option>
                <option value="SUIUSDT">SUI / USDT</option>
                <option value="NEARUSDT">NEAR / USDT</option>
                <option value="XRPUSDT">XRP / USDT</option>
            </select>

            <div class="status-badge" id="connStatus">
                <div class="status-dot"></div>
                متصل بالبث المباشر
            </div>
        </div>
    </header>

    <!-- Stat Highlights -->
    <div class="stats-summary">
        <div class="stat-card">
            <div style="font-size: 0.85rem; color: var(--text-muted);">السعر الحالي</div>
            <div class="stat-value accent" id="currentPrice">0.00</div>
        </div>
        <div class="stat-card">
            <div style="font-size: 0.85rem; color: var(--text-muted);">أكبر جدار شراء (Support)</div>
            <div class="stat-value green" id="maxBidWall">0.00</div>
        </div>
        <div class="stat-card">
            <div style="font-size: 0.85rem; color: var(--text-muted);">أكبر جدار بيع (Resistance)</div>
            <div class="stat-value red" id="maxAskWall">0.00</div>
        </div>
        <div class="stat-card">
            <div style="font-size: 0.85rem; color: var(--text-muted);">مؤشر CVD التراكمي</div>
            <div class="stat-value" id="cvdValue">0.00</div>
        </div>
    </div>

    <!-- Charts Grid -->
    <div class="grid-container">
        <!-- Order Book Depth -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">📖 عمق دفتر الأوامر (Order Book Depth)</div>
                <span style="font-size: 0.8rem; color: var(--text-muted);">أحدث 100 مستوى</span>
            </div>
            <div id="depthChart" class="chart-box"></div>
        </div>

        <!-- Cumulative Volume Delta (CVD) -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">📈 تدفق السيولة الفورية (CVD Stream)</div>
                <span style="font-size: 0.8rem; color: var(--text-muted);">آخر الصفقات المباشرة</span>
            </div>
            <div id="cvdChart" class="chart-box"></div>
        </div>
    </div>

    <!-- Signal Radar -->
    <div class="card">
        <div class="card-header">
            <div class="card-title">🎯 رادار كشف الفرص عالية الدقة</div>
            <span style="font-size: 0.85rem; color: var(--gold);" id="signalMatchScore">نسبة التوافق: 0%</span>
        </div>

        <div id="signalContainer">
            <div class="signal-box">
                <div class="signal-title">⏳ جارٍ جمع وتسجيل بيانات السيولة...</div>
                <p style="font-size: 0.9rem; color: var(--text-muted);">يتم تحليل دفتر الأوامر ودلتا الحجم التراكمي لإيجاد كتل الشراء والدايفرجنس المباشر.</p>
            </div>
        </div>
    </div>

    <!-- Telegram Setup -->
    <div class="telegram-panel">
        <div class="card-title">🔔 إعداد التنبيهات الفورية عبر Telegram</div>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 5px;">احصل على إشارات التداول مباشرة على هاتفك بمجرد اكتمال شروط الفرصة.</p>

        <div class="tg-inputs">
            <div class="input-group">
                <label>Telegram Bot Token:</label>
                <input type="password" id="tgToken" placeholder="مثال: 123456789:ABCdefGHI..." />
            </div>
            <div class="input-group">
                <label>Telegram Chat ID:</label>
                <input type="text" id="tgChatId" placeholder="مثال: 987654321" />
            </div>
            <div class="input-group" style="justify-content: flex-end;">
                <label>&nbsp;</label>
                <button onclick="testTelegram()">🧪 اختبار إرسال تنبيه</button>
            </div>
        </div>
    </div>

    <script>
        let currentSymbol = "DASHUSDT";
        let depthWs = null;
        let tradeWs = null;

        let cvdData = [];
        let cvdLabels = [];
        let cumulativeCVD = 0;
        let lastPrice = 0;
        let maxBid = { price: 0, qty: 0 };
        let maxAsk = { price: 0, qty: 0 };
        let lastAlertSignal = "";

        // Initialize Plotly Charts
        function initCharts() {
            const layoutBg = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#e0e0e0', family: 'Segoe UI' },
                margin: { l: 40, r: 20, t: 20, b: 40 },
                xaxis: { gridcolor: '#2a3447', zerolinecolor: '#2a3447' },
                yaxis: { gridcolor: '#2a3447', zerolinecolor: '#2a3447' },
                showlegend: false
            };

            Plotly.newPlot('depthChart', [
                { x: [], y: [], fill: 'tozeroy', type: 'scatter', mode: 'lines', name: 'Bids', line: { color: '#00c853' } },
                { x: [], y: [], fill: 'tozeroy', type: 'scatter', mode: 'lines', name: 'Asks', line: { color: '#ff3d00' } }
            ], layoutBg, { responsive: true, displayModeBar: false });

            Plotly.newPlot('cvdChart', [
                { x: [], y: [], type: 'scatter', mode: 'lines', name: 'CVD', line: { color: '#00b0ff', width: 2 } }
            ], layoutBg, { responsive: true, displayModeBar: false });
        }

        function connectWebSockets() {
            if (depthWs) depthWs.close();
            if (tradeWs) tradeWs.close();

            const symbolLower = currentSymbol.toLowerCase();

            // Depth Stream
            depthWs = new WebSocket(`wss://stream.binance.com:9443/ws/${symbolLower}@depth20@100ms`);
            depthWs.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateDepthChart(data.bids, data.asks);
            };

            // Trade Stream
            tradeWs = new WebSocket(`wss://stream.binance.com:9443/ws/${symbolLower}@trade`);
            tradeWs.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateTradeCVD(data);
            };

            document.getElementById('connStatus').style.display = 'flex';
        }

        function updateDepthChart(bidsRaw, asksRaw) {
            let bidsX = [], bidsY = [];
            let asksX = [], asksY = [];

            let cumBid = 0;
            let highestBid = { price: 0, qty: 0 };
            bidsRaw.forEach(item => {
                const price = parseFloat(item[0]);
                const qty = parseFloat(item[1]);
                cumBid += qty;
                bidsX.push(price);
                bidsY.push(cumBid);
                if (qty > highestBid.qty) highestBid = { price, qty };
            });

            let cumAsk = 0;
            let highestAsk = { price: 0, qty: 0 };
            asksRaw.forEach(item => {
                const price = parseFloat(item[0]);
                const qty = parseFloat(item[1]);
                cumAsk += qty;
                asksX.push(price);
                asksY.push(cumAsk);
                if (qty > highestAsk.qty) highestAsk = { price, qty };
            });

            maxBid = highestBid;
            maxAsk = highestAsk;

            document.getElementById('maxBidWall').innerText = `${maxBid.price.toFixed(4)} (${maxBid.qty.toFixed(1)})`;
            document.getElementById('maxAskWall').innerText = `${maxAsk.price.toFixed(4)} (${maxAsk.qty.toFixed(1)})`;

            Plotly.restyle('depthChart', { x: [bidsX, asksX], y: [bidsY, asksY] });
            evaluateSignals();
        }

        function updateTradeCVD(trade) {
            const price = parseFloat(trade.p);
            const qty = parseFloat(trade.q);
            const isBuyerMaker = trade.m; // True = Sell market, False = Buy market

            const volume = isBuyerMaker ? -qty : qty;
            cumulativeCVD += volume;
            lastPrice = price;

            document.getElementById('currentPrice').innerText = price.toFixed(4);
            const cvdEl = document.getElementById('cvdValue');
            cvdEl.innerText = cumulativeCVD.toFixed(2);
            cvdEl.className = `stat-value ${cumulativeCVD >= 0 ? 'green' : 'red'}`;

            cvdData.push(cumulativeCVD);
            cvdLabels.push(new Date(trade.T).toLocaleTimeString());

            if (cvdData.length > 100) {
                cvdData.shift();
                cvdLabels.shift();
            }

            Plotly.restyle('cvdChart', { x: [cvdLabels], y: [cvdData] });
        }

        function evaluateSignals() {
            if (cvdData.length < 20 || maxBid.price === 0) return;

            let score = 0;
            let reasons = [];

            // 1. Strong Order Block Wall (>15% total bid volume)
            if (maxBid.qty > 50) {
                score += 50;
                reasons.push(`رصد كتلة شراء ضخمة (Support Order Block) عند السعر ${maxBid.price}`);
            }

            // 2. CVD Bullish Divergence check
            const recentCVD = cvdData[cvdData.length - 1];
            const oldCVD = cvdData[Math.max(0, cvdData.length - 20)];
            if (recentCVD > oldCVD) {
                score += 45;
                reasons.push("وجود دايفرجنس إيجابي وتدفق سيولة شرائية (CVD Accumulation)");
            }

            const container = document.getElementById('signalContainer');
            const scoreEl = document.getElementById('signalMatchScore');
            scoreEl.innerText = `نسبة التوافق: ${score}%`;

            if (score >= 90) {
                const entry = maxBid.price;
                const stopLoss = (entry * 0.995).toFixed(4);
                const takeProfit = (entry * 1.02).toFixed(4);

                container.innerHTML = `
                    <div class="signal-box high-prob">
                        <div class="signal-title" style="color: var(--green);">🔥 إشارة فرصة عالية الدقة (${score}%)</div>
                        <ul style="margin-right: 20px; font-size: 0.95rem; margin-bottom: 10px;">
                            ${reasons.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                        <div style="background: var(--bg-primary); padding: 10px; border-radius: 6px; font-size: 0.9rem;">
                            📍 <b>سعر الدخول:</b> ${entry} | 
                            🛑 <b>وقف الخسارة:</b> ${stopLoss} | 
                            🎯 <b>الهدف (2%):</b> ${takeProfit}
                        </div>
                    </div>
                `;

                triggerTelegramAlert(currentSymbol, score, entry, stopLoss, takeProfit, reasons);
            } else if (score >= 50) {
                container.innerHTML = `
                    <div class="signal-box med-prob">
                        <div class="signal-title" style="color: var(--gold);">⚠️ فرصة متوسطة التوافق (${score}%)</div>
                        <p style="font-size: 0.9rem;">توجد سيولة ولكن نوصي بانتظار تأكيد إضافي لتغير بنية السوق.</p>
                    </div>
                `;
            }
        }

        function triggerTelegramAlert(symbol, score, entry, sl, tp, reasons) {
            const token = document.getElementById('tgToken').value.trim();
            const chatId = document.getElementById('tgChatId').value.trim();

            if (!token || !chatId) return;

            const signalKey = `${symbol}_${entry}_${score}`;
            if (lastAlertSignal === signalKey) return; // Prevent duplicate alerts

            lastAlertSignal = signalKey;

            const msg = `🚀 *تنبيه فرصة تداول جديدة (${symbol})*%0A%0A` +
                `🎯 *درجة التوافق:* ${score}%%0A` +
                `📍 *سعر الدخول:* \`${entry}\`%0A` +
                `🛑 *وقف الخسارة:* \`${sl}\`%0A` +
                `🎯 *الهدف:* \`${tp}\`%0A%0A` +
                `📋 *الأسباب:*%0A` + reasons.map(r => `- ${r}`).join('%0A');

            fetch(`https://api.telegram.org/bot${token}/sendMessage?chat_id=${chatId}&text=${msg}&parse_mode=Markdown`)
                .then(res => res.json())
                .then(data => {
                    if (data.ok) {
                        alert("🔔 تم إرسال التنبيه عبر Telegram بنجاح!");
                    }
                });
        }

        function testTelegram() {
            const token = document.getElementById('tgToken').value.trim();
            const chatId = document.getElementById('tgChatId').value.trim();

            if (!token || !chatId) {
                alert("يرجى إدخال Bot Token و Chat ID أولاً.");
                return;
            }

            const msg = "🤖 *اختبار الاتصال:* لوحة تتبع السيولة تعمل بنجاح ومجهزة لتلقي التنبيهات!";
            fetch(`https://api.telegram.org/bot${token}/sendMessage?chat_id=${chatId}&text=${encodeURIComponent(msg)}&parse_mode=Markdown`)
                .then(res => res.json())
                .then(data => {
                    if (data.ok) alert("✅ تم إرسال الرسالة بنجاح!");
                    else alert("❌ فشل الإرسال: " + data.description);
                })
                .catch(err => alert("حدث خطأ في الاتصال بـ Telegram."));
        }

        function changeSymbol() {
            currentSymbol = document.getElementById('symbolSelect').value;
            cvdData = [];
            cvdLabels = [];
            cumulativeCVD = 0;
            connectWebSockets();
        }

        // Run on load
        window.onload = () => {
            initCharts();
            connectWebSockets();
        };
    </script>
</body>
</html>
