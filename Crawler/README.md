# 🕷️ Hướng dẫn Chạy Scraper (TopCV)

### 1. Cài đặt thư viện
```powershell
pip install -r requirements.txt undetected-chromedriver
```

### 2. Chạy scraper
```powershell
python scraper.py
```

### 3. Tùy chỉnh chế độ chạy (ở cuối file `scraper.py`)

| Nhu cầu | Cấu hình trong `scraper.py` | Kết quả |
| :--- | :--- | :--- |
| **Chạy thử / Demo** | `max_jobs=5`, `max_pages_per_url=1` | Cào nhanh ~5 tin (~1 phút) |
| **Cào nộp bài (Full)** | `max_jobs=None`, `max_pages_per_url=12` | Cào đủ 800 - 1.500+ tin |

---

## 📁 Ý nghĩa các tệp trong thư mục

- **`scraper.py`**: Mã nguồn chính thu thập dữ liệu từ TopCV, tự động vượt Cloudflare và bóc tách đầy đủ 9 trường bắt buộc.
- **`raw_data.csv`**: Tệp dữ liệu thô chính thức sau khi cào (chuẩn UTF-8 with BOM, bảo toàn nguyên bản text).
- **`raw_jobs_data.csv`**: Bản sao lưu dự phòng của dữ liệu thô.
- **`explore_data.ipynb`**: Notebook đối soát chất lượng dữ liệu (Data Audit) và xem trước kỹ năng trích xuất.
- **`requirements.txt`**: Danh sách thư viện Python phụ thuộc.

---

> 💡 **Lưu ý:**
> - Nếu gặp Cloudflare, chỉ cần **tick vào ô xác minh trên Chrome**, bot sẽ **tự động chạy tiếp**.
> - Dữ liệu được tự động lưu liên tục vào `raw_data.csv`.
