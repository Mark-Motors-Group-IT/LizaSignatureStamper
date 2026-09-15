# Mark Motors Group - Invoice Approval & Digital Signature

This application allows management (Liza Mrak) to review, approve, and digitally stamp invoices across dealership locations with cryptographic tamper-proofing.

## How to Run
1. Double-click **RunInvoiceApproval.bat** (it configures the Python environment and dependencies automatically).
2. Select the month folder from `J:\Accounting Marketing\2026` (e.g., `December`).

## Workflow & Location Filing System
- **Folder Discovery**: The application opens the `Locations` folder for the selected month and scans every location folder (e.g. `Alfa-Mas`, `Audi Ottawa`, `Porsche`, `JLR`, `INEOS`, `Mercedes-Benz`, etc.) for pending PDFs.
- **Approval Workflow**:
  - Signs the PDF with Liza Mrak's tamper-proof digital stamp and metadata.
  - Moves the original unstamped file to `Locations/<Location>/original/<filename>.pdf`.
  - Replaces the file in the location folder (`Locations/<Location>/<filename>.pdf`) with the newly stamped approved copy.
- **Denial Workflow**:
  - Moves denied invoices directly into `Locations/<Location>/denyed/<filename>.pdf`.
- **Automatic Filtering**: Subfolders (`original`, `denyed`, `denied`, etc.) and already stamped/approved invoices are automatically filtered out when opening the month.

## Signature Verification
To independently verify the authenticity of any stamped invoice:
```cmd
python verify_signature.py path\to\invoice.pdf
```

