# Thu thập dữ liệu TopCV

## Chạy crawler

Yêu cầu Python và Google Chrome.

```powershell
cd Crawler
pip install -r requirements.txt
python scraper.py
```

Mặc định dùng URL đã cấu hình cuối `scraper.py`, duyệt hết phân trang, không giới hạn tin.
Xuất `raw_data_YYYYMMDD_HHMMSS.csv`, không ghi đè CSV đã tồn tại và không sửa dữ liệu cũ.

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
| `Kinh_Nghiem_Min`, `Kinh_Nghiem_Max` | Cận năm kinh nghiệm; tháng chia 12; cận không rõ để trống |
| `Mo_Ta_Cong_Viec` | HTML riêng khối mô tả, không lẫn yêu cầu/quyền lợi |
| `Yeu_Cau`, `Quyen_Loi` | HTML riêng từng mục, kèm tag yêu cầu/phúc lợi bổ sung |
| `Yeu_Cau_Quyen_Loi` | Hai mục trên ghép lại, giữ HTML |
| `Cap_Bac` | Cấp bậc nguyên văn tại “Thông tin chung” |
| `Cap_Bac_Chuan`, `Nguon_Cap_Bac_Chuan` | Fresher/Junior/Middle/Senior/Lead từ nhãn rõ ràng ở cấp bậc/tiêu đề; ghi nguồn suy luận |
| `Kinh_Nghiem_Quan_Ly`, `Hinh_Thuc`, `Loai_Hinh` | Kinh nghiệm quản lý, hình thức và loại hình làm việc |
| `URL_Goc`, `URL_Tim_Kiem` | URL tin trực tiếp bỏ tracking và trang danh sách nguồn |
| `Timestamp`, `Timestamp_Bat_Dau` | Thời điểm lấy tin và bắt đầu lượt chạy, ISO 8601 có múi giờ |
| `Truong_Thieu` | Danh sách các trường chưa lấy được |

Không tự gán “Nhân viên” thành Junior, không suy cấp bậc chỉ bằng số năm kinh nghiệm.
“Không yêu cầu kinh nghiệm” có cận dưới 0 nhưng không có cận trên.
Cận “trên/dưới” là ngưỡng số; đọc cùng trường gốc để biết tính mở/đóng.

Đây là dữ liệu thô cho bước 2.1: giữ HTML để notebook làm sạch, chuẩn hóa lương,
địa điểm và kỹ năng ở tập sạch riêng. Cột cấp bậc hỗ trợ bước 2.2,
không thay thế toàn bộ EDA/KDD của PDF.

## Lưu trữ và truy cập

CSV dùng UTF-8 BOM, giữ HTML và nội dung nhiều dòng. Lưu sau mỗi tin và khi dừng.
Tin lỗi ghi vào `<tên-file>.errors.csv` kèm URL, thời gian, lý do.
Trang thiếu mô tả/không đúng giao diện không được lưu thành tin hợp lệ.
Thông tin không có trên nguồn để trống, đánh dấu bằng `Truong_Thieu`, không tự bịa.

Đọc `robots.txt` trước khi chạy, kiểm tra quyền truy cập URL, chờ ngẫu nhiên,
cuộn kích hoạt lazy loading và đợi DOM. Nếu gặp xác minh, thao tác thủ công trong
Chrome; không bảo đảm vượt được chặn truy cập.

Kiểm thử:

```powershell
python -m unittest discover -s . -p "test_scraper.py"
```
