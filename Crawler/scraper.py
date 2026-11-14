"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  TopCV Web Scraper — ITEC3417 Bài Tập Lớn Khai Phá Dữ Liệu                ║
║  Mục tiêu: Thu thập 800–1.500+ tin tuyển dụng CNTT & Khoa học dữ liệu      ║
║  Output : CSV dữ liệu thô, HTML gốc và dấu vết thu thập                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
Quy trình:
  1. Duyệt trang danh sách tìm kiếm (search listing) → gom URL từng việc làm
  2. Truy cập từng trang chi tiết → đọc đúng nhãn, giữ HTML nội dung
  3. Lưu sau mỗi tin; ghi riêng URL lỗi và không ghi đè dữ liệu cũ
"""

import argparse
import re
import time
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests

import pandas as pd
from bs4 import BeautifulSoup

# Selenium imports
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException

# ── Chọn driver phù hợp ──────────────────────────────────────────────────────
try:
    import undetected_chromedriver as uc
    USE_UC = True
    print("[INFO] Đang dùng undetected-chromedriver (vượt Cloudflare tốt nhất)")
except ImportError:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    USE_UC = False
    print("[WARN] Chưa cài undetected-chromedriver → dùng Selenium chuẩn")
    print("[WARN] Khuyến nghị chạy: pip install undetected-chromedriver")


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 1 — KHỞI TẠO TRÌNH DUYỆT
# ══════════════════════════════════════════════════════════════════════════════

def init_driver():
    """
    Khởi tạo Chrome với cấu hình ẩn dấu vết Bot để tránh bị Cloudflare chặn.
    undetected-chromedriver tự động patch binary Chrome ở mức C++ nên không bị
    phát hiện qua navigator.webdriver.
    """
    if USE_UC:
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = uc.Chrome(options=options, headless=False, use_subprocess=True)
    else:
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
        )
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
        )
    return driver


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 2 — CÁC HÀM TIỆN ÍCH & KIỂM TRA
# ══════════════════════════════════════════════════════════════════════════════

def check_and_bypass_cloudflare(driver, max_wait_seconds=120):
    """
    Kiểm tra nếu gặp màn hình Cloudflare challenge.
    Tự động phát hiện khi người dùng đã tick xong trên trình duyệt và tự động
    tiếp tục ngay lập tức — KHÔNG CẦN quay lại terminal nhấn phím ENTER.
    """
    title = driver.title.lower()
    page_src = driver.page_source.lower()

    if "you have been blocked" in page_src or ("attention required" in title and "blocked" in page_src):
        print("\n[❌ CẢNH BÁO] IP bị Cloudflare chặn tạm thời!")
        print("   → Vui lòng chuyển sang mạng khác (ví dụ: phát 4G/hotspot điện thoại).")
        print("   → Hệ thống đang tự động theo dõi, sẽ tự chạy tiếp ngay khi mạng được đổi...")
        start_wait = time.time()
        while time.time() - start_wait < max_wait_seconds:
            time.sleep(2.0)
            if "you have been blocked" not in driver.page_source.lower():
                print("   [✓] Đã khôi phục kết nối! Tự động tiếp tục...")
                return
        return

    if any(kw in title for kw in ["just a moment", "verify", "bảo mật", "checking"]):
        print("\n[⚠️ XÁC MINH] Cloudflare yêu cầu kiểm tra người dùng thật!")
        print("   >>> Vui lòng tick vào ô 'Verify you are human' trên cửa sổ Chrome...")
        print("   >>> (Hệ thống sẽ tự động chạy tiếp ngay khi bạn tick xong, không cần bấm phím nào!)")
        
        start_wait = time.time()
        while time.time() - start_wait < max_wait_seconds:
            time.sleep(1.5)
            curr_title = driver.title.lower()
            # Khi người dùng tick xong, Cloudflare chuyển hướng về trang TopCV và title đổi
            if not any(kw in curr_title for kw in ["just a moment", "verify", "bảo mật", "checking"]):
                print("   [✓] Xác minh thành công! Đang tự động tiếp tục...")
                time.sleep(1.2)
                return
        print("   [!] Hết thời gian chờ xác minh (quá 2 phút).")


def auto_scroll(driver, steps=4):
    """
    Cuộn trang nhẹ để kích hoạt tải dữ liệu động (Lazy Loading) trên TopCV.
    """
    for _ in range(steps):
        driver.execute_script(f"window.scrollBy(0, {random.randint(400, 750)});")
        time.sleep(random.uniform(0.4, 0.9))
    driver.execute_script("window.scrollBy(0, -200);")
    time.sleep(0.3)


def is_date_string(text):
    """Kiểm tra chuỗi có phải ngày đăng tuyển (tránh nhầm với địa điểm)"""
    if not text:
        return False
    return any(p in text.lower() for p in ["ngày trước", "tuần trước", "tháng trước", "hôm nay", "giờ trước"])


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 3 — TRÍCH XUẤT CHI TIẾT TRANG CÔNG VIỆC (HỖ TRỢ CẢ GIAO DIỆN MỚI & CŨ)
# ══════════════════════════════════════════════════════════════════════════════

def _text(node):
    return node.get_text(" ", strip=True) if node else None


def _labeled_values(soup):
    """Đọc đúng cặp nhãn/giá trị, không quét text của các div cha."""
    values = {}
    layouts = [
        (".box-header-job-list-info__item, .list-info__content",
         ".list-info__content__title", ".list-info__content__desc"),
        (".job-detail__info--section", ".job-detail__info--section-content-title",
         ".job-detail__info--section-content-value"),
        (".box-job-information-general-info-list__item",
         ".box-job-information-general-info-list__item--content-title",
         ".box-job-information-general-info-list__item--content-desc"),
        (".box-general-group-info-item", ".box-general-group-info-title",
         ".box-general-group-info-value"),
    ]
    for items, label_selector, value_selector in layouts:
        for item in soup.select(items):
            label = _text(item.select_one(label_selector))
            value = _text(item.select_one(value_selector))
            if label and value:
                values.setdefault(label.casefold().strip(" :"), value)
    return values


def _experience_years(raw):
    """Khoảng năm; cận không xác định để trống, không biến thiếu thành 0."""
    text = (raw or "").casefold()
    if any(word in text for word in ("không yêu cầu", "chưa có kinh nghiệm")):
        return 0.0, None
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:[-–]|đến)\s*(\d+(?:[.,]\d+)?)\s*(năm|tháng)", text)
    if match:
        scale = 12 if match[3] == "tháng" else 1
        return float(match[1].replace(",", ".")) / scale, float(match[2].replace(",", ".")) / scale
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(năm|tháng)", text)
    if not match:
        return None, None
    number = float(match[1].replace(",", ".")) / (12 if match[2] == "tháng" else 1)
    if "dưới" in text:
        return 0.0, number
    if any(word in text for word in ("trên", "từ", "ít nhất", "tối thiểu", "trở lên", "+")):
        return number, None
    return number, number


def _seniority(title, raw_level):
    """Chỉ ánh xạ nhãn rõ ràng; 'Nhân viên' không đồng nghĩa Junior."""
    for source, text in (("Cap_Bac", raw_level), ("Tieu_De", title)):
        text = (text or "").casefold()
        for level, pattern in (
            ("Lead", r"\b(lead|leader|head|manager)\b|trưởng nhóm|trưởng/phó phòng|trưởng phòng"),
            ("Senior", r"\bsenior\b"),
            ("Middle", r"\b(middle|mid-level|mid level)\b"),
            ("Junior", r"\bjunior\b"),
            ("Fresher", r"\b(fresher|intern|internship|trainee)\b|thực tập|mới tốt nghiệp"),
        ):
            if re.search(pattern, text):
                return level, source
    return None, None


def parse_topcv_html(html, job_url, fallback_info=None):
    """Phân tích DOM đã tải; các trường thô không chuẩn hóa hoặc bỏ HTML."""
    fallback = fallback_info or {}
    soup = BeautifulSoup(html, "html.parser")
    title = _text(soup.select_one("h1.box-header-job__title, h1.job-detail__info--title, h1.title"))
    # Không lưu trang lỗi/challenge chỉ vì card danh sách có tiêu đề.
    sections = soup.select(".box-job-information-detail-item, .job-description__item")
    if not title or not sections:
        raise ValueError("Không nhận diện được trang chi tiết TopCV")
    values = _labeled_values(soup)
    company = _text(soup.select_one(".box-company-info a.name, .job-detail__company--information a.name, .company-name-label a"))
    salary = _text(soup.select_one(".box-header-job__salary--title, .salary-text")) or values.get("mức lương")
    location = None
    for item in soup.select(".box-job-information-address-and-time-list__item"):
        label = _text(item.select_one(".box-job-information-address-and-time-list__item--title"))
        if label and label.casefold() == "địa điểm làm việc":
            location = _text(item.select_one(".box-job-information-address-and-time-list__item--content"))
            break
    content = {}
    for item in sections:
        heading = _text(item.select_one(".box-job-information-detail-item__title, h3"))
        if not heading:
            continue
        heading = heading.casefold()
        key = None
        if "mô tả công việc" in heading or "job description" in heading:
            key = "Mo_Ta_Cong_Viec"
        elif "yêu cầu" in heading:
            key = "Yeu_Cau"
        elif "quyền lợi" in heading or "chế độ" in heading:
            key = "Quyen_Loi"
        node = item.select_one(".box-job-information-detail-item__text, .job-description__item--content")
        if key and node:
            # Giữ cả nội dung phụ (kỹ năng/phúc lợi) nằm ngoài khối text.
            nodes = [node, *item.select(".required-tags")]
            content[key] = "\n".join(str(part) for part in nodes)
    if not content.get("Mo_Ta_Cong_Viec"):
        raise ValueError("Thiếu khối mô tả công việc; không lưu tin giả đầy đủ")
    experience = values.get("kinh nghiệm") or values.get("kinh nghiệm chuyên môn") or fallback.get("Kinh_Nghiem")
    low, high = _experience_years(experience)
    level = values.get("cấp bậc")
    seniority, seniority_source = _seniority(title, level)
    job = {
        "Tieu_De": title,
        "Ten_Cong_Ty": company or fallback.get("Ten_Cong_Ty"),
        "Dia_Diem": location or values.get("địa điểm") or fallback.get("Dia_Diem"),
        "Muc_Luong_Goc": salary or fallback.get("Muc_Luong_Goc"),
        "Kinh_Nghiem": experience,
        **{key: content.get(key) for key in ("Mo_Ta_Cong_Viec", "Yeu_Cau", "Quyen_Loi")},
        "Yeu_Cau_Quyen_Loi": "\n".join(filter(None, (content.get("Yeu_Cau"), content.get("Quyen_Loi")))) or None,
        "URL_Goc": job_url,
        "Timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "Cap_Bac": level,
        "Cap_Bac_Chuan": seniority,
        "Nguon_Cap_Bac_Chuan": seniority_source,
        "Kinh_Nghiem_Min": low,
        "Kinh_Nghiem_Max": high,
        "Kinh_Nghiem_Quan_Ly": values.get("kinh nghiệm quản lý"),
        "Hinh_Thuc": values.get("hình thức làm việc") or values.get("hình thức"),
        "Loai_Hinh": values.get("loại hình làm việc"),
    }
    job["Truong_Thieu"] = ";".join(
        key for key in ("Ten_Cong_Ty", "Dia_Diem", "Muc_Luong_Goc", "Kinh_Nghiem", "Yeu_Cau", "Quyen_Loi", "Cap_Bac")
        if not job.get(key)
    )
    return job


def parse_topcv_job_detail(driver, job_url, fallback_info=None):
    driver.get(job_url)
    time.sleep(random.uniform(2.0, 3.2))
    check_and_bypass_cloudflare(driver)
    WebDriverWait(driver, 20).until(
        lambda browser: browser.find_elements(By.CSS_SELECTOR, ".box-job-information-detail-item__text, .job-description__item--content")
    )
    auto_scroll(driver, steps=3)
    return parse_topcv_html(driver.page_source, job_url, fallback_info)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 4 — TRÍCH XUẤT THÔNG TIN NHANH TỪ DANH SÁCH (CARD LISTING)
# ══════════════════════════════════════════════════════════════════════════════

def extract_card_fallback(card):
    """Lấy dữ liệu dự phòng từ thẻ công việc trên trang danh sách tìm kiếm"""
    dia_diem = None
    for sel in [".label-content a.address", "div.label-content label.address", "span.address", "div.city-label"]:
        el = card.select_one(sel)
        if el:
            txt = el.get_text(strip=True)
            if txt and not is_date_string(txt):
                dia_diem = txt
                break

    def get_first(selectors):
        for s in selectors:
            el = card.select_one(s)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return None

    return {
        "Tieu_De": get_first(["h3.title a", "h2.title a", "a.job-title"]),
        "Ten_Cong_Ty": get_first(["a.company", "div.company-name", "span.company-name"]),
        "Muc_Luong_Goc": get_first(["label.title-salary", "span.salary", "div.salary"]),
        "Dia_Diem": dia_diem,
        "Kinh_Nghiem": get_first(["label.exp", "span.exp", "div.exp"]),
    }


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 5 — HÀM ĐIỀU PHỐI THU THẬP DỮ LIỆU CHÍNH
# ══════════════════════════════════════════════════════════════════════════════

def _page_url(base_url, page):
    parts = urlsplit(base_url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "page"]
    return urlunsplit(parts._replace(query=urlencode([*query, ("page", page)]), fragment=""))


def _job_url(href, base_url):
    parts = urlsplit(urljoin(base_url, href))
    job_path = re.fullmatch(r"/viec-lam/[^/]+/\d+\.html|/brand/[^/]+/tuyen-dung/[^/]+-j\d+\.html", parts.path)
    if parts.scheme not in ("https", "http") or parts.hostname not in ("www.topcv.vn", "topcv.vn") or not job_path:
        return None
    return urlunsplit(parts._replace(query="", fragment=""))


def crawl_topcv(search_urls, max_pages_per_url=None, output_csv="raw_data.csv", max_jobs=None):
    """Duyệt tới trang cuối; giới hạn chỉ áp dụng khi người chạy chỉ định."""
    output = Path(output_csv)
    # Không ghi đè bộ dữ liệu người dùng đã có.
    if output.exists():
        raise FileExistsError(f"{output} đã tồn tại. Chọn --output khác để giữ dữ liệu cũ.")
    output.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get("https://www.topcv.vn/robots.txt", timeout=30)
    response.raise_for_status()
    robots = RobotFileParser()
    robots.parse(response.text.splitlines())
    driver = init_driver()
    all_jobs, failures, seen_urls = [], [], set()
    run_timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    errors_path = output.with_suffix(".errors.csv")

    def save():
        if all_jobs:
            pd.DataFrame(all_jobs).to_csv(output, index=False, encoding="utf-8-sig")
        if failures:
            pd.DataFrame(failures).to_csv(errors_path, index=False, encoding="utf-8-sig")

    def visit_allowed(url):
        if not robots.can_fetch("*", url):
            raise PermissionError(f"robots.txt không cho phép: {url}")
        time.sleep(max(random.uniform(2.0, 3.5), robots.crawl_delay("*") or 0))

    try:
        for base_url in search_urls:
            page_num = int(dict(parse_qsl(urlsplit(base_url).query)).get("page", "1"))
            pages_read, page_signatures = 0, set()
            while max_pages_per_url is None or pages_read < max_pages_per_url:
                if max_jobs is not None and len(all_jobs) >= max_jobs:
                    break
                page_url = _page_url(base_url, page_num)
                print(f"[Trang {page_num}] {page_url}")
                visit_allowed(page_url)
                driver.get(page_url)
                check_and_bypass_cloudflare(driver)
                WebDriverWait(driver, 25).until(
                    lambda browser: browser.find_elements(By.CSS_SELECTOR, ".job-item-search-result, .job-item-2, .job-item")
                )
                auto_scroll(driver, steps=5)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                cards = soup.select(".job-item-search-result, .job-item-2, .job-item")
                targets = {}
                for card in cards:
                    anchor = card.select_one("h3.title a, h2.title a, a.job-title")
                    url = _job_url(anchor.get("href", ""), page_url) if anchor else None
                    if url:
                        targets.setdefault(url, extract_card_fallback(card))
                if not targets:
                    raise ValueError(f"Không nhận diện được danh sách tin: {page_url}")
                signature = frozenset(targets)
                if signature in page_signatures:
                    raise ValueError(f"TopCV trả lại trang cũ, dừng để tránh lặp: {page_url}")
                page_signatures.add(signature)
                next_link = soup.select_one('.pagination a[rel="next"], a[rel="next"]')
                for job_url, fallback in targets.items():
                    if max_jobs is not None and len(all_jobs) >= max_jobs:
                        break
                    job_id = re.search(r"(?:/|-j)(\d+)\.html$", job_url)[1]
                    if job_id in seen_urls:
                        continue
                    seen_urls.add(job_id)
                    try:
                        visit_allowed(job_url)
                        job = parse_topcv_job_detail(driver, job_url, fallback)
                        job.update(URL_Tim_Kiem=page_url, Timestamp_Bat_Dau=run_timestamp)
                        all_jobs.append(job)
                        print(f"[{len(all_jobs)}] {job['Tieu_De']} | thiếu: {job['Truong_Thieu'] or 'không'}")
                    except (WebDriverException, ValueError, PermissionError) as error:
                        failures.append({
                            "URL_Goc": job_url, "URL_Tim_Kiem": page_url,
                            "Timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
                            "Loi": str(error),
                        })
                        print(f"[LỖI] {job_url}: {error}")
                    save()
                pages_read += 1
                if not next_link:
                    if not soup.select_one(".pagination"):
                        raise ValueError("Không nhận diện được phân trang; không thể xác nhận đã cào hết")
                    print("[HẾT TRANG] Không còn liên kết tiếp theo.")
                    break
                # data-href của TopCV chỉ có page; giữ nguyên bộ lọc URL đầu vào.
                next_href = next_link.get("data-href") or next_link.get("href") or ""
                next_page = dict(parse_qsl(urlsplit(urljoin(page_url, next_href)).query)).get("page")
                if not next_page or not next_page.isdigit() or int(next_page) <= page_num:
                    raise ValueError(f"Không đọc được trang kế tiếp: {next_href}")
                page_num = int(next_page)
    finally:
        save()
        driver.quit()
        print(f"[ĐÃ LƯU] {len(all_jobs)} tin, {len(failures)} lỗi; dữ liệu: {output}")
    return all_jobs


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 6 — ĐIỂM BẮT ĐẦU CHƯƠNG TRÌNH
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    TOPCV_SEARCH_URLS = [
        "https://www.topcv.vn/tim-viec-lam-quan-tri-website-cr257cb270cl1097?type_keyword=1&disable_auto_detect_type_keyword=1&sba=1&category_family=r257~b258_b259_b263_b265_b266_b267_b268_b270l1097&saturday_status=0"
    ]

    parser = argparse.ArgumentParser(description="Thu thập dữ liệu thô TopCV, giữ HTML và dấu vết thời gian.")
    parser.add_argument("--url", action="append", help="URL TopCV; có thể truyền nhiều lần.")
    parser.add_argument("--max-pages", type=int, help="Giới hạn số trang để demo; mặc định duyệt hết.")
    parser.add_argument("--max-jobs", type=int, help="Giới hạn số tin để demo; mặc định không giới hạn.")
    parser.add_argument("--output", default=f"raw_data_{datetime.now():%Y%m%d_%H%M%S}.csv")
    args = parser.parse_args()
    if any(value is not None and value < 1 for value in (args.max_pages, args.max_jobs)):
        parser.error("--max-pages và --max-jobs phải lớn hơn 0")
    crawl_topcv(args.url or TOPCV_SEARCH_URLS, args.max_pages, args.output, args.max_jobs)
