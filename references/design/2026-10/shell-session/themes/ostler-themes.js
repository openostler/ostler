(function(){
const F={fig:'Figtree',bit:'Bitter',bar:'Barlow',barc:'Barlow Condensed',man:'Manrope',atk:'Atkinson Hyperlegible'};
const L=[
{id:'night',name:'Night',who:'Everyone: the calm default that works on every screen, day or night.',font:F.fig,head:F.fig,num:F.fig,lic:'Figtree · SIL OFL 1.1',wN:700,
 bg:'#0a1020',strip:'#0a1020',rail:'#0d1424',s1:'#121a2c',s2:'#1a2439',s3:'#243049',tx:'#eef2f9',t2:'#b0bacb',acc:'#22a6e0',on:'#0a1020',sec:'#8e9ab0',spd:'#c9b0f7',
 ramp:['#3b2a6b','#5b3fb0','#8b6ae0','#b49be6','#e0d4fb'],r:24,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'none',bdName:'None',tex:'',texName:'None',gauge:'arc',sweep:'arc',map:'Dark vector',mapF:'none',
 hu:'night',huNote:'Head unit, any time'},
{id:'heritage',name:'Heritage',who:'Classic Land Rover owners who want brass-and-leather warmth on a period-correct dash.',font:F.fig,head:F.bit,num:F.bit,lic:'Bitter + Figtree · SIL OFL 1.1',wN:700,
 bg:'#1a130d',strip:'#150f0a',rail:'#1f170f',s1:'#291e15',s2:'#35281c',s3:'#4a3826',tx:'#f4e9d6',t2:'#d2bf9f',acc:'#d8975a',on:'#1a130d',sec:'#b89a5a',spd:'#f2d3a0',
 ramp:['#4a3523','#7a5534','#a8743f','#d29a5c','#f2d3a0'],r:14,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'inset 0 0 0 1px rgba(184,154,90,.38)',bdName:'1 px brass hairline',
 tex:'repeating-linear-gradient(97deg,rgba(255,236,210,.035) 0 2px,transparent 2px 9px)',texName:'Wood grain · parked only',gauge:'needle',sweep:'needle',map:'Sepia',mapF:'sepia(.6) saturate(.85) brightness(.95)',
 hu:'night',huNote:'Head unit at night; texture drops when Moving'},
{id:'expedition',name:'Expedition',who:'Off-roaders and overlanders who want the map and big, rugged, gloved-hand targets.',font:F.bar,head:F.bar,num:F.bar,lic:'Barlow · SIL OFL 1.1',wN:700,
 bg:'#1b1d12',strip:'#16180e',rail:'#202317',s1:'#272a1b',s2:'#333725',s3:'#4a5034',tx:'#f3eed9',t2:'#d2cdac',acc:'#8fd0e0',on:'#10140a',sec:'#b8ad7a',spd:'#f4ecc2',
 ramp:['#3f4128','#6d6c3e','#a19a58','#d0c483','#f4ecc2'],r:10,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'inset 0 0 0 2px rgba(243,238,217,.10)',bdName:'2 px sand edge',tex:'',texName:'Topo contours on maps',
 gauge:'bar',sweep:'seg',map:'Olive topo',mapF:'sepia(.65) hue-rotate(28deg) saturate(.85) brightness(1.05)',topo:true,
 hu:'night',huNote:'Head unit, day and night'},
{id:'glass',name:'Glass',who:'Phone and tablet users who like a layered, map-first look when parked.',font:F.fig,head:F.fig,num:F.fig,lic:'Figtree · SIL OFL 1.1',wN:600,
 bg:'#0b1830',strip:'rgba(9,18,38,.28)',stripSafe:'#0d1a33',rail:'rgba(9,18,38,.28)',railSafe:'#0d1a33',s1:'rgba(18,32,62,.30)',s1Safe:'#16263f',s2:'rgba(255,255,255,.12)',s2Safe:'#22345a',s3:'rgba(255,255,255,.16)',s3Safe:'#2e4370',
 tx:'#f2f6fc',t2:'#ccd6e8',acc:'#5cc8ff',on:'#06142a',sec:'#9fb6d8',spd:'#a9e4fb',ramp:['#3a3a8f','#4d6fd1','#5ca8f0','#86d8f6','#d6f4ff'],r:28,
 glow:'0 0 28px rgba(92,200,255,.45)',tglow:'0 0 24px rgba(92,200,255,.55)',blur:22,alpha:'30 % cards, 22 px blur',border:'inset 0 0 0 1px rgba(255,255,255,.12)',bdName:'1 px light edge',tex:'',texName:'None',
 gauge:'arc',sweep:'arc',map:'Full-bleed dark',mapF:'saturate(1.15)',bgMap:true,bgImg:'radial-gradient(90% 70% at 15% 10%,#2b4f8f 0%,transparent 60%),radial-gradient(80% 60% at 90% 95%,#1b6b8a 0%,transparent 60%),linear-gradient(160deg,#10203f,#060c1a)',
 hu:'safe',huNote:'Phone and parked; HU gets the opaque Moving-safe variant'},
{id:'minimal',name:'Minimal',who:'People who want almost nothing on screen: flat, quiet, one thin accent.',font:F.man,head:F.man,num:F.man,lic:'Manrope · SIL OFL 1.1',wN:300,
 bg:'#151719',strip:'#151719',rail:'#191b1e',s1:'#1d2023',s2:'#272a2e',s3:'#3a3f45',tx:'#eceef0',t2:'#aeb4bb',acc:'#9cc4ff',on:'#0f1114',sec:'#7d848c',spd:'#eceef0',
 ramp:['#3a3e44','#5a6068','#858c95','#b6bcc3','#e8ebee'],r:8,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'none',bdName:'None',tex:'',texName:'None',
 gauge:'thin',sweep:'thin',map:'Greyscale',mapF:'grayscale(1) brightness(.95)',
 hu:'safe',huNote:'Head unit OK; Moving lifts numerals from 300 to 500 weight'},
{id:'race',name:'Race',who:'Drive-mode fans who want a RealDash-style cluster with sweeps and a shift-light bar.',font:F.barc,head:F.barc,num:F.barc,lic:'Barlow Condensed · SIL OFL 1.1',wN:700,
 bg:'#000000',strip:'#000000',rail:'#08080a',s1:'#0d0d10',s2:'#18181c',s3:'#2a2a31',tx:'#ffffff',t2:'#c2c2cc',acc:'#e14bff',on:'#000000',sec:'#7a7a85',spd:'#ffffff',
 ramp:['#3a1d8a','#6a2fe0','#a646f2','#e055d6','#ff9be6'],r:4,glow:'0 0 18px rgba(225,75,255,.5)',tglow:'0 0 20px rgba(225,75,255,.6)',blur:0,alpha:'Opaque',border:'none',bdName:'None',tex:'',texName:'None',
 gauge:'race',sweep:'race',shift:true,map:'Black, magenta trace',mapF:'grayscale(.5) contrast(1.15) brightness(.8)',
 hu:'night',huNote:'Head unit at night; glow is off when Moving'},
{id:'deep',name:'Deep night',who:'Night drivers with OLED screens who want the least light possible in the cabin.',font:F.fig,head:F.fig,num:F.fig,lic:'Figtree · SIL OFL 1.1',wN:600,
 bg:'#000000',strip:'#000000',rail:'#040507',s1:'#07090d',s2:'#0e1219',s3:'#1a202b',tx:'#c6cedb',t2:'#939db0',acc:'#2a8fbf',on:'#000000',sec:'#5d6779',spd:'#9d8fd6',
 ramp:['#1f1838','#352a63','#504190','#7262b2','#998bd0'],r:24,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'none',bdName:'None',tex:'',texName:'None',
 gauge:'arc',sweep:'arc',map:'Dimmed dark',mapF:'brightness(.55) saturate(.7)',
 hu:'night',huNote:'Best for head units after dark'},
{id:'contrast',name:'High contrast',who:'Bright-sun drivers and anyone who needs maximum legibility and strong edges.',font:F.atk,head:F.atk,num:F.atk,lic:'Atkinson Hyperlegible · SIL OFL 1.1',wN:700,
 bg:'#ffffff',strip:'#ffffff',rail:'#ffffff',s1:'#ffffff',s2:'#eceef1',s3:'#c9ced6',tx:'#000000',t2:'#1f2733',acc:'#0047a0',on:'#ffffff',sec:'#3d4654',spd:'#2a1a6e',
 ramp:['#c9bdf5','#9a86e8','#6d50d8','#4b2fb0','#2a1a6e'],r:8,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'inset 0 0 0 3px #000000',bdName:'3 px black stroke',tex:'',texName:'None',
 gauge:'bar',sweep:'arc',thick:true,map:'Light, high contrast',mapF:'invert(1) hue-rotate(180deg) contrast(1.25)',
 hu:'day',huNote:'Daytime and sunlight; too bright for night'},
{id:'air',name:'Air',who:'Phone and tablet owners who want cards that float like frosted glass over a soft, blurred scene.',font:'Figtree',head:'Figtree',num:'Barlow Condensed',lic:'Figtree + Barlow Condensed · SIL OFL 1.1',wN:300,
 bg:'#121722',strip:'rgba(255,255,255,.06)',stripSafe:'#1c2230',rail:'rgba(255,255,255,.06)',railSafe:'#1c2230',s1:'rgba(255,255,255,.10)',s1Safe:'#232a39',s2:'rgba(255,255,255,.14)',s2Safe:'#2d3546',s3:'rgba(255,255,255,.24)',s3Safe:'#3b4458',
 tx:'#f4f6fa',t2:'#d3d8e2',acc:'#7fd0ff',on:'#0b1220',sec:'#aab3c2',spd:'#e6e9ef',ramp:['#3c4a6e','#5a6f9e','#8197c4','#adbfe0','#e3ebf8'],r:30,
 glow:'0 0 30px rgba(255,255,255,.25)',tglow:'',blur:30,alpha:'10 % cards, 30 px blur',border:'inset 0 1px 0 rgba(255,255,255,.35),inset 0 0 0 1px rgba(255,255,255,.16),0 18px 40px rgba(0,0,0,.35)',bdName:'Light rim + float shadow',
 tex:'linear-gradient(180deg,rgba(255,255,255,.12),rgba(255,255,255,0) 55%)',texName:'Top sheen · parked only',gauge:'thin',sweep:'thin',map:'Blurred, desaturated',mapF:'blur(3px) grayscale(.5) brightness(.75)',bgMap:true,
 bgImg:'radial-gradient(80% 60% at 20% 15%,#4a5a76 0%,transparent 60%),radial-gradient(70% 60% at 85% 85%,#21566a 0%,transparent 60%),linear-gradient(165deg,#1b2231,#0a0d14)',
 hu:'safe',huNote:'Phone and parked; HU gets opaque, unblurred cards'},
{id:'ledger',name:'Ledger',who:'People who like fintech-app clarity: monochrome, big confident numbers, pill buttons and one scarce cobalt.',font:'Instrument Sans',head:'Instrument Sans',num:'Instrument Sans',lic:'Instrument Sans · SIL OFL 1.1',wN:600,
 bg:'#0e1013',strip:'#0e1013',rail:'#0e1013',s1:'#1a1d21',s2:'#25292e',s3:'#363b42',tx:'#f4f4f5',t2:'#a9abb0',acc:'#7b82ff',on:'#0b0d12',sec:'#717378',spd:'#f4f4f5',
 ramp:['#2c2f5e','#454ba8','#6a70e6','#9ea3ff','#d6d8ff'],r:28,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'none',bdName:'None · depth from surface steps',tex:'',texName:'None',
 gauge:'arc',sweep:'arc',map:'Monochrome',mapF:'grayscale(1) brightness(.85) contrast(1.1)',hu:'night',huNote:'Head unit, any time'},
{id:'tide',name:'Tide',who:'Data lovers who want chart-grade precision: fine scales, nautical teal and quiet density.',font:'IBM Plex Sans',head:'IBM Plex Sans',num:'IBM Plex Sans',lic:'IBM Plex Sans · SIL OFL 1.1',wN:500,
 bg:'#05212a',strip:'#041c24',rail:'#06252f',s1:'#0a2e39',s2:'#103b48',s3:'#1b5262',tx:'#e6f5f6',t2:'#a4cdd2',acc:'#5fe0d2',on:'#03191f',sec:'#7fb1b8',spd:'#c9eefb',
 ramp:['#13465a','#1f6f86','#2f9bb0','#69c6d2','#c9eefb'],r:12,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'none',bdName:'None',tex:'',texName:'Chart graticule on maps',
 gauge:'thin',sweep:'arc',map:'Nautical teal',mapF:'sepia(.35) hue-rotate(140deg) saturate(1.4) brightness(.85)',hu:'night',huNote:'Head unit, day and night'},
{id:'lunar',name:'Lunar',who:'Night drivers who want a calm, celestial cabin: ink-violet sky, silver numerals, one moonlit glow when parked.',font:'Outfit',head:'Outfit',num:'Outfit',lic:'Outfit · SIL OFL 1.1',wN:300,
 bg:'#0a0918',strip:'#0a0918',rail:'#0d0c1f',s1:'#14122b',s2:'#1e1b3d',s3:'#2d2955',tx:'#eceaff',t2:'#b8b4e0',acc:'#b7aeff',on:'#0a0918',sec:'#8b86b8',spd:'#f2f0fb',
 ramp:['#2a2350','#43397f','#6458b0','#9188d6','#d8d3f6'],r:26,glow:'0 0 34px rgba(183,174,255,.32)',tglow:'',blur:0,alpha:'Opaque',border:'none',bdName:'None',tex:'',texName:'None',
 gauge:'thin',sweep:'thin',map:'Violet night',mapF:'hue-rotate(35deg) saturate(.8) brightness(.75)',hu:'night',huNote:'Head unit at night; glow off when Moving'},
{id:'tactile',name:'Tactile',who:'People who miss physical switchgear: chunky keys with real bevels, bold type, segmented dials.',font:'Space Grotesk',head:'Space Grotesk',num:'Space Grotesk',lic:'Space Grotesk · SIL OFL 1.1',wN:700,
 bg:'#1b1a18',strip:'#161513',rail:'#1f1e1b',s1:'#2a2926',s2:'#35332f',s3:'#4a4741',tx:'#f5f2ea',t2:'#c9c4b8',acc:'#a8d8ff',on:'#14130f',sec:'#9d978a',spd:'#f5f2ea',
 ramp:['#3d3a52','#5a5585','#7f78b8','#aaa4dc','#ddd9f4'],r:18,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'inset 0 1px 0 rgba(255,255,255,.10),inset 0 -3px 0 rgba(0,0,0,.45),0 4px 0 rgba(0,0,0,.55)',bdName:'Bevel + key shadow',tex:'',texName:'None',
 gauge:'bar',sweep:'seg',map:'Graphite',mapF:'grayscale(.7) brightness(.9)',hu:'night',huNote:'Head unit, any time; great with gloves'},
{id:'slab',name:'Slab',who:'People who want loud, raw and unmistakable: thick black outlines, hard offset shadows, clashing pastels.',font:'Archivo',head:'Archivo',num:'Archivo',lic:'Archivo · SIL OFL 1.1',wN:800,lightBg:1,
 bg:'#fff1d6',strip:'#fff1d6',rail:'#fff1d6',s1:'#ffffff',s2:'#c9b8ff',s3:'#7ce0ff',tx:'#111111',t2:'#2c2c2c',acc:'#2b4dff',on:'#ffffff',sec:'#111111',spd:'#111111',
 ramp:['#c9b8ff','#9c86ff','#6c50f0','#3f22c4','#1d0b78'],r:6,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'inset 0 0 0 3px #111111,5px 5px 0 #111111',bdName:'3 px black + 5 px hard shadow',tex:'',texName:'None',
 gauge:'bar',sweep:'seg',map:'Light, inked',mapF:'invert(1) hue-rotate(180deg) grayscale(.6) contrast(1.3)',bgImg:'radial-gradient(circle at 1px 1px,rgba(17,17,17,.18) 1.2px,transparent 1.5px) 0 0/22px 22px',
 hu:'day',huNote:'Daytime; too bright for night cabins'},
{id:'prism',name:'Prism',who:'Parked showpiece: vivid frosted panels floating over colourful bokeh, with glowing glass rims.',font:'Plus Jakarta Sans',head:'Plus Jakarta Sans',num:'Plus Jakarta Sans',lic:'Plus Jakarta Sans · SIL OFL 1.1',wN:600,
 bg:'#140b2e',strip:'rgba(255,255,255,.08)',stripSafe:'#221845',rail:'rgba(255,255,255,.08)',railSafe:'#221845',s1:'rgba(255,255,255,.12)',s1Safe:'#2a1f52',s2:'rgba(255,255,255,.16)',s2Safe:'#372a66',s3:'rgba(255,255,255,.28)',s3Safe:'#4a3a85',
 tx:'#ffffff',t2:'#e4dcff',acc:'#7ef2ff',on:'#140b2e',sec:'#c2b5f0',spd:'#ffffff',ramp:['#5b2bd1','#9b3bd6','#e04fb0','#ff8a7a','#ffd3a8'],r:28,
 glow:'0 0 36px rgba(126,242,255,.45)',tglow:'',blur:26,alpha:'12 % cards, 26 px blur',border:'inset 0 0 0 1.5px rgba(255,255,255,.42),inset 0 1px 0 rgba(255,255,255,.6),0 20px 40px rgba(10,0,40,.4)',bdName:'Vivid glass rim',
 tex:'linear-gradient(135deg,rgba(255,255,255,.18),rgba(255,255,255,0) 50%)',texName:'Specular sheen · parked only',gauge:'arc',sweep:'race',map:'Saturated dark',mapF:'saturate(1.4) hue-rotate(20deg) brightness(.8)',
 bgImg:'radial-gradient(28% 34% at 18% 22%,rgba(224,79,176,.75),transparent 70%),radial-gradient(30% 36% at 82% 30%,rgba(91,43,209,.85),transparent 70%),radial-gradient(34% 40% at 60% 88%,rgba(255,138,122,.55),transparent 70%),radial-gradient(22% 26% at 35% 70%,rgba(60,190,255,.45),transparent 70%),linear-gradient(160deg,#1c0f3e,#0a0620)',
 hu:'safe',huNote:'Parked and phone; HU gets opaque violet panels'},
{id:'paper',name:'Paper',who:'People who want the app to disappear: white space, black type, nothing decorative.',font:'DM Sans',head:'DM Sans',num:'DM Sans',lic:'DM Sans · SIL OFL 1.1',wN:500,lightBg:1,
 bg:'#ffffff',strip:'#ffffff',rail:'#ffffff',s1:'#f4f4f2',s2:'#e9e9e6',s3:'#d6d6d1',tx:'#111111',t2:'#55555a',acc:'#111111',on:'#ffffff',sec:'#8a8a8f',spd:'#111111',
 ramp:['#d6d6d1','#a8a8a4','#7a7a77','#4a4a48','#111111'],r:4,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'none',bdName:'None',tex:'',texName:'None',
 gauge:'thin',sweep:'thin',map:'Light greyscale',mapF:'invert(1) hue-rotate(180deg) grayscale(1) brightness(1.08)',hu:'day',huNote:'Daytime; Auto hands over to Night after dusk'},
{id:'soft',name:'Soft',who:'People who like neumorphic calm: everything gently extruded from one soft-grey surface.',font:'Plus Jakarta Sans',head:'Plus Jakarta Sans',num:'Plus Jakarta Sans',lic:'Plus Jakarta Sans · SIL OFL 1.1',wN:700,lightBg:1,
 bg:'#e3e7ee',strip:'#e3e7ee',rail:'#e3e7ee',s1:'#e3e7ee',s2:'#e3e7ee',s3:'#d3d9e3',tx:'#232a38',t2:'#4a5366',acc:'#3555d6',on:'#ffffff',sec:'#7a8396',spd:'#232a38',
 ramp:['#c6cde0','#97a3cc','#6b7bc0','#4559b0','#26388a'],r:22,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'7px 7px 16px #b9c0cc,-7px -7px 16px #ffffff',bdName:'Dual soft extrusion',tex:'',texName:'None',
 gauge:'arc',sweep:'arc',map:'Light, soft',mapF:'invert(1) hue-rotate(180deg) grayscale(.8) brightness(1.02) contrast(.9)',hu:'day',huNote:'Daytime and phone; edges too subtle at night'},
{id:'bakelite',name:'Bakelite',who:'Retro-tech fans: moulded brown plastic, chrome-edged keys, glowing vacuum-fluorescent digits.',font:'Bitter',head:'Bitter',num:'Share Tech Mono',lic:'Bitter + Share Tech Mono · SIL OFL 1.1',wN:400,
 bg:'#1a110d',strip:'#140d0a',rail:'#1f1510',s1:'#2c1e17',s2:'#3a2820',s3:'#5a3f30',tx:'#f1e6d0',t2:'#d1c0a2',acc:'#e9d8b2',on:'#1a110d',sec:'#a8916e',spd:'#8ff5d6',
 ramp:['#1f4f48','#2c7a6c','#43a891','#6dd4b6','#b8f7e4'],r:10,glow:'0 0 26px rgba(143,245,214,.4)',tglow:'',blur:0,alpha:'Opaque',border:'inset 0 1px 0 rgba(255,255,255,.22),inset 0 -3px 0 rgba(0,0,0,.55),0 0 0 2px #6b5a4a,0 3px 6px rgba(0,0,0,.6)',bdName:'Chrome bezel + key bevel',
 tex:'linear-gradient(180deg,rgba(255,240,220,.10),rgba(0,0,0,.18))',texName:'Moulded sheen · parked only',gauge:'needle',sweep:'needle',map:'Warm sepia',mapF:'sepia(.8) saturate(.7) brightness(.8)',hu:'night',huNote:'Head unit at night; VFD glow off when Moving'},
{id:'clay',name:'Clay',who:'Playful, friendly cabins: puffy pastel shapes that look moulded and squishy.',font:'Nunito',head:'Nunito',num:'Nunito',lic:'Nunito · SIL OFL 1.1',wN:800,lightBg:1,
 bg:'#ece3ff',strip:'#ece3ff',rail:'#ece3ff',s1:'#f8f3ff',s2:'#e3d8ff',s3:'#cdbcff',tx:'#251a47',t2:'#4f4378',acc:'#5a3cf0',on:'#ffffff',sec:'#7d72a8',spd:'#251a47',
 ramp:['#cdbcff','#a68cff','#7f5cf5','#5a3cf0','#3a1fb5'],r:32,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'inset -6px -8px 14px rgba(110,80,200,.20),inset 6px 8px 14px rgba(255,255,255,.95),0 14px 26px rgba(110,80,200,.28)',bdName:'Inflated inner + drop shadow',
 tex:'linear-gradient(150deg,rgba(255,255,255,.7),rgba(255,255,255,0) 60%)',texName:'Pastel puff gradient · parked only',gauge:'arc',sweep:'arc',map:'Pastel',mapF:'invert(1) hue-rotate(200deg) saturate(.6) brightness(1.05)',hu:'day',huNote:'Daytime, phone and passenger'},
{id:'tonal',name:'Tonal',who:'Android-native feel: tonal surfaces and containers tinted from one seed colour.',font:'Lexend',head:'Lexend',num:'Lexend',lic:'Lexend · SIL OFL 1.1',wN:500,
 bg:'#141218',strip:'#141218',rail:'#1d1b20',s1:'#211f26',s2:'#2b2930',s3:'#4a4458',tx:'#e6e0e9',t2:'#cac4d0',acc:'#d0bcff',on:'#381e72',sec:'#938f99',spd:'#eaddff',
 ramp:['#381e72','#4f378b','#6750a4','#9a82db','#eaddff'],r:20,glow:'',tglow:'',blur:0,alpha:'Opaque',border:'none',bdName:'None · tonal elevation',tex:'',texName:'None',
 gauge:'arc',sweep:'arc',map:'Seed-tinted dark',mapF:'hue-rotate(250deg) saturate(.6) brightness(.85)',hu:'night',huNote:'Head unit, any time; seed colour from wallpaper later'},
{id:'clarity',name:'Clarity',who:'People who like platform-native polish: crisp type, grouped lists, a lightly translucent bar.',font:'Albert Sans',head:'Albert Sans',num:'Albert Sans',lic:'Albert Sans · SIL OFL 1.1',wN:600,lightBg:1,
 bg:'#f2f2f7',strip:'rgba(242,242,247,.72)',stripSafe:'#f2f2f7',rail:'rgba(249,249,251,.8)',railSafe:'#f9f9fb',s1:'#ffffff',s2:'#e8e8ed',s3:'#d1d1d6',tx:'#000000',t2:'#3c3c43',acc:'#0062cc',on:'#ffffff',sec:'#8e8e93',spd:'#000000',
 ramp:['#c9d6f2','#8fa9e6','#5a7fd8','#3157c2','#173a9a'],r:14,glow:'',tglow:'',blur:20,alpha:'Bars only · 72 %, 20 px blur',border:'none',bdName:'None',tex:'',texName:'None',
 gauge:'thin',sweep:'arc',map:'Light standard',mapF:'invert(1) hue-rotate(180deg) brightness(1.05)',hu:'day',huNote:'Daytime; pairs with Night after dusk'},
{id:'blueprint',name:'Blueprint',who:'Engineers and restorers: the car as a technical drawing, white linework on blueprint blue.',font:'IBM Plex Mono',head:'IBM Plex Mono',num:'IBM Plex Mono',lic:'IBM Plex Mono · SIL OFL 1.1',wN:500,
 bg:'#0b3a75',strip:'#0a3468',rail:'#0a3468',s1:'rgba(255,255,255,.05)',s2:'rgba(255,255,255,.10)',s3:'rgba(255,255,255,.22)',tx:'#ffffff',t2:'#d2e2f7',acc:'#ffffff',on:'#0b3a75',sec:'#a9c3e6',spd:'#ffffff',
 ramp:['#3a6aa8','#5d8bc6','#8eb2e0','#bcd3f0','#ffffff'],r:2,glow:'',tglow:'',blur:0,alpha:'5 % tint',border:'inset 0 0 0 1.5px rgba(255,255,255,.75)',bdName:'1.5 px white linework',tex:'',texName:'Drafting grid on background',
 gauge:'thin',sweep:'needle',map:'Cyanotype',mapF:'grayscale(1) sepia(1) hue-rotate(175deg) saturate(3) brightness(.75)',
 bgImg:'linear-gradient(rgba(255,255,255,.07) 1px,transparent 1px) 0 0/24px 24px,linear-gradient(90deg,rgba(255,255,255,.07) 1px,transparent 1px) 0 0/24px 24px,linear-gradient(rgba(255,255,255,.12) 1px,transparent 1px) 0 0/120px 120px,linear-gradient(90deg,rgba(255,255,255,.12) 1px,transparent 1px) 0 0/120px 120px',
 hu:'night',huNote:'Head unit, any time'}];
function hex(c){c=c.replace('#','');return [0,2,4].map(i=>parseInt(c.slice(i,i+2),16))}
function parse(c){if(c.startsWith('rgba')){const m=c.match(/[\d.]+/g).map(Number);return {rgb:m.slice(0,3),a:m[3]}}return {rgb:hex(c),a:1}}
function over(c,base){const p=parse(c),b=Array.isArray(base)?base:hex(base);return p.rgb.map((v,i)=>Math.round(v*p.a+b[i]*(1-p.a)))}
function lum(rgb){const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(rgb[0])+.7152*f(rgb[1])+.0722*f(rgb[2])}
function ratio(a,b){const x=lum(Array.isArray(a)?a:hex(a)),y=lum(Array.isArray(b)?b:hex(b));return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)}
window.OstlerThemes={list:L,byId:Object.fromEntries(L.map(t=>[t.id,t])),ratio,over,hex};
})();

(function(){const T=window.OstlerThemes;
T.resolve=function(id,o){o=o||{};const t=T.byId[id]||T.list[0],safe=!!o.moving;const pick=k=>safe&&t[k+'Safe']?t[k+'Safe']:t[k];const q=x=>"'"+x+"',system-ui,sans-serif";
return {id:t.id,name:t.name,bg:t.bg,tx:t.tx,t2:t.t2,acc:t.acc,on:t.on,sec:t.sec,spd:t.spd,ramp:t.ramp,s1:pick('s1'),s2:pick('s2'),s3:pick('s3'),strip:pick('strip'),rail:pick('rail'),
 bf:!safe&&t.blur?'blur('+t.blur+'px)':'none',glow:!safe&&t.glow?t.glow:'none',tex:!safe&&t.tex?t.tex:'none',bd:t.border,
 r:t.r,r2:Math.max(4,t.r-8),rc:t.r>=20?999:t.r,ff:q(t.font),fh:q(t.head),fn:q(t.num),wN:safe&&t.wN<500?500:t.wN,
 mapF:t.mapF,gauge:t.gauge,sweep:t.sweep,shift:!!t.shift,topo:!!t.topo,thick:!!t.thick,bgMap:!!t.bgMap,bgImg:t.bgImg||'none',light:t.id==='contrast',lt:t.id==='contrast'||!!t.lightBg,okT:(t.id==='contrast'||t.lightBg)?'#1f7a4b':'#2f9e63',warnT:(t.id==='contrast'||t.lightBg)?'#8a6110':'#bf8a1a',alT:(t.id==='contrast'||t.lightBg)?'#c0283f':'#ef6a7d'}};
const P=(cx,cy,r,a)=>[cx+r*Math.cos(a),cy+r*Math.sin(a)];
const arc=(cx,cy,r,a0,a1)=>{const p=P(cx,cy,r,a0),q=P(cx,cy,r,a1);return 'M'+p[0].toFixed(1)+' '+p[1].toFixed(1)+'A'+r+' '+r+' 0 '+(a1-a0>Math.PI?1:0)+' 1 '+q[0].toFixed(1)+' '+q[1].toFixed(1)};
const A0=Math.PI*.75,SW=Math.PI*1.5,RED='#ef6a7d';
T.sweep=function(h,c,o){const s=o.size,cx=s/2,cy=s/2,k=c.sweep,f=o.f,red=o.red||.8,neu=c.light?'#000':c.t2,K=[];
 const w=c.thick?22:k==='thin'?3:k==='needle'?4:k==='race'?18:14,r=s/2-w/2-6;
 if(k==='needle'){const r2=s/2-8;K.push(h('path',{key:'a',d:arc(cx,cy,r2,A0,A0+SW),stroke:c.s3,strokeWidth:3,fill:'none'}));K.push(h('path',{key:'b',d:arc(cx,cy,r2,A0+SW*red,A0+SW),stroke:RED,strokeWidth:7,fill:'none'}));
  for(let i=0;i<=25;i++){const a=A0+SW*i/25,m=i%5===0,p=P(cx,cy,r2-(m?20:10),a),q=P(cx,cy,r2-2,a);K.push(h('line',{key:'t'+i,x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:c.t2,strokeWidth:m?3:1.5}))}
  for(let i=0;i<=5;i++){const p=P(cx,cy,r2-38,A0+SW*i/5);K.push(h('text',{key:'n'+i,x:p[0],y:p[1]+6,textAnchor:'middle',fill:c.t2,style:{font:'600 '+Math.round(s/22)+'px '+c.fn}},String(i)))}
  const a=A0+SW*f,p=P(cx,cy,r2*.62,a),q=P(cx,cy,r2-6,a);K.push(h('line',{key:'nd',x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:c.acc,strokeWidth:6,strokeLinecap:'round'}))}
 else if(k==='seg'){const n=30;for(let i=0;i<n;i++){const a0=A0+SW*i/n+.012,a1=A0+SW*(i+1)/n-.012,lit=i/n<f,rz=i/n>=red;K.push(h('path',{key:i,d:arc(cx,cy,r,a0,a1),stroke:lit?(rz?RED:c.tx):(rz?'rgba(239,106,125,.3)':c.s3),strokeWidth:w+6,fill:'none'}))}}
 else{K.push(h('path',{key:'tr',d:arc(cx,cy,r,A0,A0+SW),stroke:c.s2,strokeWidth:w,fill:'none',strokeLinecap:k==='race'?'butt':'round'}));
  K.push(h('path',{key:'rz',d:arc(cx,cy,r,A0+SW*red,A0+SW),stroke:RED,strokeWidth:Math.max(3,w*.4),fill:'none',opacity:.85}));
  if(k==='race'){const n=c.ramp.length;for(let i=0;i<n;i++){const a0=A0+SW*f*i/n,a1=A0+SW*f*(i+1)/n;K.push(h('path',{key:'v'+i,d:arc(cx,cy,r,a0,a1+.01),stroke:c.ramp[i],strokeWidth:w,fill:'none'}))}}
  else K.push(h('path',{key:'v',d:arc(cx,cy,r,A0,A0+SW*f),stroke:neu,strokeWidth:w,fill:'none',strokeLinecap:'round'}))}
 return h('svg',{width:s,height:s,viewBox:'0 0 '+s+' '+s,style:{position:'absolute',left:0,top:0}},K)};
T.bar=function(h,c,o){const k=c.gauge,f=Math.max(0,Math.min(1,o.f)),b=o.band||[.3,.7],al=!!o.alarm,col=al?RED:(c.light?'#000':c.tx),K=[];
 if(k==='needle'){const cx=100,cy=52,r=44,a0=Math.PI,s=Math.PI;K.push(h('path',{key:'t',d:arc(cx,cy,r,a0,a0+s),stroke:c.s3,strokeWidth:3,fill:'none'}));K.push(h('path',{key:'b',d:arc(cx,cy,r,a0+s*b[0],a0+s*b[1]),stroke:c.t2,strokeWidth:7,fill:'none',opacity:.5}));
  for(let i=0;i<=10;i++){const a=a0+s*i/10,p=P(cx,cy,r-(i%5?6:11),a),q=P(cx,cy,r,a);K.push(h('line',{key:'k'+i,x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:c.t2,strokeWidth:i%5?1.5:2.5}))}
  const a=a0+s*f,q=P(cx,cy,r-2,a);K.push(h('line',{key:'n',x1:cx,y1:cy,x2:q[0],y2:q[1],stroke:al?RED:c.acc,strokeWidth:4,strokeLinecap:'round'}));K.push(h('circle',{key:'h',cx,cy,r:6,fill:c.s3}));
  return h('svg',{viewBox:'0 0 200 58',width:'100%',height:o.h||46,preserveAspectRatio:'xMidYMax meet'},K)}
 if(k==='bar'&&!c.thick){const n=12;for(let i=0;i<n;i++){const inb=i/n>=b[0]&&i/n<b[1];K.push(h('rect',{key:i,x:i*(200/n)+1,y:2,width:200/n-4,height:16,rx:2,fill:i/n<f?col:(inb?c.s3:c.s2)}))}return h('svg',{viewBox:'0 0 200 20',width:'100%',height:o.h||16,preserveAspectRatio:'none'},K)}
 const H=c.thick?16:k==='thin'?3:8;K.push(h('rect',{key:'t',x:0,y:(20-H)/2,width:200,height:H,rx:H/2,fill:c.s2,stroke:c.thick?'#000':'none',strokeWidth:c.thick?2:0}));
 K.push(h('rect',{key:'b',x:200*b[0],y:(20-H)/2,width:200*(b[1]-b[0]),height:H,fill:c.s3}));
 K.push(h('rect',{key:'m',x:Math.min(196,200*f-3),y:c.thick?0:1,width:k==='thin'?3:6,height:c.thick?20:18,rx:2,fill:col}));
 return h('svg',{viewBox:'0 0 200 20',width:'100%',height:o.h||14,preserveAspectRatio:'none'},K)};
T.shift=function(h,c,o){const n=12,K=[];for(let i=0;i<n;i++){const lit=i/n<o.f,rz=i>=n-2;K.push(h('rect',{key:i,x:i*(400/n)+2,y:0,width:400/n-6,height:20,rx:3,fill:lit?(rz?RED:c.ramp[Math.min(c.ramp.length-1,Math.floor(i/n*c.ramp.length))]):c.s2}))}return h('svg',{viewBox:'0 0 400 20',width:o.w,height:o.h||16,preserveAspectRatio:'none'},K)};
T.donut=function(h,c,o){const s=o.size,cx=s/2,r=s/2-s*.09,w=s*.16,tot=o.vals.reduce((a,b)=>a+b,0);let a=-Math.PI/2;const K=[];
 o.vals.forEach((v,i)=>{const a1=a+Math.PI*2*v/tot;K.push(h('path',{key:i,d:arc(cx,cx,r,a+.03,a1-.03),stroke:c.ramp[i],strokeWidth:w,fill:'none'}));a=a1});
 return h('svg',{width:s,height:s,viewBox:'0 0 '+s+' '+s},K)};
T.contrast=function(id){const t=T.byId[id],base=t.bgMap?'#0e1422':t.bg,s1=T.over(t.s1,base),s1s=t.s1Safe?T.hex(t.s1Safe):s1;
 const R=(n,fg,bg,min)=>{const v=T.ratio(T.hex(fg),bg);return {n,v:v.toFixed(1)+':1',ok:v>=min,min}};
 return [R('Text on background',t.tx,T.hex(t.bg),4.5),R(t.bgMap?'Text on card over map':'Text on card',t.tx,s1,4.5),R('Secondary on card',t.t2,s1,4.5),R('Label on accent',t.on,T.hex(t.acc),4.5),R('Accent on background',t.acc,T.hex(t.bg),3),R('Speed digits on card',t.spd,s1s,4.5)]};
})();
(function(){const T=window.OstlerThemes;
const WP=[[0.08,0.86],[0.2,0.74],[0.3,0.78],[0.42,0.6],[0.5,0.62],[0.58,0.44],[0.66,0.4],[0.72,0.26],[0.84,0.2],[0.92,0.1]];
T.trace=function(h,c,o){const w=o.w,hh=o.h,pl=o.pl||0,pad=o.pad||24;const X=x=>pl+pad+x*(w-pl-pad*2),Y=y=>pad+y*(hh-pad-(o.pb||pad));const K=[];
 if(c.topo){for(let i=1;i<9;i++)K.push(h('ellipse',{key:'e'+i,cx:X(.62),cy:Y(.42),rx:i*w*.07,ry:i*hh*.08,fill:'none',stroke:'rgba(243,238,217,.10)',strokeWidth:1}))}
 else{for(let i=0;i<7;i++)K.push(h('path',{key:'g'+i,d:'M'+X(i/6-.1)+' '+Y(1.05)+' L'+X(i/6+.25)+' '+Y(-.05),stroke:c.s3,strokeWidth:i%3?1:3,fill:'none',opacity:.6}));K.push(h('path',{key:'gh',d:'M'+X(0)+' '+Y(.5)+' C '+X(.3)+' '+Y(.3)+' '+X(.6)+' '+Y(.75)+' '+X(1)+' '+Y(.55),stroke:c.s3,strokeWidth:4,fill:'none',opacity:.6}))}
 const sp=[1,2,3,2,4,3,4,2,1];for(let i=0;i<WP.length-1;i++){const a=WP[i],b=WP[i+1];K.push(h('line',{key:'c'+i,x1:X(a[0]),y1:Y(a[1]),x2:X(b[0]),y2:Y(b[1]),stroke:c.light?'#fff':'#05080f',strokeWidth:9,strokeLinecap:'round'}));}
 for(let i=0;i<WP.length-1;i++){const a=WP[i],b=WP[i+1];K.push(h('line',{key:'l'+i,x1:X(a[0]),y1:Y(a[1]),x2:X(b[0]),y2:Y(b[1]),stroke:c.ramp[sp[i]],strokeWidth:5,strokeLinecap:'round'}))}
 return h('svg',{width:'100%',height:'100%',viewBox:'0 0 '+w+' '+hh,preserveAspectRatio:'xMidYMid slice',style:{position:'absolute',left:0,top:0}},K)};})();
(function(){const T=window.OstlerThemes,base=T.resolve;
const LAY={grid:['"veh g1 g2 map" "veh flt trip map"','1.15fr 1fr 1fr 1.15fr','1fr 1fr','Vehicle left, map right'],
 mapL:['"map g1 g2 veh" "map flt trip veh"','1.3fr 1fr 1fr 1.1fr','1fr 1fr','Map-first left'],
 center:['"g1 veh map g2" "flt veh map trip"','1fr 1.15fr 1.15fr 1fr','1fr 1fr','Centred pair, gauges flank'],
 stack:['"veh veh map map" "g1 g2 flt trip"','1fr 1fr 1fr 1fr','1.25fr 1fr','Wide hero row, tile row'],
 stackMap:['"map map veh veh" "g1 g2 flt trip"','1fr 1fr 1fr 1fr','1.25fr 1fr','Wide map row, tile row']};
const SH={
 night:{},
 heritage:{lay:'center',rail:'tab',lbl:'smallcaps',hero:'ring'},
 expedition:{rCard:'4px',rc:4,rTile:3,lay:'mapL',rail:'block',strip:'line',lbl:'wide',hero:'square',gap:6,mapFirst:1},
 glass:{lay:'mapL',rail:'float',strip:'float',mapFirst:1},
 minimal:{rCard:'8px',rc:8,lay:'stack',rail:'bar',strip:'line',lbl:'sentence',hero:'bare',gap:16,hdW:300,hdS:32},
 race:{rCard:'2px 22px 2px 22px',rc:2,rTile:2,lay:'center',rail:'block',lbl:'wide',hero:'cut',numIt:'italic',numLs:'-.01em'},
 deep:{rail:'bar',strip:'line',hero:'bare'},
 contrast:{rail:'block',lbl:'heavy',hero:'square'},
 air:{rCard:'32px',rc:999,lay:'stackMap',rail:'float',strip:'float',lbl:'sentence',hero:'bare',gap:14,mapFirst:1,numLs:'-.01em'},
 ledger:{rCard:'28px',rc:999,lay:'stack',rail:'pill',strip:'float',lbl:'sentence',hero:'bare',hdW:700,hdS:36,hdLs:'-.03em',numLs:'-.03em'},
 tide:{rCard:'6px',rc:6,rTile:4,lay:'mapL',rail:'bar',strip:'line',lbl:'wide',hero:'ring',gap:8,mapFirst:1},
 lunar:{rCard:'26px',rc:999,lay:'center',rail:'float',lbl:'sentence',hero:'ring',hdW:300,hdS:32,gap:14},
 tactile:{rCard:'18px',rc:12,rTile:12,rail:'block',lbl:'chip',hero:'square',gap:12},
 slab:{rCard:'0px',rc:0,rTile:0,lay:'stack',rail:'block',lbl:'ink',hero:'square',gap:16,hdW:900,hdTT:'uppercase',hdLs:'-.01em'},
 prism:{rCard:'30px',rc:999,lay:'center',rail:'float',strip:'float',lbl:'sentence',hero:'ring',gap:14},
 paper:{rCard:'0px',rc:2,rTile:0,lay:'stack',rail:'bar',strip:'line',lbl:'sentence',hero:'bare',gap:20,hdW:500,hdS:34,hdLs:'-.02em'},
 soft:{rCard:'26px',rc:999,rail:'pill',lbl:'sentence',hero:'ring',gap:18},
 bakelite:{rCard:'10px',rc:6,lay:'center',rail:'tab',lbl:'brass',hero:'ring'},
 clay:{rCard:'38px',rc:999,rTile:24,rail:'float',lbl:'sentence',hero:'ring',gap:16,hdW:900},
 tonal:{rCard:'16px',rc:8,rail:'pill',lbl:'sentence',hero:'ring',gap:12},
 clarity:{rCard:'14px',rc:999,lay:'stack',rail:'tint',lbl:'sentence',hero:'ring',hdW:800,hdS:34,hdLs:'-.02em'},
 blueprint:{rCard:'0px',rc:0,rTile:0,lay:'mapL',rail:'tab',strip:'line',lbl:'tag',hero:'cut',gap:12,mapFirst:1,hdTT:'uppercase',hdLs:'.04em'}};
const LBL={caps:['uppercase','.06em',700,'normal','transparent',null,'0',0,'Uppercase micro-label'],
 wide:['uppercase','.14em',800,'normal','transparent',null,'0',0,'Uppercase, wide tracking'],
 heavy:['uppercase','.04em',800,'normal','transparent','tx','0',0,'Heavy uppercase, full ink'],
 sentence:['none','0',500,'normal','transparent',null,'0',0,'Sentence case, quiet'],
 smallcaps:['none','.05em',600,'all-small-caps','transparent',null,'0',0,'Small caps'],
 chip:['uppercase','.06em',700,'normal','s3','tx','2px 10px',999,'Label in a key-cap chip'],
 ink:['uppercase','.04em',800,'normal','#111111','#ffffff','2px 8px',0,'Black ink tag'],
 brass:['none','.05em',700,'all-small-caps','#c9a96a','#1a110d','1px 8px',3,'Brass plate, small caps'],
 tag:['uppercase','.1em',600,'normal','rgba(255,255,255,.16)','#ffffff','1px 8px',0,'Drawing callout tag']};
const RAIL={pill:'Soft pill on active',block:'Solid accent block',bar:'Accent edge bar',tab:'Folder tab into content',float:'Floating detached dock',tint:'Tint only, no shape'};
const STRIP={bar:'Full-width bar',float:'Floating capsule',line:'Open, hairline under'};
const HERO={ring:'Round plate',square:'Squared plate',bare:'No plate, digits on canvas',cut:'Chamfered plate'};
T.sheetOf=id=>Object.assign({lay:'grid',rail:'pill',strip:'bar',lbl:'caps',hero:'ring'},SH[id]||{});
T.resolve=function(id,o){const c=base(id,o),s=T.sheetOf(id),L=LAY[s.lay],B=LBL[s.lbl];
 const rc=s.rc!=null?s.rc:c.rc,r2=s.rTile!=null?s.rTile:c.r2,rCard=s.rCard||c.r+'px';
 return Object.assign(c,{rc,r2,rCard,gap:s.gap||10,homeAreas:L[0],homeCols:L[1],homeRows:L[2],layoutName:L[3],
  lblTT:B[0],lblLs:B[1],lblW:B[2],lblFV:B[3],lblBg:B[4]==='s3'?c.s3:B[4],lblC:B[5]==='tx'?c.tx:(B[5]||c.t2),lblP:B[6],lblR:B[7],lblName:B[8],
  hdTT:s.hdTT||'none',hdLs:s.hdLs||'0',hdW:s.hdW||700,hdS:s.hdS||28,numIt:s.numIt||'normal',numLs:s.numLs||'0',
  rail:s.rail,railName:RAIL[s.rail],strip:s.strip,stripName:STRIP[s.strip],hero:s.hero,heroName:HERO[s.hero],
  heroR:s.hero==='ring'?'50%':s.hero==='square'?rCard:'0',heroBg:s.hero==='bare'?'transparent':c.s1,
  heroClip:s.hero==='cut'?'polygon(14% 0,86% 0,100% 14%,100% 86%,86% 100%,14% 100%,0 86%,0 14%)':'none',
  oVeh:s.mapFirst?2:1,oGrid:3,oMap:s.mapFirst?1:4})};})();
(function(){const T=window.OstlerThemes;
const P={
 night:{},
 heritage:{font:'Bitter',head:'DM Serif Display',num:'Bitter',lic:'DM Serif Display + Bitter · SIL OFL 1.1',wN:600,
  bg:'#1d1310',strip:'#170f0c',rail:'#21160f',s1:'#2b1d17',s2:'#3a281f',s3:'#54392b',tx:'#f3e7cf',t2:'#d4c09c',acc:'#d9a85b',on:'#1d1310',sec:'#a88f6c',spd:'#f3e7cf',
  ramp:['#3d2f5a','#5b4785','#7f69b0','#ab98d6','#e0d6f2'],r:14,glow:'0 0 26px rgba(217,168,91,.28)',border:'inset 0 0 0 1.5px rgba(217,168,91,.55)',bdName:'Brass hairline inlay',
  tex:'repeating-linear-gradient(96deg,rgba(255,226,180,.045) 0 2px,transparent 2px 9px),repeating-linear-gradient(92deg,rgba(0,0,0,.10) 0 1px,transparent 1px 23px)',texName:'Walnut grain · parked only',
  bgImg:'radial-gradient(120% 90% at 50% 0%,#3a2218 0%,transparent 70%),repeating-radial-gradient(circle at 20% 30%,rgba(255,240,220,.025) 0 1px,transparent 1px 4px)',gauge:'needle',sweep:'needle',map:'Sepia chart',mapF:'sepia(.85) saturate(.6) brightness(.72)'},
 expedition:{font:'Barlow',head:'Barlow Condensed',num:'Barlow Condensed',lic:'Barlow + Barlow Condensed · SIL OFL 1.1',wN:800,
  bg:'#1c2114',strip:'#161a10',rail:'#1f2516',s1:'#262d1b',s2:'#323a24',s3:'#46502f',tx:'#f2ecd6',t2:'#cfc7a6',acc:'#e8b84a',on:'#1c2114',sec:'#9e9877',spd:'#f2ecd6',
  r:4,border:'inset 0 0 0 2px #3e4728',bdName:'2 px olive frame',thick:true,topo:true,gauge:'bar',sweep:'seg',
  bgImg:'repeating-radial-gradient(circle at 28% 38%,rgba(232,184,74,.06) 0 1px,transparent 1px 28px),repeating-radial-gradient(circle at 78% 72%,rgba(242,236,214,.05) 0 1px,transparent 1px 34px)',texName:'Topo contours on background',map:'Topographic khaki',mapF:'sepia(.6) hue-rotate(35deg) saturate(.8) brightness(.8)'},
 glass:{r:24,bgImg:'radial-gradient(40% 50% at 15% 20%,rgba(60,170,230,.55),transparent 70%),radial-gradient(40% 50% at 85% 80%,rgba(40,90,200,.6),transparent 70%),linear-gradient(160deg,#0d1d3a,#050b18)'},
 minimal:{font:'Manrope',head:'Manrope',num:'Manrope',wN:200,bg:'#0e0e0f',strip:'#0e0e0f',rail:'#0e0e0f',s1:'#141416',s2:'#1d1d20',s3:'#2c2c30',tx:'#f5f5f5',t2:'#a3a3a8',acc:'#8fd0ff',on:'#0e0e0f',spd:'#f5f5f5',
  ramp:['#2c2c3c','#4a4a6a','#6f6f9c','#a0a0cc','#e2e2f4'],r:0,glow:'',border:'inset 0 -1px 0 #2c2c30',bdName:'Hairline underline only',tex:'',gauge:'thin',sweep:'thin',mapF:'grayscale(1) brightness(.7)'},
 race:{font:'Barlow',head:'Barlow Condensed',num:'Barlow Condensed',wN:800,bg:'#050505',strip:'#000000',rail:'#0a0a0a',s1:'#121212',s2:'#1c1c1c',s3:'#2c2c2c',tx:'#ffffff',t2:'#c4c4c4',acc:'#ffd400',on:'#000000',spd:'#ffffff',
  glow:'0 0 24px rgba(255,212,0,.35)',border:'inset 4px 0 0 #ffd400',bdName:'Yellow leading edge',shift:true,gauge:'bar',sweep:'race',
  bgImg:'repeating-linear-gradient(45deg,rgba(255,255,255,.035) 0 2px,transparent 2px 6px),repeating-linear-gradient(-45deg,rgba(255,255,255,.025) 0 2px,transparent 2px 6px)',texName:'Carbon weave on background'},
 deep:{wN:300,bg:'#000000',strip:'#000000',rail:'#000000',s1:'#070708',s2:'#0f0f11',s3:'#1b1b1f',tx:'#b8bcc4',t2:'#7d838e',acc:'#1f7fa8',on:'#000000',spd:'#9aa6c8',
  ramp:['#1a1830','#2a2650','#3d3870','#575090','#7c74b0'],glow:'',border:'inset 0 0 0 1px #16161a',bdName:'1 px near-black hairline',tex:'',gauge:'thin',sweep:'thin',mapF:'grayscale(.6) brightness(.45)'},
 contrast:{font:'Atkinson Hyperlegible',head:'Atkinson Hyperlegible',num:'Atkinson Hyperlegible',wN:700,bg:'#ffffff',strip:'#ffffff',rail:'#ffffff',s1:'#ffffff',s2:'#efefef',s3:'#d0d0d0',tx:'#000000',t2:'#1a1a1a',acc:'#0050a0',on:'#ffffff',spd:'#000000',
  r:10,border:'inset 0 0 0 3px #000000',bdName:'3 px black stroke',thick:true,gauge:'bar',sweep:'seg',glow:'',tex:''}};
const SX={
 night:{rCard:'20px',rc:999,strip:'float',gap:12,hdW:800},
 heritage:{rCard:'14px',rc:8,rTile:6,lay:'center',rail:'tab',strip:'line',lbl:'caps',lblX:['none','.08em',600,'all-small-caps','transparent','#d9a85b','0',0,'Engraved brass small caps'],hero:'ring',gap:12,hdW:400,hdS:34},
 expedition:{rCard:'4px',rc:4,rTile:2,lay:'mapL',rail:'block',strip:'bar',lbl:'caps',lblX:['uppercase','.16em',800,'normal','#e8b84a','#1c2114','1px 8px',2,'Stencilled hazard tag'],hero:'square',gap:6,mapFirst:1,hdW:800,hdS:32,hdTT:'uppercase',hdLs:'.02em'},
 glass:{rCard:'24px 24px 24px 6px',rc:999,lay:'center',rail:'float',strip:'float',lbl:'sentence',hero:'ring',gap:14},
 minimal:{rCard:'0px',rc:999,rTile:0,lay:'stack',rail:'tint',strip:'line',lbl:'caps',lblX:['none','.01em',300,'normal','transparent',null,'0',0,'Light sentence case'],hero:'bare',gap:24,hdW:200,hdS:40,hdLs:'-.02em',numLs:'-.04em'},
 race:{rCard:'2px 22px 2px 22px',rc:2,rTile:0,lay:'center',rail:'block',strip:'bar',lbl:'caps',lblX:['uppercase','.08em',800,'normal','#ffd400','#000000','1px 8px',0,'Yellow race tag'],hero:'cut',gap:8,numIt:'italic',numLs:'-.02em',hdW:800,hdS:32,hdTT:'uppercase'},
 deep:{rCard:'18px',rc:999,lay:'stack',rail:'bar',strip:'line',lbl:'caps',lblX:['none','.02em',500,'normal','transparent','#7d838e','0',0,'Dim sentence case'],hero:'bare',gap:14,hdW:400,hdS:30},
 contrast:{rCard:'10px',rc:10,rTile:6,lay:'grid',rail:'block',strip:'bar',lbl:'heavy',hero:'square',gap:10,hdW:800,hdS:32},
 slab:{},blueprint:{}};
T.list.forEach(x=>{if(P[x.id])Object.assign(x,P[x.id]);T.byId[x.id]=x});
if(T.byId.slab)T.byId.slab.bgImg='repeating-linear-gradient(0deg,rgba(17,17,17,.08) 0 1px,transparent 1px 22px),repeating-linear-gradient(90deg,rgba(17,17,17,.08) 0 1px,transparent 1px 22px)';
if(T.byId.blueprint)T.byId.blueprint.bgImg='repeating-linear-gradient(0deg,rgba(255,255,255,.12) 0 1px,transparent 1px 120px),repeating-linear-gradient(90deg,rgba(255,255,255,.12) 0 1px,transparent 1px 120px),repeating-linear-gradient(0deg,rgba(255,255,255,.06) 0 1px,transparent 1px 24px),repeating-linear-gradient(90deg,rgba(255,255,255,.06) 0 1px,transparent 1px 24px)';
const so=T.sheetOf;T.sheetOf=id=>Object.assign(so(id),SX[id]||{});
const ro=T.resolve;T.resolve=function(id,o){const c=ro(id,o),s=T.sheetOf(id),B=s.lblX;
 if(B)Object.assign(c,{lblTT:B[0],lblLs:B[1],lblW:B[2],lblFV:B[3],lblBg:B[4],lblC:B[5]||c.t2,lblP:B[6],lblR:B[7],lblName:B[8]});return c};})();