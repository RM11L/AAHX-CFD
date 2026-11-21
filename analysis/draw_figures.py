"""Publication figures. Data are read without changing source measurements or models."""
from pathlib import Path
import sys,json,hashlib
sys.stdout.reconfigure(encoding='utf-8')
O=Path(__file__).resolve().parent; R=O.parent; F=R/'results/figures';F.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'.plotdeps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle,Polygon,Circle,Ellipse,FancyArrowPatch
from matplotlib.ticker import MaxNLocator,FormatStrFormatter
import numpy as np
import pandas as pd
DESK=R
FIT=R/'data'
SOURCES=[FIT/'fit_300_derived_reference.csv',FIT/'paired_54_derived_reference.csv',R/'data/experimental_cfd_comparison_27.csv',R/'data/experimental_pointwise_error_bars.csv',R/'data/case_repeatability.csv']
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':11,'axes.titlesize':11,'text.color':'black','axes.labelcolor':'black','axes.edgecolor':'black','xtick.color':'black','ytick.color':'black','figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white','pdf.fonttype':42,'svg.fonttype':'none','mathtext.default':'regular'})
COLORS={50:'#0072B2',100:'#D55E00',150:'#009E73'};MARKERS={50:'o',100:'s',150:'^'};LINES={50:'-',100:'--',150:':'}
manifest={}
def save(fig,name,extra=None):
 if name in {'Figure_1','Figure_2','Figure_3a','Figure_7','Figure_8','Figure_9'}:
  plt.close(fig);return # User requested that all schematics remain unchanged.
 if name in {'Figure_4','Figure_11','Figure_12','Figure_13','Figure_14','Figure_15','Figure_16'}:
  for ax in fig.axes:ax.set_box_aspect(1)
 if name in {'Figure_4','Figure_11','Figure_12','Figure_13','Figure_15','Figure_16'}:
  deviation='±5%' if name=='Figure_4' else '±10%'
  for ax in fig.axes:
   existing=ax.get_legend()
   if existing is not None:ax.add_artist(existing)
   ax.legend(handles=[Line2D([0],[0],color='black',lw=.8,label='1:1'),Line2D([0],[0],color='black',ls='--',lw=.8,label=deviation)],loc='lower right' if name=='Figure_4' else 'upper left',frameon=False,fontsize=9.5,labelcolor='black',handlelength=2)
 fig.canvas.draw()
 square_axes=[]
 if name in {'Figure_4','Figure_11','Figure_12','Figure_13','Figure_14','Figure_15','Figure_16'}:
  for ax in fig.axes:
   bounds=ax.get_window_extent()
   assert abs(bounds.width-bounds.height)<.01,(name,bounds.width,bounds.height)
   square_axes.append({'width_px':bounds.width,'height_px':bounds.height})
 output_name={10:'Figure_9',11:'Figure_10',12:'Figure_11',13:'Figure_12',14:'Figure_13',15:'Figure_14',16:'Figure_15'}.get(int(name.split('_')[1]),name)
 for ext in ['png','pdf']:
  fig.savefig(F/(output_name+'.'+ext),dpi=450,facecolor='white')
 manifest[name]={'axes':[{'xlabel':a.get_xlabel(),'ylabel':a.get_ylabel(),'title':a.get_title()} for a in fig.axes],'size_inches':list(fig.get_size_inches()),'square_axes':square_axes,'extra':extra}
 plt.close(fig)
def style(ax,equal=False):
 ax.grid(False);ax.tick_params(direction='out',width=.8,labelsize=9)
 for s in ax.spines.values():s.set_linewidth(.8);s.set_color('black')
 if equal:ax.set_aspect('equal',adjustable='box')
def blank(size):
 fig,ax=plt.subplots(figsize=size);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off');return fig,ax
def arrow(ax,a,b,style='->',lw=1,**kw):
 ax.add_patch(FancyArrowPatch(a,b,arrowstyle=style,mutation_scale=10,color='black',lw=lw,**kw))
def label(ax,x,y,text,size=10,ha='center',va='center',**kw):return ax.text(x,y,text,fontsize=size,color='black',ha=ha,va=va,**kw)
def dim(ax,a,b,text,offset=(0,0),size=10):
 arrow(ax,a,b,'<->',.8);m=(np.asarray(a)+np.asarray(b))/2+np.asarray(offset);label(ax,*m,text,size)
def box(ax,x,y,w,h,text,size=9):
 ax.add_patch(Rectangle((x,y),w,h,ec='black',fc='white',lw=.85));label(ax,x+w/2,y+h/2,text,size)

unc=pd.read_csv(SOURCES[3]);means=unc.pivot(index='file',columns='quantity',values='mean');u=unc.pivot(index='file',columns='quantity',values='expanded_abs');exp=means.add_suffix('_mean').join(u.add_suffix('_u95'))
exp['temperature_C']=exp.index.to_series().str.split('_').str[1].astype(int)
exp['hot_nominal_flow']=exp.index.to_series().str.split('_').str[2].astype(int);exp['cold_nominal_flow']=exp.index.to_series().str.split('_').str[3].str.replace('.xlsx','',regex=False).astype(int)
rep=pd.read_csv(SOURCES[4]).set_index('file')
rep=rep.loc[sorted(rep.index,key=lambda f:tuple(map(int,f.removesuffix('.xlsx').split('_')[1:])))].copy()
assert len(exp)==27 and np.allclose(exp.Q_mean_mean,(exp.Q_hot_mean+exp.Q_cold_mean)/2)
def temp_legend(ax,**kwargs):
 leg=ax.legend(title=r'$T_{h,i}$ (°C)',frameon=False,fontsize=9,title_fontsize=10,**kwargs)
 for t in leg.get_texts():t.set_color('black')
def grouped(ax,x,y,xerr=None,yerr=None):
 for t,g in exp.groupby('temperature_C',sort=True):
  ax.errorbar(g[x],g[y],xerr=None if xerr is None else g[xerr],yerr=None if yerr is None else g[yerr],fmt=MARKERS[t],color=COLORS[t],ecolor='black',ms=4.7,mec='black',mew=.4,elinewidth=.7,capsize=1.6,label=str(t),zorder=3)
exp['Qh_kW']=exp.Q_hot_mean/1000;exp['Qc_kW']=exp.Q_cold_mean/1000;exp['Qm_kW']=exp.Q_mean_mean/1000
exp['Qh_u_kW']=exp.Q_hot_u95/1000;exp['Qc_u_kW']=exp.Q_cold_u95/1000;exp['Qm_u_kW']=exp.Q_mean_u95/1000
fig,ax=plt.subplots(figsize=(5.2,4.9));line=np.linspace(0,14,100)
for slope,ls in [(1,'-'),(.95,'--'),(1.05,'--')]:ax.plot(line,line*slope,color='black',ls=ls,lw=.8)
grouped(ax,'Qh_kW','Qc_kW','Qh_u_kW','Qc_u_kW');ax.set(xlim=(1.8,13.1),ylim=(1.8,13.1),xlabel=r'Hot-side heat transfer rate, $\dot{Q}_h$ (kW)',ylabel=r'Cold-side heat transfer rate, $\dot{Q}_c$ (kW)');style(ax,True);temp_legend(ax,loc='upper left');fig.subplots_adjust(left=.16,right=.98,bottom=.14,top=.98);save(fig,'Figure_4')

# Effectiveness follows the manuscript Eqs. (6)–(7), using unaltered measured heat rates/temperatures.
Ch=rep.Q_hot_W_mean/(rep.T_hot_in_C_mean-rep.T_hot_out_C_mean);Cc=rep.Q_cold_W_mean/(rep.T_cold_out_C_mean-rep.T_cold_in_C_mean)
eps=rep.Q_avg_W/(np.minimum(Ch,Cc)*(rep.T_hot_in_C_mean-rep.T_cold_in_C_mean));exp['epsilon']=eps
assert round(exp.loc['1_50_600_1200.xlsx','epsilon'],3)==.374
assert round(exp.loc['1_100_600_1200.xlsx','epsilon'],3)==.413
assert round(exp.loc['1_150_600_1200.xlsx','epsilon'],3)==.441
fig,axes=plt.subplots(2,3,figsize=(7.4,6.4),layout='constrained');images=[]
for row,(col,cmap,vmin,vmax) in enumerate([('Qm_kW','YlOrRd',2,12),('epsilon','YlGnBu',.24,.45)]):
 for j,t in enumerate([50,100,150]):
  a=axes[row,j];data=exp[exp.temperature_C.eq(t)].pivot(index='hot_nominal_flow',columns='cold_nominal_flow',values=col).sort_index()
  # White cells and colored numerical data avoid coloured commentary and preserve exact displayed values.
  im=a.imshow(data.values,origin='lower',cmap=cmap,vmin=vmin,vmax=vmax,aspect='equal');images.append(im)
  a.set(xticks=range(3),xticklabels=[600,900,1200],yticks=range(3),yticklabels=[600,900,1200],title=rf'$T_{{h,i}}={t}$ °C')
  for yy in range(3):
   for xx in range(3):
    val=data.iloc[yy,xx];a.text(xx,yy,f'{val:.2f}' if row==0 else f'{val:.3f}',ha='center',va='center',color='black',fontsize=9,bbox=dict(facecolor='white',edgecolor='none',alpha=.88,pad=1.5))
  a.set_xlabel(r'$\dot{V}_{c,i}$ (m$^3$ h$^{-1}$)')
  if j==0:a.set_ylabel(r'$\dot{V}_{h,i}$ (m$^3$ h$^{-1}$)')
  style(a)
 cb=fig.colorbar(images[-1],ax=list(axes[row,:]),shrink=.75,pad=.02);cb.set_label(r'(a) Mean heat transfer rate, $\dot{Q}_{mean}$ (kW)' if row==0 else r'(b) Heat exchanger effectiveness, $\varepsilon$ (–)',fontsize=10)
fig.get_layout_engine().set(hspace=.13,wspace=.04);save(fig,'Figure_5')
exp.reset_index().to_csv(R/'results/experimental_plot_values.csv',index=False,encoding='utf-8-sig')

fig,axes=plt.subplots(1,2,figsize=(8,4.0))
for a,side,panel in zip(axes,['hot','cold'],['(a) Hot side','(b) Cold side']):
 for t,g in exp.groupby('temperature_C',sort=True):
  x=rep.loc[g.index,f'V_{side}_in_m3h_mean'];y=g[f'dp_{side}_mean'];err=g[f'dp_{side}_u95'];a.errorbar(x,y,yerr=err,fmt=MARKERS[t],ms=4,color=COLORS[t],ecolor='black',mec='black',mew=.35,elinewidth=1.0,capsize=3.0)
  gg=g.assign(v=x).groupby(f'{side}_nominal_flow').agg(x=('v','mean'),y=(f'dp_{side}_mean','mean'));a.plot(gg.x,gg.y,LINES[t],color=COLORS[t],lw=1,label=str(t))
 a.set(xlabel=r'Inlet volume flow rate, $\dot{V}_{'+('h' if side=='hot' else 'c')+r',i}$ (m$^3$ h$^{-1}$)',ylabel=r'Pressure drop, $\Delta p_{'+('h' if side=='hot' else 'c')+r'}$ (Pa)',title=panel,xlim=(530,1290),ylim=(0,300),xticks=[600,900,1200]);style(a);temp_legend(a,loc='upper left')
fig.subplots_adjust(left=.09,right=.98,bottom=.18,top=.9,wspace=.30);save(fig,'Figure_6')

exp['dp_sum']=exp.dp_hot_mean+exp.dp_cold_mean;exp['dp_sum_u']=np.hypot(exp.dp_hot_u95,exp.dp_cold_u95)
fig,ax=plt.subplots(figsize=(6.0,4.5));grouped(ax,'dp_sum','Qm_kW','dp_sum_u','Qm_u_kW');ax.set(xlim=(100,485),ylim=(1.5,12.5),xlabel=r'Sum of side pressure drops, $\Delta p_h+\Delta p_c$ (Pa)',ylabel=r'Mean heat transfer rate, $\dot{Q}_{mean}$ (kW)');style(ax);temp_legend(ax,loc='upper left');fig.subplots_adjust(left=.14,right=.98,bottom=.16,top=.98);save(fig,'Figure_7')

cases=np.arange(1,28);mismatch=100*np.abs(rep.Q_cold_W_mean-rep.Q_hot_W_mean)/rep.Q_cold_W_mean
hot=2*rep.dp_hot_Pa_rel_sem_pct.to_numpy();cold=2*rep.dp_cold_Pa_rel_sem_pct.to_numpy()
fig,axes=plt.subplots(1,2,figsize=(8,3.5));axes[0].bar(cases,mismatch,color='#0072B2',width=.65,edgecolor='black',lw=.3)
axes[0].axhline(mismatch.mean(),color='black',lw=.9);axes[0].axhline(np.percentile(mismatch,95),color='black',lw=.9,ls='--')
axes[0].set(title='(a) Heat balance',ylabel=r'Relative heat balance difference, $\delta Q$ (%)',ylim=(0,10.2),xlim=(.5,27.5))
axes[1].plot(cases,hot,'o-',ms=3,color='#0072B2',lw=.9,label='Hot side');axes[1].plot(cases,cold,'s--',ms=3,color='#D55E00',lw=.9,label='Cold side')
axes[1].set(title='(b) Pressure drop repeatability',ylabel=r'Relative repeatability, $2u_A/\overline{\Delta p}$ (%)',ylim=(0,1),xlim=(.5,27.5));axes[1].legend(frameon=False,fontsize=9)
for a in axes:a.set_xlabel('Operating point');a.set_xticks([1,5,10,15,20,25,27]);style(a)
fig.subplots_adjust(left=.10,right=.985,bottom=.17,top=.88,wspace=.35);save(fig,'Figure_10',{'mismatch_mean':float(mismatch.mean()),'mismatch_95th':float(np.percentile(mismatch,95))})

validation=pd.read_csv(SOURCES[2]);unmap={(r.file,r.quantity):r for r in unc.itertuples()}
for metric,num,symbol,desc,unit in [('U',11,'U','Overall heat transfer coefficient',r'W m$^{-2}$ K$^{-1}$'),('hot_dp',12,r'\Delta p_h','Hot-side pressure drop','Pa'),('cold_dp',13,r'\Delta p_c','Cold-side pressure drop','Pa')]:
 suffix='W_m2_K' if metric=='U' else 'Pa';x=validation[f'{metric}_experiment_{suffix}'].to_numpy();y=validation[f'{metric}_CFD_{suffix}'].to_numpy();quant={'U':'U','hot_dp':'dp_hot','cold_dp':'dp_cold'}[metric]
 rel=[float(unmap[(f'1_{int(r.hot_inlet_C)}_{int(r.hot_flow_m3_h)}_{int(r.cold_flow_m3_h)}.xlsx',quant)].expanded_rel_pct)/100 for r in validation.itertuples()]
 fig,ax=plt.subplots(figsize=(4.7,4.7));lo=max(0,min(x.min(),y.min())*.87);hi=max(x.max(),y.max())*1.13;z=np.linspace(lo,hi,150)
 for slope,ls in [(1,'-'),(.9,'--'),(1.1,'--')]:ax.plot(z,slope*z,color='black',lw=.8,ls=ls)
 ax.errorbar(x,y,xerr=np.array([float(unmap[(f'1_{int(r.hot_inlet_C)}_{int(r.hot_flow_m3_h)}_{int(r.cold_flow_m3_h)}.xlsx',quant)].expanded_abs) for r in validation.itertuples()]),fmt='o',ms=4,color='#0072B2',mec='black',mew=.3,ecolor='black',elinewidth=1.0,capsize=3.0,zorder=3)
 ax.set(xlim=(lo,hi),ylim=(lo,hi),xlabel=rf'Experimental ${symbol}$ ({unit})',ylabel=rf'CFD ${symbol}$ ({unit})');style(ax,True);fig.subplots_adjust(left=.19,right=.98,bottom=.17,top=.98);save(fig,f'Figure_{num}',{'quantity':desc,'n':27,'MAPE_pct':float(np.mean(np.abs(y/x-1))*100),'uncertainty_basis':'U: Type A covariance propagation, k=2; pressure: Type A + reference accuracy, k=2'})

fit=pd.read_csv(SOURCES[0]);fit['Tin_300']=fit.P9/300
fig,axes=plt.subplots(3,2,figsize=(7,9),layout='constrained')
for a,(col,name) in zip(axes.flat,[('e_H',r'(a) $e/H$ (–)'),('D_H',r'(b) $D/H$ (–)'),('P_D',r'(c) $P/D$ (–)'),('W_D',r'(d) $W/D$ (–)'),('P14',r'(e) Feature count, $N$ (–)'),('Tin_300',r'(f) $T_{in}/(300\ \mathrm{K})$ (–)')]):
 a.scatter(fit.Re_rect,fit[col],s=9,c='#0072B2',edgecolor='none');a.set(xlabel=r'Reynolds number, $Re_{rect}$ (–)',ylabel=name);a.xaxis.set_major_locator(MaxNLocator(4));style(a)
 if col=='P14':a.yaxis.set_major_locator(MaxNLocator(integer=True))
save(fig,'Figure_14',{'n':300,'y_coordinates':'Actual variable values; previous arbitrary band normalization removed'})

for num,frame in [(15,fit),(16,pd.read_csv(SOURCES[1]))]:
 fig,axes=plt.subplots(1,2,figsize=(7.3,3.8))
 for a,col,sym,title,lim in zip(axes,['Nu','f_min'],['Nu','f_{min}'],['(a) Nusselt number','(b) Darcy friction factor'],[75,.08]):
  x=frame[col].to_numpy();y=frame[col+'_pred_300'].to_numpy();z=np.linspace(0,lim,150)
  for slope,ls in [(1,'-'),(.9,'--'),(1.1,'--')]:a.plot(z,slope*z,color='black',lw=.8,ls=ls)
  a.scatter(x,y,s=11,c='#0072B2',edgecolor='black',linewidth=.2,zorder=3)
  a.set(xlim=(0,lim),ylim=(0,lim),xlabel=rf'CFD ${sym}$ (–)',ylabel=rf'Correlation ${sym}$ (–)',title=title);style(a,True);a.xaxis.set_major_locator(MaxNLocator(4));a.yaxis.set_major_locator(MaxNLocator(4))
  if col=='f_min':a.xaxis.set_major_formatter(FormatStrFormatter('%.2f'));a.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
 fig.subplots_adjust(left=.09,right=.985,bottom=.18,top=.89,wspace=.35);save(fig,f'Figure_{num}',{'n':len(frame)})

for p,digest in hashes.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest
(R/'results/figure_manifest.json').write_text(json.dumps({'figures':manifest,'source_hashes':hashes},ensure_ascii=False,indent=2),encoding='utf-8')
print('Generated',len(manifest),'figures in PNG and PDF; source data hashes unchanged.')

