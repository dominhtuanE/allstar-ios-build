# Allstar Warrior – build iOS (server riêng)

Repo này **chỉ chứa script build** (không có dữ liệu game, không có IP server). GitHub Actions dùng máy Mac miễn phí
để build “IPA khung”: engine Cocos Creator **2.4.2** (JSB) + vài bản vá. Dữ liệu game được ghép vào trên máy Windows.

## Bản vá (ci/patch.py)
- `FileUtils::getPathForFilename`: không thấy file → thử tên bỏ đuôi (tài nguyên gốc của game bị bỏ đuôi; trừ `.jsc`).
- `AppController`: mọi lệnh native `xxx:` của SDK gốc → trả `"{}"` (không có SDK trên bản này).
- Màn hình dọc, tên “Allstar Warrior”, cho phép http/ws không mã hoá (server riêng), bỏ yêu cầu opengles-1.

## Các bước
1. **Tạo repo GitHub** (để *Public* thì dùng máy Mac miễn phí không giới hạn; Private có 2000 phút/tháng, máy Mac tính x10).
   Đẩy nội dung thư mục `ios_build/` lên nhánh `main`.
2. Vào tab **Actions → build-ios-shell → Run workflow**. Đợi ~20–40 phút.
   - Thành công: tải artifact **allstar-ios-shell** (file `.zip` chứa `AllstarShell.ipa`).
   - Thất bại: tải artifact **build-log** gửi lại để sửa.
3. Trên Windows (thư mục `allstar_warrior`):
   ```
   python tools/build_ipa.py <đường dẫn allstar-ios-shell.zip> <IP server> 8910
   ```
   → `dist/AllstarWarrior_private.ipa` (~3 GB).
4. **Cài lên iPhone bằng Sideloadly** (Windows): cài iTunes + iCloud bản tải từ trang Apple (không dùng bản Microsoft Store),
   cắm iPhone, kéo file IPA vào Sideloadly, đăng nhập Apple ID → Start.
   - iPhone: *Cài đặt → Cài đặt chung → VPN & Quản lý thiết bị* → tin cậy Apple ID của bạn.
   - iOS 16 trở lên: bật *Cài đặt → Quyền riêng tư & Bảo mật → Chế độ nhà phát triển*.
   - Apple ID miễn phí: app hết hạn sau **7 ngày** → mở Sideloadly cài lại (giữ nguyên dữ liệu nếu cùng bundle id).
5. iPhone và máy chạy server phải cùng mạng Wi-Fi (hoặc dùng IP VPS). Lần đầu mở, iOS hỏi quyền “mạng cục bộ” → Cho phép.
