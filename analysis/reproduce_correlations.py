"""Reconstruct the published dimensionless reduction and log-least-squares fit.

Run from any directory. Install numpy and pandas from requirements.txt first.
Raw dimensional tables are read-only. New results go to results.
"""
from pathlib import Path
import json
import platform
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ['P3','P4','P7','P8','P9','P10','P11','P13','P14']
RAW = INPUTS + ['P5','P6','P12']


def load_dimensional(path):
    frame = pd.read_csv(path)
    assert frame.shape[1] == 12
    frame.columns = RAW
    frame[['P3','P9','P5']] += 273.15
    return frame


def reduce(frame):
    f = frame.copy()
    diameter, depth, width, height, pitch = [f[c].to_numpy(float)*.001 for c in ['P7','P8','P10','P11','P13']]
    radius = ((diameter/2)**2 + depth**2)/(2*depth)
    half_angle = np.arcsin(np.clip(diameter/(2*radius), 0, 1))
    segment = radius**2*half_angle-diameter/2*np.sqrt(np.maximum(radius**2-(diameter/2)**2, 0))
    f['Ac_m2'] = width*height-2*segment
    f['Pwet_m'] = 2*(width+height)+2*(2*radius*half_angle-diameter)
    assert (f.Ac_m2>0).all()
    f['Dh_min_m'] = 4*f.Ac_m2/f.Pwet_m
    f['Dh_rect_m'] = 2*width*height/(width+height)
    f['rho_kg_m3'] = 101325/(287.05*f.P9)
    f['mu_Pa_s'] = 1.716e-5*(f.P9/273.15)**1.5*(273.15+111)/(f.P9+111)
    f['k_W_m_K'] = .024024*(f.P9/273.15)**.9
    f['cp_J_kg_K'] = 1007.
    f['u_min_m_s'] = f.P4*width*height/f.Ac_m2
    f['Re_rect'] = f.rho_kg_m3*f.P4*f.Dh_rect_m/f.mu_Pa_s
    f['Re_min'] = f.rho_kg_m3*f.u_min_m_s*f.Dh_min_m/f.mu_Pa_s
    f['L_NP_m'] = f.P14*pitch
    f['f_min'] = f.P6*f.Dh_min_m/(.5*f.rho_kg_m3*f.u_min_m_s**2*f.L_NP_m)
    assert ((f.P5>np.minimum(f.P3,f.P9)) & (f.P5<np.maximum(f.P3,f.P9))).all()
    f['LMTD_K'] = (f.P5-f.P9)/np.log((f.P3-f.P9)/(f.P3-f.P5))
    f['Q_air_W'] = f.rho_kg_m3*f.P4*width*height*f.cp_J_kg_K*(f.P5-f.P9)
    f['Nu'] = f.Q_air_W*f.Dh_rect_m/(f.P12*f.LMTD_K*f.k_W_m_K)
    for name,a,b in [('e_H','P8','P11'),('D_H','P7','P11'),('P_D','P13','P7'),('W_D','P10','P7')]:
        f[name] = f[a]/f[b]
    assert np.isfinite(f[['Nu','f_min']]).all().all()
    assert f[['Nu','f_min']].gt(0).all().all()
    return f


def matrix(frame, quantity):
    names = ['Re_rect' if quantity=='Nu' else 'Re_min','e_H','D_H','P_D','W_D','P14']
    log_inputs = np.log(frame[names].to_numpy(float))
    if quantity=='f_min':
        log_inputs = np.column_stack([log_inputs, np.log(frame.P3/frame.P9)])
    return np.column_stack([np.ones(len(frame)), log_inputs])


def main():
    destination = ROOT/'results'
    destination.mkdir(parents=True,exist_ok=True)
    fit = reduce(load_dimensional(ROOT/'data/cfd_300_input_output.csv'))
    paired = reduce(load_dimensional(ROOT/'data/cfd_54_input_output.csv'))
    candidate = reduce(pd.read_csv(ROOT/'data/candidate_307_raw_K_mm.csv'))
    old_nu_beta = np.linalg.lstsq(matrix(candidate,'Nu'), np.log(candidate.Nu), rcond=None)[0]
    candidate['Nu_residual_pct_307'] = 100*(np.exp(matrix(candidate,'Nu')@old_nu_beta)/candidate.Nu-1)
    rejected = candidate.Nu_residual_pct_307.abs().sort_values(ascending=False,kind='stable').index[:7]
    def keys(frame):
        return [tuple(np.round(a,5)) for a in frame[INPUTS].to_numpy()]
    assert set(keys(candidate.drop(rejected)))==set(keys(fit))
    assert set(keys(paired)).issubset(set(keys(fit)))
    assert len(fit)==300 and len(set(keys(fit)))==300
    fit['record_id'] = [f'CFD{i+1:04d}' for i in range(len(fit))]
    paired['record_id'] = [f'PAIR{i+1:04d}' for i in range(len(paired))]
    report = {'python':platform.python_version(), 'numpy':np.__version__, 'pandas':pd.__version__,
              'fit_weight':'one per unique input record', 'models':{}}
    for quantity in ['Nu','f_min']:
        x = matrix(fit,quantity)
        beta,_,rank,_ = np.linalg.lstsq(x,np.log(fit[quantity]),rcond=None)
        assert rank==x.shape[1]
        report['models'][quantity] = {'log_coefficients':beta.tolist(),'C':float(np.exp(beta[0])), 'rank':int(rank)}
        for name,frame in [('fit300',fit),('paired54',paired)]:
            frame[quantity+'_pred_300'] = np.exp(matrix(frame,quantity)@beta)
            frame[quantity+'_error_pct_300'] = 100*(frame[quantity+'_pred_300']/frame[quantity]-1)
            reference = pd.read_csv(ROOT/'data'/('fit_300_derived_reference.csv' if name=='fit300' else 'paired_54_derived_reference.csv'))
            assert np.allclose(frame[quantity],reference[quantity],rtol=1e-9)
            assert np.allclose(frame[quantity+'_pred_300'],reference[quantity+'_pred_300'],rtol=1e-9)
            report['models'][quantity][name+'_MAPE_pct'] = float(frame[quantity+'_error_pct_300'].abs().mean())
    fit.to_csv(destination/'fitting_300_derived.csv',index=False,encoding='utf-8-sig')
    paired.to_csv(destination/'paired_54_derived.csv',index=False,encoding='utf-8-sig')
    candidate.loc[rejected].to_csv(destination/'selection_seven_records.csv',index=False,encoding='utf-8-sig')
    (destination/'model_coefficients.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
