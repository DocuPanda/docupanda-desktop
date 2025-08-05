# 🐼 DocuPanda Desktop

A simple, user-friendly desktop app to effortlessly upload and download datasets with DocuPanda.

---

## 🚀 What is DocuPanda?

[DocuPanda](https://www.docupanda.io) is a powerful document processing platform that transforms your documents into searchable, structured data.

- 🔍 **Searchable PDFs:** Instantly find text using Ctrl+F (Windows/Linux) or Command+F (Mac), thanks to built-in OCR technology.
- 📦 **Standardized JSON Data:** Extract structured data from your documents based on custom schemas defined at [docupanda.io](https://www.docupanda.io).

### 🗂️ Example Output

For instance, from a lease agreement, DocuPanda can extract:
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

✅ DocuPanda handles checkmarks, handwriting, tables, signatures, and more—if you can see it, DocuPanda can process it.

---

## 🎯 Features

### 📤 Easy Upload

- Select "Upload Dataset"
- Choose your folder with documents
- Name your dataset
- (Optional) Choose a schema to standardize the documents (e.g. "rental schema")
- Hit "Confirm Upload"

### 📥 Simple Download

- Select "Download Dataset Results"
- Pick your dataset from the list
- Choose your save location
- Click "Confirm Download"

Downloading the dataset will give you the following things:

1. Every file is downloaded as a PDF with an OCR layer (that means its searchable and copyable) - even if your original upload was an image ot html. So invoice.png -> invoice.pdf 
2. If you chose to also standardize the results, you will also get a .json file with the standardized results. So e.g. rental.pdf -> rental.json

### ❓ What's a Schema?

- A schema is a set of expectations of what you want to extract from a document. Rental amount in a lease, patient insurance number in a medical record, etc.
- You can create your own schemas at [docupanda.io](https://www.docupanda.io). Simply pick a few example documents, and explain with words what you want to extract. DocuPanda will then create a schema for you.
- Once a schema is made, you can apply it to documents of varying layouts, formats, and even languages - even if the schema was created using an English document, you can expect it to work out of the box in German, Chinese or any other 60+ supported languages.

---

## 🛠️ Getting Started

### ✅ Prerequisites

- Python 3.9+
- DocuPanda account with an API key ([Get yours here](https://www.docupanda.io/settings/general))

### 📦 Installation

#### Option 1: Run from Source

```bash
git clone https://github.com/yourusername/docupanda-desktop.git
cd docupanda-desktop
pip install -e .
flet run src/main.py
```

#### Option 2: Build Executable

```bash
bash build.sh
# Find your executable in the 'dist' folder
```

### 🚦 First Use

- Launch the app
- Enter your API key
- You're set to upload & download datasets!

---

## 📑 Supported File Types

- 📄 PDF (`.pdf`)
- 🖼️ Images (`.jpg`, `.jpeg`, `.png`, `.tiff`, `.webp`)
- 📝 Text (`.txt`)
- 📃 HTML and Word (`.html`, `.docx`)

---

## 🐞 Troubleshooting

- ⚠️ **Errors**: Visible in-app
- 📁 **Detailed Logs**:
  - **macOS**: `~/Library/Application Support/DocuPanda/logs/`
  - **Windows**: `%LOCALAPPDATA%\DocuPanda\logs\`
  - **Linux**: `~/.docupanda/logs/`

---

## 🙋‍♂️ Need Help?

- Review your logs first
- Reach out to [DocuPanda Support](https://www.docupanda.io/support) with logs for swift assistance

---

## 📄 License

[MIT License](LICENSE)

