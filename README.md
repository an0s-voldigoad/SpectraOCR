# 🔎 SpectraOCR

<p align="center">
  <b>Advanced OCR • Multilingual Text Extraction • Cybersecurity Intelligence</b><br>
  <i>A beginner-friendly, Linux-focused OCR toolkit built around a single Python application.</i>
</p>

<p align="center">

![Platform](https://img.shields.io/badge/platform-Linux-black?style=for-the-badge&logo=linux)
![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![OCR](https://img.shields.io/badge/OCR-Tesseract-green?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)

</p>

---

## 🧭 What is SpectraOCR?

**SpectraOCR** is a command-line OCR and document-analysis tool designed for Linux users.

It can extract text from images, PDFs, and multiple images at once. It combines multiple image-preprocessing techniques and OCR configurations, then provides a cybersecurity-oriented analysis layer for identifying useful indicators such as IP addresses, URLs, domains, email addresses, hashes, CVE IDs, file paths, and security keywords.

> **Simple idea:** `Image/PDF → OCR → Clean Text → Security Analysis → IOC Extraction → Report`

---

# ✨ Features

### 🖼️ Advanced Image OCR
- Grayscale, contrast enhancement, denoising
- Otsu and adaptive thresholding
- Inverted thresholding
- Multiple Tesseract PSM modes
- OCR confidence scoring
- Multiple-pass result comparison
- Word-level result reconstruction

### 📄 PDF OCR
- Extracts existing PDF text when available
- OCRs scanned/image-based PDF pages
- Handles multi-page documents

### 📁 Batch OCR
Process supported images in a folder:
`.png`, `.jpg`, `.jpeg`, `.bmp`, `.tif`, `.tiff`, `.webp`

### 🧪 Image Preprocessing
Creates:
```text
gray.png
contrast.png
denoised.png
otsu.png
adaptive.png
otsu_inv.png
adaptive_inv.png
```

### 🌍 Multilingual OCR
Uses your installed Tesseract language packs.

Examples:
```text
eng
eng+hin
eng+hin+ben
eng+tam
```

Check languages:
```bash
tesseract --list-langs
```

### 🛡️ Cybersecurity Analysis
Detects patterns for:
- IP addresses
- URLs
- Domains
- Email addresses
- MD5/SHA-1/SHA-256 hashes
- CVE identifiers
- Linux/Windows-style file paths
- Security-related keywords

### 🚨 IOC Extraction
Dedicated extraction of Indicators of Compromise from OCR text.

### 📊 OCR Confidence
Displays confidence information for OCR passes and compares results.

### 📝 Reports
Generates:
- TXT reports
- JSON reports

Reports contain source, language, confidence, OCR text, and detected indicators.

---

# 🖥️ Menu

```text
[1]  Advanced Image OCR
[2]  PDF OCR
[3]  Batch OCR
[4]  Image Preprocessing
[5]  Security Analysis
[6]  IOC Extraction
[7]  Generate Report
[8]  Language Manager
[9]  System Check
[A]  About
[0]  Exit
```

---

# 🚀 Installation

## 1. Clone

```bash
git clone https://github.com/YOUR-USERNAME/SpectraOCR.git
cd SpectraOCR
```

Replace `YOUR-USERNAME` with your GitHub username.

## 2. Install system requirements

Debian/Kali:

```bash
sudo apt update
sudo apt install python3 python3-pip tesseract-ocr
```

Install the Tesseract language packages you need. For example:

```bash
sudo apt install tesseract-ocr-eng
```

Check:

```bash
tesseract --list-langs
```

## 3. Install Python dependencies

```bash
pip3 install -r requirements.txt
```

Dependencies:

```text
opencv-python
numpy
pytesseract
PyMuPDF
```

## 4. Verify

```bash
python3 spectraocr.py --check
```

Version:

```bash
python3 spectraocr.py --version
```

---

# ▶️ Running SpectraOCR

```bash
python3 spectraocr.py
```

Or:

```bash
./spectraocr.py
```

---

# 🧑‍💻 Beginner Quick Start

## 🖼️ OCR an image

Run:

```bash
python3 spectraocr.py
```

Choose:

```text
1 → Advanced Image OCR
```

Enter:

```text
/home/kali/SpectraOCR/test.png
```

Select your language.

SpectraOCR performs multiple OCR passes and displays the strongest result.

## 📄 OCR the included PDF

Choose:

```text
2 → PDF OCR
```

Enter:

```text
/home/kali/SpectraOCR/test.pdf
```

## 📁 Batch OCR

Create a folder:

```bash
mkdir my_images
```

Put images inside it, then choose:

```text
3 → Batch OCR
```

Enter:

```text
my_images
```

The batch output is saved as:

```text
my_images/spectraocr_batch.txt
```

## 🧪 Preprocess an image

Choose:

```text
4 → Image Preprocessing
```

Enter your image path.

Variants are saved to:

```text
spectraocr_preprocessed/
```

## 🛡️ Security Analysis

Run OCR first, then choose:

```text
5 → Security Analysis
```

The extracted text is analyzed for security-relevant patterns.

## 🚨 IOC Extraction

Run OCR first, then:

```text
6 → IOC Extraction
```

## 📝 Generate a report

After OCR:

```text
7 → Generate Report
```

Reports are saved in:

```text
spectraocr_report/
```

---

# 🔬 Example Workflow

```text
                    ┌───────────────┐
                    │ Image / PDF   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  SpectraOCR   │
                    │      OCR      │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Extracted     │
                    │ Text          │
                    └───────┬───────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
        ┌────────────────┐    ┌────────────────┐
        │ Security       │    │ IOC Extraction │
        │ Analysis       │    │                │
        └───────┬────────┘    └───────┬────────┘
                │                     │
                └──────────┬──────────┘
                           ▼
                  ┌─────────────────┐
                  │ TXT / JSON      │
                  │ Report          │
                  └─────────────────┘
```

---

# 🎯 Use Cases

SpectraOCR can be useful for:

- OCR learning and experimentation
- Document digitization
- Screenshot text extraction
- Document analysis
- Defensive security analysis
- Authorized security investigations
- Cybersecurity education
- Security research
- Structured OCR reporting

---

# ⚠️ Limitations

SpectraOCR is an OCR and pattern-analysis tool. It does **not** guarantee that:

- OCR text is perfectly accurate
- A detected IP is malicious
- A URL is malicious
- A detected keyword represents a real credential
- Every IOC will be detected

Poor image quality can reduce OCR accuracy. Important findings should always be verified against the original document.

---

# 🔐 Responsible Use

Use SpectraOCR only on documents, systems, and data you are authorized to inspect.

It is intended for legitimate OCR, defensive security research, cybersecurity education, document processing, and authorized investigations.

Always respect applicable laws, organizational policies, and privacy requirements.

---

# 🗺️ Roadmap

- [ ] Better OCR result ranking
- [ ] Better table extraction
- [ ] Automatic document orientation detection
- [ ] Screenshot-specific OCR mode
- [ ] Better handwriting OCR
- [ ] CSV IOC export
- [ ] HTML reports
- [ ] Additional OCR engines
- [ ] Configurable OCR profiles
- [ ] Confidence visualization
- [ ] Optional threat-intelligence integrations
- [ ] Plugin architecture

---

# 🤝 Contributing

Contributions are welcome.

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/SpectraOCR.git
cd SpectraOCR
```

Test changes with:

```bash
python3 -m py_compile spectraocr.py
python3 spectraocr.py --check
```

Then submit a pull request.

---

# 📂 Project Structure

```text
SpectraOCR/
├── spectraocr.py
├── requirements.txt
├── test.png
├── test.pdf
├── README.md
├── LICENSE
└── .gitignore
```

Generated data such as reports and preprocessing images is created only when those features are used.

---

# 📜 License

SpectraOCR is released under the **MIT License**.

See [`LICENSE`](LICENSE) for the full license text.

---

# ⭐ Support the Project

If SpectraOCR is useful:

⭐ Star the repository  
🐛 Report bugs  
💡 Suggest features  
🔧 Submit improvements  
📢 Share the project

---

<p align="center">
  <b>🔎 SpectraOCR — Read. Analyze. Extract. Report.</b>
</p>
