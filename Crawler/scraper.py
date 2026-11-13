"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  TopCV Web Scraper — ITEC3417 Bài Tập Lớn Khai Phá Dữ Liệu                ║
║  Mục tiêu: Thu thập 800–1.500+ tin tuyển dụng CNTT & Khoa học dữ liệu      ║
║  Output : raw_data.csv / raw_jobs_data.csv (Đủ 9 cột gốc theo đề bài)       ║
╚══════════════════════════════════════════════════════════════════════════════╝
Quy trình:
  1. Duyệt trang danh sách tìm kiếm (search listing) → gom URL từng việc làm
  2. Truy cập từng trang chi tiết (job detail) → bóc tách chuẩn xác 9 trường
  3. Tự động lưu lũy tiến sau mỗi trang → không lo mất dữ liệu nếu bị ngắt
"""

import re
import time
import random
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup

# Selenium imports
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
    WebDriverException,
)

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

def parse_topcv_job_detail(driver, job_url, fallback_info=None):
    """
    Truy cập trang chi tiết công việc và bóc tách đầy đủ các trường:
    1. Tieu_De
    2. Ten_Cong_Ty
    3. Dia_Diem
    4. Muc_Luong_Goc
    5. Kinh_Nghiem
    6. Mo_Ta_Cong_Viec
    7. Yeu_Cau_Quyen_Loi
    8. URL_Goc
    9. Timestamp
    + Cap_Bac, Hinh_Thuc (hỗ trợ phân lớp nâng cao)
    """
    fallback_info = fallback_info or {}
    try:
        driver.get(job_url)
        time.sleep(random.uniform(2.0, 3.2))
        check_and_bypass_cloudflare(driver)

        if "you have been blocked" in driver.page_source.lower():
            print(f"  [BỊ CHẶN] Không thể vào {job_url}")
            return None

        auto_scroll(driver, steps=3)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # ── 1. TIÊU ĐỀ CÔNG VIỆC ─────────────────────────────────────────────
        tieu_de = None
        for sel in ["h1.job-detail__info--title", "h1.title", "h1"]:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                tieu_de = el.get_text(separator=" ", strip=True)
                break
        tieu_de = tieu_de or fallback_info.get("Tieu_De")

        # ── 2. TÊN CÔNG TY ───────────────────────────────────────────────────
        ten_cong_ty = None
        for sel in [
            ".box-header-job a.name",
            ".box-company-info a.name",
            ".company-name-label a",
            "h2.company-name",
            "a.name",
            ".company-title a",
        ]:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                txt = el.get_text(strip=True)
                if "topcv" not in txt.lower():
                    ten_cong_ty = txt
                    break
        ten_cong_ty = ten_cong_ty or fallback_info.get("Ten_Cong_Ty")

        # ── 3. MỨC LƯƠNG GỐC ─────────────────────────────────────────────────
        muc_luong = None
        salary_el = soup.select_one(".box-header-job__salary--title, .box-header-job__salary, .job-detail__info--section-content-value, .salary-text")
        if salary_el and salary_el.get_text(strip=True):
            muc_luong = salary_el.get_text(strip=True)
        if not muc_luong:
            for it in soup.select(".box-header-job-list-info__item, .list-info__content, .job-detail__info--section"):
                txt = it.get_text(separator=" ", strip=True)
                if any(k in txt.lower() for k in ["mức lương", "lương", "thu nhập"]):
                    desc = it.select_one(".list-info__content__desc, .job-detail__info--section-content-value")
                    muc_luong = desc.get_text(strip=True) if desc else txt
                    break
        muc_luong = muc_luong or fallback_info.get("Muc_Luong_Goc")

        # ── 4. ĐỊA ĐIỂM LÀM VIỆC ─────────────────────────────────────────────
        dia_diem = None
        # Ưu tiên mục địa điểm chi tiết
        for it in soup.select(".box-job-information-address-and-time-list__item, .job-detail__company--information-item.company-address"):
            t_el = it.select_one(".box-job-information-address-and-time-list__item--title, .title")
            if t_el and "địa điểm" in t_el.get_text().lower():
                txt = it.get_text(separator=" - ", strip=True).replace(t_el.get_text(strip=True), "").strip(" - ")
                if txt and not is_date_string(txt):
                    dia_diem = txt
                    break
        # Fallback từ header tóm tắt
        if not dia_diem:
            for it in soup.select(".box-header-job-list-info__item, .list-info__content"):
                txt = it.get_text(separator=" ", strip=True)
                if "địa điểm" in txt.lower():
                    desc = it.select_one(".list-info__content__desc")
                    val = desc.get_text(strip=True) if desc else txt.replace("Địa điểm", "").strip()
                    if val and not is_date_string(val):
                        dia_diem = val
                        break
        # Fallback từ card danh sách
        if not dia_diem or is_date_string(dia_diem):
            dia_diem = fallback_info.get("Dia_Diem")

        # ── 5. KINH NGHIỆM YÊU CẦU ───────────────────────────────────────────
        kinh_nghiem = None
        for it in soup.select(".box-header-job-list-info__item, .job-tags__group, .job-detail__info--section"):
            txt = it.get_text(separator=" ", strip=True)
            if "kinh nghiệm" in txt.lower():
                desc = it.select_one(".list-info__content__desc, .job-detail__info--section-content-value")
                kinh_nghiem = desc.get_text(strip=True) if desc else txt
                match = re.search(r"(\d+\s*-\s*\d+\s*năm|\d+\s*năm|trên\s*\d+\s*năm|dưới\s*\d+\s*năm|không yêu cầu kinh nghiệm|chưa có kinh nghiệm|fresher)", kinh_nghiem, re.IGNORECASE)
                if match:
                    kinh_nghiem = match.group(0)
                break
        kinh_nghiem = kinh_nghiem or fallback_info.get("Kinh_Nghiem")

        # ── 6. MÔ TẢ CÔNG VIỆC ───────────────────────────────────────────────
        mo_ta = None
        # Layout 2024 (TopCV mới)
        for it in soup.select("div.box-job-information-detail-item"):
            t_el = it.select_one(".box-job-information-detail-item__title")
            if t_el and any(k in t_el.get_text().lower() for k in ["mô tả công việc", "job description", "mô tả"]):
                cnt = it.select_one(".box-job-information-detail-item__text")
                mo_ta = cnt.get_text(separator="\n", strip=True) if cnt else it.get_text(separator="\n", strip=True)
                break
        # Layout legacy (TopCV cũ)
        if not mo_ta:
            for it in soup.select("div.job-description__item"):
                h3 = it.select_one("h3")
                if h3 and any(k in h3.get_text().lower() for k in ["mô tả công việc", "job description", "mô tả"]):
                    cnt = it.select_one(".job-description__item--content")
                    mo_ta = cnt.get_text(separator="\n", strip=True) if cnt else it.get_text(separator="\n", strip=True)
                    break
        if not mo_ta:
            cnt = soup.select_one("div.job-description, div.box-job-information-detail")
            if cnt:
                mo_ta = cnt.get_text(separator="\n", strip=True)

        # ── 7. YÊU CẦU ỨNG VIÊN & QUYỀN LỢI ─────────────────────────────────
        yeu_cau = None
        quyen_loi = None

        # Layout 2024
        for it in soup.select("div.box-job-information-detail-item"):
            t_el = it.select_one(".box-job-information-detail-item__title")
            if not t_el:
                continue
            txt = t_el.get_text().lower()
            if any(k in txt for k in ["yêu cầu ứng viên", "yêu cầu công việc", "yêu cầu"]):
                cnt = it.select_one(".box-job-information-detail-item__text")
                tags_el = it.select_one(".required-tags, .job-tags")
                tags_txt = ("\n\n[Kỹ năng yêu cầu]: " + tags_el.get_text(separator=" ", strip=True)) if tags_el else ""
                yeu_cau = (cnt.get_text(separator="\n", strip=True) if cnt else it.get_text(separator="\n", strip=True)) + tags_txt
            elif any(k in txt for k in ["quyền lợi", "chế độ", "đãi ngộ"]):
                cnt = it.select_one(".box-job-information-detail-item__text")
                quyen_loi = cnt.get_text(separator="\n", strip=True) if cnt else it.get_text(separator="\n", strip=True)

        # Layout legacy
        if not yeu_cau or not quyen_loi:
            for it in soup.select("div.job-description__item"):
                h3 = it.select_one("h3")
                if not h3:
                    continue
                txt = h3.get_text().lower()
                cnt = it.select_one(".job-description__item--content")
                c_text = cnt.get_text(separator="\n", strip=True) if cnt else it.get_text(separator="\n", strip=True)
                if not yeu_cau and any(k in txt for k in ["yêu cầu"]):
                    yeu_cau = c_text
                elif not quyen_loi and any(k in txt for k in ["quyền lợi", "chế độ"]):
                    quyen_loi = c_text

        yeu_cau_quyen_loi = "\n\n---\n\n".join(filter(None, [yeu_cau, quyen_loi])) or None

        # ── 8. CẤP BẬC & HÌNH THỨC (Cột bổ sung hỗ trợ phân lớp) ─────────────
        cap_bac = None
        hinh_thuc = None
        for it in soup.select("div.box-job-information-general-info-list div, div.box-general-group-info-item, div.job-detail__info--section"):
            txt = it.get_text(separator=" : ", strip=True)
            if "cấp bậc" in txt.lower() and not cap_bac:
                parts = txt.split(":")
                cap_bac = parts[-1].strip() if len(parts) > 1 else txt
            elif any(k in txt.lower() for k in ["hình thức", "loại hình"]) and not hinh_thuc:
                parts = txt.split(":")
                hinh_thuc = parts[-1].strip() if len(parts) > 1 else txt

        return {
            "Tieu_De": tieu_de,
            "Ten_Cong_Ty": ten_cong_ty,
            "Dia_Diem": dia_diem,
            "Muc_Luong_Goc": muc_luong,
            "Kinh_Nghiem": kinh_nghiem,
            "Mo_Ta_Cong_Viec": mo_ta,
            "Yeu_Cau_Quyen_Loi": yeu_cau_quyen_loi,
            "URL_Goc": job_url,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Cap_Bac": cap_bac,
            "Hinh_Thuc": hinh_thuc,
        }

    except Exception as e:
        print(f"  [!] Lỗi bóc tách chi tiết: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 4 — TRÍCH XUẤT THÔNG TIN NHANH TỪ DANH SÁCH (CARD LISTING)
# ══════════════════════════════════════════════════════════════════════════════

def extract_card_fallback(card):
    """Lấy dữ liệu dự phòng từ thẻ công việc trên trang danh sách tìm kiếm"""
    dia_diem = None
    for sel in ["div.label-content label.address", "span.address", "div.city-label"]:
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

def crawl_topcv(search_urls, max_pages_per_url=12, output_csv="raw_data.csv", max_jobs=None):
    """
    Điều phối toàn bộ quá trình thu thập dữ liệu từ TopCV.
    - search_urls: danh sách URL từ khóa
    - max_pages_per_url: số trang duyệt tối đa mỗi từ khóa
    - output_csv: tên file xuất dữ liệu
    - max_jobs: giới hạn số lượng tin để test (vd: max_jobs=3 hoặc 5)
    """
    driver = init_driver()
    all_jobs = []
    seen_urls = set()

    COL_ORDER = [
        "Tieu_De", "Ten_Cong_Ty", "Dia_Diem", "Muc_Luong_Goc",
        "Kinh_Nghiem", "Mo_Ta_Cong_Viec", "Yeu_Cau_Quyen_Loi",
        "URL_Goc", "Timestamp", "Cap_Bac", "Hinh_Thuc"
    ]

    try:
        for base_url in search_urls:
            if max_jobs and len(all_jobs) >= max_jobs:
                break

            print(f"\n{'='*70}")
            print(f"[*] Bắt đầu nhóm từ khóa: {base_url}")
            print(f"{'='*70}")

            for page_num in range(1, max_pages_per_url + 1):
                if max_jobs and len(all_jobs) >= max_jobs:
                    break

                connector = "&" if "?" in base_url else "?"
                page_url = f"{base_url}{connector}page={page_num}"
                print(f"\n[Trang {page_num:02d}] {page_url}")

                driver.get(page_url)
                time.sleep(random.uniform(2.5, 3.8))
                check_and_bypass_cloudflare(driver)
                auto_scroll(driver, steps=5)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                job_cards = soup.select(
                    "div.job-item-search-result, div.job-item-2, div.job-item, div[class*='job-item']"
                )

                if not job_cards:
                    print("  → Hết tin hoặc không tải được trang. Chuyển sang từ khóa kế tiếp.")
                    break

                card_targets = []
                for card in job_cards:
                    if max_jobs and (len(all_jobs) + len(card_targets)) >= max_jobs:
                        break
                    a_tag = card.select_one("h3.title a, h2.title a, a[href*='/viec-lam/']")
                    if not a_tag:
                        continue
                    href = a_tag.get("href", "").strip()
                    if not href:
                        continue
                    clean_url = href.split("?")[0]
                    if clean_url in seen_urls or "/viec-lam/" not in clean_url:
                        continue

                    card_targets.append((clean_url, extract_card_fallback(card)))
                    seen_urls.add(clean_url)

                print(f"  → Phát hiện {len(card_targets)} việc làm mới (Tổng đã gom URL: {len(seen_urls)})")

                # Cào chi tiết từng việc làm
                for idx, (job_url, fallback) in enumerate(card_targets, 1):
                    if max_jobs and len(all_jobs) >= max_jobs:
                        break

                    print(f"\n  [{len(all_jobs)+1:04d}] Đang bóc tách: {job_url}")
                    job_data = parse_topcv_job_detail(driver, job_url, fallback_info=fallback)

                    if job_data and job_data.get("Tieu_De"):
                        all_jobs.append(job_data)
                        tieu_de_rut_gon = (job_data["Tieu_De"] or "")[:50]
                        mo_ta_len = len(job_data.get("Mo_Ta_Cong_Viec") or "")
                        yeu_cau_len = len(job_data.get("Yeu_Cau_Quyen_Loi") or "")
                        print(f"        ✓ Tiêu đề: {tieu_de_rut_gon}...")
                        print(f"          Công ty: {job_data.get('Ten_Cong_Ty')} | Lương: {job_data.get('Muc_Luong_Goc')} | Địa điểm: {job_data.get('Dia_Diem')}")
                        print(f"          Mô tả JD: {mo_ta_len} ký tự | Yêu cầu & Quyền lợi: {yeu_cau_len} ký tự")
                    else:
                        print("        ✗ Không thể bóc tách nội dung chi tiết")

                    # Nghỉ ngẫu nhiên 2 - 3.5 giây để tôn trọng server
                    time.sleep(random.uniform(2.0, 3.5))

                # Lưu tạm dữ liệu định kỳ
                if all_jobs:
                    df_temp = pd.DataFrame(all_jobs).reindex(columns=COL_ORDER)
                    df_temp.to_csv(output_csv, index=False, encoding="utf-8-sig")
                    df_temp.to_csv("raw_jobs_data.csv", index=False, encoding="utf-8-sig")
                    print(f"\n  💾 Đã lưu lũy tiến: {len(all_jobs)} tin vào {output_csv}")

                if max_jobs and len(all_jobs) >= max_jobs:
                    break

                time.sleep(random.uniform(3.0, 5.0))

    finally:
        try:
            driver.close()
        except Exception:
            pass
        try:
            driver.quit()
        except Exception:
            pass
        print(f"\n{'='*70}")
        print(f"[HOÀN TẤT] Tổng số tin tuyển dụng đã thu thập: {len(all_jobs)}")
        if all_jobs:
            df_final = pd.DataFrame(all_jobs)
            print(f"  - Tin có Mô tả công việc (JD): {df_final['Mo_Ta_Cong_Viec'].notna().sum()}/{len(all_jobs)}")
            print(f"  - Tin có Yêu cầu & Quyền lợi:  {df_final['Yeu_Cau_Quyen_Loi'].notna().sum()}/{len(all_jobs)}")
            print(f"  - Tin có Địa điểm chuẩn:       {df_final['Dia_Diem'].notna().sum()}/{len(all_jobs)}")
            print(f"  - Tin có Mức lương gốc:        {df_final['Muc_Luong_Goc'].notna().sum()}/{len(all_jobs)}")
        print(f"[FILE XUẤT] {output_csv} và raw_jobs_data.csv")
        print(f"{'='*70}")


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 6 — ĐIỂM BẮT ĐẦU CHƯƠNG TRÌNH
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    TOPCV_SEARCH_URLS = [
        "https://www.topcv.vn/tim-viec-lam-data-analyst",
        "https://www.topcv.vn/tim-viec-lam-data-engineer",
        "https://www.topcv.vn/tim-viec-lam-data-scientist",
        "https://www.topcv.vn/tim-viec-lam-ai-engineer",
        "https://www.topcv.vn/tim-viec-lam-machine-learning",
        "https://www.topcv.vn/tim-viec-lam-python",
        "https://www.topcv.vn/tim-viec-lam-sql",
        "https://www.topcv.vn/tim-viec-lam-power-bi",
        "https://www.topcv.vn/tim-viec-lam-backend-developer",
        "https://www.topcv.vn/tim-viec-lam-cntt-phan-mem-cr257",
    ]

    # Thiết lập chạy thử 3 việc làm trước
    crawl_topcv(
        search_urls=TOPCV_SEARCH_URLS,
        max_pages_per_url=1,
        output_csv="raw_data.csv",
        max_jobs=50,  # Chạy thử 3 công việc
    )
