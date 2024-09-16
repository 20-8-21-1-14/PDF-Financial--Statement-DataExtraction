import pytesseract
import re
import cv2
import pdf2image
import numpy as np
import pandas as pd

pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"
keysword_constant = ["Báo cáo tình hình tài chính", "Tài sản", "Thu nhập"]
# TODO: add all pattern able to extract
lai_truoc_thue_pt1 = r'Lợi nhuận trước thuế[\s:]*([\d\.,\-]+)', re.IGNORECASE
lai_truoc_thue_pt2= r'TỎNG LỢI NHUẬN TRƯỚC THUÊ[\s:]\s*(\(?\d{1,3}(?:\.\d{3})*\)?)\s+(\d{1,3}(?:\.\d{3})*)\s+(\d{1,3}(?:\.\d{3})*)'
lai_truoc_thue_pt3= r'TỔNG LỢI NHUẬN TRƯỚC THUẾ[\s:]\s*(\(?\d{1,3}(?:\.\d{3})*\)?)\s+(\d{1,3}(?:\.\d{3})*)\s+(\d{1,3}(?:\.\d{3})*)'

lai_sau_thue_pt1 = r'Lợi nhuận kế toán sau thuế[\s:]*([\d\.,\-]+)'
lai_sau_thue_pt2 = r'LỢI NHUẬN SAU THUẾ[\s:]\s*(\(?\d{1,3}(?:\.\d{3})*\)?)\s+(\d{1,3}(?:\.\d{3})*)\s+(\d{1,3}(?:\.\d{3})*)' 
date_regex = r'ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}'

pattern_lai_truoc_thue = re.compile(lai_truoc_thue_pt2, flags=re.IGNORECASE)
pattern_lo_truoc_thue = re.compile(r'Lỗ kế toán trước thuế[\s:]*([\d\.,\-]+)', flags=re.IGNORECASE)
pattern_lai_sau_thue = re.compile(lai_sau_thue_pt2, flags=re.IGNORECASE)
pattern_lo_sau_thue = re.compile(r'Lỗ kế toán sau thuế[\s:]*([\d\.,\-]+)', flags=re.IGNORECASE)
pattern_von_dieu_le = r'vốn điều lệ của.*?là\s([\d\.\,]+)\sđong'

def extract_financial_data(pdf_file):
    data = []
    matches_von_dieu_le = []
    lai_truoc_thue = []
    lo_truoc_thue = []
    lai_sau_thue = []
    lo_sau_thue = []
    date_match = []
    company_name = None

    pages = pdf2image.convert_from_bytes(pdf_file.read())  # Using bytes here

    for i, page in enumerate(pages):
        gray = cv2.cvtColor(np.array(page), cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        text = pytesseract.image_to_string(thresh, lang="vie")
        if i==0:
            date_match = re.findall(date_regex, text)
            lines = text.splitlines()
            for line in lines:
                if len(line) > 0 and not re.search(r'\d', line):
                    company_name = line.strip()
                    break
        i += 1
        
        if len(text) <= 2500:
            if not matches_von_dieu_le:
                matches_von_dieu_le = re.findall(pattern_von_dieu_le, text)
            if not lai_truoc_thue:
                if re.findall(pattern_lai_truoc_thue, text):
                    lai_truoc_thue = re.findall(pattern_lai_truoc_thue, text)
            if not lo_truoc_thue:
                lo_truoc_thue = re.findall(pattern_lo_truoc_thue, text)
            if not lai_sau_thue:
                if re.findall(pattern_lai_sau_thue, text):
                    lai_sau_thue = re.findall(pattern_lai_sau_thue, text)
            if not lo_sau_thue:
                lo_sau_thue = pattern_lo_sau_thue.findall(text)

    if lai_truoc_thue or lai_sau_thue or lo_truoc_thue or lo_sau_thue or matches_von_dieu_le:
        data.append(
            {
                "TenCongTy": company_name if company_name else "",
                "NgayBaoCao": date_match[0] if date_match else "",
                "VonDieuLe": matches_von_dieu_le[0] if matches_von_dieu_le else "",
                "LaiTruocThue": lai_truoc_thue[0].apply(lambda x: " - ".join(x) if isinstance(x, tuple) else x) if lai_truoc_thue else "",
                "LoTruocThue": lo_truoc_thue if lo_truoc_thue else "",
                "LaiSauThue": lai_sau_thue[0].apply(lambda x: " - ".join(x) if isinstance(x, tuple) else x) if lai_sau_thue else "",
                "LoSauThue": lo_sau_thue if lo_sau_thue else "",
            }
        )


    print(data)
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
