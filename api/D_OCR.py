import pytesseract
import re
import cv2
import pdf2image
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

# Precompile all patterns once at the start for efficiency
patterns = {
    "lai_truoc_thue": re.compile(r'TỎNG LỢI NHUẬN TRƯỚC THUÊ[\s:]?\s*(\(?-?\d{1,3}(?:\.\d{3})*\)?)\s+(\(?-?\d{1,3}(?:\.\d{3})*\)?)', re.IGNORECASE),
    "lo_truoc_thue": re.compile(r'Lỗ kế toán trước thuế[\s:]*([\d\.,\-]+)', re.IGNORECASE),
    "lai_sau_thue": re.compile(r'LỢI NHUẬN SAU THUẾ[\s:]?\s*(\(?-?\d{1,3}(?:\.\d{3})*\)?)\s+(\(?-?\d{1,3}(?:\.\d{3})*\)?)', re.IGNORECASE),
    "lo_sau_thue": re.compile(r'Lỗ kế toán sau thuế[\s:]*([\d\.,\-]+)', re.IGNORECASE),
    "von_dieu_le": re.compile(r'vốn điều lệ của.*?là\s([\d\.\,]+)\sđong'),
    "date_regex": re.compile(r'ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}'),
    "company_name": re.compile(r'(.*?\n.*?)(?=\s*Báo cáo tài chính)', re.IGNORECASE),
}

def extract_text_from_image(page):
    gray = cv2.cvtColor(np.array(page), cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    return pytesseract.image_to_string(thresh, lang="vie")

def process_page(i, page, company_name, matches_von_dieu_le, lai_truoc_thue, lo_truoc_thue, lai_sau_thue, lo_sau_thue, date_match):
    text = extract_text_from_image(page)
    
    if i == 0:
        date_match.extend(patterns["date_regex"].findall(text))
        company_name.extend(patterns["company_name"].findall(text))

    if len(text) > 1000:
        if not matches_von_dieu_le:
            matches_von_dieu_le.extend(patterns["von_dieu_le"].findall(text))
        if not lai_truoc_thue:
            lai_truoc_thue.extend(patterns["lai_truoc_thue"].findall(text))
        if not lo_truoc_thue:
            lo_truoc_thue.extend(patterns["lo_truoc_thue"].findall(text))
        if not lai_sau_thue:
            lai_sau_thue.extend(patterns["lai_sau_thue"].findall(text))
        if not lo_sau_thue:
            lo_sau_thue.extend(patterns["lo_sau_thue"].findall(text))

def clean_field(value):
    if isinstance(value, list):
        cleaned_values = [v for v in value if v != "This field may not be blank."]
        if not cleaned_values:
            return ""
        return cleaned_values[0]
    return value

def process_tuple_or_string(field):
    if isinstance(field, tuple):
        return " - ".join(field)
    return clean_field(field)

def extract_financial_data(pdf_file):
    data = []
    matches_von_dieu_le = []
    lai_truoc_thue = []
    lo_truoc_thue = []
    lai_sau_thue = []
    lo_sau_thue = []
    date_match = []
    company_name = []

    pages = pdf2image.convert_from_bytes(pdf_file.read())

    # Use ThreadPoolExecutor to process pages in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_page, i, page, company_name, matches_von_dieu_le, lai_truoc_thue, lo_truoc_thue, lai_sau_thue, lo_sau_thue, date_match) for i, page in enumerate(pages)]
        for future in futures:
            future.result()

    if lai_truoc_thue or lai_sau_thue or lo_truoc_thue or lo_sau_thue or matches_von_dieu_le:
        data.append(
            {
                "TenCongTy": clean_field(company_name[0].replace('\n','')) if company_name else "",
                "NgayBaoCao": clean_field(date_match[0]) if date_match else "",
                "VonDieuLe": process_tuple_or_string(matches_von_dieu_le[0]) if matches_von_dieu_le else "",
                "LaiTruocThue": process_tuple_or_string(lai_truoc_thue[0]) if lai_truoc_thue else "",
                "LoTruocThue": process_tuple_or_string(lo_truoc_thue[0]) if lo_truoc_thue else "",
                "LaiSauThue": process_tuple_or_string(lai_sau_thue[0]) if lai_sau_thue else "",
                "LoSauThue": process_tuple_or_string(lo_sau_thue[0]) if lo_sau_thue else "",
            }
        )

    df = pd.DataFrame(
        data=data,
        columns=[
            "TenCongTy",
            "NgayBaoCao",
            "VonDieuLe",
            "LaiTruocThue",
            "LoTruocThue",
            "LaiSauThue",
            "LoSauThue",
        ],
    )
    print(df)
    return df.to_dict(orient='records')
