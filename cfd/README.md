# CFD workflow files

The scripts below preserve working project-specific safeguards. Run native scripts through Workbench's **File > Scripting > Run Script File** only after checking the active project, design-point mapping, boundary names, available storage and Ansys licence. Do not run an execution script while another update is active.

| File | Purpose and requirements |
| --- | --- |
| `build_protruded_passage.py` | SpaceClaim V23 parametric geometry. Six geometric inputs; even feature count. The script rebuilds the geometry and named selections. |
| `fluent_reference.set` | Saved reference settings, with machine-specific inert file paths replaced by `FLTG.1`. Loading settings requires a compatible mesh and matching zones. |
| `export_saved_settings.wbjn` | Read-only native parameter and saved-file export for the reference `AAHX-kT-check` project, DPs 480-545. Creates a numbered audit directory; does not solve. |
| `export_field_diagnostics.wbjn` | Read-only field audit of reference DPs 534-545. Loads one saved case at a time, checks inputs and settings, and evaluates both the extended outlet and the original outlet plane. Contains explicit reference mappings and a saved-file timestamp threshold. |
| `preflight_thermal_batch.wbjn` | Archives and inspects the already-completed DP480/source216 baseline in the historical fixed-mesh project. No new iterations. |
| `run_thermal_batch54.wbjn` | Historical 54-record plan runner. Changes P3/P4/P9 and **runs Fluent**, retaining fresh fields and a status log. Reuses the source216 baseline and computes the remaining 53 records. |
| `BF54_plan.json` | The runner's historical source213-266 input plan, including repeated inputs and its original baseline outputs. It is not the final 54-record data table. |
| `baseline216_field.tsv` | Archived diagnostic readout for the baseline required by the historical runner. It does not replace the saved case/data needed by preflight. |

## Reference settings

The saved settings include energy transport, SST k-omega, inherited discrete-ordinates radiation, velocity inlet, pressure outlet and isothermal heated surfaces. Energy and wall turbulent Prandtl numbers are both 0.65. Actual defaults and inactive variable blocks coexist in a Fluent `.set` file; inspect active model flags and zone settings together when adapting it.

Air conductivity is piecewise linear in temperature:

| Temperature (K) | Conductivity (W/(m K)) |
| ---: | ---: |
| 283.15 | 0.0251214165 |
| 298.15 | 0.0262469313 |
| 323.15 | 0.0280828635 |
| 348.15 | 0.0298725706 |
| 373.15 | 0.0316198891 |
| 398.15 | 0.0333282444 |
| 423.15 | 0.0350007000 |

The geometry script keeps `DEVELOP_LENGTH = 42.5` mm and adds `OUTLET_EXTRA_LENGTH = 60.0` mm at the outlet. The original outlet coordinate varies with pitch and count: `x_old = ((N - 1) * pitch / 2 + 62.5) / 1000` metres. The extended outlet is at `x_old + 0.06`. Static-pressure differences at these two locations are separate quantities.

## Use the archived fixed-mesh thermal runner

This runner is specific to an existing project named `AAHX_54_W45_P45_dp480.wbpj`, current DP480, with D25/e3.6/W45/H7/P45 mm and N6. It expects the Fluent system and a CFD-Post system named `Post`. Source216 has Tw30 degrees Celsius, velocity7.8 m/s and Tin50 degrees Celsius. Its archived case/data filenames are asserted by preflight. The historical plan uses 5.2/7.8/10.4 m/s; the final dimensional table in `data/cfd_54_input_output.csv` is a separate dataset.

1. Work in a copy of the matching saved Workbench project. Keep the retained geometry, mesh and baseline case/data files together.
2. Place `BF54_plan.json` beside the `.wbpj`. The adapted scripts derive this directory from `GetProjectFile()`; no personal absolute path is required.
3. Run `preflight_thermal_batch.wbjn`. Check the generated `BF54_extended` report and the actual baseline field identity.
4. Only after the baseline passes, run `run_thermal_batch54.wbjn`. It locks the batch directory, checks geometry/mesh hashes at each record, retains fresh fields and stops on a failed identity, backflow, temperature-range or mass-balance check. Keep all archived outputs when resuming.

The runner does not configure the turbulence model, material law or mesh from scratch. Its existing project determines these settings. Review residual histories and monitor stability in addition to the scripted checks; reaching the configured iteration limit alone does not establish convergence. Read-only diagnostics change the CFD-Post loaded session and create audit files, but do not overwrite source case/data.

## Output conventions

`t_outlet` is area averaged. Native pressure reports use absolute mass-flux weighting; the aligned audit also records area and signed mass-flow variants explicitly. With backflow these averages differ. The minimum outlet streamwise velocity and reverse-flow area fraction are diagnostics; undefined or absent field values are not treated as zero. Mass balance, temperature bounds and retained-file identity are checked separately. An energy-flux closure including radiation requires its own verified report.

Project-specific IDs and cut-off timestamps remain visible so that adapting a script requires an explicit review rather than silently selecting an unrelated saved field. Mesh generation and complete solver-case reconstruction still require the retained Ansys project; large CAD, mesh and case/data files are excluded from version control.
