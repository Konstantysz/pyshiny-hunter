# PyShiny Hunter

PyShiny Hunter is a Python-based tool designed to automate shiny Pokémon hunting in Pokémon Black 2 using the DeSmuME emulator. It processes emulator frames, detects encounters, and identifies shiny Pokémon using image processing and OCR.

---

## Features

- Automates shiny Pokémon hunting in Pokémon Black 2.
- Uses OpenCV for image processing and Tesseract OCR for text recognition.
- Supports custom input handling for the DeSmuME emulator.
- Tracks Pokémon encounters and logs results.

---

## Prerequisites

Before setting up the repository, ensure you have the following installed:

1. **Python 3.9 or higher**  
   Download and install Python from [python.org](https://www.python.org/).

2. **Tesseract OCR**

   - Install Tesseract OCR from [Tesseract GitHub](https://github.com/tesseract-ocr/tesseract) or via your package manager:
     - **Windows**: Download the installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
     - **Linux**: Use your package manager (e.g., `sudo apt install tesseract-ocr`).
     - **Mac**: Use Homebrew: `brew install tesseract`.
   - Ensure Tesseract is added to your system's PATH.

3. **DeSmuME Emulator**
   - Install the DeSmuME emulator. This repository uses the `py-desmume` Python bindings for interaction.

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/pyshiny-hunter.git
cd pyshiny-hunter
```

### 2. Create a Virtual Environment

Set up a virtual environment to isolate dependencies:

```bash
python -m venv venv
```

Activate the virtual environment:

- Windows:

```bash
venv/Scripts/Acctivate.ps1
```

- Linux/Mac:

```bash
source venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Verify Tesseract Installation

Ensure Tesseract is correctly installed and accessible:

```bash
tesseract --version
```

## Usage

### 1. Run the Script

Use the py_desmume_hunter.py script to start the shiny hunting process:

```bash
python py_desmume_hunter.py /path/to/my_rom.nds--state /path/to/my_save_state.dst
```

#### Command-Line Arguments:

- `rom`: Path to the `.nds` ROM file (required).
- `--sav`: Path to the `.sav` save file (optional).
- `--state`: Path to the `.dst` save state file (optional).

### 3. Output

- The script will log encounters and notify you when a shiny Pokémon is found.
- Save states for shiny Pokémon will be stored in the `roms/states/` directory.

## Troubleshooting

1. **Tesseract Not Found**
   Ensure Tesseract is installed and added to your system's PATH.

2. **Missing ROM or Save Files**
   Place your `.nds` ROM and save files in the appropriate directories.

3. **Dependencies Not Installed**
   Ensure you activated the virtual environment and installed dependencies using `pip install -r requirements.txt`.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve the project.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
