(function(){
if(window.OstlerMaps)return;
const STYLE='https://tiles.openfreemap.org/styles/dark';
const WP=[[-1.9118,53.2591],[-1.7720,53.2790],[-1.7779,53.3439]];
const RAMP=['#5a4ab0','#7559cf','#9370e3','#ae8ff0','#c9b0f7','#e4d4fc'];
const JOBS={
 hu7:{w:1024,h:544,pl:420,pr:40,z:12.4},hu5:{w:800,h:432,pl:320,pr:30,z:12.0},phone:{w:393,h:686,pb:300,pt:20,z:11.9},
 split7:{w:584,h:544,pb:100,z:13.2},split5:{w:460,h:432,pb:80,z:12.9},splitP:{w:393,h:300,z:12.9},wide:{w:776,h:624,pb:60,pt:110,z:13.4},
 off7:{w:286,h:150,z:14.6,trail:1},tW:{w:300,h:240,fit:1},tWp:{w:361,h:160,fit:1},tHU:{w:1024,h:544,fit:1,pl:410},tPH:{w:393,h:520,fit:1},gPH:{w:393,h:852,fit:1},shareP:{w:361,h:280,fit:1,trim:1},placesP:{w:361,h:340,fit:1},webW:{w:1240,h:700,fit:1,trim:1,pl:420},off5:{w:220,h:92,z:14.4,trail:1},offP:{w:152,h:104,z:14.2,trail:1}};
const PTS={sam:{f:0.58},priya:{f:0.40},tom:{f:0.365},alex:{rel:[0.034,0.012]}};
let map,host,routeP,chain=Promise.resolve();const cache={};
const wait=()=>new Promise(r=>{const f=()=>window.maplibregl?r(window.maplibregl):setTimeout(f,100);f()});
function densify(wp){const o=[];for(let i=0;i<wp.length-1;i++)for(let k=0;k<60;k++){const f=k/60;o.push([wp[i][0]+(wp[i+1][0]-wp[i][0])*f,wp[i][1]+(wp[i+1][1]-wp[i][1])*f])}o.push(wp[wp.length-1]);return o}
function route(){if(!routeP)routeP=(async()=>{try{const ctl=new AbortController();setTimeout(()=>ctl.abort(),7000);
 const r=await fetch('https://router.project-osrm.org/route/v1/driving/'+WP.map(p=>p.join(',')).join(';')+'?overview=full&geometries=geojson',{signal:ctl.signal});
 const j=await r.json();const c=j.routes[0].geometry.coordinates;if(c.length>2)return c;throw 0}catch(e){return densify(WP)}})();return routeP}
const speedAt=f=>Math.max(0,62+26*Math.sin(f*9+1)+10*Math.sin(f*23));
function trailFC(c,off,n){const feats=[];let cur=[],b=-1;for(let i=0;i<c.length;i++){const nb=Math.min(5,Math.floor(speedAt((i+off)/n)/20));if(b<0)b=nb;cur.push(c[i]);
 if(nb!==b||i===c.length-1){feats.push({type:'Feature',properties:{c:RAMP[b]},geometry:{type:'LineString',coordinates:cur}});cur=[c[i]];b=nb}}
 return {type:'FeatureCollection',features:feats.filter(f=>f.geometry.coordinates.length>1)}}
let failed=false;async function ensure(){if(failed)throw 'map unavailable';if(map)return map;const lib=await wait();host=document.createElement('div');
 host.style.cssText='position:fixed;left:-6000px;top:0;width:400px;height:400px;pointer-events:none';document.body.appendChild(host);
 map=new lib.Map({container:host,style:STYLE,attributionControl:false,interactive:false,preserveDrawingBuffer:true,fadeDuration:0,pixelRatio:Math.min(2,window.devicePixelRatio||1)});
 await Promise.race([new Promise(r=>map.once('load',r)),new Promise((_,j)=>setTimeout(()=>{failed=true;j('load timeout')},12000))]);const E={type:'FeatureCollection',features:[]};const L={'line-cap':'round','line-join':'round'};
 map.addSource('trail',{type:'geojson',data:E});map.addSource('ends',{type:'geojson',data:E});map.addLayer({id:'en',type:'line',source:'ends',layout:{'line-cap':'butt'},paint:{'line-color':'#c9b0f7','line-width':4,'line-dasharray':[1.2,1.4],'line-opacity':['get','o']}});map.addSource('ahead',{type:'geojson',data:E});
 map.addLayer({id:'ah-c',type:'line',source:'ahead',layout:L,paint:{'line-color':'#05080f','line-width':10}});
 map.addLayer({id:'ah',type:'line',source:'ahead',layout:L,paint:{'line-color':'#22a6e0','line-width':5}});
 map.addLayer({id:'tr-c',type:'line',source:'trail',layout:L,paint:{'line-color':'#05080f','line-width':8}});
 map.addLayer({id:'tr',type:'line',source:'trail',layout:L,paint:{'line-color':['get','c'],'line-width':4.5}});
 return map}
async function render(name){const o=JOBS[name];const m=await ensure();const c=await route();
 host.style.width=o.w+'px';host.style.height=o.h+'px';m.resize();
 const n=c.length;let ci=Math.floor(n*(o.trail?0.5:0.47)),s0=o.trail?Math.max(0,ci-Math.floor(n*0.1)):0;
 if(o.fit){s0=o.trim?Math.floor(n*0.08):0;ci=o.trim?Math.floor(n*0.92):n-1}
 m.getSource('trail').setData(trailFC(c.slice(s0,ci+1),s0,n));
 const ends=[];if(o.trim){const seg=(a,b,rev)=>{const k=3;for(let j=0;j<k;j++){const i0=a+Math.floor((b-a)*j/k),i1=a+Math.floor((b-a)*(j+1)/k)+1;ends.push({type:'Feature',properties:{o:rev?[0.12,0.35,0.7][j]:[0.7,0.35,0.12][j]},geometry:{type:'LineString',coordinates:c.slice(i0,i1)}})}};seg(0,s0,true);seg(ci,n-1,false)}
 m.getSource('ends').setData({type:'FeatureCollection',features:ends.filter(e=>e.geometry.coordinates.length>1)});
 m.getSource('ahead').setData({type:'FeatureCollection',features:o.trail?[]:[{type:'Feature',properties:{},geometry:{type:'LineString',coordinates:c.slice(ci)}}]});
 if(o.fit){m.setPadding({top:0,bottom:0,left:0,right:0});let a=[180,90,-180,-90];c.forEach(p=>{a[0]=Math.min(a[0],p[0]);a[1]=Math.min(a[1],p[1]);a[2]=Math.max(a[2],p[0]);a[3]=Math.max(a[3],p[1])});m.fitBounds([[a[0],a[1]],[a[2],a[3]]],{padding:{left:(o.pl||0)+30,right:30,top:30,bottom:30},duration:0})}
 else m.jumpTo({center:c[ci],zoom:o.z,padding:{left:o.pl||0,right:o.pr||0,top:o.pt||0,bottom:o.pb||0}});m.triggerRepaint();
 await Promise.race([new Promise(r=>m.once('idle',r)),new Promise(r=>setTimeout(r,6000))]);
 const at=f=>c[Math.max(0,Math.min(n-1,Math.floor(n*f)))];
 const pt=(a,b)=>{const p=m.project(a);let rot=0;if(b){const q=m.project(b);rot=Math.round(Math.atan2(q.y-p.y,q.x-p.x)*180/Math.PI+90)}return {x:Math.round(p.x),y:Math.round(p.y),rot}};
 const pts={car:pt(c[ci],c[Math.min(n-1,ci+6)])};
 for(const k in PTS){const p=PTS[k];pts[k]=p.rel?pt([c[ci][0]+p.rel[0],c[ci][1]+p.rel[1]]):pt(at(p.f),at(p.f+0.006))}
 const a=m.project(c[ci]),b=m.project([c[ci][0],c[ci][1]+3/111.2]);pts.r3=Math.round(Math.abs(a.y-b.y));pts.start=pt(c[0]);pts.end=pt(c[n-1]);
 return {url:m.getCanvas().toDataURL('image/jpeg',0.86),pts,w:o.w,h:o.h}}
window.OstlerMaps={get(name){if(!cache[name]){chain=chain.then(()=>Promise.race([render(name),new Promise((_,j)=>setTimeout(()=>j('render timeout'),15000))])).catch(e=>{console.warn('map',name,e);return null});cache[name]=chain}return cache[name]}};
})();
