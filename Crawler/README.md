# Thu thập dữ liệu TopCV

## Chạy crawler

Yêu cầu Python và Google Chrome.

```powershell
cd Crawler
pip install -r requirements.txt
python scraper.py
```

Mặc định dùng URL đã cấu hình cuối `scraper.py`, duyệt hết phân trang, không giới hạn tin.
Xuất `data/raw/raw_data_YYYYMMDD_HHMMSS.csv` theo thư mục gốc project, dù chạy từ root hay `Crawler/`. Không ghi đè dữ liệu cũ.

Truyền URL khác, đặt trong ngoặc kép để giữ các tham số `&`:

```powershell
python scraper.py --url "https://www.topcv.vn/tim-viec-lam-python" --output raw_python.csv
```

Demo:

```powershell
python scraper.py --max-pages 1 --max-jobs 3 --output demo_topcv.csv
```

Có thể lặp `--url` nhiều lần; khử trùng URL trong cùng lượt chạy.
URL có `page` sẽ bắt đầu tại trang đó. Đọc `rel="next"` / `data-href`, giữ bộ lọc
ban đầu và dừng khi hết trang. Trang lặp hoặc lỗi tải danh sách gây dừng kèm lỗi,
không được coi là đã cào hết. Không bảo đảm đạt 800–1.500 tin: số lượng phụ thuộc nguồn.

## Dữ liệu đối chiếu PDF

| Trường | Nội dung |
| --- | --- |
| `Tieu_De`, `Ten_Cong_Ty` | Tiêu đề và công ty |
| `Muc_Luong_Goc` | Lương hiển thị nguyên văn, gồm “Thoả thuận” |
| `Dia_Diem` | Ưu tiên địa chỉ làm việc chi tiết, dự phòng tóm tắt/card |
| `Kinh_Nghiem` | Kinh nghiệm chuyên môn nguyên văn |
| `Mo_Ta_Cong_Viec` | HTML riêng khối mô tả, không lẫn yêu cầu/quyền lợi |
| `Yeu_Cau` | HTML mục yêu cầu ứng viên, giữ tiêu đề và nội dung bổ sung |
| `Quyen_Loi` | HTML mục quyền lợi, giữ tiêu đề và nội dung bổ sung |
| `Cap_Bac` | Cấp bậc nguyên văn tại “Thông tin chung” |
| `URL_Goc` | URL trực tiếp của tin, bỏ tracking |
| `Timestamp` | Thời điểm lấy tin, ISO 8601 có múi giờ |

CSV mới có 11 cột trên. Không tách khoảng năm kinh nghiệm, không chuẩn hóa lương,
không suy luận cấp bậc và không tạo các cột metadata phụ trong dữ liệu thô.

Nhận diện mục yêu cầu/quyền lợi bằng class cấu trúc TopCV trước, dự phòng tiêu đề
Việt/Anh (`Candidate Requirements`, `Requirements`, `Qualifications`, `Benefits`).
Địa chỉ chi tiết hỗ trợ cả nhãn `Địa điểm làm việc` và `Location`.
Nội dung HTML giữ nguyên ngôn ngữ của bài đăng.

Đây là dữ liệu thô cho bước 2.1: giữ HTML để notebook làm sạch, chuẩn hóa lương,
địa điểm và kỹ năng ở tập sạch riêng. Cột cấp bậc hỗ trợ bước 2.2,
không thay thế toàn bộ EDA/KDD của PDF.

## Lưu trữ và truy cập

CSV dùng UTF-8 BOM, giữ HTML và nội dung nhiều dòng. Lưu sau mỗi tin và khi dừng.
Tin lỗi ghi vào `outputs/logs/<tên-file>.errors.csv` kèm URL, thời gian, lý do.
Trang thiếu mô tả/không đúng giao diện không được lưu thành tin hợp lệ.
Thông tin không có trên nguồn để trống, không tự điền hay suy đoán.

Đọc `robots.txt` trước khi chạy, kiểm tra quyền truy cập URL, chờ ngẫu nhiên,
cuộn kích hoạt lazy loading và đợi DOM. Nếu gặp xác minh, thao tác thủ công trong
Chrome; không bảo đảm vượt được chặn truy cập.

Các CSV cũ vẫn giữ schema gộp `Yeu_Cau_Quyen_Loi`, không tự chuyển đổi hay ghi đè.
Notebook khám phá dữ liệu cũ nằm tại `notebooks/explore_data_legacy.ipynb`.
Các bước xử lý KDD sẽ chạy trong `.ipynb`, không đưa vào scraper.
