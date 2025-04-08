# 🐼 DocuPanda Desktop

> A user-friendly desktop app for uploading and downloading datasets to and from the [DocuPanda](https://www.docupanda.io) platform.

![DocuPanda Logo](src/assets/icon.png)

---

## 🚀 What is DocuPanda?

[DocuPanda](https://www.docupanda.io) is a powerful document processing platform designed to simplify your document workflows by:

1. **Making documents searchable**: Automatically embed OCR (Optical Character Recognition) layers into PDFs, allowing quick text searches (Ctrl+F / Cmd+F).
2. **Standardizing document data**: Extract structured data into consistent JSON formats, tailored to schemas defined by you.

*Example JSON from a lease agreement:*
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

---

## 🌟 Features

### Upload Documents

- Click **"Upload Dataset"**.
- Select a folder containing your documents.
- Enter your dataset name.
- *(Optional)* Choose a schema for data standardization.
- Click **"Confirm Upload"**.

### Download Processed Documents

- Click **"Download Dataset Results"**.
- Select your desired dataset.
- Choose your download destination.
- Click **"Confirm Download"**.

### Supported File Types

- **PDF:** `.pdf`
- **Images:** `.jpg`, `.jpeg`, `.png`, `.tiff`, `.webp`
- **Text:** `.txt`

---

## ⚙️ Getting Started

### Prerequisites

- **Python 3.9+**
- **Active DocuPanda Account & API Key** ([Get API Key](https://www.docupanda.io/settings/general))

### Installation

#### 🔧 Option 1: Run from Source

```bash
git clone https://github.com/yourusername/docupanda-desktop.git
cd docupanda-desktop
pip install -e .
flet run src/main.py
```

#### 🛠️ Option 2: Build Executable

```bash
bash build.sh
```

> Executable found in the `dist/` folder.

### First-time Use

1. Launch DocuPanda Desktop.
2. Enter your DocuPanda API key when prompted.
3. Start uploading and downloading your datasets!

---

## 🐞 Troubleshooting

- **Error Messages**: Displayed directly in the app window.
- **Log Files**: Detailed logs located at:
  - **macOS:** `~/Library/Application Support/DocuPanda/logs/`
  - **Windows:** `%LOCALAPPDATA%\DocuPanda\logs\`
  - **Linux:** `~/.docupanda/logs/`

---

## 🙋‍♀️ Need Help?

- Check log files first for detailed errors.
- [Contact DocuPanda Support](https://www.docupanda.io/support) with logs if issues persist.

---

## 🤝 Contributing

We warmly welcome contributions! Here's how you can help:

1. **Fork** the repository.
2. **Create** a new branch for your feature or bugfix:
   ```bash
   git checkout -b your-feature-name
   ```
3. **Make** your changes and **commit** them clearly.
4. **Push** the branch to your fork:
   ```bash
   git push origin your-feature-name
   ```
5. **Open** a Pull Request (PR). We'll review and merge it as soon as possible!

We're excited to have your contributions to make DocuPanda Desktop even better!

---

## 📄 License

[MIT License](LICENSE)

