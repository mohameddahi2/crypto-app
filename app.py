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
                if (qty > highestAsk.qty) highestAsk = { price, qty };هذا الجزء من الكود يمثل **المنطق الخاص بتتبع السيولة، حساب التراكمي الشرائي/البيعي (CVD)، وتوليد التنبيهات** لوحة التحكم (Dashboard) عبر منصة Binance مع التكامل مع Telegram.

تضمن الكود عدة مشاكل وعيوب منطقية وتقنية في إدارة الموارد والأداء. فيما يلي أبرز الملاحظات وتصحيحها:

### 1. المشاكل العالية الخطورة (High Priority Issues)
* **تسريب الذاكرة (Memory Leak) في التنبيهات:** عند إرسال التنبيه التلقائي عبر Telegram في `triggerTelegramAlert` يتم استخدام `fetch` بدون تعامل صحيح مع الأخطاء (Error Handling)، مما قد يتسبب في تعليق المتصفح.
* **استدعاءات مكررة لـ WebSocket دون إغلاق القديم:** في دالة `changeSymbol()`، يتم طلب الاتصال مجدداً `connectWebSockets()` بدون إغلاق الاتصالات المفتوحة سابقاً (`tradeWs.close()`) مما يستهلك الباندويث والذاكرة بشكل متزايد.
* **إعادة رسم الرسم البياني المفرطة (Chart Redraw Thrashing):** يتم استدعاء `Plotly.restyle` مع كل صفقة (Trade) تلقائياً داخل `updateTradeCVD`. إذا كان هناك مئات الصفات في الثانية، سيتسبب هذا في تجمد واجهة المستخدم (UI Freeze).

---

### الكود المصحح والمحسن (Optimized Code)

يمكنك استبدال الجزء البرمجي لديك بالتحديث التالي المحسّن بالكامل:

```javascript
            // Trade Stream
            if (tradeWs) tradeWs.close(); // إغلاق الاتصال القديم لمنع تسريب الذاكرة
            
            tradeWs = new WebSocket(`wss://[stream.binance.com:9443/ws/$](https://stream.binance.com:9443/ws/$){symbolLower}@trade`);
            
            // تحسين الأداء: تقليل عدد مرات إعادة الرسم (Throttling)
            let lastChartUpdate = Date.now();

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
            const isBuyerMaker = trade.m; // True = Market Sell, False = Market Buy

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

            // تحديث الرسم البياني كل 250 ميلي ثانية لتفادي بطء المتصفح
            const now = Date.now();
            if (now - lastChartUpdate > 250) {
                Plotly.restyle('cvdChart', { x: [cvdLabels], y: [cvdData] });
                lastChartUpdate = now;
            }
        }

        function evaluateSignals() {
            if (cvdData.length < 20 || maxBid.price === 0) return;

            let score = 0;
            let reasons = [];

            // 1. Strong Order Block Wall
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

        async function triggerTelegramAlert(symbol, score, entry, sl, tp, reasons) {
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

            try {
                const res = await fetch(`[https://api.telegram.org/bot$](https://api.telegram.org/bot$){token}/sendMessage?chat_id=${chatId}&text=${msg}&parse_mode=Markdown`);
                const data = await res.json();
                if (!data.ok) {
                    console.error("Telegram Alert Failed:", data.description);
                }
            } catch (err) {
                console.error("Network error on sending Telegram alert:", err);
            }
        }

        async function testTelegram() {
            const token = document.getElementById('tgToken').value.trim();
            const chatId = document.getElementById('tgChatId').value.trim();

            if (!token || !chatId) {
                alert("يرجى إدخال Bot Token و Chat ID أولاً.");
                return;
            }

            const msg = "🤖 *اختبار الاتصال:* لوحة تتبع السيولة تعمل بنجاح ومجهزة لتلقي التنبيهات!";
            try {
                const res = await fetch(`[https://api.telegram.org/bot$](https://api.telegram.org/bot$){token}/sendMessage?chat_id=${chatId}&text=${encodeURIComponent(msg)}&parse_mode=Markdown`);
                const data = await res.json();
                if (data.ok) {
                    alert("✅ تم إرسال الرسالة بنجاح!");
                } else {
                    alert("❌ فشل الإرسال: " + data.description);
                }
            } catch (err) {
                alert("حدث خطأ في الاتصال بـ Telegram.");
            }
        }

        function changeSymbol() {
            currentSymbol = document.getElementById('symbolSelect').value;
            cvdData = [];
            cvdLabels = [];
            cumulativeCVD = 0;
            
            // تنظيف الاتصال السابق قبل إعادة التوصيل
            if (tradeWs) tradeWs.close();
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
