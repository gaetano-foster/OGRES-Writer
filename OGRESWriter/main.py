import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import struct
from tkinterdnd2 import TkinterDnD, DND_FILES

# --- ogres file format constants ---
OGRES_HEADER = b'OGRES'
OGRES_LAYER_HEADER_SIZE = 6  # 2 (width) + 2 (height) + 2 (sz_total)

class OGRESConverter(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("OGRES Converter")
        self.geometry("600x520")
        self.images = []

        self.setup_ui()

    def setup_ui(self):
        # drag & drop area
        self.drop_area = tk.Label(
            self,
            text="Drag & Drop Images or .ogres Here\n(or click to browse)",
            relief="groove",
            padx=20,
            pady=20
        )
        self.drop_area.pack(fill="both", expand=True, padx=10, pady=10)
        self.drop_area.bind("<Button-1>", self.browse_files)

        # enable drag and drop
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.on_drop)

        # sprite sheet slicing controls
        cells_frame = tk.Frame(self)
        cells_frame.pack(fill="x", padx=10, pady=(0,8))

        self.cells_var = tk.BooleanVar(value=False)
        self.cells_chk = tk.Checkbutton(cells_frame, text="Add as sprite sheet?", variable=self.cells_var)
        self.cells_chk.pack(side="left")

        tk.Label(cells_frame, text="Sprite width:").pack(side="left", padx=(12,2))
        self.cell_w_entry = tk.Entry(cells_frame, width=6)
        self.cell_w_entry.pack(side="left")

        tk.Label(cells_frame, text="Sprite height:").pack(side="left", padx=(12,2))
        self.cell_h_entry = tk.Entry(cells_frame, width=6)
        self.cell_h_entry.pack(side="left")

        tk.Label(cells_frame, text="Number of sprites:").pack(side="left", padx=(12, 2))
        self.cell_n_entry = tk.Entry(cells_frame, width=6)
        self.cell_n_entry.pack(side="left")

        # image list preview
        self.tree = ttk.Treeview(self, columns=("Path"), show="headings", height=8)
        self.tree.heading("Path", text="Loaded Images")
        self.tree.pack(fill="both", expand=False, padx=10, pady=5)

        # action buttons
        btns = tk.Frame(self)
        btns.pack(fill="x", padx=10, pady=8)

        self.clear_btn = tk.Button(btns, text="Clear", command=self.clear_list)
        self.clear_btn.pack(side="left")

        self.save_btn = tk.Button(btns, text="Save as OGRES", command=self.save_ogres, state="disabled")
        self.save_btn.pack(side="right")

    def browse_files(self, event=None):
        files = filedialog.askopenfilenames(
            title="Select Images or .ogres",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp"),
                ("OGRES Files", "*.ogres"),
                ("All Supported", "*.png *.jpg *.jpeg *.bmp *.ogres")
            ]
        )
        if files:
            self.load_inputs(files)

    def on_drop(self, event):
        # extract file paths from drop
        files = self.tk.splitlist(event.data)
        self.load_inputs(files)

    def load_inputs(self, files):
        # route .ogres files to importer, others as images (optionally slice)
        added = 0
        for path in files:
            lower = path.lower()
            try:
                if lower.endswith(".ogres"):
                    count = self.import_ogres(path)
                    added += count
                elif lower.endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    self.load_image_or_sheet(path)
                    added += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load {path}:\n{e}")

        if self.images:
            self.save_btn.config(state="normal")

        if added > 0:
            messagebox.showinfo("Loaded", f"added {added} item(s)")

    def load_image_or_sheet(self, path):
        img = Image.open(path)
        if self.cells_var.get():
            cw = self._parse_int(self.cell_w_entry.get())
            ch = self._parse_int(self.cell_h_entry.get())
            if cw is None or ch is None or cw <= 0 or ch <= 0:
                messagebox.showwarning("cells", "invalid cell size; adding image as-is")
                self._append_image(img, path)
                return
            tiles = self.slice_sheet(img, cw, ch, os.path.basename(path))
            for tile, name in tiles:
                self.images.append((tile, name))
                self.tree.insert("", "end", values=(name,))
        else:
            self._append_image(img, path)

    def slice_sheet(self, img, cell_w, cell_h, base_name):
        # simple grid slice; ignores partial edges
        num_cells = self._parse_int(self.cell_n_entry.get())
        idx = 1
        should_stop = True
        if num_cells is None or num_cells == 0:
            messagebox.showwarning("Unspecified Sprite Count")
            should_stop = False
        cols = img.width // cell_w
        rows = img.height // cell_h
        if cols == 0 or rows == 0:
            raise ValueError("cell size larger than image")

        tiles = []
        for r in range(rows):
            for c in range(cols):
                box = (c * cell_w, r * cell_h, c * cell_w + cell_w, r * cell_h + cell_h)
                tile = img.crop(box)
                name = f"{base_name}_{r}_{c}"
                tiles.append((tile, name))
                if idx == num_cells:
                    break
                else:
                    idx += 1
            if idx == num_cells:
                break
        return tiles

    def import_ogres(self, path):
        # read .ogres and append its images
        with open(path, "rb") as f:
            # header
            magic = f.read(5)
            if magic != OGRES_HEADER:
                raise ValueError("not an OGRES file")
            layer_count = struct.unpack("<H", f.read(2))[0]
            sz_image = struct.unpack("<I", f.read(4))[0]

            start = f.tell()
            end = start + sz_image
            if sz_image == 0:
                return 0

            count = 0
            for i in range(layer_count):
                # layer header
                wh = f.read(6)
                if len(wh) != 6:
                    raise ValueError("truncated layer header")
                width, height, sz_total = struct.unpack("<HHH", wh)

                # pixel data
                pixel_bytes = width * height * 3
                data = f.read(pixel_bytes)
                if len(data) != pixel_bytes:
                    raise ValueError("truncated pixel data")

                # note: do not change channel order. preserve exactly as stored.
                img = Image.frombytes("RGB", (width, height), data)

                name = f"{os.path.basename(path)}_layer_{i}"
                self.images.append((img, name))
                self.tree.insert("", "end", values=(name,))
                count += 1

            # safety: ensure we didn't read past declared region
            if f.tell() > end:
                raise ValueError("read beyond declared sz_image region")
            return count

    def _append_image(self, img, path):
        name = os.path.basename(path)
        self.images.append((img, name))
        self.tree.insert("", "end", values=(name,))

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
            # build layers in memory
            layer_blobs = []
            for img, _ in self.images:
                # do not alter channel order; keep current behavior
                if img.mode == "RGBA":
                    img = img.convert("RGB")
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                pixels = img.tobytes()  # keep as-is
                width, height = img.size
                sz_total = OGRES_LAYER_HEADER_SIZE + len(pixels)
                header = struct.pack("<HHH", width, height, sz_total)
                layer_blobs.append(header + pixels)

            total_size = sum(len(b) for b in layer_blobs)

            with open(output_path, "wb") as f:
                # global header
                f.write(OGRES_HEADER)
                f.write(struct.pack("<H", len(layer_blobs)))
                f.write(struct.pack("<I", total_size))

                # layers
                for blob in layer_blobs:
                    f.write(blob)

            messagebox.showinfo("Success", f"saved {len(layer_blobs)} layers to:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save OGRES file:\n{e}")

    def clear_list(self):
        # clear both ui and cache
        self.images.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.save_btn.config(state="disabled")

    def _parse_int(self, s):
        try:
            return int(s.strip())
        except Exception:
            return None


if __name__ == "__main__":
    app = OGRESConverter()
    app.mainloop()
