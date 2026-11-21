"""Reproduce pointwise error bars from seven-record sufficient statistics.

The covariance columns retain the correlations between simultaneous temperatures.
Pressure bars combine Type A and the documented EJA reference accuracy.
Thermal bars describe Type-A repeatability with coverage factor 2.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from CoolProp.CoolProp import PropsSI

ROOT = Path(__file__).resolve().parents[1]


def overall_u(t, vh, vc, area):
    thi, tho, tci, tco = np.asarray(t)+273.15
    ch = PropsSI('D','T',thi,'P',101325,'Air')*vh*PropsSI('C','T',(thi+tho)/2,'P',101325,'Air')
    cc = PropsSI('D','T',tci,'P',101325,'Air')*vc*PropsSI('C','T',(tci+tco)/2,'P',101325,'Air')
    cmin, cmax = min(ch,cc), max(ch,cc)
    target = (abs(ch*(thi-tho))+abs(cc*(tco-tci)))/2/(cmin*(thi-tci))
    ratio = cmin/cmax
    def effectiveness(ntu):
        return 1-np.exp((np.exp(-ratio*ntu**.78)-1)*ntu**.22/ratio)
    assert 0<target<1
    lo, hi = 1e-8, 50.
    while effectiveness(hi)<target:
        hi *= 2
        assert hi<1e6
    for _ in range(300):
        mid=(lo+hi)/2
        value=effectiveness(mid)
        if abs(value-target)<1e-10:
            return mid*cmin/area
        if value<target:
            lo=mid
        else:
            hi=mid
    return (lo+hi)/2*cmin/area


def main():
    data=pd.read_csv(ROOT/'data/experimental_uncertainty_inputs.csv')
    results=[]
    for row in data.itertuples():
        for quantity in ['Q_hot','Q_cold','Q_mean','dp_hot','dp_cold']:
            mean=getattr(row,quantity+'_mean')
            ua=getattr(row,quantity+'_sd')/np.sqrt(row.n)
            ub=1.08/np.sqrt(3) if quantity.startswith('dp') else 0.
            results.append(dict(Case=row.Case,file=row.file,quantity=quantity,mean=mean,
                                expanded_abs=2*np.hypot(ua,ub),expanded_rel_pct=200*np.hypot(ua,ub)/mean))
        t=np.array([row.Th_in_C,row.Th_out_C,row.Tc_in_C,row.Tc_out_C])
        covariance=np.array([[getattr(row,f'covmean_{i}_{j}') for j in range(4)] for i in range(4)])
        step=.001
        gradient=np.array([(overall_u(t+np.eye(4)[j]*step,row.Vh_m3_s,row.Vc_m3_s,row.area_m2)-
                            overall_u(t-np.eye(4)[j]*step,row.Vh_m3_s,row.Vc_m3_s,row.area_m2))/(2*step) for j in range(4)])
        mean=overall_u(t,row.Vh_m3_s,row.Vc_m3_s,row.area_m2)
        expanded=2*np.sqrt(max(0.,gradient@covariance@gradient))
        results.append(dict(Case=row.Case,file=row.file,quantity='U',mean=mean,
                            expanded_abs=expanded,expanded_rel_pct=100*expanded/mean))
    output=pd.DataFrame(results).sort_values(['Case','quantity'])
    reference=pd.read_csv(ROOT/'data/experimental_pointwise_error_bars.csv').sort_values(['Case','quantity'])
    for col in ['mean','expanded_abs','expanded_rel_pct']:
        assert np.allclose(output[col],reference[col],rtol=1e-7,atol=1e-9),col
    destination=ROOT/'results'
    destination.mkdir(parents=True,exist_ok=True)
    output.to_csv(destination/'pointwise_error_bars.csv',index=False,encoding='utf-8-sig')
    print('All 162 pointwise error bars reproduced.')


if __name__=='__main__':
    main()
