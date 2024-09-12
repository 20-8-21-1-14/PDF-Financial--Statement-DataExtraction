import pytesseract
import re
import cv2
import pdf2image
import numpy as np
import pandas as pd

pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
keysword_constant = ['Báo cáo tình hình tài chính','Tài sản', 'Thu nhập']
#TODO: add all pattern able to extract 
lai_truoc_thue_pt1 = r'Lợi nhuận trước thuế[\s:]*([\d\.,\-]+)', re.IGNORECASE
lai_truoc_thue_pt2= r'TỎNG LỢI NHUẬN TRƯỚC THUÊ: ((?:\(\d{1,3}(?:\.\d{3})*\))|\d{1,3}(?:\.\d{3})*) (?:\d{1,3}(?:\.\d{3})*)*'
lai_truoc_thue_pt3= r'TỔNG LỢI NHUẬN TRƯỚC THUẾ: ((?:\(\d{1,3}(?:\.\d{3})*\))|\d{1,3}(?:\.\d{3})*) (?:\d{1,3}(?:\.\d{3})*)*'

lai_sau_thue_pt1 = r'Lợi nhuận kế toán sau thuế[\s:]*([\d\.,\-]+)'
lai_sau_thue_pt2 = r'LỢI NHUẬN SAU THUẾ[\s:]*((?:\(\d{1,3}(?:\.\d{3})*\))|\d{1,3}(?:\.\d{3})*) (?:\d{1,3}(?:\.\d{3})*)*' 

pattern_lai_truoc_thue = re.compile(lai_truoc_thue_pt2, re.IGNORECASE)
pattern_lo_truoc_thue = re.compile(r'Lỗ kế toán trước thuế[\s:]*([\d\.,\-]+)', re.IGNORECASE)
pattern_lai_sau_thue = re.compile(lai_sau_thue_pt2, re.IGNORECASE)
pattern_lo_sau_thue = re.compile(r'Lỗ kế toán sau thuế[\s:]*([\d\.,\-]+)', re.IGNORECASE)
pattern_von_dieu_le = r'vốn điều lệ của.*?là\s([\d\.\,]+)\sđong'

def main():
    data = []
    matches_von_dieu_le = []
    lai_truoc_thue = []
    lo_truoc_thue = []
    lai_sau_thue= []
    lo_sau_thue = [] 
    
    pages = pdf2image.convert_from_path('VCB-BCTChopnhatkiemtoan2022.pdf') # path to pdf files here
    i = 0
    for page in pages:
        gray = cv2.cvtColor(np.array(page), cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        text = pytesseract.image_to_string(thresh, lang="vie")
        if len(text) > 1000:
            
            if not matches_von_dieu_le:
                matches_von_dieu_le = re.findall(pattern_von_dieu_le, text)
            if not lai_truoc_thue:
                lai_truoc_thue = pattern_lai_truoc_thue.findall(text)
            if not lo_truoc_thue:
                lo_truoc_thue = pattern_lo_truoc_thue.findall(text)
            if not lai_sau_thue:
                lai_sau_thue = pattern_lai_sau_thue.findall(text)
            if not lo_sau_thue:
                lo_sau_thue = pattern_lo_sau_thue.findall(text)
                
        # if "Lỗ" in text:
        #     print(text)

    if lai_truoc_thue or lai_sau_thue or lo_truoc_thue or lo_sau_thue or matches_von_dieu_le:
        data.append({
            'VonDieuLe': matches_von_dieu_le if matches_von_dieu_le else None,
            'LaiTruocThue': lai_truoc_thue if lai_truoc_thue  else None,
            'LoTruocThue': lo_truoc_thue if lo_truoc_thue else None,
            'LaiLoSauThue': lai_sau_thue if lai_sau_thue else None,
            'LoSauThue':  lo_sau_thue if lo_sau_thue else None,
        })       
    df = pd.DataFrame(data=data, columns=['VonDieuLe', 'LaiTruocThue', 'LoTruocThue', 'LaiSauThue','LoSauThue'])
    # Write the DataFrame to a CSV file
    df.to_csv('extracted_data.csv', index=False)

        


if __name__ == "__main__":
    main()
