# AAHX CFD and analysis

Research code and tabulated inputs and outputs for a protruded-plate air-to-air heat exchanger. The repository brings together SpaceClaim geometry generation, a saved Fluent settings snapshot, Workbench execution and diagnostics, and the numerical reduction used for the heat-transfer and pressure-drop correlations.

## Contents

| Directory | Contents |
| --- | --- |
| `cfd/` | Parametric geometry, Fluent settings, native Workbench scripts, and a historical 54-record thermal-batch plan. |
| `analysis/` | Dimensional reduction, logarithmic regression, experimental uncertainty propagation, metrics and result plots. |
| `data/` | The 300-record correlation database, 54 experiment-paired passage records, 27 experimental means, calculation references, mapping and reconstruction inputs. |
| `SOURCE_MANIFEST.json` | Original and repository SHA-256 hashes, including the files adapted for portable paths. |

## Run the analysis

Use Python 3.10 or later. From the repository root:

```sh
python -m pip install -r requirements.txt
python analysis/reproduce_correlations.py
python analysis/reproduce_uncertainty.py
python analysis/recalculate_metrics.py
python analysis/draw_figures.py
```

The scripts locate their inputs relative to their own files. Derived outputs and figures are written to `results/`; the source tables remain unchanged. The correlation reconstruction checks the supplied full-precision reference responses and predictions. The uncertainty script checks all 162 pointwise experimental error bars. Plotting exports result figures in PNG and PDF; the separate apparatus and literature schematics are not generated here.

Expected correlation errors from the supplied reference tables:

| Records | Nu MAPE | Minimum-section Darcy friction-factor MAPE |
| --- | ---: | ---: |
| 300 fitting records | 4.0576% | 8.7244% |
| 54 experiment-paired passage records | 3.2071% | 5.9252% |

The 54 passage records correspond to 27 experimental operating points. They contain 51 distinct input combinations represented in the fitting database; this comparison measures agreement within the fitting source. Record identities, duplicate consolidation and the candidate-to-fitting selection are documented in [the processing record](data/Data_processing_record.md).

## Quantities and units

The dimensional input-output tables have nine inputs followed by three outputs:

`P3, P4, P7, P8, P9, P10, P11, P13, P14, P5, P6, P12`

| Parameter | Quantity | Unit |
| --- | --- | --- |
| P3 | Heat-source temperature | degrees Celsius |
| P4 | Inlet velocity | m/s |
| P7 | Protrusion diameter | mm |
| P8 | Protrusion depth | mm |
| P9 | Inlet temperature | degrees Celsius |
| P10 | Passage width | mm |
| P11 | Passage height | mm |
| P13 | Feature pitch | mm |
| P14 | Feature count, an even integer | dimensionless |
| P5 | Area-averaged outlet temperature | degrees Celsius |
| P6 | Inlet minus outlet static pressure | Pa |
| P12 | Heated surface area reported for the passage | square metres |

The candidate reconstruction file explicitly uses kelvin and millimetres. CSVs are UTF-8 with a byte-order mark. Derived tables label their units in the headers. The friction factor is the **Darcy** factor referenced to the minimum free-flow section, with normalization length `N * pitch`. Nu uses the rectangular hydraulic diameter. The reduction functions explicitly define their reference density, viscosity, conductivity and heat capacity; these definitions are distinct from the solver material tables. Experimental U uses an area of 5.2 square metres and the four-temperature cross-flow effectiveness-NTU reduction.

## CFD execution

See [the CFD workflow notes](cfd/README.md) before running any `.wbjn` file. These are native **Ansys Workbench 2023 R1** scripts and use the existing project's Fluent and CFD-Post systems. The geometry script uses the SpaceClaim V23 scripting API. The saved Fluent settings record SST, two turbulent Prandtl parameters of 0.65, and temperature-dependent air conductivity.

The geometry includes the original 42.5 mm development length plus an **additional 60 mm at the outlet**. Full saved meshes and solution fields are kept outside this repository. The Workbench scripts require the matching project, design points, boundary names and saved fields described in the workflow notes; this collection does not supply a tested from-zero, one-command CFD rebuild.

The Python analysis scripts can run without Ansys. A syntax check of the Ansys scripts does not establish that a new project can execute them. No simulation is launched by the analysis commands above.
