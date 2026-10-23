# Fintech Bot — tín hiệu đầu tư cổ phiếu Việt Nam (BT1)

## Phân tích và kế hoạch tham khảo

`/stock MÃ_CỔ_PHIẾU` và alert dùng cùng báo cáo: xu hướng giá/EMA, RSI, RVOL, căn cứ tín hiệu, hỗ trợ/kháng cự và ATR. Chỉ BUY với dữ liệu mới có kịch bản giá: vùng C đến C+0,25 ATR; mốc vô hiệu C−2 ATR; mục tiêu 2R/3R tính từ đầu trên vùng mua. Đây là kịch bản chưa tính phí, trượt giá và giới hạn giá sàn; không phải xác suất thắng hay dự báo. Backtest vẫn kiểm định quy tắc TA gốc, chưa kiểm định các mục tiêu tham khảo này.

SELL dành cho đánh giá thoát vị thế đang giữ; HOLD hiển thị CHỜ. `/signals` chỉ liệt kê tối đa 30 mã có tín hiệu không bị đánh dấu cache/cũ, kèm tổng số và tiến độ. Chart hiển thị thêm hỗ trợ/kháng cự 20 phiên. Bộ kiểm tra sau nâng cấp: 49 bài đạt.

Sản phẩm gồm một FastAPI local dashboard và Telegram long-polling bot. Khi đặt `SSI_CONSUMER_ID` và `SSI_CONSUMER_SECRET`, dữ liệu giao dịch chính lấy từ SSI FastConnect Data (REST + stream `X:ALL`); Chỉ sử dụng SSI; thiếu khóa thì báo lỗi cấu hình. Hệ thống có cache SQLite, kiểm tra schema, retry/backoff và thông báo lỗi rõ ràng.

## Chạy demo

**Muốn chạy khi Mac tắt:** sử dụng bản Docker Compose trên VPS theo [CHAY_24_7.md](docs/CHAY_24_7.md). Bản này có HTTPS, mật khẩu quản trị, volume bền vững và tự khởi động lại. Cần máy chủ thật để kích hoạt; source local không tự tạo hosting.

```bash
cd /Users/nguyenchitinh/Documents/Codex/2026-09-10/tao/outputs/FintechBot
source .venv/bin/activate
python run.py
```

Mở http://127.0.0.1:8010. Với SSI, lần chạy đầu lấy danh sách mã qua `api/v2/Market/SecuritiesDetails (HOSE/HNX/UPCOM; RepeatedInfo; SecType=S)` và dữ liệu OHLC qua `api/v2/Market/DailyOhlc`; giá trong phiên lấy snapshot/stream. Bot quét lại mỗi 15 phút.

## Kết nối Telegram

Mở mục **Kết nối Telegram**, tạo bot bằng `@BotFather` → `/newbot`, nhập token vào biểu mẫu. Mở bot, gửi `/start`, sau đó `/subscribe`. Token chỉ lưu tại `data/telegram.json` với quyền file riêng tư và không nằm trong source code. Bot chạy long polling, chỉ nhận chat riêng, chống gửi trùng theo mã/phiên/hướng.

Các lệnh: `/signals`, `/stock MÃ_CỔ_PHIẾU`, `/fund MÃ_CỔ_PHIẾU`, `/backtest MÃ_CỔ_PHIẾU`, `/chart MÃ_CỔ_PHIẾU`, `/subscribe`, `/unsubscribe`, `/status`, `/help`, `/share`.

## Mời mọi người sử dụng

Sau khi kết nối token, chia sẻ link `https://t.me/<username_bot>`. Mọi người chỉ cần mở link, bấm Start rồi `/subscribe`; không cần token hoặc Chat ID. Mỗi người có trạng thái đăng ký riêng. `/share` trả link mời; menu nhanh cung cấp các lệnh chính. Chủ bot giữ dashboard trên localhost. Bot chỉ trả lời khi máy chạy dịch vụ còn hoạt động và có mạng; muốn liên tục 24/7 cần máy chủ luôn bật.

## Kiến trúc

`SSI FastConnect REST/stream → ssi_provider.py (Bearer, chuẩn hóa, cache) → strategy.py (EMA/RSI/RVOL) → engine.py (quét toàn thị trường) → app.py (REST/UI) và bot.py (Telegram)`. Chỉ dùng dữ liệu và cache SSI.

### Bật SSI

Từ file `config.py` và SDK bạn cung cấp, tạo `.env` trong thư mục chạy và đặt `SSI_CONSUMER_ID`, `SSI_CONSUMER_SECRET`, sau đó nạp biến trước khi chạy: `set -a; source .env; set +a`. Không chép file `.env` vào ZIP. Cài `ssi-fc-data==2.2.2`; SDK tự lấy Bearer từ `api/v2/Market/AccessToken`. Stream dùng `MarketDataStream(...).start(..., 'X:ALL')`. Fintech Bot chỉ gọi market data, không có code đặt lệnh.

Ứng dụng bind `127.0.0.1` ở chế độ local; Docker hỗ trợ triển khai máy chủ theo tài liệu 24/7. SQLite dùng WAL. OHLCV lấy trực tiếp từ SSI DailyOhlc, quyết định dùng phiên đã đóng.

### Kiểm tra bản chỉ dùng SSI (10/09/2026)

- 47 bài kiểm tra tự động đạt.
- API thật trả danh sách 1.813 cổ phiếu qua SecuritiesDetails; chỉ nhận SecType=S.
- Đã kiểm tra 308 phiên lịch sử, giá intraday lúc 14:45 ngày 10/09, phân tích TA, backtest 6 tháng và tạo PNG chart trên dữ liệu SSI.
- Chưa xác nhận hoàn tất một lượt quét toàn bộ 1.813 mã hoặc triển khai VPS. Kết quả từng mã phụ thuộc dữ liệu SSI có sẵn.
- BCTC chưa có nguồn SSI được tích hợp: /fund hiển thị thiếu dữ liệu; bộ lọc cơ bản không phát BUY từ số liệu thiếu. Chiến lược TA vẫn hoạt động.
- Chỉ đọc cache có khóa market:ssi:; cache nguồn cũ không được sử dụng.

## Lệnh ảnh biểu đồ

`/chart MÃ_CỔ_PHIẾU` gửi ảnh PNG của mã người dùng nhập. Ảnh gồm 80 phiên đóng cửa điều chỉnh, EMA20/EMA50, khối lượng và ô giá gần nhất được yêu cầu mới từ SSI FastConnect mỗi lần gọi. Giá gần nhất chưa điều chỉnh được hiển thị riêng để không trộn với lịch sử điều chỉnh. Cả ảnh và caption ghi thời điểm nguồn, thời điểm lấy ảnh, cảnh báo cache/độ trễ nếu có.

Đây là ảnh chụp theo yêu cầu của chart ngày kèm giá mới nhất, không phải chuỗi nến realtime trong phiên và không tự cập nhật sau khi gửi. Nếu SSI không trả quote hợp lệ, bot vẫn gửi chart lịch sử và ghi rõ chưa lấy được giá mới nhất. Dùng lại lệnh để lấy ảnh mới.

Có thể thử tại tab Kết nối Telegram trên dashboard, chưa cần gửi tin thật. Sau cập nhật cần cài lại `requirements.txt` rồi khởi động lại dịch vụ; bản VPS chạy `docker compose up -d --build`. Menu lệnh được đồng bộ khi bot khởi động.

Gửi ảnh dùng Telegram [sendPhoto](https://core.telegram.org/bots/api#sendphoto).

## Giả định backtest

`/backtest MÃ_CỔ_PHIẾU` dùng vốn 100 triệu, lô 100, mua ở open phiên sau, phí 0,15% mỗi chiều, thuế bán 0,1%, trượt giá 0,1%, khóa bán 3 phiên. Có warm-up 60 phiên, chỉ mô phỏng long-only và định giá vị thế cuối kỳ theo close. Kết quả là mô phỏng giáo dục, không phải cam kết lợi nhuận.

## Kiểm thử

```bash
cd /Users/nguyenchitinh/Documents/Codex/2026-09-10/tao/outputs/FintechBot
.venv/bin/python -m pytest -q
```

38 bài kiểm tra bao phủ chỉ báo nhân quả, RSI, backtest, cache, chống gửi trùng, xác thực mã, đăng nhập quản trị, chặn sai nguồn, định dạng ảnh PNG, giá được lấy mới mỗi lần gọi và upload ảnh Telegram bằng API giả lập. Đã kiểm tra ảnh với dữ liệu provider mô phỏng; chưa kiểm thử gửi ảnh tới tài khoản Telegram thật.

## Hạn chế dữ liệu

SSI có thể giới hạn tốc độ hoặc mất kết nối stream. Bot không bypass CAPTCHA/IP block và không tắt kiểm tra TLS; nó retry rồi dùng bản cache gần nhất, đánh dấu `cached/stale`, đồng thời không phát alert mới từ dữ liệu cũ. Khi nộp bài, có thể chụp màn hình dashboard và phần backtest làm minh chứng demo.
