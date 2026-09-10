import os
import sys
import hashlib
import fitz # type: ignore

def verify_pdf_signature(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' does not exist.")
        return False
        
    try:
        doc = fitz.open(pdf_path)
        
        # Locate Info dictionary
        rc, val = doc.xref_get_key(-1, "Info")
        if rc != "xref":
            doc.close()
            print("====================================================")
            print(" VERIFICATION RESULT: UNSTAMPED / NO DIGITAL SIGNATURE")
            print("====================================================")
            print("This PDF does not contain the required signature metadata.")
            return False
            
        info_xref = int(val.replace("0 R", "").strip())
        
        # Read custom keys
        _, approved_by = doc.xref_get_key(info_xref, "ApprovedBy")
        _, approved_date = doc.xref_get_key(info_xref, "ApprovedDate")
        _, approved_host = doc.xref_get_key(info_xref, "ApprovedHost")
        _, approved_user = doc.xref_get_key(info_xref, "ApprovedUser")
        _, approved_hash = doc.xref_get_key(info_xref, "ApprovedHash")
        
        # Check if keys are null or empty
        if any(x == "null" or not x for x in [approved_by, approved_date, approved_host, approved_user, approved_hash]):
            doc.close()
            print("====================================================")
            print(" VERIFICATION RESULT: UNSTAMPED / NO DIGITAL SIGNATURE")
            print("====================================================")
            print("This PDF is missing digital signature details.")
            return False
            
        # Re-calculate hash for verification using PDF text content layers (excluding the stamp text itself)
        text_content = []
        for p in doc:
            for line in p.get_text().splitlines():
                line_strip = line.strip()
                # Skip the stamp text lines to match the pre-stamped state
                if "Liza Mrak - Approved" in line_strip: continue
                if line_strip.startswith("Date:"): continue
                if line_strip.startswith("Host:"): continue
                if line_strip.startswith("User:"): continue
                if line_strip.startswith("Code:"): continue
                text_content.append(line_strip)
                
        hasher = hashlib.sha256()
        hasher.update("\n".join(text_content).encode('utf-8'))
        hasher.update(str(len(doc)).encode())
        for p in doc:
            hasher.update(str(p.rect.width).encode())
            hasher.update(str(p.rect.height).encode())
            
        doc.close()
            
        # Mix in the signing event data and the password
        supersecretpassword = "MarkMotorsGroup_LizaMrak_SecureApproval_2026_Key!"
        
        hasher.update(approved_host.encode('utf-8'))
        hasher.update(approved_user.encode('utf-8'))
        hasher.update(approved_date.encode('utf-8'))
        hasher.update(supersecretpassword.encode('utf-8'))
        calculated_hash = hasher.hexdigest()[:8].upper()
        
        print("====================================================")
        print("         SIGNATURE VERIFICATION REPORT              ")
        print("====================================================")
        print(f"File:          {os.path.basename(pdf_path)}")
        print(f"Signer Name:   {approved_by}")
        print(f"Approval Date: {approved_date}")
        print(f"Signing Host:  {approved_host}")
        print(f"Signing User:  {approved_user}")
        print(f"Stamp Hash:    {approved_hash}")
        print(f"Verify Hash:   {calculated_hash}")
        print("----------------------------------------------------")
        
        if calculated_hash == approved_hash:
            print(" VERIFICATION STATUS: [SUCCESS] - AUTHENTIC SIGNATURE")
            print(" Authenticated: The PDF content has not been tampered with")
            print(" and was signed on the specified host machine.")
            print("====================================================")
            return True
        else:
            print(" VERIFICATION STATUS: [FAILED] - FAKE OR TAMPERED STAMP")
            print(" Cryptographic verification failed. The hash code does not")
            print(" match, indicating the stamp was copied or files modified.")
            print("====================================================")
            return False
            
    except Exception as e:
        print(f"Error reading PDF or signature details: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_signature.py <path_to_pdf>")
    else:
        verify_pdf_signature(sys.argv[1])
