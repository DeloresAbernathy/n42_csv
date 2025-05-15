#!/usr/bin/env python3

import argparse
from spectrumlib import SpectrumAnalyzer

def main():
    parser = argparse.ArgumentParser(description="Process gamma spectrum and peaks.")
    parser.add_argument("n42_file", help="Path to .n42 spectrum file")
    parser.add_argument("csv_file", help="Path to Interspec peak CSV")
    parser.add_argument("--json", default="spectrum.json", help="Output JSON filename")
    parser.add_argument("--png", default="spectrum.png", help="Output PNG plot filename")
    parser.add_argument("--html", default="spectrum.html", help="Output HTML viewer filename")

    args = parser.parse_args()

    analyzer = SpectrumAnalyzer(args.n42_file, args.csv_file)
    analyzer.load_data()
    analyzer.generate_json(args.json)
    analyzer.save_plot(args.png)
    analyzer.save_html(args.json, args.html)

if __name__ == "__main__":
    main()
