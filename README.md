# Thu thập và khai phá dữ liệu tuyển dụng khối nghề phần mềm tại Việt Nam

Bài tập lớn môn Khai phá dữ liệu — Nhóm 07. Dữ liệu được thu thập từ TopCV và xử lý trong Jupyter Notebook

## Cấu trúc

```text
Crawler/
  scraper.py                     Công cụ thu thập dữ liệu
  requirements.txt               Thư viện cho crawler
data/
  raw/                           Các bản cào có timestamp trong tên file
  processed/clean_data.csv       Dữ liệu sau tiền xử lý
notebooks/
  Nhom07_MiningPipeline.ipynb     Notebook xử lý và phân tích
  raw_jobs_data.csv              Bản sao dữ liệu thô được notebook chọn
outputs/
  logs/                          URL và thông tin lỗi khi cào
  figures/                       Biểu đồ xuất từ notebook
reports/                         Báo cáo và slide
```

## Cài đặt

Yêu cầu Python và Google Chrome. Từ thư mục gốc project:

```powershell
python -m pip install -r Crawler/requirements.txt
python -m pip install jupyterlab numpy matplotlib seaborn stopwordsiso
```

## Thu thập dữ liệu

Chạy thử một trang, tối đa ba tin:

```powershell
python Crawler/scraper.py --max-pages 1 --max-jobs 3
```

Bỏ hai tham số giới hạn để duyệt toàn bộ URL đã cấu hình. Xem cách chọn URL và file xuất tại [Crawler/README.md](Crawler/README.md).

## Xử lý dữ liệu

```powershell
jupyter lab
```

Mở `notebooks/Nhom07_MiningPipeline.ipynb`, chọn kernel của môi trường đã cài thư viện và chạy các cell từ trên xuống.

Notebook chọn bản cào mới nhất theo timestamp trong tên `raw_data_YYYYMMDD_HHMMSS.csv`, sao chép nguyên vẹn thành `notebooks/raw_jobs_data.csv`. Kết quả xử lý được xuất vào `data/processed/clean_data.csv`; các file cào nguồn không bị sửa. Hai file đầu ra này được ghi đè khi chạy lại.
