(function(){if(window.OS)return;
const ST={ok:'#2f9e63',warn:'#bf8a1a',alarm:'#ef6a7d',okInk:'#06140c',warnInk:'#1a1204',alarmInk:'#1a0a0e'};
const TH={
 night:{id:'night',name:'Night',bg:'#0a1020',s1:'#121a2c',s2:'#1a2439',s3:'#243049',tx:'#eef2f9',t2:'#b0bacb',t3:'#8e9ab0',acc:'#22a6e0',accSoft:'rgba(34,166,224,.18)',accTx:'#6cc6ee',on:'#0a1020',line:'#243049',scrim:'rgba(3,6,14,.62)',ok:'#2f9e63',warn:'#bf8a1a',alarm:'#ef6a7d',okT:'#4fbf83',warnT:'#e0a93a',alarmT:'#ef6a7d',spd:'#c9b0f7',glow:'0 0 28px rgba(34,166,224,.35)'},
 nightdim:{id:'nightdim',name:'Night dim',bg:'#04070e',s1:'#0a0f1a',s2:'#101727',s3:'#182237',tx:'#c8cfdb',t2:'#939caf',t3:'#78829a',acc:'#1d8cbf',accSoft:'rgba(29,140,191,.20)',accTx:'#58b4dd',on:'#04070e',line:'#182237',scrim:'rgba(0,0,0,.66)',ok:'#2a8c58',warn:'#a87a17',alarm:'#d65e70',okT:'#46ad76',warnT:'#c99634',alarmT:'#e06b7c',spd:'#b29be0',glow:'none'},
 day:{id:'day',name:'Day',bg:'#f3f5f9',s1:'#ffffff',s2:'#e9edf3',s3:'#d8dee8',tx:'#0e1626',t2:'#3b4556',t3:'#5a6475',acc:'#0070b8',accSoft:'#dcecf8',accTx:'#005f9c',on:'#ffffff',line:'#d8dee8',scrim:'rgba(14,22,38,.38)',ok:'#2f9e63',warn:'#bf8a1a',alarm:'#ef6a7d',okT:'#1f7a4b',warnT:'#8a6110',alarmT:'#c0283f',spd:'#5b3fb0',glow:'0 10px 30px rgba(0,112,184,.18)'}};
const CL={
 phone:{id:'phone',name:'Phone',W:393,H:852,hu:false,cols:4,rows:6,slots:5,fs:13,fsS:12,fsH:22,chip:32,strip:48,icon:52,gap:10},
 hu5:{id:'hu5',name:'HU-5',W:800,H:480,hu:true,cols:6,rows:4,slots:5,dock:80,fs:18,fsS:18,fsH:24,chip:48,strip:60,icon:56,gap:8},
 hu7:{id:'hu7',name:'HU-7',W:1024,H:600,hu:true,cols:6,rows:4,slots:5,dock:96,fs:18,fsS:18,fsH:26,chip:48,strip:64,icon:64,gap:10},
 hu9:{id:'hu9',name:'HU-9/10',W:1280,H:720,hu:true,cols:8,rows:4,slots:6,dock:112,fs:20,fsS:18,fsH:28,chip:52,strip:68,icon:68,gap:12},
 huwide:{id:'huwide',name:'HU-wide',W:1920,H:720,hu:true,cols:12,rows:4,slots:7,dock:112,fs:20,fsS:18,fsH:28,chip:52,strip:68,icon:68,gap:12}};
const P=(cx,cy,r,a)=>[cx+r*Math.cos(a),cy+r*Math.sin(a)];
function arc(cx,cy,r,a0,a1){const p=P(cx,cy,r,a0),q=P(cx,cy,r,a1);return 'M'+p[0].toFixed(1)+' '+p[1].toFixed(1)+'A'+r+' '+r+' 0 '+(a1-a0>Math.PI?1:0)+' 1 '+q[0].toFixed(1)+' '+q[1].toFixed(1)}
function gauge(h,c,o){const s=o.size,w=o.w||Math.max(8,s*.05),r=s/2-w/2-4,a0=Math.PI*.8333,sw=Math.PI*1.3333,K=[];
 K.push(h('path',{key:'t',d:arc(s/2,s/2,r,a0,a0+sw),stroke:c.s3,strokeWidth:w,fill:'none',strokeLinecap:'round'}));
 if(o.band)K.push(h('path',{key:'b',d:arc(s/2,s/2,r+w*.9,a0+sw*o.band[0],a0+sw*o.band[1]),stroke:c.t3,strokeWidth:3,fill:'none',opacity:.6}));
 if(o.red)K.push(h('path',{key:'r',d:arc(s/2,s/2,r,a0+sw*o.red,a0+sw),stroke:c.alarm,strokeWidth:w*.35,fill:'none'}));
 const steps=o.steps||0;if(steps){const n=Math.round(o.f*steps);for(let i=0;i<n;i++){K.push(h('path',{key:'s'+i,d:arc(s/2,s/2,r,a0+sw*i/steps+.012,a0+sw*(i+1)/steps-.012),stroke:o.col||c.t2,strokeWidth:w,fill:'none'}))}}
 else K.push(h('path',{key:'v',d:arc(s/2,s/2,r,a0,a0+sw*o.f),stroke:o.col||c.t2,strokeWidth:w,fill:'none',strokeLinecap:'round'}));
 return h('svg',{width:s,height:s,viewBox:'0 0 '+s+' '+s,style:{position:'absolute',left:0,top:0}},K)}
function bar(h,c,o){const f=o.f,b=o.band||[.3,.7];return h('svg',{viewBox:'0 0 200 12',width:'100%',height:o.h||10,preserveAspectRatio:'none'},[
 h('rect',{key:'t',x:0,y:3,width:200,height:6,rx:3,fill:c.s3}),h('rect',{key:'b',x:200*b[0],y:3,width:200*(b[1]-b[0]),height:6,fill:c.t3,opacity:.45}),
 h('rect',{key:'m',x:Math.min(195,200*f-2.5),y:0,width:5,height:12,rx:2,fill:o.col||c.tx})])}
function spark(h,c,o){const pts=o.pts,w=200,hh=40,mx=Math.max(...pts),mn=Math.min(...pts);const d=pts.map((v,i)=>(i?'L':'M')+(i*w/(pts.length-1)).toFixed(1)+' '+(hh-4-(v-mn)/(mx-mn||1)*(hh-8)).toFixed(1)).join(' ');
 return h('svg',{viewBox:'0 0 '+w+' '+hh,width:'100%',height:o.h||28,preserveAspectRatio:'none'},[h('path',{key:'l',d,stroke:o.col||c.t2,strokeWidth:1.5,fill:'none',vectorEffect:'non-scaling-stroke'})])}
function donut(h,c,o){const s=o.size,r=s/2-s*.1,w=s*.16,tot=o.vals.reduce((a,b)=>a+b,0);let a=-Math.PI/2;const ramp=['#3b2a6b','#5b3fb0','#8b6ae0','#b49be6','#e0d4fb'];
 return h('svg',{width:s,height:s,viewBox:'0 0 '+s+' '+s},o.vals.map((v,i)=>{const a1=a+Math.PI*2*v/tot;const p=h('path',{key:i,d:arc(s/2,s/2,r,a+.03,a1-.03),stroke:ramp[i],strokeWidth:w,fill:'none'});a=a1;return p}))}
window.OS={TH,CL,ST,gauge,bar,spark,donut,ramp:['#3b2a6b','#5b3fb0','#8b6ae0','#b49be6','#e0d4fb']};
})();