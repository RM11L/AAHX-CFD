"""Recalculate the four scatterplot metrics from archived full-precision CSVs."""
from pathlib import Path
import csv
import json
import math
from statistics import fmean

root = Path(__file__).resolve().parents[1]
reports = []
for filename, expected_n, figure in [
    ('fit_300_derived_reference.csv', 300, 'Fig. 14'),
    ('paired_54_derived_reference.csv', 54, 'Fig. 15'),
]:
    with (root / 'data' / filename).open(encoding='utf-8-sig', newline='') as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == expected_n
    for column, label in [('Nu', 'Nu'), ('f_min', 'f_min')]:
        actual = [float(row[column]) for row in rows]
        predicted = [float(row[column + '_pred_300']) for row in rows]
        assert all(math.isfinite(value) and value > 0 for value in actual + predicted)
        average = fmean(actual)
        error = [(prediction - value) / value for value, prediction in zip(actual, predicted)]
        reports.append({
            'figure': figure,
            'quantity': label,
            'n': len(actual),
            'mean_CFD': average,
            'MAPE_percent': 100 * fmean(abs(value) for value in error),
            'mean_signed_error_percent': 100 * fmean(error),
        })
print(json.dumps(reports, ensure_ascii=False, indent=2))
