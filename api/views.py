from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pytesseract
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import FinancialDataSerializer
from .D_OCR import process_document

pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

class FinancialDataExtractionView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        print("File",request.FILES.get('file'))
        pdf_file = request.FILES.get('file')
        if not pdf_file:
            return Response({"error": "PDF file is required."}, status=status.HTTP_400_BAD_REQUEST)

        data = process_document(pdf_file) 

        # Return the extracted data
        serializer = FinancialDataSerializer(data=data, many=True)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
