from pathlib import Path
import pandas as pd, numpy as np, matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from joblib import load
from src.features import FEATURE_COLUMNS
ROOT=Path(__file__).resolve().parent; AS=ROOT/'assets'
NAVY='#132446'; CYAN='#2F9EAC'; TEAL='#1B7F84'; PURPLE='#7868D9'; LIGHT='#F4F7FC'; MID='#D9E3F0'; TEXT='#20314F'; MUTED='#61718A'; RED='#C95652'; GREEN='#2F9476'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
df=pd.read_csv(ROOT/'data'/'synthetic_twin_stream.csv',parse_dates=['timestamp'])
bundle=load(ROOT/'models'/'glucotwin_model.joblib')
el=df[df.current_glucose_mg_dl<180].copy(); el['risk']=bundle['model'].predict_proba(el[FEATURE_COLUMNS])[:,1]
low=el[el.risk<.04].sort_values('risk').iloc[0]
high=el[el.new_high_glucose_event_next_2h==1].sort_values('risk',ascending=False).iloc[0]
elev=df[df.current_glucose_mg_dl>=180].iloc[0]

def render(row, filename, mode):
    p=df[df.patient_id==row.patient_id].sort_values('timestamp').reset_index(drop=True)
    # choose the nearest row corresponding to the state we are rendering
    idx=int((p.timestamp-row.timestamp).abs().argmin()); row=p.iloc[idx]
    risk=float(bundle['model'].predict_proba(pd.DataFrame([{c:float(row[c]) for c in FEATURE_COLUMNS}]))[0,1]) if float(row.current_glucose_mg_dl)<180 else None
    hist=p.iloc[max(0,idx-23):idx+1]
    fig=plt.figure(figsize=(16,9),facecolor=LIGHT)
    fig.text(.035,.94,'GlucoTwin India',fontsize=25,fontweight='bold',color=NAVY)
    fig.text(.035,.905,f'Synthetic patient {row.patient_id}  |  Observation: {row.timestamp.strftime("%d %b %Y · %H:%M")}',fontsize=10.5,color=MUTED)
    kpis=[('CURRENT CGM',f"{row.current_glucose_mg_dl:.0f} mg/dL",'simulated sensor value'),('2-HOUR MODEL SCORE',f"{risk*100:.0f}%" if risk is not None else 'Not applied','synthetic model estimate'),('HISTORICAL CONTEXT',f"HbA1c {row.hba1c_pct:.1f}%",f"BMI {row.bmi:.1f} · {row.diabetes_duration_years:.0f}y duration"),('WEARABLE SIGNAL',f"{row.resting_hr_bpm:.0f} bpm",f"HRV {row.hrv_ms:.0f} ms")]
    for i,(lab,val,sub) in enumerate(kpis):
        x=.035+i*.24
        fig.patches.append(FancyBboxPatch((x,.77),.22,.095,boxstyle='round,pad=.009,rounding_size=.012',transform=fig.transFigure,facecolor='white',edgecolor=MID,linewidth=1.2))
        fig.text(x+.012,.835,lab,fontsize=8,color=MUTED,fontweight='bold'); fig.text(x+.012,.801,val,fontsize=15,color=NAVY,fontweight='bold'); fig.text(x+.012,.78,sub,fontsize=7.5,color=MUTED)
    ax=fig.add_axes([.055,.29,.54,.39]); ax.set_facecolor('white')
    ax.plot(hist.timestamp,hist.current_glucose_mg_dl,marker='o',markersize=3,linewidth=2.5,color=CYAN,label='Synthetic CGM')
    ax.axhline(180,color=RED,linestyle='--',linewidth=1.4,label='Prototype event threshold')
    ax.set_title('Glucose trajectory · last 24 hours',loc='left',fontweight='bold',color=NAVY,pad=12); ax.set_ylabel('mg/dL',color=MUTED); ax.grid(axis='y',color='#E9EEF5'); ax.spines[['top','right','left']].set_visible(False); ax.tick_params(axis='x',labelrotation=15,labelsize=7,colors=MUTED); ax.tick_params(axis='y',labelsize=8,colors=MUTED); ax.legend(frameon=False,fontsize=8,loc='upper left')
    fig.patches.append(FancyBboxPatch((.63,.39),.33,.29,boxstyle='round,pad=.012,rounding_size=.018',transform=fig.transFigure,facecolor='white',edgecolor=MID,linewidth=1.2))
    fig.text(.655,.64,'FORECAST & REVIEW CUE',fontsize=9,color=MUTED,fontweight='bold')
    if mode=='elevated':
        title='Current elevated reading'; title_color=RED; body='Current value is already above the prototype threshold.'; body2='Do not interpret this as an early-warning forecast.'
    elif risk >= float(bundle['threshold']):
        title='Review threshold met'; title_color=RED; body=f'Model estimate of a 2h crossing: {risk:.0%}.'; body2='Review sensor quality and recent context.'
    elif risk >= .7*float(bundle['threshold']):
        title='Watchlist'; title_color='#9A6A11'; body=f'Model estimate of a 2h crossing: {risk:.0%}.'; body2='Check the timeline and signal quality.'
    else:
        title='Below review threshold'; title_color=GREEN; body=f'Model estimate of a 2h crossing: {risk:.0%}.'; body2='Low score does not mean zero risk.'
    fig.text(.655,.585,title,fontsize=16,color=title_color,fontweight='bold'); fig.text(.655,.535,body,fontsize=9.5,color=NAVY); fig.text(.655,.49,body2,fontsize=9,color=TEXT); fig.text(.655,.425,'Clinician review only. No prescription.',fontsize=8,color=MUTED)
    fig.text(.055,.22,'HISTORICAL EHR SNAPSHOT',fontsize=10,fontweight='bold',color=NAVY)
    fields=[('AGE',f"{int(row.age_years)}"),('BMI',f"{row.bmi:.1f}"),('DIABETES DURATION',f"{row.diabetes_duration_years:.1f} y"),('HYPERTENSION','Yes' if row.hypertension else 'No'),('ADHERENCE',f"{row.medication_adherence:.0%}")]
    for i,(lab,val) in enumerate(fields):
        x=.055+i*.18; fig.patches.append(FancyBboxPatch((x,.13),.155,.065,boxstyle='round,pad=.007,rounding_size=.01',transform=fig.transFigure,facecolor='#EAF0F8',edgecolor=MID)); fig.text(x+.009,.17,lab,fontsize=7,color=MUTED,fontweight='bold'); fig.text(x+.009,.143,val,fontsize=11,color=NAVY,fontweight='bold')
    fig.text(.035,.06,'All records are synthetic. Probability scores are model estimates from a simulator-trained model, not clinical results.',fontsize=8.5,color=MUTED)
    fig.savefig(AS/filename,dpi=150,bbox_inches='tight',facecolor=fig.get_facecolor()); plt.close(fig)
    print(filename, row.patient_id, row.timestamp, 'glucose',row.current_glucose_mg_dl,'risk',risk)
render(low,'dashboard_low_review.png','low')
render(high,'dashboard_high_review.png','high')
render(elev,'dashboard_current_elevated.png','elevated')
