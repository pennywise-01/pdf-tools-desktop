# PDF Tools Desktop App - Development Plan

This document outlines the architecture, principles, and development roadmap for the PDF Tools Desktop application. It is designed to be a comprehensive guide for developers.

---

## 1. Core Principles & Mandatory Requirements

These are foundational rules that must be applied across all stages of development. They are not optional.

*   **Security First:** Every feature, from file handling to UI, must be implemented with security as the primary consideration. This includes input validation, secure file operations, and protecting user data.
*   **Local-Only Operation (Default):** The application must be fully functional offline. By default, it is forbidden from making any outbound network calls. Any optional network features (like license validation or cloud integration) must be explicitly enabled by the user with clear consent.
*   **User Privacy by Design:** The application must not collect, store, or transmit any personal user data or document contents. All processing must happen on the user's local machine.
*   **Cross-Platform Goal:** While development may start on a single OS, the long-term goal is to ensure compatibility with Windows, macOS, and Linux. Technology choices should reflect this.
*   **Transparent Auditing:** An encrypted, local-only audit log should be maintained for all significant file modification events, providing users with a history of their actions for compliance or personal tracking.

---

## 2. Desktop Application Architecture

This is a standalone desktop application, not a web service. This has important architectural implications:

*   **No Hosted Backend:** The application does not require a backend server for its core functionality. All PDF processing logic runs directly on the user's computer. The "backend" is simply the Python code that responds to user interactions in the UI.
*   **Local File System:** The app reads from and writes to the user's local file system directly.
*   **Native UI:** The user interface, built with PyQt6, is a native OS window, providing the performance and feel of a traditional desktop program.
*   **Self-Contained:** The final distributable application will be a self-contained package (e.g., an `.exe` or `.app`) with the Python interpreter and all necessary libraries bundled inside. No external dependencies are needed for the user to install.

---

## 3. Tech Stack

*   **Core:** Python 3.11+, PyQt6 (for the UI)
*   **PDF Libraries:** `pikepdf` (structure/security), `PyMuPDF` (rendering/conversion), `pdf2docx` (Word conversion)
*   **Security Libraries:** `cryptography` (for AES encryption & audit logs), `pyarmor` (for code obfuscation)
*   **OCR Engine:** Tesseract

---

## 4. MVP Development Plan

Development will proceed in stages (MVPs). "Simple Tasks" are foundational, while "Complex Tasks" may be designated as "Pro" features in the monetized version.

### MVP 1: The "Secure Core" & Basic Manipulation
**Goal:** A working app that can open, save, and perform core structural changes securely.
*   **Simple Task:** Merge multiple PDFs into one.
*   **Complex Task:** Split a PDF by a user-defined page range (e.g., "1-5, 8, 11-15"), with robust validation.
*   **Complex Task:** Remove selected pages from a PDF.
*   **Security Feature:** AES-256 password protection (setting user and owner passwords).

### MVP 2: The "Visual Architect"
**Goal:** Enable visual interaction with PDF pages for intuitive editing.
*   **Simple Task:** Rotate pages by 90-degree increments.
*   **Complex Task:** An interactive "Grid View" with page thumbnails for drag-and-drop page reordering.
*   **Complex Task:** Extract selected pages into a new PDF document.
*   **Security Feature:** Metadata Scrubber to remove fields like Author, GPS data, etc.

### MVP 3: The "Converter" - Images & HTML
**Goal:** Move data from common formats *into* the PDF format.
*   **Simple Task:** Convert multiple JPG/PNG images into a single PDF.
*   **Complex Task:** Convert a local HTML file or a URL into a PDF document.
*   **Complex Task:** Render PDF pages as high-resolution (e.g., 300 DPI) JPG/PNG images.
*   **Security Feature:** Digital Signatures (PAdES standard) using a user-provided .p12/.pfx certificate.

### MVP 4: The "Optimizer" & Redaction
**Goal:** Manage file size and permanently remove sensitive content.
*   **Simple Task:** Add a text watermark (e.g., "CONFIDENTIAL") to pages.
*   **Complex Task:** Smart Compression with a quality slider (balancing image downsampling, font subsetting, etc.).
*   **Complex Task:** True Redaction that "burns" content out of the file, rather than just covering it.
*   **Security Feature:** Secure File Shredding (DoD 5220.22-M) to make deleted files unrecoverable.

### MVP 5: The "Intelligent Layer" - OCR
**Goal:** Make scanned documents searchable and usable.
*   **Simple Task:** Repair corrupted PDF files by rebuilding the XREF table.
*   **Complex Task:** Integrate the Tesseract OCR engine to add an invisible, searchable text layer to image-based PDFs.
*   **Security Feature:** Local-Only Network Lock (a hard-coded block on all outbound network calls).

### MVP 6: The "Office Bridge"
**Goal:** Interoperability with Microsoft Office formats.
*   **Simple Task:** Extract all text from a PDF into a plain `.txt` file.
*   **Complex Task:** Convert PowerPoint (`.pptx`) and Excel (`.xlsx`) files to PDF.
*   **Complex Task:** Convert a PDF into a Microsoft Excel (`.xlsx`) file, detecting and reconstructing tables.
*   **Complex Task:** Convert a PDF into a Microsoft Word (`.docx`) file, reconstructing layouts, paragraphs, and tables.
*   **Security Feature:** Implement the encrypted local Audit Log.

---

## 5. Monetization Plan (Phase 2)

Once the core features are built, these MVPs will focus on creating a "Pro" version.

### MVP 7: Monetization & Licensing
**Goal:** Implement a "Freemium" model where core features are free and advanced ("Complex Task") features require payment.
*   **UI Locking:** Mark Pro features in the UI. Clicking them prompts the user to purchase a license.
*   **Payment Workflow:**
    1.  **Model:** A **one-time payment** for a perpetual license is recommended for this type of utility. It's user-friendly and avoids subscription fatigue.
    2.  **Gateway:** Use **Paddle** as the Merchant of Record. It handles all tax compliance (VAT, sales tax) automatically, which is a major burden for solo developers.
    3.  **Activation:** Upon payment, the user receives a license key. The app must have a window to enter the key.
*   **Security Feature:** Use asymmetric cryptography for **offline license key validation**. The app holds a public key to verify licenses signed by a private key on the payment server. This respects the local-only principle.

### MVP 8: Anti-Tampering
**Goal:** Harden the application against attempts to bypass the paywall.
*   **Code Obfuscation:** Use `pyarmor` to make the Python bytecode unreadable, protecting the licensing logic.
*   **Integrity Checks:** The app should calculate a checksum of its own core files on startup and exit if tampering is detected.
*   **Anti-Analysis:** Implement checks to detect if the app is running inside a debugger or a known reverse-engineering virtual machine, and refuse to run if so.

---

## 6. Suggestions for Success

1.  **Iterative User Feedback:** After MVP 1-2 are complete, release an alpha version to a small group of users and gather feedback to guide further development.
2.  **Focus on Performance:** PDF operations can be slow. Use background threads (`QThread` in PyQt6) extensively to ensure the UI remains responsive at all times.
3.  **Invest in Professional UI/UX:** A clean, intuitive, and professional-looking interface is not an afterthought—it is critical for user trust and adoption. Establish a consistent design language and workflow from the start.

---

## 7. Build & Distribution

*   **Packaging:** Use `PyInstaller` or `cx_Freeze` to package the Python application, its dependencies, and the Tesseract binaries into a single, self-contained executable for each target platform (Windows, macOS, Linux).
*   **Code Signing:** For Windows and macOS, purchase a code-signing certificate to sign the final executable. This is essential to avoid warnings from operating systems and antivirus software, and it is a prerequisite for distribution on platforms like the Mac App Store.

---

## 8. MVP7 Implementation and Production Activation Docs

The implementation status, architecture choice, and full production go-live checklist for licensing are documented in:

*   `docs/licensing/MVP7_IMPLEMENTATION_AND_GO_LIVE.md`
*   `docs/licensing/MVP7_LICENSE_RUNBOOK.md`
*   `services/licensing-worker/README.md`
*   `services/licensing-worker/openapi.yaml`