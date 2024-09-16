from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

class FinancialDataExtractionViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('financial-data-extract')  # Use the name of the URL pattern

    def test_extract_financial_data_success(self):
        # Simulate a file upload
        pdf_content = b'%PDF-1.4 example pdf content'  # This should be a valid PDF content
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")

        # Send POST request with file
        response = self.client.post(self.url, {'file': pdf_file}, format='multipart')

        # Check the response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Here, add assertions to check if the returned data matches the expected output

    def test_extract_financial_data_no_file(self):
        # Send POST request without file
        response = self.client.post(self.url, {}, format='multipart')

        # Check the response status
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "PDF file is required.")
