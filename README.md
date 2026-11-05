# ShopMate AI Backend

Backend FastAPI của ShopMate AI. Hướng dẫn chạy cùng frontend nằm trong README của `shopmate-ai-frontend`.

## Thông báo Telegram

Backend gửi vào một group Telegram khi có khách vào web và khi có lượt chat. Để trống `TELEGRAM_BOT_TOKEN` hoặc `TELEGRAM_CHAT_ID` thì tính năng này tắt.

### Cài đặt

1. Nhắn `/newbot` cho `@BotFather` và lấy token.
2. Thêm bot vào group.
3. Trong group, gửi `/start@ten_bot_cua_ban`.
4. Mở `https://api.telegram.org/bot<TOKEN>/getUpdates` và lấy `message.chat.id`. ID của group là số âm.
5. Điền vào `.env`, rồi restart backend:

```dotenv
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Token là secret: không commit, không đặt ở frontend. Nếu lộ, hãy thu hồi bằng `/revoke` với `@BotFather`.

### Nội dung được gửi

- **Khách vào web:** mã khách, trang đầu tiên, nguồn truy cập, trình duyệt và hệ điều hành. Mỗi IP báo tối đa một lần trong `SESSION_NOTICE_INTERVAL_SECONDS`.
- **Chat:** mã khách, câu hỏi và câu trả lời cắt còn 300 ký tự, tool đã dùng, thời gian xử lý. Email và các số từ 9 chữ số trở lên được che trước khi gửi. IP không được gửi; mã khách là 6 ký tự đầu của hash IP. Việc che này chỉ theo mẫu, nên tên hoặc địa chỉ nhà vẫn có thể lọt.

### Giới hạn

- Gửi tối đa khoảng 15 tin mỗi phút. Khi quá tải, thông báo khách vào web bị bỏ trước và group nhận một tin báo số lượng đã bỏ.
- Hàng đợi nằm trong bộ nhớ, nên restart server sẽ mất các tin chưa gửi.
- Khách có thể không được báo nếu trình duyệt chặn request, và ai cũng có thể gọi API để tạo lượt giả. Đây là thông báo theo dõi, không phải số liệu thống kê.

### Deploy sau proxy

Đặt `FORWARDED_ALLOW_IPS` thành dải IP của proxy. Nếu không, mã khách và mọi rate limit sẽ dựa trên IP của proxy thay vì IP của khách. Không đặt `*`, vì khi đó khách có thể tự khai IP giả.
