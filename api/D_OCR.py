import easyocr
import re
import cv2
import pdf2image
import numpy as np
import pandas as pd
import pickle
from concurrent.futures import ThreadPoolExecutor
import os

easyocr_reader = easyocr.Reader(['en', 'vi'], gpu=False, verbose=False)  # You can enable GPU by setting gpu=True
max_page_limit = 13 
MODEL_PATH = os.path.join("api", "resource", "text_classification_model.pkl")
with open(MODEL_PATH, "rb") as f:
    text_classification_model = pickle.load(f)

patterns = {
    "lai_truoc_thue": re.compile(r'T.*?LỢI NHUẬN TRƯỚC THU[ÊÉẾE].*?[\s:]?\s*((\(?-?\d{1,3}(?:\.\d{3})*(?:,\d+)?\)?\s*)+)',
                                 re.IGNORECASE),
    "lo_truoc_thue": re.compile(r'Lỗ kế toán trước thuế[\s:]*([\d\.,\-]+)', re.IGNORECASE),
    "lai_sau_thue": re.compile(
        r".*?L[ỢÔƠO]I NHU[AÂẬẠ]N SAU THU[ÊÉẾE][\s:]?\s*(\(?-?\d{1,3}(?:\.\d{3})*\)?)\s+(\(?-?\d{1,3}(?:\.\d{3})*\)?)", re.IGNORECASE),
    "lo_sau_thue": re.compile(r'Lỗ kế toán sau thuế[\s:]*([\d\.,\-]+)', re.IGNORECASE),
    "von_dieu_le": re.compile(r'vốn điều lệ của.*?là\s([\d\.\,]+)\sđong'),
    "date_regex": re.compile(r'Giấy phép Thành lập và Hoạt động số.*? năm (\d{4})'),
    "company_name": re.compile(r'(.*?)(?=\s*Báo cáo tài chính)', re.IGNORECASE),
    "company_taxCode": re.compile(r'mã số doanh nghiệp\s*(\d{10})', re.IGNORECASE),
    "year_col": re.compile(r'(\d{4})\s+(\d{4})\s+Triệu VND', re.IGNORECASE)
}

patterns_process_business_registration = {
    "company_name": re.compile(r'Tên.*?ty.*?viết bằng V[iíìị][êệeẹ]t[:\s]+(.+?)\s+Tên', re.IGNORECASE),
    "von_dieu_le": re.compile(r'v.*?n đ.*?u l.*?.*?[\s:]?\s([\d\.\,]+)\sđ.*ng', re.IGNORECASE),
    "company_taxCode": re.compile(r'Mã số doanh nghiệp[\s:]?\s*(\d+)', re.IGNORECASE),
    "tru_so_chinh": re.compile(
        r"[ĐD]ịa\s*(?:chỉ|chí)?\s*(?:trụ|trú)?\s*(?:sở|số)?\s*(?:chính)?\s*(.+?)\s+[Đđ]iện thoại:", re.IGNORECASE),
    "nam_thanh_lap": re.compile(r'Đăng ký lần đầu[\s:]?\s*ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})')
}

data = []
financial_statement = []
matches_von_dieu_le = []
company_tax_code = []
lai_truoc_thue = []
lo_truoc_thue = []
lai_sau_thue = []
lo_sau_thue = []
date_match = []
company_name = []
global years
company_address = []


def extract_text_and_detect(pages):
    first_page_text = extract_text_from_image(pages[0])
    first_page_text = clean_text(first_page_text)
    document_type = detect_document_type(first_page_text)

    return document_type


def clean_text(text):
    cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
    return ' '.join(cleaned_lines)


def preprocess_text(text):
    """
    Preprocess the input text for better classification.
    :param text: Raw input text.
    :return: Preprocessed text.
    """
    processed_text = text.lower().strip()
    return processed_text


def detect_document_type(text):
    """
    Detect the type of document based on the text using a pre-trained classification model.
    :param text: Text content of the document.
    :return: Document type as an integer (0, 1, or -1).
    """
    # Preprocess the text before classification
    preprocessed_text = preprocess_text(text)

    # Use the loaded model to predict the document type
    predicted_label = text_classification_model.predict([preprocessed_text])

    # Return the corresponding document type
    if predicted_label == 0:
        return 0
    elif predicted_label == 1:
        return 1
    else:
        return -1


def process_financial_statement(pages):
    years = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(
                process_page,
                i, page, company_name, company_tax_code, matches_von_dieu_le,
                lai_truoc_thue, lo_truoc_thue, lai_sau_thue, lo_sau_thue, date_match, years
            )
            for i, page in enumerate(pages)
        ]
        for future in futures:
            future.result()

    years = [year for match in years for year in match]

    if lai_truoc_thue or lai_sau_thue or lo_truoc_thue or lo_sau_thue or matches_von_dieu_le:
        for i, y in enumerate(years):
            if i < len(lai_truoc_thue[0]):
                accounting_loss_before_tax = float(lai_truoc_thue[0][i].split()[0].replace('.', '').strip())
            else:
                accounting_loss_before_tax = None

            if i < len(lai_sau_thue[0]):
                accounting_loss_after_tax = float(lai_sau_thue[0][i].replace('.', '').strip())
            else:
                accounting_loss_after_tax = None

            # Append the data for each year
            financial_statement.append({
                "year": int(y),  # Convert year to integer
                "accounting_loss_before_tax": accounting_loss_before_tax,
                "accounting_loss_after_tax": accounting_loss_after_tax,
            })

        data.append(
            {
                "tax_code": clean_field(company_tax_code[0].replace('\n', '')) if company_tax_code else "",
                "company_name": clean_field(company_name[0].replace('\n', ' ')) if company_name else "",
                "address": "Some Address",
                "start_years_of_business": clean_field(date_match[0]) if date_match else "",
                "is_business": True,
                "dl": int(
                    process_tuple_or_string(matches_von_dieu_le[0]).replace('.', '')) if matches_von_dieu_le else None,
                # Von Dieu Le
                "financial_statement": financial_statement
            }
        )

    df = pd.DataFrame(
        data=data,
        columns=[
            "tax_code",
            "company_name",
            "address",
            "start_years_of_business",
            "is_business",
            "dl",
            "financial_statement"
        ],
    )

    print(df)
    return df.to_dict(orient='records')


def process_business_registration(pages):
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(process_business_registration_page, i, page, company_name, company_tax_code,
                                   matches_von_dieu_le, date_match, company_address) for i, page in enumerate(pages)]
        for future in futures:
            future.result()

    date_match_process = ""
    if date_match:
        date_match_process = extract_date(date_match[0])

    print("data", company_tax_code, company_name, "Diachi:", company_address, date_match_process,
          matches_von_dieu_le)
    financial_statement.append({
        "year": None,
        "accounting_loss_before_tax": None,
        "accounting_loss_after_tax": None,
    })

    data.append(
        {
            "tax_code": clean_field(company_tax_code[0].replace('\n', '')) if company_tax_code else "",
            "company_name": clean_field(company_name[0].replace('\n', ' ')) if company_name else "",
            "address": clean_field(company_address[0]) if company_address else "",
            "start_years_of_business": date_match_process if date_match_process else "",
            "is_business": True,
            "dl": int(
                process_tuple_or_string(matches_von_dieu_le[0]).replace('.', '')) if matches_von_dieu_le else None,
            "financial_statement": financial_statement
        }
    )
    df = pd.DataFrame(
        data=data,
        columns=[
            "tax_code",
            "company_name",
            "address",
            "start_years_of_business",
            "is_business",
            "dl",
            "financial_statement"
        ],
    )
    return df.to_dict(orient='records')


def extract_date(text):
    if text:
        day, month, year = text
        formatted_date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        return formatted_date
    else:
        return None


def extract_text_from_image(page):
    """
    Extracts text from an image using EasyOCR.
    :param image_path: Path to the image file.
    :return: Extracted text as a string.
    """
    gray = cv2.cvtColor(np.array(page), cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    result = easyocr_reader.readtext(thresh, detail=0)  # detail=0 returns only the text
    return ' '.join(result)


def process_page(i, page, company_name, company_taxCode, matches_von_dieu_le, lai_truoc_thue, lo_truoc_thue,
                 lai_sau_thue, lo_sau_thue, date_match, years):
    """
    Processes a single page to extract relevant financial information.
    :param i: Page index.
    :param page: Path to the page image or image object.
    :param company_name: List to store extracted company names.
    :param company_taxCode: List to store extracted company tax codes.
    :param matches_von_dieu_le: List to store 'von dieu le' matches.
    :param lai_truoc_thue: List to store 'lai truoc thue' matches.
    :param lo_truoc_thue: List to store 'lo truoc thue' matches.
    :param lai_sau_thue: List to store 'lai sau thue' matches.
    :param lo_sau_thue: List to store 'lo sau thue' matches.
    :param date_match: List to store extracted date matches.
    :param years: List to store extracted years.
    """
    text = extract_text_from_image(page)
    text = clean_text(text)
    
    if(i==12 or i == 11):
        print(text)
    if i == 0:
        company_name.extend(patterns["company_name"].findall(text))
    if not date_match:
        date_match.extend(patterns["date_regex"].findall(text))
    if not years:
        years_match = patterns["year_col"].findall(text)
        if years_match:
            years.extend(patterns["year_col"].findall(text))

    if len(text) > 1000:
        if not company_taxCode:
            company_taxCode.extend(patterns["company_taxCode"].findall(text))
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


def process_business_registration_page(i, page, company_name, company_taxCode, matches_von_dieu_le, date_match,
                                       comp_address):
    text = extract_text_from_image(page)
    text = clean_text(text)

    if not company_name:
        company_name.extend(patterns_process_business_registration["company_name"].findall(text))
    if not date_match:
        date_match.extend(patterns_process_business_registration["nam_thanh_lap"].findall(text))
    if not company_taxCode:
        company_taxCode.extend(patterns_process_business_registration["company_taxCode"].findall(text))
    if not comp_address:
        comp_address.extend(patterns_process_business_registration["tru_so_chinh"].findall(text))
        if company_address:
            comp_address = [match.strip() for match in comp_address] if comp_address else []
    if not matches_von_dieu_le:
        matches_von_dieu_le.extend(patterns_process_business_registration["von_dieu_le"].findall(text))


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
    pages = pdf2image.convert_from_bytes(pdf_file.read(), poppler_path=r'D:\\pj\RPA_PJ\\PDF-Financial--Statement-DataExtraction\\api\\resource\\poppler-24.07.0\\Library\\bin')
    years = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(process_page, i, page, company_name, company_tax_code, matches_von_dieu_le, lai_truoc_thue,
                            lo_truoc_thue, lai_sau_thue, lo_sau_thue, date_match, years) 
                            for i, page in enumerate(pages) if i <= max_page_limit]
        for future in futures:
            future.result()

    years = [year for match in years for year in match]

    if lai_truoc_thue or lai_sau_thue or lo_truoc_thue or lo_sau_thue or matches_von_dieu_le:
        for i, y in enumerate(years):
            if i < len(lai_truoc_thue[0]):
                accounting_loss_before_tax = float(lai_truoc_thue[0][i].split()[0].replace('.', '').strip())
            else:
                accounting_loss_before_tax = None

            if i < len(lai_sau_thue[0]):
                accounting_loss_after_tax = float(lai_sau_thue[0][i].replace('.', '').strip())
            else:
                accounting_loss_after_tax = None

            # Append the data for each year
            financial_statement.append({
                "year": int(y),  # Convert year to integer
                "accounting_loss_before_tax": accounting_loss_before_tax,
                "accounting_loss_after_tax": accounting_loss_after_tax,
            })

        data.append(
            {
                "tax_code": clean_field(company_tax_code[0].replace('\n', '')) if company_tax_code else "",
                "company_name": clean_field(company_name[0].replace('\n', ' ')) if company_name else "",
                "address": "Some Address",
                "start_years_of_business": clean_field(date_match[0]) if date_match else "",
                "is_business": True,
                "dl": int(
                    process_tuple_or_string(matches_von_dieu_le[0]).replace('.', '')) if matches_von_dieu_le else None,
                # Von Dieu Le
                "financial_statement": financial_statement
            }
        )

    df = pd.DataFrame(
        data=data,
        columns=[
            "tax_code",
            "company_name",
            "address",
            "start_years_of_business",
            "is_business",
            "dl",
            "financial_statement"
        ],
    )

    print(df)
    return df.to_dict(orient='records')


def process_document(pdf_file):
    pages = pdf2image.convert_from_bytes(pdf_file.read())
    document_type = extract_text_and_detect(pages)
    print(f"Detected document type: {document_type}")

    if document_type == 0:
        return process_financial_statement(pages)
    elif document_type == 1:
        return process_business_registration(pages)
    else:
        return print("Unknown document type. Cannot process.")
