import unittest

from scraper import _experience_years, _job_url, _page_url, parse_topcv_html
from urllib.parse import parse_qs, urlsplit


class TopCVParserTests(unittest.TestCase):
    def test_fields_follow_labels_and_keep_html(self):
        html = '''
        <h1 class="box-header-job__title">Senior Python Developer</h1>
        <div class="box-company-info"><a class="name">Công ty A</a></div>
        <div class="job-detail__info--section">
          <div class="job-detail__info--section-content-title">Địa điểm</div>
          <div class="job-detail__info--section-content-value">Đà Nẵng</div>
        </div>
        <div class="job-detail__info--section">
          <div class="job-detail__info--section-content-title">Mức lương</div>
          <div class="job-detail__info--section-content-value">15 - 25 triệu</div>
        </div>
        <div class="job-detail__info--section">
          <div class="job-detail__info--section-content-title">Kinh nghiệm</div>
          <div class="job-detail__info--section-content-value">Trên 3 năm</div>
        </div>
        <div class="box-job-information-general-info-list__item">
          <h3 class="box-job-information-general-info-list__item--content-title">Cấp bậc</h3>
          <div class="box-job-information-general-info-list__item--content-desc">Nhân viên</div>
        </div>
        <div class="box-job-information-general-info-list__item">
          <h3 class="box-job-information-general-info-list__item--content-title">Số lượng tuyển</h3>
          <div class="box-job-information-general-info-list__item--content-desc">5 người</div>
        </div>
        <div class="job-description__item"><h3>Mô tả công việc</h3>
          <div class="job-description__item--content"><p>Viết <strong>Python</strong></p></div>
        </div>
        <div class="job-description__item"><h3>Yêu cầu ứng viên</h3>
          <div class="job-description__item--content"><ul><li>SQL</li></ul></div>
        </div>
        <div class="job-description__item"><h3>Quyền lợi</h3>
          <div class="job-description__item--content"><p>Bảo hiểm</p></div>
        </div>'''
        job = parse_topcv_html(html, 'https://www.topcv.vn/viec-lam/python/123.html')
        self.assertEqual(job['Muc_Luong_Goc'], '15 - 25 triệu')
        self.assertEqual(job['Dia_Diem'], 'Đà Nẵng')
        self.assertEqual(job['Kinh_Nghiem'], 'Trên 3 năm')
        self.assertEqual((job['Kinh_Nghiem_Min'], job['Kinh_Nghiem_Max']), (3, None))
        self.assertEqual(job['Cap_Bac'], 'Nhân viên')
        self.assertEqual((job['Cap_Bac_Chuan'], job['Nguon_Cap_Bac_Chuan']), ('Senior', 'Tieu_De'))
        self.assertIn('<strong>Python</strong>', job['Mo_Ta_Cong_Viec'])
        self.assertIn('<li>SQL</li>', job['Yeu_Cau'])
        self.assertNotIn('Bảo hiểm', job['Yeu_Cau'])
        self.assertIn('Bảo hiểm', job['Quyen_Loi'])

    def test_challenge_is_not_a_job_even_with_card_fallback(self):
        with self.assertRaises(ValueError):
            parse_topcv_html('<h1>Just a moment</h1>', 'https://www.topcv.vn', {'Tieu_De': 'Python Developer'})

    def test_experience_bounds(self):
        for raw, expected in [
            ('6 - 12 tháng', (0.5, 1)), ('Dưới 1 năm', (0, 1)),
            ('Trên 5 năm', (5, None)), ('Từ 2 năm trở lên', (2, None)),
            ('Không yêu cầu kinh nghiệm', (0, None)), (None, (None, None)),
        ]:
            with self.subTest(raw=raw):
                self.assertEqual(_experience_years(raw), expected)

    def test_pagination_replaces_page_preserving_filters(self):
        url = _page_url('https://www.topcv.vn/tim-viec-lam?category_family=a~b&page=2&type_keyword=1', 3)
        self.assertEqual(parse_qs(urlsplit(url).query), {
            'category_family': ['a~b'], 'page': ['3'], 'type_keyword': ['1'],
        })

    def test_brand_jobs_are_not_dropped_or_confused_with_company_pages(self):
        base = 'https://www.topcv.vn/tim-viec-lam-python'
        path = '/brand/msbank/tuyen-dung/business-analyst-j2339802.html'
        self.assertEqual(_job_url(path + '?tracking=1', base), 'https://www.topcv.vn' + path)
        self.assertEqual(_job_url('/viec-lam/python/123.html?tracking=1', base),
                         'https://www.topcv.vn/viec-lam/python/123.html')
        self.assertIsNone(_job_url('/brand/msbank', base))
        self.assertIsNone(_job_url('https://example.com' + path, base))


if __name__ == '__main__':
    unittest.main()
