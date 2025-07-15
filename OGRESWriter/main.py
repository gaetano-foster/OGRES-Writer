import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import struct
from tkinterdnd2 import TkinterDnD, DND_FILES

# --- OGRES File Format Constants ---
OGRES_HEADER = b'OGRES'
OGRES_LAYER_HEADER_SIZE = 6  # 2 (width) + 2 (height) + 2 (sz_total)

class OGRESConverter(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.iconbitmap("ogres.ico")
        self.title("OGRES Writer")
        self.geometry("600x400")
        self.images = []  # Stores (Image, path) tuples

        # GUI Elements
        self.setup_ui()

    def setup_ui(self):
        # drag and drop area
        self.drop_area = tk.Label(
            self,
            text="Drag & Drop Images Here\n(or click to browse)",
            relief="groove",
            padx=20,
            pady=20
        )
        self.drop_area.pack(fill="both", expand=True, padx=10, pady=10)
        self.drop_area.bind("<Button-1>", self.browse_files)

        # enable drag and drop
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.on_drop)

        # image list preview
        self.tree = ttk.Treeview(self, columns=("Path"), show="headings")
        self.tree.heading("Path", text="Loaded Images")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # save button
        self.save_btn = tk.Button(
            self,
            text="Save as OGRES",
            command=self.save_ogres,
            state="disabled"
        )
        self.save_btn.pack(pady=10)

    def browse_files(self, event):
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")]
        )
        if files:
            self.load_images(files)

    def on_drop(self, event):
        # extract file paths from the drag and drop event
        files = self.tk.splitlist(event.data)
        valid_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        if valid_files:
            self.load_images(valid_files)

    def load_images(self, files):
        for path in files:
            try:
                img = Image.open(path)
                self.images.append((img, path))
                self.tree.insert("", "end", values=(os.path.basename(path)))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load {path}: {e}")

        if self.images:
            self.save_btn.config(state="normal")

    def save_ogres(self):
        if not self.images:
            return

        output_path = filedialog.asksaveasfilename(
            title="Save OGRES File",
            defaultextension=".ogres",
            filetypes=[("OGRES Files", "*.ogres")]
        )
        if not output_path:
            return

        try:
            with open(output_path, "wb") as f:
                # Write global header (OGRES + layer count + total size placeholder)
                f.write(OGRES_HEADER)
                f.write(struct.pack("<H", len(self.images)))  # <H = little-endian WORD
                f.write(b"\x00\x00\x00\x00")  # Placeholder for total size (DWORD)

                # Write each layer
                layer_data = []
                for img, _ in self.images:
                    # Convert to BGR (strip alpha if needed)
                    if img.mode == "RGBA":
                        img = img.convert("RGB")
                    pixels = img.tobytes()

                    # Layer header: width (WORD), height (WORD), sz_total (WORD)
                    width, height = img.size
                    sz_total = OGRES_LAYER_HEADER_SIZE + len(pixels)
                    layer_header = struct.pack("<HHH", width, height, sz_total)

                    # Combine header + pixel data
                    layer_data.append(layer_header + pixels)

                # Calculate total size and update header
                total_size = sum(len(layer) for layer in layer_data)
                f.seek(7)  # Skip header (5 + 2 bytes)
                f.write(struct.pack("<I", total_size))  # Update total size (DWORD)

                # Write all layers
                for layer in layer_data:
                    f.write(layer)

            messagebox.showinfo("Success", f"Saved {len(self.images)} layers to:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save OGRES file: {e}")


if __name__ == "__main__":
    app = OGRESConverter()
    app.mainloop()