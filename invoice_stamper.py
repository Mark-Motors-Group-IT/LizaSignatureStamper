from tkinter import _test
import os
import shutil
import fitz  # PyMuPDF library  # type: ignore
from datetime import datetime
from PIL import Image, ImageTk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog

# GL Code to Description mappings based on accounting legends
GL_MAPPING = {
    "1494": "Shop Supplies",
    "1502": "Prepaid Advertising",
    "1762": "Furniture & Fixtures",
    "1786": "Computer Equipment",
    "6014": "Advertising",
    "6015": "Sales Promotion",
    "6047": "Express Freight",
    "6051": "Data Processing",
    "6052": "Office Supply",
    "6053": "Telephone",
    "6054": "Travel",
    "6055": "Membership",
    "6084": "Building Maintenance",
    "6103": "Shop Supplies",
    "2803": "Uniform",
    "9003": "Repair Equipment",
    "8200": "Maintenance Building",
    "7900": "Software/Data Processing",
    "6000": "Office Supplies",
    "7000": "Travel",
    "7700": "Training",
    "3200": "Subscription / Membership",
    "28200": "Computer Equipment",
    "64420": "Shop Supplies",
    "64430": "Uniform",
    "64630": "Repair Equipment",
    "60840": "Maintenance Building",
    "60510": "Software/Data Processing",
    "60520": "Office Supplies",
    "60450": "Travel",
    "64440": "Training",
    "60140": "Subscription / Membership",
    "17420": "Computer Equipment"
}

# Location Mappings
LOCATIONS = {
    "JLR": "M1304-JLR00",
    "ALFA/MAS": "M1844",
    "AO": "M",
    "AWO": "H",
    "PORSCHE": "P",
    "AUDI CITY": "L",
    "MERCEDES": "GMB",
    "CORNWALL VW": "CCVW",
    "GATINEAU VW": "GVW"
}

class MonthSelector(tb.Toplevel):
    def __init__(self, parent, base_path):
        super().__init__(parent)
        self.title("Select Month")
        self.geometry("400x350")
        self.parent = parent
        self.base_path = base_path
        self.result = None
        
        self.setup_ui()
        self.center_on_screen()

    def setup_ui(self):
        container = tb.Frame(self, padding=20)
        container.pack(fill="both", expand=True)
        
        tb.Label(container, text="Select Invoice Month", font=("Helvetica", 14, "bold")).pack(pady=(0, 20))
        
        # Get available months
        try:
            months = [d for d in os.listdir(self.base_path) if os.path.isdir(os.path.join(self.base_path, d))]
            months.sort(key=lambda x: os.path.getmtime(os.path.join(self.base_path, x)), reverse=True)
        except Exception:
            months = []
            
        self.month_var = tb.StringVar()
        self.month_btn = tb.Menubutton(container, textvariable=self.month_var, bootstyle="outline-primary")
        self.month_btn.pack(fill="x", pady=10)
        
        self.month_menu = tb.Menu(self.month_btn, tearoff=0)
        for m in months:
            self.month_menu.add_command(label=m, command=lambda val=m: self.month_var.set(val))
        self.month_btn['menu'] = self.month_menu
        
        if months:
            self.month_var.set(months[0])
            
        btn_frame = tb.Frame(container)
        btn_frame.pack(side="bottom", fill="x", pady=(20, 0))
        
        tb.Button(btn_frame, text="Cancel", command=self.destroy, bootstyle="outline-secondary").pack(side="left", expand=True, fill="x", padx=(0, 5))
        tb.Button(btn_frame, text="Open", command=self.on_open, bootstyle="primary").pack(side="right", expand=True, fill="x", padx=(5, 0))

    def on_open(self):
        selected = self.month_var.get()
        if selected:
            path = os.path.join(self.base_path, selected)
            locations_dir = os.path.join(path, "Locations")
            
            # Auto-create Locations folder if it doesn't exist
            if not os.path.exists(locations_dir):
                os.makedirs(locations_dir)
                
            self.result = (path, locations_dir)
            self.destroy()

    def center_on_screen(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

class InvoiceStamperApp:
    def __init__(self, root, month_path):
        self.root = root
        self.root.title("Mark Motors Group - Invoice Approval")
        self.root.geometry("1400x900")
        
        self.month_path = month_path
        locations_dir = os.path.join(month_path, "Locations")
        
        self.pdf_files = []
        
        if os.path.exists(locations_dir):
            for loc_folder in os.listdir(locations_dir):
                if loc_folder.lower() == "approved":
                    continue
                loc_path = os.path.join(locations_dir, loc_folder)
                if os.path.isdir(loc_path):
                    for f in os.listdir(loc_path):
                        if f.lower().endswith('.pdf'):
                            base, ext = os.path.splitext(f)
                            base_lower = base.lower().strip()
                            if base_lower.endswith('approved') or base_lower.endswith('denyed') or base_lower.endswith('denied'):
                                continue
                            self.pdf_files.append({
                                "abs_path": os.path.join(loc_path, f),
                                "filename": f,
                                "location": loc_folder
                            })
        else:
            messagebox.showerror("Error", f"Locations directory '{locations_dir}' does not exist.")
            
        self.current_index = 0
        self.current_pdf_doc = None  
        
        # UI Elements
        self.preview_container = None
        self.preview_label = None
        self.right_frame = None
        self.scroll_frame = None
        self.scroll_content = None
        self.scrollbar = None
        self.title_label = None
        self.status_label = None
        
        self.filename_label = None
        self.location_label = None
        
        self.approve_btn = None
        self.deny_btn = None
        self.back_btn = None
        self.skip_btn = None
        self.finish_btn = None
        
        self.preview_images = [] # Keep references to PhotoImage objects
        
        self.setup_ui()
        self.load_current_pdf()

    def setup_ui(self):
        # Header with Logo
        header_frame = tb.Frame(self.root, bootstyle="dark", padding=10)
        header_frame.pack(fill="x")
        
        try:
            logo_img = Image.open("logo.png")
            # Maintain aspect ratio
            logo_img.thumbnail((250, 60), Image.Resampling.LANCZOS)
            self.logo_tk = ImageTk.PhotoImage(logo_img)
            logo_label = tb.Label(header_frame, image=self.logo_tk, bootstyle="dark")
            logo_label.pack(side="left", padx=20)
        except Exception:
            tb.Label(header_frame, text="MARK MOTORS GROUP", font=("Helvetica", 20, "bold"), bootstyle="inverse-dark").pack(side="left", padx=20)
            
        tb.Label(header_frame, text="INVOICE APPROVAL", font=("Outfit", 16, "bold"), bootstyle="inverse-dark").pack(side="right", padx=30)

        # Main Layout
        self.main_container = tb.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)
        
        self.main_container.columnconfigure(0, weight=3) # Left (PDF)
        self.main_container.columnconfigure(1, weight=1) # Right (Form)
        self.main_container.rowconfigure(0, weight=1)

        # --- Left Frame: PDF Preview ---
        self.left_frame = tb.Frame(self.main_container, padding=10)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        
        # Scrollable Canvas for multi-page preview
        self.preview_canvas = tb.Canvas(self.left_frame, highlightthickness=0)
        self.preview_scrollbar = tb.Scrollbar(self.left_frame, orient="vertical", command=self.preview_canvas.yview)
        self.preview_canvas.configure(yscrollcommand=self.preview_scrollbar.set)
        
        self.preview_scrollbar.pack(side="right", fill="y")
        self.preview_canvas.pack(side="left", fill="both", expand=True)
        
        self.preview_content = tb.Frame(self.preview_canvas, bootstyle="secondary")
        self.preview_window = self.preview_canvas.create_window((0, 0), window=self.preview_content, anchor="nw")
        
        # Sync width and scrollregion
        self.preview_canvas.bind("<Configure>", self._on_preview_canvas_configure)
        self.preview_content.bind("<Configure>", lambda e: self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all")))

        # Global mousewheel binding
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

        # --- Right Frame: Form Inputs ---
        self.right_frame = tb.Frame(self.main_container, padding=20)
        self.right_frame.grid(row=0, column=1, sticky="nsew")

        # Scrollable area for form
        self.scroll_frame = tb.Canvas(self.right_frame)
        self.scroll_content = tb.Frame(self.scroll_frame)
        self.scrollbar = tb.Scrollbar(self.right_frame, orient="vertical", command=self.scroll_frame.yview)
        self.scroll_frame.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.scroll_frame.pack(side="left", fill="both", expand=True)
        self.scroll_id = self.scroll_frame.create_window((0, 0), window=self.scroll_content, anchor="nw")
        
        # Ensure scroll content fits the canvas width
        self.scroll_frame.bind("<Configure>", self._on_canvas_configure)
        self.scroll_content.bind("<Configure>", lambda e: self.scroll_frame.configure(scrollregion=self.scroll_frame.bbox("all")))

        # Title Card
        title_container = tb.Frame(self.right_frame)
        title_container.pack(fill="x", pady=(0, 20), anchor="w")
        
        self.title_label = tb.Label(title_container, text="Invoice Approval", font=("Outfit", 20, "bold"), bootstyle="primary")
        self.title_label.pack(anchor="w")
        
        self.status_label = tb.Label(title_container, text="Loading...", font=("Helvetica", 11), bootstyle="secondary")
        self.status_label.pack(anchor="w")

        tb.Separator(self.right_frame).pack(fill="x", pady=(0, 20))

        # Information Display Card
        info_card = tb.Labelframe(self.scroll_content, text="Details", padding=15, bootstyle="info")
        info_card.pack(fill="x", pady=(0, 20))
        
        tb.Label(info_card, text="File Name:", font=("Helvetica", 10, "bold"), bootstyle="secondary").pack(anchor="w")
        self.filename_label = tb.Label(info_card, text="", font=("Helvetica", 11), wraplength=300)
        self.filename_label.pack(anchor="w", pady=(2, 10))
        
        tb.Label(info_card, text="Staged Location:", font=("Helvetica", 10, "bold"), bootstyle="secondary").pack(anchor="w")
        self.location_label = tb.Label(info_card, text="", font=("Helvetica", 11, "bold"), bootstyle="info")
        self.location_label.pack(anchor="w", pady=(2, 0))

        # --- Action Buttons ---
        
        # Approve Button (Big Green)
        self.approve_btn = tb.Button(
            self.scroll_content, text="Γ£ô Approve", 
            command=self.approve_pdf, bootstyle="success", width=25
        )
        self.approve_btn.pack(fill="x", pady=(0, 10), ipady=12)

        # Deny Button (Big Red)
        self.deny_btn = tb.Button(
            self.scroll_content, text="Γ£ò Deny", 
            command=self.deny_pdf, bootstyle="danger", width=25
        )
        self.deny_btn.pack(fill="x", pady=(0, 20), ipady=12)

        tb.Separator(self.scroll_content).pack(fill="x", pady=10)

        # Navigation Frame
        self.nav_frame = tb.Frame(self.scroll_content)
        self.nav_frame.pack(fill="x", pady=(10, 10))
        
        self.back_btn = tb.Button(
            self.nav_frame, text="Γçá Go Back", 
            command=self.go_back, bootstyle="outline-secondary"
        )
        self.back_btn.pack(side="left", expand=True, fill="x", padx=(0, 5), ipady=8)

        self.skip_btn = tb.Button(
            self.nav_frame, text="Skip Γçó", 
            command=self.skip_pdf, bootstyle="outline-secondary"
        )
        self.skip_btn.pack(side="right", expand=True, fill="x", padx=(5, 0), ipady=8)

        # Finish Button
        self.finish_btn = tb.Button(
            self.scroll_content, text="Γ£ò Finish & Close", 
            command=self.root.destroy, bootstyle="outline-danger", width=25
        )
        self.finish_btn.pack(fill="x", pady=(20, 0), ipady=12)
        
    def _on_canvas_configure(self, event):
        # Update width of scrollable frame to match canvas
        self.scroll_frame.itemconfig(self.scroll_id, width=event.width)
    def _on_preview_canvas_configure(self, event):
        # Update width of PDF preview content to match canvas
        self.preview_canvas.itemconfig(self.preview_window, width=event.width)

    def _on_mousewheel(self, event):
        # Determine which canvas to scroll based on mouse position
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        if not widget: return
        
        # Check if we are over the PDF preview or its children
        is_preview = False
        curr = widget
        while curr:
            if curr == self.preview_canvas:
                is_preview = True
                break
            curr = curr.master
            
        # Check if we are over the form scroll area
        is_form = False
        if not is_preview:
            curr = widget
            while curr:
                if curr == self.scroll_frame:
                    is_form = True
                    break
                curr = curr.master

        if is_preview:
            self.preview_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        elif is_form:
            self.scroll_frame.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def detect_location(self, filename):
        # Sort locations by length descending to match longer names first
        sorted_locs = sorted(LOCATIONS.keys(), key=len, reverse=True)
        for loc in sorted_locs:
            if loc.upper() in filename.upper():
                return loc
            # Also check if the mapped value is in the filename
            val = LOCATIONS[loc]
            if val and val.upper() in filename.upper():
                return loc
        return "Unknown"

    def sanitize_filename(self, text):
        """Remove invalid characters for filenames."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            text = text.replace(char, '')
        return "".join(c for c in text if c.isprintable()).strip()

    def load_current_pdf(self):
        # Update Back button state
        if self.current_index > 0:
            self.back_btn.config(state="normal")
        else:
            self.back_btn.config(state="disabled")

        # Check if we hit the end
        if self.current_index >= len(self.pdf_files):
            self.status_label.config(text="All Invoices Processed!")
            self.title_label.config(text="Finished Batch")
            
            # Clear previous preview
            for widget in self.preview_content.winfo_children():
                widget.destroy()
            self.preview_images = []
            
            tb.Label(self.preview_content, text="No more PDFs to process.\nClick 'Go Back' or 'Finish & Close'.", 
                     font=("Helvetica", 14), bootstyle="secondary").pack(pady=100)
            
            # Disable inputs & forward flow
            self.approve_btn.config(state="disabled")
            self.deny_btn.config(state="disabled")
            self.skip_btn.config(state="disabled")
            
            # Draw attention to finish/back
            self.finish_btn.configure(bootstyle="danger")
            return
            
        # If we are processing normally, ensure inputs are enabled
        self.approve_btn.config(state="normal")
        self.deny_btn.config(state="normal")
        self.skip_btn.config(state="normal")

        # Clear previous preview
        for widget in self.preview_content.winfo_children():
            widget.destroy()
        self.preview_images = []
        
        invoice = self.pdf_files[self.current_index]
        filename = invoice["filename"]
        location = invoice["location"]
        abs_path = invoice["abs_path"]
        
        self.status_label.config(text=f"File {self.current_index + 1} of {len(self.pdf_files)}")
        self.title_label.config(text="Invoice Approval")
        
        self.filename_label.config(text=filename)
        self.location_label.config(text=location)
        
        try:
            if self.current_pdf_doc:
                self.current_pdf_doc.close()
                
            self.current_pdf_doc = fitz.open(abs_path)
            doc = self.current_pdf_doc

            # Dynamically size based on canvas width
            self.preview_canvas.update_idletasks()
            canvas_width = self.preview_canvas.winfo_width()
            target_width = max(600, canvas_width - 30) # Account for scrollbar and padding

            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Render to an image (Pixmap)
                zoom = 1.5 # Balance quality and performance
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                mode = "RGBA" if pix.alpha else "RGB"
                img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                
                # Fit to width
                ratio = target_width / float(img.size[0])
                target_height = int(float(img.size[1]) * ratio)
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                tk_img = ImageTk.PhotoImage(img)
                self.preview_images.append(tk_img) # Keep reference
                
                lbl = tb.Label(self.preview_content, image=tk_img, bootstyle="secondary")
                lbl.pack(pady=10, padx=10, anchor="center")
            
            # Scroll to top
            self.preview_canvas.yview_moveto(0)
        except Exception as e:
            tb.Label(self.preview_content, text=f"Could not load preview:\n{e}").pack(pady=20)

    def approve_pdf(self):
        if self.current_index >= len(self.pdf_files):
            return
            
        invoice = self.pdf_files[self.current_index]
        abs_path = invoice["abs_path"]
        filename = invoice["filename"]
        location = invoice["location"]
        
        # Close PDF doc before moving it
        if self.current_pdf_doc:
            self.current_pdf_doc.close()
            self.current_pdf_doc = None
            
        # Target: Month Path/Locations/Approved/<Location Name>/
        locations_dir = os.path.join(self.month_path, "Locations")
        approved_dir = os.path.join(locations_dir, "Approved")
        dest_dir = os.path.join(approved_dir, location)
        
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            
        base, ext = os.path.splitext(filename)
        new_filename = f"{base} approved{ext}"
        dest_path = os.path.join(dest_dir, new_filename)
        
        # Handle collision
        counter = 1
        while os.path.exists(dest_path):
            counter += 1
            dest_path = os.path.join(dest_dir, f"{base} approved_{counter}{ext}")
            
        try:
            # 1. Open PDF and apply secure stamp
            doc = fitz.open(abs_path)
            page = doc[0]
            
            # Generate security information
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            import socket
            import getpass
            import hashlib
            
            hostname = socket.gethostname()
            username = getpass.getuser()
            
            # Generate a unique secure hash/code based on document content text and supersecretpassword
            supersecretpassword = "MarkMotorsGroup_LizaMrak_SecureApproval_2026_Key!"
            
            text_content = []
            for p in doc:
                for line in p.get_text().splitlines():
                    line_strip = line.strip()
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
                
            hasher.update(hostname.encode())
            hasher.update(username.encode())
            hasher.update(timestamp_str.encode())
            hasher.update(supersecretpassword.encode('utf-8'))
            sec_code = hasher.hexdigest()[:8].upper()
            
            stamp_text = (
                "Liza Mrak - Approved\n"
                f"Date: {timestamp_str}\n"
                f"Host: {hostname}\n"
                f"User: {username}\n"
                f"Code: {sec_code}"
            )
            
            # Draw green box in top-left corner
            rect = fitz.Rect(30, 30, 250, 110)
            
            shape = page.new_shape()
            shape.draw_rect(rect)
            shape.finish(color=(0.0, 0.5, 0.0), fill=(0.9, 1.0, 0.9), fill_opacity=0.9, width=1.5)
            shape.commit()
            
            page.insert_textbox(
                rect, 
                stamp_text, 
                fontsize=10, 
                fontname="helv", 
                color=(0, 0.4, 0),
                align=0
            )
            
            # Set custom metadata in PDF using low-level xref keys
            doc.set_metadata({"title": "Approved Invoice"})
            rc, val = doc.xref_get_key(-1, "Info")
            if rc == "xref":
                info_xref = int(val.replace("0 R", "").strip())
                doc.xref_set_key(info_xref, "ApprovedBy", fitz.get_pdf_str("Liza Mrak"))
                doc.xref_set_key(info_xref, "ApprovedDate", fitz.get_pdf_str(timestamp_str))
                doc.xref_set_key(info_xref, "ApprovedHost", fitz.get_pdf_str(hostname))
                doc.xref_set_key(info_xref, "ApprovedUser", fitz.get_pdf_str(username))
                doc.xref_set_key(info_xref, "ApprovedHash", fitz.get_pdf_str(sec_code))
            
            # Save the stamped PDF
            temp_path = abs_path + ".tmp"
            doc.save(temp_path)
            doc.close()
            
            # Replace original file with stamped temp file
            if os.path.exists(temp_path):
                os.replace(temp_path, abs_path)
                
            # 2. Move to destination directory
            shutil.move(abs_path, dest_path)
            
            self.pdf_files.pop(self.current_index)
            self.load_current_pdf()
        except Exception as e:
            messagebox.showerror("Error", f"Could not approve/stamp invoice:\n{e}")

    def deny_pdf(self):
        if self.current_index >= len(self.pdf_files):
            return
            
        invoice = self.pdf_files[self.current_index]
        abs_path = invoice["abs_path"]
        filename = invoice["filename"]
        
        # Close PDF doc before moving
        if self.current_pdf_doc:
            self.current_pdf_doc.close()
            self.current_pdf_doc = None
            
        file_dir = os.path.dirname(abs_path)
        base, ext = os.path.splitext(filename)
        new_filename = f"{base} denyed{ext}"
        dest_path = os.path.join(file_dir, new_filename)
        
        # Handle collision
        counter = 1
        while os.path.exists(dest_path):
            counter += 1
            dest_path = os.path.join(file_dir, f"{base} denyed_{counter}{ext}")
            
        try:
            shutil.move(abs_path, dest_path)
            self.pdf_files.pop(self.current_index)
            self.load_current_pdf()
        except Exception as e:
            messagebox.showerror("Error", f"Could not deny invoice:\n{e}")

    def skip_pdf(self):
        self.current_index += 1
        self.load_current_pdf()
        
    def go_back(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_pdf()

if __name__ == "__main__":
    BASE_DIR = r"J:\Accounting Marketing\2026"
    if not os.path.exists(BASE_DIR):
        # Fallback to local directory for development/testing
        BASE_DIR = os.path.abspath(r"c:\ITPrograms\Invoiceautomation\mock_J_drive")
        if not os.path.exists(BASE_DIR):
            os.makedirs(BASE_DIR)
            
    # Root with a sleek theme
    root = tb.Window(themename="darkly")
    root.withdraw() # Hide until month is selected
    
    selector = MonthSelector(root, BASE_DIR)
    root.wait_window(selector)
    
    if selector.result:
        month_path, locations_dir = selector.result
        root.deiconify()
        app = InvoiceStamperApp(root, month_path)
        root.mainloop()
    else:
        root.destroy()
