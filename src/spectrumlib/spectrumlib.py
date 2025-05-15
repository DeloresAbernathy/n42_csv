# src/spectrumlib/spectrumlib.py

import SpecUtils
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from pathlib import Path


class SpectrumAnalyzer:
    def __init__(self, n42_file, csv_file):
        self.n42_file = n42_file
        self.csv_file = csv_file
        self.meas = None
        self.energies = None
        self.counts = None
        self.energy_midpoints = None
        self.peaks_df = None
        self.result_json = None

    def load_data(self):
        spec = SpecUtils.SpecFile()
        spec.loadFile(self.n42_file, SpecUtils.ParserType.Auto)
        self.meas = spec.measurements()[0]
        self.energies = self.meas.channelEnergies()
        self.counts = self.meas.gammaCounts()
        self.energy_midpoints = 0.5 * (
            np.array(self.energies[:-1]) + np.array(self.energies[1:])
        )

        df = pd.read_csv(self.csv_file, header=[0, 1])
        df.columns = [
            "Centroid", "Net_Area", "Net_Area_Uncertainty", "Peak_CPS", "FWHM", "FWHM_Percent",
            "Chi_Sqr", "ROI_Total_Counts", "ROI_ID", "File_Name", "LiveTime", "Date", "Time",
            "Nuclide", "Photopeak_Energy", "ROI_Lower_Energy", "ROI_Upper_Energy", "Color",
            "User_Label", "Continuum_Type", "Skew_Type", "Continuum_Coefficients",
            "Skew_Coefficients", "RealTime"
        ]
        df["Nuclide"] = df["Nuclide"].astype(str).str.strip()
        df["User_Label"] = df["User_Label"].astype(str).str.strip()
        self.peaks_df = df[df["Nuclide"] != ""]
        
        if not Path(self.n42_file).exists():
            raise FileNotFoundError(f"{self.n42_file} not found")
        
        return self

    def generate_json(self, output_file):
        def build_peak(row):
            return {
                "type": "Linear",
                "lowerEnergy": float(row["ROI_Lower_Energy"]),
                "upperEnergy": float(row["ROI_Upper_Energy"]),
                "referenceEnergy": float(row["Centroid"]),
                "coeffs": [0, 0],
                "coeffUncerts": [0, 0],
                "fitForCoeff": [True, True],
                "peaks": [{
                    "lineColor": row["Color"] if isinstance(row["Color"], str) else "#6666ff",
                    "type": "GaussianDefined",
                    "skewType": "NoSkew",
                    "Centroid": [float(row["Photopeak_Energy"]), 0.00, True],
                    "Width": [0.00, 0.00, True],
                    "Amplitude": [float(row["Net_Area"]), 0, True],
                    "LandauAmplitude": [0, -1, False],
                    "LandauMode": [0, -1, False],
                    "LandauSigma": [0, -1, False],
                    "Chi2": [0, -1, False],
                    "forCalibration": True,
                    "forSourceFit": True,
                    "sourceType": "NormalGamma",
                    "nuclide": {
                        "name": row["Nuclide"],
                        "decayParent": row["Nuclide"],
                        "decayChild": "Cs133",
                        "DecayGammaEnergy": float(row["Photopeak_Energy"])
                    }
                }]
            }

        blocks = [build_peak(row) for _, row in self.peaks_df.iterrows()]
        self.result_json = [{
            "title": "Foreground",
            "id": 0,
            "backgroundID": 1,
            "type": "FOREGROUND",
            "peaks": blocks,
            "liveTime": float(self.meas.liveTime()),
            "realTime": float(self.meas.realTime()),
            "neutrons": float(self.meas.neutronCountsSum()) if self.meas.containedNeutron() else None,
            "lineColor": "black",
            "x": list(self.energy_midpoints),
            "y": list(self.counts),
            "yScaleFactor": 1
        }]

        with open(output_file, "w") as f:
            json.dump(self.result_json, f, indent=2)

    def save_plot(self, output_png):
        cmap = plt.get_cmap("tab10")
        nuclides = sorted(self.peaks_df["Nuclide"].unique())
        colors = {nuc: cmap(i % 10) for i, nuc in enumerate(nuclides)}

        plt.figure(figsize=(18, 8))
        plt.plot(self.energy_midpoints, self.counts, color='black', lw=1)
        plt.yscale('log')
        plt.xlabel("Energy (keV)")
        plt.ylabel("Counts")
        plt.grid(True, which='both', ls='--', alpha=0.3)

        for _, row in self.peaks_df.iterrows():
            energy = row["Centroid"]
            nuclide = row["Nuclide"]
            color = colors[nuclide]
            idx = (np.abs(self.energy_midpoints - energy)).argmin()
            y_val = self.counts[idx]
            plt.axvline(energy, color=color, linestyle='--', alpha=0.3)
            plt.text(energy + 3, y_val, nuclide, verticalalignment='center',
                     horizontalalignment='left', fontsize=8, color=color)

        plt.tight_layout()
        plt.savefig(output_png, dpi=300)
        plt.close()

    def save_html(self, json_file, output_html):
        json_name = Path(json_file).name

        html = f"""<!DOCTYPE html>
    <html>
    <head>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
    <title>Interactive Spectrum Viewer</title>
    <script src="d3.v3.min.js"></script>
    <script src="SpectrumChartD3.js"></script>
    <link rel="stylesheet" href="SpectrumChartD3.css">
    <link rel="stylesheet" href="SpectrumChartD3StandAlone.css">
    <style>
        body {{ font-family: sans-serif; margin: 100px; }}
        .chart {{ width: 80%; height: 0vh; }}
    </style>
    </head>
    <body onload="init()">

    <div id="chart1" class="chart" oncontextmenu="return false;" style="margin-left: auto; margin-right: auto; min-height: 100px;"></div>

    <!-- Options Panel -->
    <div style="margin-top: 50px; display: inline-block;">
    <label>Y Scale:
        <select onchange="onyscalechange(this,graph)">
        <option value="lin">Linear</option>
        <option value="log" selected>Log</option>
        <option value="sqrt">Sqrt</option>
        </select>
    </label>
    <label><input type="checkbox" onchange="ongridxchange(this,graph)" checked>Grid X</label>
    <label><input type="checkbox" onchange="ongridychange(this,graph)" checked>Grid Y</label>

    <br><label><input type="checkbox" onchange="showForegroundPeaks(this,graph)" checked>Draw foreground peaks</label>
    <label><input type="checkbox" onchange="showTitle(this,graph)" checked>Show Title</label>

    <br><label><input id="legendoption" type="checkbox" onchange="setShowLegend(this,graph);" checked>Draw Legend</label>
    <label><input type="checkbox" onchange="setCompactXAxis(this,graph);">Compact x-axis</label>
    <label><input type="checkbox" onchange="setShowMouseStats(this,graph);" checked>Mouse Position stats</label>
    <label><input type="checkbox" onchange="setShowAnimation(this,graph)">Show zoom animation with duration:
        <input type="number" size=3 value="200" min="0" id="animation-duration" oninput="setAnimationDuration(this.value,graph);"> ms
    </label>

    <br><label><input type="checkbox" onchange="setShowUserLabels(this,graph);">Show User Labels</label>
    <label><input type="checkbox" onchange="setShowPeakLabels(this,graph);" checked>Show Peak Labels</label>
    <label><input type="checkbox" onchange="setShowNuclideNames(this,graph);" checked>Show Nuclide Names</label>
    <label><input type="checkbox" onchange="setShowNuclideEnergies(this,graph);" checked>Show Nuclide Energies</label>

    <br><label><input type="checkbox" onchange="setAdjustYAxisPadding(this,graph);" checked>Adjust for y-labels</label>
    <label><input type="checkbox" onchange="setWheelScrollYAxis(this,graph);" checked>Scroll over y-axis zooms-y</label>

    <br><label><input type="checkbox" onchange="setComptonEdge(this,graph);">Show compton edge</label>
    <label><input type="checkbox" onchange="setComptonPeaks(this,graph);">Show compton peak energy with angle:
        <input type="number" size=5 value="180" max="180" min="0" oninput="setComptonPeakAngle(this.value,graph);"> degrees
    </label>
    <label><input type="checkbox" onchange="setEscapePeaks(this,graph);">Show escape peak energies</label>
    <label><input type="checkbox" onchange="setSumPeaks(this,graph);">Show sum peak energies</label>

    <br><label><input type="checkbox" onchange="setShowXAxisSliderChart(this,graph);">Show x-axis slider chart</label>
    <label><input type="checkbox" onchange="setXRangeArrows(this,graph)" checked>Show x-axis range continue arrows</label>
    </div>

    <script>
    function init(){{
    var xobj = new XMLHttpRequest();
    xobj.overrideMimeType("application/json");
    xobj.open('GET', '{json_name}', true);
    xobj.onreadystatechange = function(){{
        if(xobj.readyState === 4){{
        var spectrum_data = JSON.parse(xobj.responseText);
        var chart_data = {{ "spectra": spectrum_data }};

        var linecolors = ["black", "blue", "red"];
        for (var i = 0; i < chart_data.spectra.length; i++) {{
            chart_data.spectra[i].lineColor = linecolors[i % linecolors.length];
        }}

        for (var i = 1; i < chart_data.spectra.length; i++) {{
            chart_data.spectra[i].yScaleFactor = chart_data.spectra[i].liveTime / chart_data.spectra[0].liveTime;
        }}

        var chart_options = {{
            title: "Gamma Spectrum Viewer",
            xlabel: "Energy (keV)",
            ylabel: "Counts",
            logYFracTop: 0.5,
            logYFracBottom: 0.1,
            logYAxisMin: 0.1
        }};

        graph = new SpectrumChartD3("chart1", chart_options);
        graph.setData(chart_data);
        graph.setLogY();  
        graph.setGridX(true);
        graph.setGridY(true);

        const handleResize = function(){{
            const chart = document.getElementById('chart1');
            chart.style.width = (0.90 * window.innerWidth) + "px";
            chart.style.height = Math.min(0.75 * window.innerWidth, 0.75 * window.innerHeight) + "px";
            graph.handleResize();
        }};

        window.addEventListener('resize', handleResize);
        handleResize();
        }}
    }};
    xobj.send(null);
    }}
    </script>

    <script>
    var onyscalechange=function(e,t){{var c=e.value;"lin"===c?t.setLinearY():"log"===c?t.setLogY():"sqrt"===c&&t.setSqrtY()}},
    ongridychange=function(e,t){{t.setGridY(e.checked)}},
    ongridxchange=function(e,t){{t.setGridX(e.checked)}},
    showForegroundPeaks=function(e,t){{t.setShowPeaks(0,e.checked)}},
    showTitle=function(e,t){{t.setTitle(e.checked?"Example Chart":null)}},
    setShowMouseStats=function(e,t){{t.setShowMouseStats(e.checked)}},
    setCompactXAxis=function(e,t){{t.setCompactXAxis(e.checked)}},
    setAdjustYAxisPadding=function(e,t){{t.setAdjustYAxisPadding(e.checked,e.checked?5:60)}},
    setWheelScrollYAxis=function(e,t){{t.setWheelScrollYAxis(e.checked)}},
    setShowAnimation=function(e,t){{t.setShowAnimation(e.checked)}},
    setAnimationDuration=function(e,t){{t.setAnimationDuration(e)}},
    setShowLegend=function(e,t){{t.setShowLegend(e.checked)}},
    setShowUserLabels=function(e,t){{t.setShowUserLabels(e.checked)}},
    setShowPeakLabels=function(e,t){{t.setShowPeakLabels(e.checked)}},
    setShowNuclideNames=function(e,t){{e.setShowNuclideNames(e.checked)}},
    setShowNuclideEnergies=function(e,t){{e.setShowNuclideEnergies(e.checked)}},
    setComptonEdge=function(e,t){{t.setComptonEdge(e.checked)}},
    setComptonPeaks=function(e,t){{t.setComptonPeaks(e.checked)}},
    setComptonPeakAngle=function(e,t){{t.setComptonPeakAngle(e)}},
    setEscapePeaks=function(e,t){{t.setEscapePeaks(e.checked)}},
    setSumPeaks=function(e,t){{t.setSumPeaks(e.checked)}},
    setXRangeArrows=function(e,t){{t.setXRangeArrows(e.checked)}},
    setShowXAxisSliderChart=function(e,t){{t.setShowXAxisSliderChart(e.checked)}};
    </script>

    </body>
    </html>
    """

        Path(output_html).write_text(html, encoding="utf-8")
        print(f"HTML file generated: {output_html}")