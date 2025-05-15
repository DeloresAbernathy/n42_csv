from spectrumlib import SpectrumAnalyzer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

n42_file = DATA / "summed_background.n42"
csv_file = DATA / "Peaks_summed_background.CSV"

a = SpectrumAnalyzer(str(n42_file), str(csv_file))
a.load_data().generate_json(ROOT / "spectrum.json")
a.save_html_local(ROOT / "spectrum_standalone.html")
