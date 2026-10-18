import sys, json, math, datetime as dt
import pandas as pd
D=sys.argv[1]; OUT=sys.argv[2]
R=lambda f: pd.read_csv(f'{D}/{f}',dtype=str)
routes=R('routes.txt'); trips=R('trips.txt'); stops=R('stops.txt')
cal=R('calendar.txt'); cd=R('calendar_dates.txt')
st=pd.read_csv(f'{D}/stop_times.txt',dtype=str,usecols=['trip_id','departure_time','stop_id','stop_sequence'])
shapes=pd.read_csv(f'{D}/shapes.txt',dtype={'shape_id':str})

def active(day):
    ds=day.strftime('%Y%m%d'); wd=day.strftime('%A').lower()
    c=cal[(cal.start_date<=ds)&(cal.end_date>=ds)&(cal[wd]=='1')]
    s=set(c.service_id)
    x=cd[cd.date==ds]
    s|=set(x[x.exception_type=='1'].service_id); s-=set(x[x.exception_type=='2'].service_id)
    return s
# jour type: mardi, plus riche parmi les 4 prochaines semaines (hors vacances = plus de courses)
best=None
for k in range(0,60):
    d=dt.date(2026,10,19)+dt.timedelta(days=k)
    if d.weekday()!=1: continue
    n=trips.service_id.isin(active(d)).sum()
    if not best or n>best[1]: best=(d,n)
day=best[0]; print('jour type',day,best[1],'courses')
def sat():
    b=None
    for k in range(0,60):
        d=dt.date(2026,10,19)+dt.timedelta(days=k)
        if d.weekday()!=5: continue
        n=trips.service_id.isin(active(d)).sum()
        if not b or n>b[1]: b=(d,n)
    return b
sd=sat(); print('samedi',sd)
def sec(t):
    h,m,_=t.split(':'); return int(h)*60+int(m)
def rdp(pts,eps):
    if len(pts)<3: return pts
    keep=[False]*len(pts); keep[0]=keep[-1]=True; stack=[(0,len(pts)-1)]
    while stack:
        a,b=stack.pop(); (ax,ay),(bx,by)=pts[a],pts[b]
        dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy; md=-1; mi=-1
        for i in range(a+1,b):
            px,py=pts[i]
            if L==0: d=math.hypot(px-ax,py-ay)
            else:
                t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L)); d=math.hypot(px-ax-t*dx,py-ay-t*dy)
            if d>md: md,mi=d,i
        if md>eps: keep[mi]=True; stack+=[(a,mi),(mi,b)]
    return [p for p,k in zip(pts,keep) if k]
shp={}
shapes=shapes.sort_values(['shape_id','shape_pt_sequence'],key=lambda c:c.astype(float) if c.name=='shape_pt_sequence' else c)
for sid,g in shapes.groupby('shape_id'):
    pts=list(zip(g.shape_pt_lat.astype(float),g.shape_pt_lon.astype(float)))
    shp[sid]=[[round(a,5),round(b,5)] for a,b in rdp(pts,0.00004)]

stops['lat']=stops.stop_lat.astype(float); stops['lon']=stops.stop_lon.astype(float)
sinfo=stops.set_index('stop_id')
def station(sid):
    p=sinfo.at[sid,'parent_station']
    return p if isinstance(p,str) and p in sinfo.index else sid

def stats(srv,rid_trips):
    pass
out_routes=[]; stop_routes={}
wd=active(day); sa=active(sd[0])
st=st.merge(trips[['trip_id','route_id','service_id','direction_id','shape_id','trip_headsign']],on='trip_id')
st['seq']=st.stop_sequence.astype(int)
for _,r in routes.sort_values('route_short_name').iterrows():
    rid=r.route_id
    tw=trips[(trips.route_id==rid)&trips.service_id.isin(wd)]
    ts=trips[(trips.route_id==rid)&trips.service_id.isin(sa)]
    tall=trips[trips.route_id==rid]
    if len(tall)==0: continue
    base=tw if len(tw) else tall
    sb=st[st.trip_id.isin(base.trip_id)]
    first=sb[sb.seq==sb.groupby('trip_id').seq.transform('min')]
    deps=sorted((lambda m:m+1440 if m<240 else m)(sec(t)) for t in first.departure_time)
    dirs=[]
    for d_,g in base.groupby('direction_id'):
        # variantes les plus utilisées (couvrent >=95% des courses, max 4)
        vc=g.shape_id.value_counts(); tot=vc.sum(); acc=0; sel=[]
        for sid,n in vc.items():
            if sid in shp: sel.append(sid)
            acc+=n
            if acc/tot>=.95 or len(sel)>=4: break
        # ordre des arrêts: course la plus représentative de la 1re variante
        lines=[]
        top=vc.index[0]
        cand=g[g.shape_id==top].trip_id
        # choisir la course avec le plus d'arrêts
        sub=st[st.trip_id.isin(cand)]
        tid=sub.groupby('trip_id').size().idxmax()
        seq=st[st.trip_id==tid].sort_values('seq')
        names=[]; ids=[]
        for sid in seq.stop_id:
            p=station(sid); ids.append(p)
        hv=g.trip_headsign.dropna().value_counts()
        head=hv.index[0] if len(hv) else sinfo.at[ids[-1],'stop_name']
        dirs.append(dict(d=int(d_),head=head,n=int(len(g)),shapes=[shp[s] for s in sel],stops=ids))
    # arrêts desservis (toutes courses)
    used=set(station(s) for s in st[st.route_id==rid].stop_id)
    for u in used: stop_routes.setdefault(u,set()).add(rid)
    # fréquence: heure de pointe (7-9h) / creuse (10-16h) par sens, moyenne
    def hw(lo,hi):
        x=[t for t in deps if lo<=t<hi]
        return round((hi-lo)/(len(x)/max(1,len(dirs)))) if len(x)>=2 else None
    out_routes.append(dict(id=rid,short=r.route_short_name,long=r.route_long_name,type=int(r.route_type),
        color='#'+r.route_color,text='#'+r.route_text_color,url=r.route_url if isinstance(r.route_url,str) else '',
        tw=int(len(tw)),ts=int(len(ts)),first=(min(deps) if deps else None),last=(max(deps) if deps else None),
        hp=hw(420,540)  ,hc=hw(600,960),dirs=dirs))
# ---- horaires complets (tous les services) ----
from collections import Counter
stn={sid:station(sid) for sid in stops.stop_id}
tt=st.departure_time.str.split(':',expand=True).astype(int)
st['sec']=tt[0]*3600+tt[1]*60+tt[2]
st=st.sort_values(['trip_id','seq'],kind='stable')
svcidx={}
def sidx(x):
    if x not in svcidx: svcidx[x]=len(svcidx)
    return svcidx[x]
def fnv(x):
    h=0x811c9dc5
    for b in x.encode():
        h^=b;h=(h*0x01000193)&0xffffffff
    return h
pats={}
for tid,g in st.groupby('trip_id',sort=False):
    secs=g.sec.values.tolist()
    if secs[0]<240*60: secs=[x+86400 for x in secs]
    for i in range(1,len(secs)):
        while secs[i]<secs[i-1]: secs[i]+=86400
    key=(g.route_id.iat[0],int(g.direction_id.iat[0]),tuple(stn[x] for x in g.stop_id.values))
    p=pats.setdefault(key,dict(h=Counter(),v={},t=[]))
    h=g.trip_headsign.iat[0]
    if isinstance(h,str): p['h'][h]+=1
    offs=tuple(round((x-secs[0])/60) for x in secs)
    vi=p['v'].setdefault(offs,len(p['v']))
    p['t'].append([round(secs[0]/60),sidx(g.service_id.iat[0]),vi,fnv(tid)])
rp={}
for (rid,d_,stp),p in pats.items():
    head=p['h'].most_common(1)[0][0] if p['h'] else sinfo.at[stp[-1],'stop_name']
    rp.setdefault(rid,[]).append(dict(d=d_,h=head,s=list(stp),o=[list(o) for o in p['v']],t=sorted(p['t'])))
for r in out_routes: r['pats']=rp.get(r['id'],[])
add_=cd[cd.exception_type=='1'].groupby('service_id').date.apply(lambda x:sorted(int(v) for v in x)).to_dict()
rm_=cd[cd.exception_type=='2'].groupby('service_id').date.apply(lambda x:sorted(int(v) for v in x)).to_dict()
cal_=cal.set_index('service_id')
svc=[None]*len(svcidx)
for sid,i in svcidx.items():
    if sid in cal_.index:
        c=cal_.loc[sid]; m=''.join(c[d] for d in ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']); a,b=int(c.start_date),int(c.end_date)
    else: m='0000000';a=b=0
    svc[i]=[m,a,b,add_.get(sid,[]),rm_.get(sid,[])]
# arrêts (stations)
ids=sorted(stop_routes, key=lambda x:x)
out_stops={}
for sid in ids:
    s=sinfo.loc[sid]
    out_stops[sid]=[s.stop_name,round(float(s.lat),5),round(float(s.lon),5),sorted(stop_routes[sid]),1 if s.wheelchair_boarding=='1' else 0]
cs=cal.start_date.min();ce=cal.end_date.max()
fmt=lambda v:f'{v[:4]}-{v[4:6]}-{v[6:]}'
pm={str(i):stn[i] for i in stops.stop_id if stn[i]!=i and stn[i] in out_stops}
fares={r.fare_id:float(r.price) for r in R('fare_attributes.txt').itertuples()}
meta=dict(fares=fares,day=str(day),sat=str(sd[0]),agency='Lignes d\'Azur',feed_start=fmt(cs),feed_end=fmt(ce),info_end='2026-11-18')
json.dump(dict(meta=meta,routes=out_routes,stops=out_stops,svc=svc,pm=pm),open(OUT,'w'),separators=(',',':'),ensure_ascii=False)
import os;print(len(out_routes),'lignes',len(out_stops),'arrêts',os.path.getsize(OUT)//1024,'Ko')
