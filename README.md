<p align="center">
  <a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ">
    <img src="200.webp" alt="Banner">
  </a>
</p>

# 🕵️ OnyIdentity – The Identity Generator

> **Warning:** This tool is for **legitimate testing, education, and creative writing only**. Don't be a dick. Use ethically.

---

## ⚡ Features

- 🎂 **Realistic age distribution** – triangular skew toward younger populations (or uniform with `--no-skew`).
- 🌍 **40+ nationalities** – American, British, German, Japanese, etc. (Faker locales).
- 📏 **Biometrically coherent** – height & weight correlated via healthy BMI.
- 🩸 **Blood type** – real world frequency distribution.
- 🖼️ **Avatar URL** – free DiceBear API (no key, offline fallback optional).
- 🔑 **Password generator** – based on first name + birth year + special char.
- 📁 **Batch generation** – create hundreds at once.
- 💾 **Export to CSV / JSON** – load test your databases.
- 🎛️ **Preset system** – save/load custom fields (job, gender, fixed height, etc.).
- 🔒 **Optional encryption** – protect generated identities with a password (AES‑256 via `cryptography`).
- 🖥️ **CLI + Interactive mode** – script it or play with prompts.
- 🧰 **Standalone EXE** – no Python required for Windows users (see releases).

---

## 🚀 Quick Start

### Option 1: Run from source (Python required)

```bash
git clone https://github.com/Onymouss/OnyIdentity.git
cd OnyIdentity
pip install -r requirements.txt
python OnyIdentity.py 
```

## Option 2: Download the EXE (Windows)
Grab the latest OnyIdentity.exe from Releases. Double click to run.
(No installation, no Python needed.)

---

### 📖 Usage Examples

### Interactive mode
Just run the script / exe and follow the menu.

### CLI

```bash
# Generate 50 French identities (skewed young) and export to CSV
python OnyIdentity.py --age 20-45 --nationality french --count 50 --output french.csv

# Generate 5 identities using a preset, encrypt output
python OnyIdentity.py --age 25-40 --preset developer --count 5 --output devs.json --encrypt MySecret

# Uniform age distribution (no skew)
python OnyIdentity.py --age 18-80 --nationality japanese --count 10 --no-skew
```

### Preset system
Create a folder presets/ next to the script/exe. Save a .preset.json like:

```bash 
json
{
  "job": "Quantum Astrologer",
  "gender": "Non-binary",
  "height_cm": 170,
  "blood_type": "AB-"
}
Then load it with:

In interactive mode: [4] Load preset

In CLI: --preset quantum_astrologer
```

---

## ⚠️ Disclaimer
This tool is for educational and security research purposes only. It should not be used as a replacement for professional antivirus software. also I used AI to clean up some of my code.

---

## 📄 Author
- [@onymouss](https://www.github.com/Onymouss)
