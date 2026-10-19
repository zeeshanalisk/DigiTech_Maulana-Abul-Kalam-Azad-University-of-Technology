from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from src.features import FEATURE_COLUMNS
from src.twin_engine import load_bundle, predict_row

ROOT=Path(__file__).resolve().parent
AS=ROOT/'assets'; DOC=ROOT/'docs'; REP=ROOT/'reports'
AS.mkdir(exist_ok=True); DOC.mkdir(exist_ok=True)
NAVY='#132446'; NAVY2='#1E3767'; CYAN='#2F9EAC'; TEAL='#1B7F84'; PURPLE='#7868D9'; GOLD='#F3C94F'; LIGHT='#F4F7FC'; MID='#D9E3F0'; TEXT='#20314F'; MUTED='#61718A'; RED='#C95652'; GREEN='#2F9476'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})

# Architecture diagram, vector PDF and high-res PNG
fig, ax=plt.subplots(figsize=(16,9))
fig.patch.set_facecolor('#F6F8FC'); ax.set_facecolor('#F6F8FC'); ax.set_xlim(0,16); ax.set_ylim(0,9); ax.axis('off')
ax.text(0.55,8.48,'GLUCOTWIN INDIA',fontsize=23,fontweight='bold',color=NAVY)
ax.text(0.55,8.10,'Digital twin architecture  |  patient-specific state + hourly stream + two-hour risk estimate',fontsize=11,color=MUTED)

def box(x,y,w,h,title,body,fc='white',ec=MID,titlec=NAVY):
    p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.16',facecolor=fc,edgecolor=ec,linewidth=1.6)
    ax.add_patch(p)
    ax.text(x+0.18,y+h-0.30,title,ha='left',va='top',fontsize=11.5,fontweight='bold',color=titlec)
    ax.text(x+0.18,y+h-0.70,body,ha='left',va='top',fontsize=9.3,color=TEXT,linespacing=1.45)

def arrow(x1,y1,x2,y2,color=CYAN,rad=0):
    p=FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=16,linewidth=2,color=color,connectionstyle=f'arc3,rad={rad}')
    ax.add_patch(p)

box(.5,5.6,3.1,1.75,'01  HISTORICAL / EHR','Age, BMI, HbA1c\nDiagnosis duration, hypertension\nSynthetic adherence factor',fc='#FFFFFF',ec='#BDD4F0')
box(.5,3.25,3.1,1.75,'02  DYNAMIC STREAM','CGM glucose + trend\nMeal log, steps, HR / HRV\nSleep, efficiency, stress proxy',fc='#FFFFFF',ec='#B9E6E7')
box(4.5,4.35,3.25,2.1,'03  TIME ALIGNMENT','Synthetic patient ID + timestamp\nFeature window at time t\nFuture-label leakage gate',fc='#EEF4FF',ec='#9EB9EB')
box(8.65,4.35,2.85,2.1,'04  ML FORECAST','Extra Trees classifier\nPatient-grouped evaluation\nValidation-tuned threshold',fc='#F0EEFF',ec='#C3BAF8')
box(12.4,5.6,3.05,1.65,'05  CLINICIAN VIEW','Two-hour probability\n24-hour trend + EHR snapshot\nReview cue, not a prescription',fc='#EAF8F3',ec='#9BD6C8')
box(12.4,3.25,3.05,1.65,'06  WHAT-IF PANEL','Vary recent carbs / steps / sleep\nShow model-input sensitivity\nNot causal or physiological proof',fc='#FFF8E8',ec='#E9D79B')
arrow(3.6,6.4,4.5,5.75)
arrow(3.6,4.1,4.5,5.05)
arrow(7.75,5.4,8.65,5.4)
arrow(11.5,5.7,12.4,6.2)
arrow(11.5,4.9,12.4,4.1)
arrow(13.9,4.9,13.9,5.55,color=PURPLE)
ax.add_patch(FancyBboxPatch((.5,.72),14.95,1.35,boxstyle='round,pad=0.03,rounding_size=.15',facecolor=NAVY,edgecolor=NAVY))
ax.text(.8,1.73,'SAFETY + GOVERNANCE LAYER',fontsize=11.5,fontweight='bold',color='#7EE3E2',va='top')
ax.text(.8,1.32,'Synthetic data only   •   No live EHR/device connection   •   Clinician remains in control   •   Retrospective labels separated from inference',fontsize=10,color='white',va='top')
ax.text(.55,.32,'Research prototype. No clinical validation; do not use for diagnosis, treatment or emergency decisions.',fontsize=8.5,color=MUTED)
fig.savefig(AS/'architecture.png',dpi=180,bbox_inches='tight',facecolor=fig.get_facecolor())
fig.savefig(DOC/'Architecture_Diagram.pdf',bbox_inches='tight',facecolor=fig.get_facecolor())
plt.close(fig)

# Training/evaluation visuals
metrics=json.loads((REP/'model_evaluation.json').read_text())
fi=pd.read_csv(REP/'feature_importance.csv').head(9).sort_values('importance')
fig,ax=plt.subplots(figsize=(9,5.2)); fig.patch.set_facecolor('white'); ax.set_facecolor('white')
ax.barh(fi.feature.str.replace('_',' '),fi.importance,color=CYAN)
ax.set_title('Global feature importance (synthetic training process)',fontweight='bold',color=NAVY,pad=12)
ax.set_xlabel('Importance'); ax.spines[['top','right','left']].set_visible(False); ax.grid(axis='x',color='#E9EEF5'); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(AS/'feature_importance.png',dpi=180,bbox_inches='tight'); plt.close(fig)

labels=['ROC-AUC','Average precision','Recall','Precision','F2 score']
vals=[metrics['test_roc_auc'],metrics['test_average_precision'],metrics['test_recall_at_threshold'],metrics['test_precision_at_threshold'],metrics['test_f2_at_threshold']]
fig,ax=plt.subplots(figsize=(8.5,4.8)); fig.patch.set_facecolor('white'); ax.set_facecolor('white')
cols=[NAVY2,CYAN,GREEN,GOLD,PURPLE]
bars=ax.bar(labels,vals,color=cols,width=.65)
ax.set_ylim(0,1); ax.set_ylabel('Metric value'); ax.set_title('Held-out synthetic test results',fontweight='bold',color=NAVY,pad=12)
ax.grid(axis='y',color='#E9EEF5'); ax.set_axisbelow(True); ax.spines[['top','right','left']].set_visible(False)
for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,v+.025,f'{v:.3f}',ha='center',fontsize=9,fontweight='bold',color=NAVY)
fig.tight_layout(); fig.savefig(AS/'model_metrics.png',dpi=180,bbox_inches='tight'); plt.close(fig)

# UI preview based on an actual selected synthetic row and the trained model (rendered concept, not a browser screenshot)
df=pd.read_csv(ROOT/'data'/'synthetic_twin_stream.csv',parse_dates=['timestamp'])
pid='GT-0008'; p=df[df.patient_id==pid].sort_values('timestamp').reset_index(drop=True)
# choose last eligible row with a little history; model scores only feature columns
idx=int(p[p.current_glucose_mg_dl<180].index.max())
row=p.iloc[idx]
bundle=load_bundle(); pr=predict_row(row,bundle)
hist=p.iloc[max(0,idx-23):idx+1]
fig=plt.figure(figsize=(16,9),facecolor='#F4F7FC')
fig.text(.035,.94,'GlucoTwin India',fontsize=25,fontweight='bold',color=NAVY)
fig.text(.035,.905,'Patient-specific glucose excursion early warning  |  UI preview for demo',fontsize=11,color=MUTED)
# top KPIs
kpi_data=[('CURRENT CGM',f"{row.current_glucose_mg_dl:.0f} mg/dL",row.timestamp.strftime('%d %b %Y · %H:%M')),('2-HOUR MODEL RISK',f"{pr['risk']*100:.0f}%",'Synthetic-domain estimate'),('HISTORICAL CONTEXT',f"HbA1c {row.hba1c_pct:.1f}%",f"BMI {row.bmi:.1f} · {row.diabetes_duration_years:.0f}y duration"),('WEARABLE SIGNAL',f"{row.resting_hr_bpm:.0f} bpm",f"HRV {row.hrv_ms:.0f} ms")]
for i,(lab,val,sub) in enumerate(kpi_data):
    x=.035+i*.24
    fig.patches.append(FancyBboxPatch((x,.77),.22,.095,boxstyle='round,pad=.009,rounding_size=.012',transform=fig.transFigure,facecolor='white',edgecolor='#D9E3F0',linewidth=1.2))
    fig.text(x+.012,.835,lab,fontsize=8,color=MUTED,fontweight='bold')
    fig.text(x+.012,.801,val,fontsize=15,color=NAVY,fontweight='bold')
    fig.text(x+.012,.78,sub,fontsize=7.5,color=MUTED)
# line chart
ax=fig.add_axes([.055,.29,.54,.39]); ax.set_facecolor('white')
ax.plot(hist.timestamp,hist.current_glucose_mg_dl,marker='o',markersize=3,linewidth=2.5,color=CYAN,label='Synthetic CGM')
ax.axhline(180,color=RED,linestyle='--',linewidth=1.4,label='Prototype event threshold')
ax.set_title('Glucose trajectory · last 24 hours',loc='left',fontweight='bold',color=NAVY,pad=12)
ax.set_ylabel('mg/dL',color=MUTED); ax.grid(axis='y',color='#E9EEF5'); ax.spines[['top','right','left']].set_visible(False); ax.tick_params(axis='x',labelrotation=15,labelsize=7,colors=MUTED); ax.tick_params(axis='y',labelsize=8,colors=MUTED); ax.legend(frameon=False,fontsize=8,loc='upper left')
# right card
fig.patches.append(FancyBboxPatch((.63,.39),.33,.29,boxstyle='round,pad=.012,rounding_size=.018',transform=fig.transFigure,facecolor='white',edgecolor='#D9E3F0',linewidth=1.2))
fig.text(.655,.64,'FORECAST & REVIEW CUE',fontsize=9,color=MUTED,fontweight='bold')
fig.text(.655,.585,pr['risk_band'],fontsize=17,color=RED if pr['risk']>=.38 else TEAL,fontweight='bold')
fig.text(.655,.54,f"Estimated chance of 180 mg/dL crossing in 2h: {pr['risk']:.0%}",fontsize=10,color=NAVY)
fig.text(.655,.485,'Review recent CGM signal quality,',fontsize=9,color=TEXT)
fig.text(.655,.46,'meal/activity context and history.',fontsize=9,color=TEXT)
fig.text(.655,.415,'Clinician review only — no prescriptions.',fontsize=8,color=MUTED)
# bottom EHR chips
fig.text(.055,.22,'HISTORICAL EHR SNAPSHOT',fontsize=10,fontweight='bold',color=NAVY)
fields=[('AGE',f"{int(row.age_years)}"),('BMI',f"{row.bmi:.1f}"),('DIABETES DURATION',f"{row.diabetes_duration_years:.1f} y"),('HYPERTENSION','Yes' if row.hypertension else 'No'),('ADHERENCE',f"{row.medication_adherence:.0%}")]
for i,(lab,val) in enumerate(fields):
    x=.055+i*.18
    fig.patches.append(FancyBboxPatch((x,.13),.155,.065,boxstyle='round,pad=.007,rounding_size=.01',transform=fig.transFigure,facecolor='#EAF0F8',edgecolor='#D9E3F0'))
    fig.text(x+.009,.17,lab,fontsize=7,color=MUTED,fontweight='bold'); fig.text(x+.009,.143,val,fontsize=11,color=NAVY,fontweight='bold')
fig.text(.035,.06,'All data shown are synthetic. The UI preview is rendered from the prototype data/model; it is not a real clinical record.',fontsize=8.5,color=MUTED)
fig.savefig(AS/'dashboard_preview.png',dpi=150,bbox_inches='tight',facecolor=fig.get_facecolor()); plt.close(fig)
print('Assets created:', *(str(p.name) for p in AS.iterdir()))
