# OGRES-Writer
# OGRES Writer GUI

<img width="640" height="64" alt="ogreslogo" src="https://github.com/user-attachments/assets/20791b94-a8d1-4b58-aedb-0bcaaa1b2114" />

**OGRES Writer** is a lightweight drag-and-drop GUI tool for packing images into the `.ogres` format. Built with Python and Tkinter, it’s designed for game developers looking to bundle sprite layers or textures into a single binary file for use with the [OGRES C library](https://github.com/yourname/OGRES).

---

## ✨ Features

* 🖼️ Drag-and-drop image loading
* 🪰 Multi-format support (`.png`, `.jpg`, `.bmp`)
* 📦 Outputs `.ogres` files with packed layers
* 💡 Auto-converts images to BGR format 
* 🪟 Simple Tkinter UI — no external dependencies besides `Pillow`

---

## 📷 Screenshots

![OGRES GUI Screenshot](https://github.com/user-attachments/assets/dc3673cf-f091-465c-8aa1-b65fdbd84cf2)

---

## 🐍 Getting Started

### Requirements

* Python 3.8+
* [`Pillow`](https://pypi.org/project/Pillow/)
* [`tkinterdnd2`](https://pypi.org/project/tkinterdnd2/)

### Installation

```bash
pip install pillow tkinterdnd2
```

### Run the app

```bash
python main.py
```
---
💾 How It Works

Each image is converted to raw BGR (no alpha)

Stored as a single .ogres file with headers

Format is directly compatible with ogres.h / ogres.c

---

## 🧠 License

MIT © 2025 Gaetano FosterUse freely for open-source and commercial projects.


