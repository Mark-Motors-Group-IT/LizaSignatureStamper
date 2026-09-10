# Mark Motors Group - Invoice Approval & Digital Signature

This application allows management (Liza Mrak) to review, approve, and digitally stamp invoices across dealership locations with cryptographic tamper-proofing.

## How to Run
1. Double-click **RunInvoiceApproval.bat** (it will configure the Python environment and dependencies automatically).
2. Select the month folder from J:\Accounting Marketing\2026 to review pending location invoices.

## Features
- **Invoice Review**: Interactive preview of pending invoices organized by location.
- **Approval & Digital Signature**: Stamps the invoice with approval metadata, signer name, timestamp, and a cryptographic verification hash.
- **Denial Workflow**: Moves denied invoices to a designated denied status for follow-up.
- **Signature Verification**: Includes erify_signature.py to independently check any PDF for authentic, untampered digital stamps.

## Signature Verification
To verify the authenticity of an approved invoice:
`cmd
python verify_signature.py path\to\invoice.pdf
`
