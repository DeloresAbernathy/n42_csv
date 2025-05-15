# n42_csv

This tool processes `.n42` gamma spectrum files and overlays peaks exported from Interspec-generated `.csv` output.

It lets you:
- Visualise the spectrum and compare it to expected peak energies
- Use Interspec CSV to highlight identified peaks without re-analyzing 
- save peak.csv from Interspec (reuse it fro n42 spectrum)
- Generate:
  - A JSON structure usable to load it via example_json_input.html
  - or create standalone.html via test.py
  - or spectrum.html (open via server)-> XMLHttpRequest() blocked by browers file://
  - A PNG log-scale spectrum plot with labeled peaks
  - 

---

## 🔧 Installation

This project depends on [`SandiaSpecUtils`](https://github.com/sandialabs/SpecUtils), which must be **built from source**.

> **Note:** There are no PyPI or wheel packages for `SpecUtils`.

### 1. Install `SpecUtils`

```bash
git clone https://github.com/sandialabs/SpecUtils.git
cd SpecUtils/bindings/python
(
python3 -m venv .venv 
source .venv/bin/activate   
)
pip install .
cd  /project/path
pip install -r requirements.txt
pip install -e .
