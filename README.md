# DocuPanda Desktop

A simple desktop application for uploading and downloading datasets to/from the DocuPanda platform.

<img src="src/assets/icon.png" alt="DocuPanda Logo" width="100" height="100">

## What is DocuPanda?

[DocuPanda](https://www.docupanda.io) is a document processing platform that:

1. **Makes documents searchable** by embedding an OCR (Optical Character Recognition) layer into PDFs, allowing you to search through document text using Ctrl+F/Command+F
2. **Standardizes document data** by extracting structured information into consistent JSON format based on schemas you define on [docupanda.io](https://www.docupanda.io)

   For example, from a lease agreement, DocuPanda might extract:
   ```json
   {
     "rentalAmount": 2000,
     "rentalCurrency": "USD",
     "leaseStartDate": "2025-05-01",
     "leaseEndDate": "2026-04-30",
     "petsAllowed": false,
     "securityDeposit": 3000
   }
   ```

This desktop app makes it easy to:

1. **Upload** documents (PDF, JPG, PNG, etc.) to DocuPanda for processing
2. **Download** the processed, searchable documents along with their structured data (JSON)

## Getting Started

### Prerequisites

- Python 3.9 or higher
- An active DocuPanda account with an API key
  - Get your API key from [DocuPanda Settings Page](https://www.docupanda.io/settings/general)

### Installation

#### Option 1: Run from source

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/docupanda-desktop.git
   cd docupanda-desktop
   ```

2. Install the project and its dependencies:
   ```
   pip install -e .
   ```

3. Run the application:
   ```
   flet run src/main.py
   ```

#### Option 2: Build executable

1. Run the build script:
   ```
   bash build.sh
   ```

2. Find the executable in the `dist` folder

### First Use

1. Launch the application
2. Enter your DocuPanda API key when prompted
3. You're ready to start uploading and downloading datasets!

## Features

### Upload Documents

1. Click "Upload Dataset"
2. Select a folder containing your documents
3. Enter a dataset name
4. Optionally select a schema for standardization
5. Click "Confirm Upload"

### Download Documents

1. Click "Download Dataset Results"
2. Select a dataset from the dropdown
3. Choose a destination folder
4. Click "Confirm Download"

## Supported File Types

- PDF (.pdf)
- Images (.jpg, .jpeg, .png, .tiff, .webp)
- Text (.txt)

## Troubleshooting

- **Error messages**: The app will display error messages in the main window
- **Log files**: Detailed logs are saved in:
  - macOS: `~/Library/Application Support/DocuPanda/logs/`
  - Windows: `%LOCALAPPDATA%\DocuPanda\logs\`
  - Linux: `~/.docupanda/logs/`

## Need Help?

If you encounter any issues or have questions, please:
1. Check the log files for detailed error information
2. Contact DocuPanda support with your log files

## License

[MIT License](LICENSE)