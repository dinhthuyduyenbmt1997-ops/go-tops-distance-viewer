# GO! + TOPS Distance Viewer

App siêu gọn chỉ dùng để tra khoảng cách nội bộ giữa các store GO! / TOPS.

## Chạy local

1. Chạy `install_once.bat` một lần.
2. Chạy `start_local.bat`.
3. Mở `http://localhost:8511`.

## Deploy thành link cố định bằng Streamlit Community Cloud

### Bước 1 — Tạo repository GitHub

Tạo một repository mới, ví dụ:

`go-tops-distance-viewer`

Upload toàn bộ nội dung folder này lên repository, giữ nguyên:

- `app.py`
- `requirements.txt`
- `data/our_store_master_go_tops.csv`
- `.streamlit/config.toml`

### Bước 2 — Deploy

Vào Streamlit Community Cloud:

`https://share.streamlit.io`

Chọn **Create app** / **Deploy an app**, sau đó:

- Repository: repository vừa tạo
- Branch: `main`
- Main file path: `app.py`

Bấm Deploy.

Sau khi deploy, Streamlit tạo một link dạng:

`https://go-tops-distance-viewer.streamlit.app`

Gửi link đó cho sếp/team. Người xem chỉ cần trình duyệt.

## Cách dùng

- Chọn **Điểm đi**
- Chọn **Điểm đến**
- App tự hiện:
  - quãng đường lái xe,
  - thời gian ước tính,
  - tuyến đường trên bản đồ.

## Master

Master được lấy từ file nội bộ hiện tại:

- GO!
- TOPS
- GO! Đan Phượng đã dùng tọa độ `21.095398, 105.6869687`.

## Lưu ý về khoảng cách

App dùng dịch vụ routing công cộng OSRM trên dữ liệu OpenStreetMap.

Vì vậy:
- không cần Google Maps API,
- không cần Billing,
- kết quả có thể khác Google Maps,
- dịch vụ public có thể đôi lúc chậm hoặc tạm thời quá tải.

App chọn tuyến có quãng đường ngắn nhất trong các alternative routes mà OSRM trả về.
