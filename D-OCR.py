import pytesseract
import re
import cv2
import pdf2image
import numpy as np
import pandas as pd

pytesseract.pytesseract.tesseract_cmd = r'Path-To-PDF'
df = pd.DataFrame(columns=['Page', 'Text'])
keysword_constant = ['Báo cáo tình hình tài chính','Tài sản', 'Thu nhập']
pattern_lai_truoc_thue = re.compile(r'Lợi nhuận trước thuế[\s:]*([\d\.,\-]+)', re.IGNORECASE)
pattern_lo_truoc_thue = re.compile(r'Lỗ kế toán trước thuế[\s:]*([\d\.,\-]+)', re.IGNORECASE)
pattern_lai_sau_thue = re.compile(r'Lợi nhuận kế toán sau thuế[\s:]*([\d\.,\-]+)', re.IGNORECASE)
pattern_lo_sau_thue = re.compile(r'Lỗ kế toán sau thuế[\s:]*([\d\.,\-]+)', re.IGNORECASE)
pattern_von_dieu_le = r'vốn điều lệ của.*?là\s([\d\.\,]+)\sđong'
df = pd.DataFrame(columns=['Page', 'VonDieuLe', 'LaiLoTruocThue', 'LaiLoSauThue'])

def main():
    pages = pdf2image.convert_from_path('VCB-BCTChopnhatkiemtoan2022.pdf')
    i = 0
    for page in pages:
        gray = cv2.cvtColor(np.array(page), cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        # Apply other preprocessing steps if needed

        # Extract text
        # Process pages and write to CSV
        text = pytesseract.image_to_string(thresh, lang="vie")
        
        lai_truoc_thue = pattern_lai_truoc_thue.findall(text)
        lo_truoc_thue = pattern_lo_truoc_thue.findall(text)
        lai_sau_thue = pattern_lai_sau_thue.findall(text)
        lo_sau_thue = pattern_lo_sau_thue.findall(text)
       
        # Check if the page contains the target keywords
        if "Tài sản" in text or "Vốn điều lệ" in text.lower():
            if "vốn điều lệ của" in text:
                # Find all matches in the data string with case-insensitive matching
                matches_von_dieu_le = re.findall(pattern_von_dieu_le, text, flags=re.IGNORECASE)
            
            if len(text) > 1000:
                df.loc[len(df)] = [i + 1, text]

        if lai_truoc_thue or lai_sau_thue or lo_truoc_thue or lo_sau_thue:
            df = df.append({
            'VonDieuLe': matches_von_dieu_le[0] if matches_von_dieu_le else None,
            'LaiTruocThue': lai_truoc_thue[0] if lai_truoc_thue else None,
            'LoTruocThue': lo_truoc_thue[0] if lo_truoc_thue else None,
            'LaiLoSauThue': lai_sau_thue[0] if lai_sau_thue else None,
            'LaiLoSauThue': lo_sau_thue[0] if lo_sau_thue else None,
            }, ignore_index=True)

        i+=1

    # Write the DataFrame to a CSV file
    df.to_csv('extracted_data.csv', index=False)

        


if __name__ == "__main__":
    main()
