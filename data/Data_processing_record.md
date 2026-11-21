# Data reduction and correlation reconstruction

## Record identity

The dimensional tables contain nine inputs and three recorded outputs. Rows of Table S7 correspond to CFD0001–CFD0300 in `fitting_record_ids.csv`. Source design-point labels are qualified by batch. The map `experimental_27_to_passages_54.csv` links each experimental operating point to its two passage records and the associated fitting record.

The 54 experiment-paired passage records contain 51 distinct nine-input combinations, all represented in the fitting database. Duplicate-input outputs were consolidated by arithmetic averaging. DP480 and DP502 in the paired batch have the same inputs, and their outlet temperature and pressure drop were averaged for the fitting record. Each distinct input combination has unit weight in logarithmic least squares. The 54 passage outputs retain their individual values for pairing with the 27 experiments.

## Dataset selection

The captured 307-record candidate table combines 253 current records with 54 legacy candidates. The 253 current records comprise 142 latest, 60 prior_actual and 51 distinct experiment-paired inputs. Legacy candidates were screened against the then-current compact correlations using absolute residual thresholds of 5% for Nu and 10% for the minimum-section friction factor, the current variable ranges, and agreement between repeated outputs.

The seven largest absolute Nu residuals from the fixed 307-record fit were excluded before the final 300-record fit. Their source labels are DP516, DP538, DP537, DP615, DP562, DP613 and DP561. This is a response-residual selection rule. The resulting database has 300 distinct inputs and 110 geometries. Figures 14 and 15 evaluate agreement within this selected fitting source.

The candidate snapshot, inclusion flags, source batches, source labels and recorded source hashes are supplied separately. The prior_actual provenance points to the historical audit manifest. The captured candidate values provide the portable numerical reconstruction input.

## Reconstruction

Install the packages in `requirements.txt`, then run `analysis/reproduce_correlations.py` from any working directory. The script reads the dimensional tables, reconstructs throat free-flow area and wetted perimeter from the two circular segments, and evaluates hydraulic diameters, inlet properties, Reynolds numbers, Nu and Darcy friction factor. It then performs double-precision logarithmic least squares and verifies all derived responses and predictions against the calculation tables. It also reconstructs the fixed 307-to-300 residual selection. Outputs are written to `results`.

The dimensional tables use degrees Celsius and millimetres. The candidate snapshot explicitly uses kelvin and millimetres. Code converts dimensions to metres. Pressure drop is inlet-face minus outlet-face static pressure. The normalization length is feature count times pitch. Dimensionless reduction uses the following reference properties.

- Ideal-gas density at 101325 Pa with gas constant 287.05 J/(kg K).
- Sutherland viscosity with reference 1.716e-5 Pa s at 273.15 K and constant 111 K.
- Specific heat capacity of 1007 J/(kg K).
- Conductivity of 0.024024 times the inlet-to-273.15-K temperature ratio to power 0.9, in W/(m K).

These reference properties define the dimensionless reduction. The solver material properties use temperature-dependent piecewise-linear tables. The Nu heat rate is reconstructed from the air-temperature change, incorporating the effects present in the solved energy field, including the enabled radiation model.

## Pointwise experimental error bars

The experimental U reduction uses the four temperatures from the test-summary report, nominal volume flow rates, dry-air CoolProp properties, an area of 5.2 square metres and the two-unmixed-stream cross-flow effectiveness–NTU relation. The supplied 27-row uncertainty-input table records these temperatures and the covariance of the seven-record means. The source summary rounds temperatures and occasionally differs from a newly rounded mean in its last reported digit.

Run `analysis/reproduce_uncertainty.py` to reconstruct all 162 plotted error bars from these sufficient statistics. U repeatability uses first-order covariance propagation through the same U calculation, with nominal flow held fixed. Heat-rate repeatability is calculated directly from the seven reported heat rates and their paired mean. Thermal error bars are twice the Type-A standard uncertainty.

Pressure error bars are twice the square root of the sum of Type-A variance and reference-accuracy variance. The latter uses a rectangular distribution with bound 1.08 Pa. The current thermal error bars quantify within-run repeatability.

The measured-flow sensitivity file evaluates the same U reduction using measured average inlet volume flows. The formal experimental comparison uses nominal flow rates as specified in the manuscript.
