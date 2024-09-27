# PDF Financial Statement Data Extraction

Welcome to the **PDF Financial Statement Data Extraction** project! This Python-based tool automates the extraction of financial data from PDF documents, making it easier to obtain key financial metrics such as revenue, expenses, profit, and more.

## 📝 Project Overview

The project uses popular Python libraries like **PyPDF2** and **Pandas** to parse and analyze financial data from PDF files. It’s designed to streamline the data extraction process, reducing manual effort and minimizing errors. The tool is highly customizable, allowing you to define the specific data points and formats you want to extract.

## 🚀 Getting Started

Follow these simple steps to set up the project and start extracting data!

### Prerequisites

Make sure you have **Anaconda** installed on your system. If not, download it [here](https://www.anaconda.com/products/distribution).

### Setting Up the Environment

1. **Create a New Environment**  
   Open the Anaconda Prompt and create a new virtual environment with Python 3.8:
   ```bash
   conda create --name financial_data_extraction python=3.8
   ```

2. **Activate the Environment**  
   Activate your new environment:
   ```bash
   conda activate financial_data_extraction
   ```

3. **Install Required Packages**  
   Navigate to the project directory and install the necessary dependencies:
   ```bash
   cd /path/to/project/directory
   pip install -r requirements.txt
   ```

### Running the Django API

1. **Apply Database Migrations**  
   Ensure the database schema is up to date:
   ```bash
   python manage.py migrate
   ```

2. **Start the Development Server**  
   Run the server to start using the API:
   ```bash
   python manage.py runserver
   ```

## 📂 Project Structure

- `pdf_extractor`: Contains all modules related to PDF parsing and data extraction.
- `api`: Handles the backend logic and API endpoints using Django.
- `tests`: Includes unit tests to ensure the functionality of the project.

## 🤝 Contributing

We welcome contributions! Feel free to open issues or submit pull requests if you have suggestions or improvements.

## 📧 Contact

If you have any questions or need help, feel free to reach out. Happy coding! 😊