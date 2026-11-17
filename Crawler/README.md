# Thu thập dữ liệu TopCV

`scraper.py` duyệt các trang kết quả và truy cập từng tin để lấy dữ liệu thô cho đề tài khối nghề phần mềm.

## Chạy

Yêu cầu Python và Google Chrome. Các lệnh dưới đây chạy từ thư mục gốc project:

```powershell
python -m pip install -r Crawler/requirements.txt
python Crawler/scraper.py
```

Mặc định sử dụng `TOPCV_SEARCH_URLS` trong script, không giới hạn số trang hoặc số tin.

Chạy thử:

```powershell
python Crawler/scraper.py --max-pages 1 --max-jobs 3
```

Chọn URL khác:

```powershell
python Crawler/scraper.py --url "https://www.topcv.vn/tim-viec-lam-software-engineering-cr257cb258"
```

Có thể truyền `--url` nhiều lần. Đặt toàn bộ URL trong dấu ngoặc kép nếu có tham số `&`. Xem các tùy chọn bằng `python Crawler/scraper.py --help`.

## Dữ liệu đầu ra

Mặc định lưu vào `data/raw/raw_data_YYYYMMDD_HHMMSS.csv`, dùng UTF-8 BOM. Với `--output`, đường dẫn tương đối được tính từ thư mục chạy lệnh. Script không ghi đè CSV đã tồn tại.

| Cột | Nội dung |
| --- | --- |
| `job_title` | Tiêu đề công việc |
| `company_name` | Tên công ty |
| `location_raw` | Địa điểm làm việc nguyên văn |
| `salary_raw` | Mức lương nguyên văn |
| `experience_raw` | Kinh nghiệm yêu cầu |
| `description_raw` | HTML mô tả công việc |
| `requirements_raw` | HTML yêu cầu ứng viên và tag bổ sung |
| `benefits_raw` | HTML quyền lợi và tag bổ sung |
| `level_raw` | Cấp bậc hiển thị trên TopCV |
| `source_url` | URL trực tiếp đến tin, bỏ tracking |
| `scraped_at` | Thời điểm cào, có múi giờ |

Crawler không chuẩn hóa lương, suy luận cấp bậc hay loại stopwords. Các bước này thực hiện trong notebook.

## Lưu ý

- Giữ bộ lọc của URL khi phân trang; khử trùng theo mã tin trong cùng lượt chạy.
- Kiểm tra `robots.txt`, chờ ngẫu nhiên và cuộn trang để tải nội dung.
- Nếu gặp xác minh truy cập, thao tác thủ công trong Chrome; có thể không lấy được tin bị chặn.
- Lưu dữ liệu sau mỗi tin. Lỗi lấy chi tiết được ghi tại `outputs/logs/<tên-file>.errors.csv`; script không tự cào lại tin lỗi.
- Tin không có khối mô tả hợp lệ sẽ không được lưu. Các trường khác không lấy được để trống.