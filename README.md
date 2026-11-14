# Khai phá dữ liệu tuyển dụng

Thu thập dữ liệu TopCV và tổ chức quy trình KDD theo `BaiTapLon.pdf`.
Scraper chỉ thu thập dữ liệu thô; xử lý và phân tích thực hiện trong notebook.

## Cấu trúc

```text
data-mining/
├── BaiTapLon.pdf
├── README.md
├── requirements.txt
├── Crawler/
│   ├── scraper.py
│   ├── requirements.txt
│   └── README.md
├── data/
│   ├── raw/                       # Bản cào gốc; dữ liệu cũ giữ nguyên schema
│   ├── processed/                 # Dữ liệu xử lý, tách biệt nguồn
│   └── dictionaries/              # Nơi lưu từ điển kỹ năng/stopwords
├── notebooks/
│   └── explore_data_legacy.ipynb   # Notebook khám phá dữ liệu cũ hiện có
├── outputs/
│   ├── figures/
│   ├── tables/
│   └── logs/
└── reports/
```

Các thư mục từ điển, biểu đồ, bảng và báo cáo hiện chỉ là nơi lưu sản phẩm;
không tạo tệp dữ liệu/báo cáo giả. Chưa triển khai notebook chuyển đổi dữ liệu cũ
hoặc notebook KDD hoàn chỉnh ở lần tổ chức thư mục này.

## Chạy

Từ thư mục gốc project:

```powershell
pip install -r requirements.txt
python Crawler/scraper.py --max-pages 1 --max-jobs 3
jupyter lab
```

Bỏ hai tham số giới hạn để cào toàn bộ URL đã cấu hình.
Scraper mặc định ghi CSV mới vào `data/raw/` và lỗi vào `outputs/logs/`,
không phụ thuộc thư mục chạy lệnh. `--output` tùy chọn nhận đường dẫn như người chạy cung cấp.
Chi tiết tại `Crawler/README.md`.

CSV mới có 11 cột:
`Tieu_De`, `Ten_Cong_Ty`, `Dia_Diem`, `Muc_Luong_Goc`, `Kinh_Nghiem`,
`Mo_Ta_Cong_Viec`, `Yeu_Cau`, `Quyen_Loi`, `Cap_Bac`, `URL_Goc`, `Timestamp`.
Hai cột yêu cầu và quyền lợi giữ HTML riêng; không chuẩn hóa trong scraper.

## Dữ liệu và notebook cũ

- Các CSV nguồn đã chuyển vào `data/raw/`, giữ nguyên nội dung và tên.
- `raw_data_20261114_140555.csv` đang bị tiến trình khác giữ nên chỉ sao chép
  vào `data/raw/`; bản tại `Crawler/` được giữ nguyên.
- `data/processed/raw_data_clean.csv` là kết quả cũ, chưa được coi là dữ liệu
  sạch hoàn chỉnh theo bước 2.1.
- `notebooks/explore_data_legacy.ipynb` đọc riêng `data/raw/raw_data.csv` theo
  schema cũ, không tự gộp mọi bản cào. Đầu ra lọc tiêu đề là
  `data/processed/legacy_title_filtered.csv`, không ghi đè dữ liệu nguồn.
- Dữ liệu cũ vẫn có `Yeu_Cau_Quyen_Loi`; thay đổi schema chỉ áp dụng lượt cào mới.

Notebook KDD sẽ đặt tại `notebooks/NhomXX_MiningPipeline.ipynb`, gồm các bước
2.1–2.5: làm sạch, EDA, gom cụm, luật kết hợp và phân lớp. Logic KDD viết trong
`.ipynb`, không tạo pipeline `.py`. Không sinh thêm test.
