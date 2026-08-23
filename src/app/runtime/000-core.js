const nm=Object.fromEntries(NODES.map(n=>[n.id,n])); const inc={},out={};
for(const e of EDGES){(out[e.source]||=[]).push(e);(inc[e.target]||=[]).push(e)}
const q=document.getElementById('q'),bf=document.getElementById('branch'),cf=document.getElementById('character'),sf=document.getElementById('status'),list=document.getElementById('list'),detail=document.getElementById('detail'),flow=document.getElementById('flow'),et=document.getElementById('et'),count=document.getElementById('count'),charinfo=document.getElementById('charinfo');
[...new Set(NODES.map(n=>n.branch))].sort().forEach(b=>{let o=document.createElement('option');o.value=b;o.textContent=b;bf.appendChild(o)});
const charWorks={}; for(const x of CHAR_LINKS){(charWorks[x.character]||=new Set()).add(x.work_id)}
Object.keys(charWorks).sort((a,b)=>a.localeCompare(b,'ja')).forEach(c=>{let o=document.createElement('option');o.value=c;o.textContent=c;cf.appendChild(o)});
let selected=null,hop=1; const esc=s=>(s??'').toString().replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
function pass(n){const z=[n.title,n.title_official,n.title_en,n.branch,n.branch_en,n.notes,n.source_note].join(' ').toLowerCase(),qq=q.value.trim().toLowerCase();if(qq&&!z.includes(qq))return false;if(bf.value&&n.branch!==bf.value)return false;
if(cf.value && !(charWorks[cf.value]||new Set()).has(n.id))return false;
if(sf.value==='released'&&!n.status.toLowerCase().includes('released'))return false;if(sf.value==='future'){let s=n.status.toLowerCase();if(!(s.includes('upcoming')||s.includes('announced')||n.release_raw==='TBA'))return false}if(sf.value==='unannounced'&&n.ja_status!=='unannounced')return false;if(sf.value==='source'&&!n.source_url)return false;return true}
function render(){
let a=NODES.filter(pass).sort((x,y)=>x.title.localeCompare(y.title,'ja'));
if(selected){
  const ctx=neighborhood(selected,hop);
  const ctxSet=new Set(ctx);
  const inCtx=a.filter(n=>ctxSet.has(n.id));
  const outCtx=a.filter(n=>!ctxSet.has(n.id));
  a=[...inCtx,...outCtx];
}
count.textContent=`${a.length} / ${NODES.length} 作品`;
list.innerHTML=a.map(n=>{
  const faded=(selected && !neighborhood(selected,hop).has(n.id)) ? ' style="opacity:.28"' : '';
  const marker=(selected && neighborhood(selected,hop).has(n.id)) ? '<span class="badge">関連</span>' : '';
  return `<div class="node-item ${selected===n.id?'selected':''}" data-id="${n.id}"${faded}><strong>${esc(n.title)}</strong>${n.source_url?'<span class="badge">公式ソース</span>':''}${marker}<div class="muted">${esc(n.title_en)} / ${esc(n.release)}</div></div>`
}).join('')||'<div class="node-item muted">該当なし</div>';
list.querySelectorAll('[data-id]').forEach(x=>x.onclick=()=>select(x.dataset.id));
if(cf.value){
  let ws=[...(charWorks[cf.value]||[])];
  charinfo.innerHTML=`<strong>${esc(cf.value)}</strong><br>主要出演・接続作品：${ws.length}件<br><span class="muted">※網羅的な全カメオ表ではなく、相関図を追うための主要出演・接続索引です。</span>`
}else{
  charinfo.textContent='上部のキャラクター欄から選ぶと、主要出演・物語接続作品だけに絞り込みます。'
}
applyCharacterHighlight()
}
function neighborhood(id,d){let seen=new Set([id]),front=new Set([id]);for(let k=0;k<d;k++){let next=new Set();for(const x of front){for(const e of(inc[x]||[])){if(!seen.has(e.source)){seen.add(e.source);next.add(e.source)}}for(const e of(out[x]||[])){if(!seen.has(e.target)){seen.add(e.target);next.add(e.target)}}}front=next}return seen}

const viewStates=new Map();
const mobileChartMotion=window.matchMedia('(max-width:760px)');
function ensureViewState(wrap){
  if(!wrap) return null;
  let st=viewStates.get(wrap);
  if(!st){st={scale:1,x:0,y:0,drag:false,lastX:0,lastY:0,raf:0};viewStates.set(wrap,st)}
  return st;
}
function ensureMobileViewBoxState(wrap){
  if(!wrap) return null;
  const svg=wrap.querySelector('svg'); if(!svg) return null;
  const st=ensureViewState(wrap);
  if(!st.baseViewBox){
    const v=svg.viewBox.baseVal;
    st.baseViewBox={x:v.x,y:v.y,w:Math.max(1,v.width),h:Math.max(1,v.height)};
    st.vbX=st.baseViewBox.x; st.vbY=st.baseViewBox.y;
    st.vbW=st.baseViewBox.w; st.vbH=st.baseViewBox.h;
    st.viewportW=Math.max(1,wrap.clientWidth); st.viewportH=Math.max(1,wrap.clientHeight);
    st.scale=1; st.x=st.vbX; st.y=st.vbY;
  }
  return st;
}
function mobileViewportAspect(wrap,st){
  const cw=st.viewportW||Math.max(1,wrap.clientWidth),ch=st.viewportH||Math.max(1,wrap.clientHeight);
  return Math.max(.000001,cw/Math.max(1,ch));
}
function mobileCameraZoom(wrap,st){
  const a=mobileViewportAspect(wrap,st),b=st.baseViewBox;
  return (b.w/b.h>=a)?b.w/Math.max(.001,st.vbW):b.h/Math.max(.001,st.vbH);
}
function mobileCameraSizeForZoom(wrap,st,zoom){
  const a=mobileViewportAspect(wrap,st),b=st.baseViewBox,z=Math.max(.000001,zoom);
  if(b.w/b.h>=a){const w=b.w/z;return {w,h:w/a}}
  const h=b.h/z;return {w:h*a,h};
}
function mobileViewBoxMetrics(wrap,st,w=st.vbW,h=st.vbH){
  const cw=st.viewportW||Math.max(1,wrap.clientWidth), ch=st.viewportH||Math.max(1,wrap.clientHeight);
  const pxPerWorld=Math.max(.000001,Math.min(cw/Math.max(1,w),ch/Math.max(1,h)));
  const drawnW=w*pxPerWorld, drawnH=h*pxPerWorld;
  return {cw,ch,pxPerWorld,offsetX:(cw-drawnW)/2,offsetY:(ch-drawnH)/2};
}
function mobileClientToWorld(wrap,st,clientX,clientY,rectOverride){
  const rect=rectOverride||wrap.getBoundingClientRect();
  const m=mobileViewBoxMetrics(wrap,st);
  const px=clientX-rect.left, py=clientY-rect.top;
  return {x:st.vbX+(px-m.offsetX)/m.pxPerWorld,y:st.vbY+(py-m.offsetY)/m.pxPerWorld,px,py};
}
function setMobileViewBox(wrap,st,x,y,w,h){
  st.vbX=x; st.vbY=y; st.vbW=Math.max(.001,w); st.vbH=Math.max(.001,h);
  st.scale=st.baseViewBox.w/st.vbW;
  st.x=st.vbX; st.y=st.vbY;
}

// v5.11.4 Canvas renderer: mobile Graphviz tabs. The source SVG remains as the
// semantic/selection model; panning and zooming redraw a clipped Canvas view.
// The mobile camera uses the viewport aspect ratio so zoom fills the portrait chart area,
// while pinch/zoom keeps the touched world point anchored under the fingers.
const mobileCanvasStates=new WeakMap();
function mobileCanvasKey(wrap){const p=wrap?.closest('.panel');return (mobileChartMotion.matches&&p&&wrap.querySelector('svg g.node'))?p.id:null;}
function isMobileCanvasWrap(wrap){return !!mobileCanvasKey(wrap);}

function canvasRootMatrix(svg,el){
  try{
    const a=svg.getCTM(), b=el.getCTM();
    if(!a||!b) return {a:1,b:0,c:0,d:1,e:0,f:0};
    const m=a.inverse().multiply(b);
    return {a:m.a,b:m.b,c:m.c,d:m.d,e:m.e,f:m.f};
  }catch(_){return {a:1,b:0,c:0,d:1,e:0,f:0}}
}
function canvasPoint(m,x,y){return {x:m.a*x+m.c*y+m.e,y:m.b*x+m.d*y+m.f}}
function canvasRootBBox(svg,el){
  try{
    const b=el.getBBox(),m=canvasRootMatrix(svg,el);
    const p=[canvasPoint(m,b.x,b.y),canvasPoint(m,b.x+b.width,b.y),canvasPoint(m,b.x,b.y+b.height),canvasPoint(m,b.x+b.width,b.y+b.height)];
    const xs=p.map(q=>q.x),ys=p.map(q=>q.y),x=Math.min(...xs),y=Math.min(...ys),x2=Math.max(...xs),y2=Math.max(...ys);
    return {x,y,w:Math.max(.001,x2-x),h:Math.max(.001,y2-y),x2,y2};
  }catch(_){return null}
}
function canvasColor(v){return (!v||v==='none'||v==='transparent'||v==='rgba(0, 0, 0, 0)')?null:v}
function canvasDash(v){
  if(!v||v==='none') return [];
  return v.split(/[ ,]+/).map(Number).filter(Number.isFinite);
}
function canvasGroupState(el){
  const g=el.closest('g.node,g.edge,g.dynamic-edge-overlay');
  if(!g) return {alpha:1,display:true,classes:''};
  const cs=getComputedStyle(g);
  return {alpha:Math.max(0,Math.min(1,parseFloat(cs.opacity)||0)),display:cs.display!=='none',classes:g.getAttribute('class')||''};
}
function canvasTextLines(el){
  const size=parseFloat(el.getAttribute('font-size')||getComputedStyle(el).fontSize)||10;
  const x0=parseFloat(el.getAttribute('x')||0),y0=parseFloat(el.getAttribute('y')||0);
  const ts=[...el.querySelectorAll(':scope > tspan')];
  if(!ts.length) return [{text:el.textContent||'',x:x0,y:y0}];
  let y=y0;
  return ts.map(t=>{
    const dy=t.getAttribute('dy');
    if(dy){const m=dy.match(/^([+-]?[0-9.]+)em$/);y+=m?parseFloat(m[1])*size:(parseFloat(dy)||0)}
    return {text:t.textContent||'',x:parseFloat(t.getAttribute('x')||x0),y};
  });
}
function canvasPrimitive(svg,el){
  const tag=el.tagName.toLowerCase(),m=canvasRootMatrix(svg,el),bbox=canvasRootBBox(svg,el); if(!bbox) return null;
  let geom=null;
  if(tag==='path'){
    const d=el.getAttribute('d'); if(!d) return null;
    try{geom=new Path2D(d)}catch(_){return null}
  }else if(tag==='polygon'||tag==='polyline'){
    const nums=(el.getAttribute('points')||'').trim().split(/[ ,]+/).map(Number).filter(Number.isFinite); if(nums.length<4)return null;
    const p=new Path2D();p.moveTo(nums[0],nums[1]);for(let i=2;i+1<nums.length;i+=2)p.lineTo(nums[i],nums[i+1]);if(tag==='polygon')p.closePath();geom=p;
  }else if(tag==='text') geom=canvasTextLines(el); else return null;
  return {el,tag,m,bbox,geom,style:null};
}
function canvasStylePrimitive(p){
  const cs=getComputedStyle(p.el),gs=canvasGroupState(p.el);
  p.style={
    display:gs.display&&cs.display!=='none',alpha:gs.alpha*Math.max(0,Math.min(1,parseFloat(cs.opacity)||1)),classes:gs.classes,
    fill:canvasColor(cs.fill),stroke:canvasColor(cs.stroke),lineWidth:parseFloat(cs.strokeWidth)||1,
    dash:canvasDash(cs.strokeDasharray),lineCap:cs.strokeLinecap||'butt',lineJoin:cs.strokeLinejoin||'miter',
    vectorEffect:cs.vectorEffect||'',fontSize:parseFloat(p.el.getAttribute('font-size')||cs.fontSize)||10,
    fontFamily:p.el.getAttribute('font-family')||cs.fontFamily||'sans-serif',textAnchor:p.el.getAttribute('text-anchor')||'start'
  };
}
function canvasShadowFor(classes){
  if(classes.includes('current-goal')||(/\bfocus\b/.test(classes)&&!classes.includes('goal-node'))) return ['#ef4444',15];
  if(classes.includes('goal-node')) return ['#f59e0b',9];
  if(classes.includes('backhl')) return ['#38bdf8',8];
  if(classes.includes('forwardhl')) return ['#34d399',8];
  if(classes.includes('bothhl')||classes.includes('pathhl')) return ['#a78bfa',8];
  if(classes.includes('contexthl')) return ['#f59e0b',6];
  if(/\bhl\b/.test(classes)) return ['#60a5fa',7];
  return null;
}
function rebuildMobileCanvas(wrap,geometry=true){
  const st=mobileCanvasStates.get(wrap); if(!st) return;
  const svg=st.svg;
  if(geometry){
    st.primitives=[...svg.querySelectorAll('path,polygon,polyline,text')].filter(el=>!el.closest('defs')).map(el=>canvasPrimitive(svg,el)).filter(Boolean);
    st.nodeBoxes=[...svg.querySelectorAll('g.node')].map(g=>({id:gt(g),box:canvasRootBBox(svg,g)})).filter(x=>x.id&&x.box);
  }
  for(const p of st.primitives) canvasStylePrimitive(p);
  renderMobileCanvasCache(wrap);
  drawMobileCanvas(wrap);
  // The full cache now contains the final selection styling; retire the fast overlay.
  st.overlayActive=false; st.overlayState=null; clearMobileSelectionOverlay(wrap);
}
function resizeMobileCanvas(wrap){
  const cs=mobileCanvasStates.get(wrap); if(!cs) return;
  const st=ensureMobileViewBoxState(wrap),w=Math.max(1,wrap.clientWidth),h=Math.max(1,wrap.clientHeight),dpr=Math.min(3,window.devicePixelRatio||1);
  st.viewportW=w;st.viewportH=h;
  const rw=Math.max(1,Math.round(w*dpr)),rh=Math.max(1,Math.round(h*dpr));
  if(cs.canvas.width!==rw||cs.canvas.height!==rh){cs.canvas.width=rw;cs.canvas.height=rh;cs.dpr=dpr}
  if(cs.overlay&&(cs.overlay.width!==rw||cs.overlay.height!==rh)){cs.overlay.width=rw;cs.overlay.height=rh}
  cs.cssW=w;cs.cssH=h;drawMobileCanvas(wrap);
}
function trimMobileCanvasCaches(active){document.querySelectorAll('.svg-wrap').forEach(w=>{if(w===active)return;const x=mobileCanvasStates.get(w);if(x){x.caches=null;x.cachePixels=0;}});}
function initMobileCanvas(wrap){
  const key=mobileCanvasKey(wrap);if(!key)return null;
  trimMobileCanvasCaches(wrap);
  let cs=mobileCanvasStates.get(wrap); if(cs){resizeMobileCanvas(wrap);if(!cs.caches)rebuildMobileCanvas(wrap,false);return cs;}
  const svg=wrap.querySelector('svg');if(!svg)return null;
  const st=ensureMobileViewBoxState(wrap); if(!st)return null;
  // Keep the semantic SVG on its original coordinate window. Canvas owns camera motion.
  svg.setAttribute('viewBox',`${st.baseViewBox.x} ${st.baseViewBox.y} ${st.baseViewBox.w} ${st.baseViewBox.h}`);
  st.lastAppliedViewBox=null;
  const canvas=document.createElement('canvas');canvas.dataset.marvelMobileCanvas=key;canvas.setAttribute('aria-hidden','true');
  wrap.insertBefore(canvas,svg.nextSibling);
  const overlay=document.createElement('canvas');overlay.dataset.marvelMobileHighlight=key;overlay.setAttribute('aria-hidden','true');
  canvas.insertAdjacentElement('afterend',overlay);wrap.classList.add('mobile-canvas-active');
  cs={wrap,svg,canvas,ctx:canvas.getContext('2d',{alpha:true,desynchronized:true}),overlay,overlayCtx:overlay.getContext('2d',{alpha:true,desynchronized:true}),primitives:[],nodeBoxes:[],syncRaf:0,dpr:1,frames:0,cullDraws:0,overlayVersion:0,overlayDrawn:0,overlayActive:false,overlayState:null};
  mobileCanvasStates.set(wrap,cs);
  const observer=new MutationObserver(records=>{
    let geometry=false,style=false;
    for(const r of records){if(r.type==='childList') geometry=true;else if(r.type==='attributes') style=true}
    if(!geometry&&!style||cs.syncRaf)return;
    cs.syncRaf=requestAnimationFrame(()=>{cs.syncRaf=0;rebuildMobileCanvas(wrap,geometry)});
  });
  observer.observe(svg,{subtree:true,childList:true,attributes:true,attributeFilter:['class','style','d','points']});cs.observer=observer;
  cs.ro=new ResizeObserver(()=>resizeMobileCanvas(wrap));cs.ro.observe(wrap);
  resizeMobileCanvas(wrap);rebuildMobileCanvas(wrap,true);
  return cs;
}
function drawCanvasPrimitive(ctx,p,scale,gesture=false){
  const ps=p.style;if(!ps||!ps.display||ps.alpha<=0)return false;
  ctx.save();ctx.transform(scale*p.m.a,scale*p.m.b,scale*p.m.c,scale*p.m.d,scale*p.m.e,scale*p.m.f);ctx.globalAlpha=ps.alpha;
  const shadow=!gesture&&canvasShadowFor(ps.classes);if(shadow){ctx.shadowColor=shadow[0];ctx.shadowBlur=shadow[1]/Math.max(.001,scale);}
  if(p.tag==='text'){
    ctx.fillStyle=ps.fill||'#111827';ctx.textAlign=ps.textAnchor==='middle'?'center':(ps.textAnchor==='end'?'right':'left');ctx.textBaseline='alphabetic';
    ctx.font=`${ps.fontSize}px ${ps.fontFamily}`;for(const line of p.geom)ctx.fillText(line.text,line.x,line.y);
  }else{
    if(ps.fill){ctx.fillStyle=ps.fill;ctx.fill(p.geom)}
    if(ps.stroke&&ps.lineWidth>0){ctx.strokeStyle=ps.stroke;ctx.lineCap=ps.lineCap;ctx.lineJoin=ps.lineJoin;ctx.setLineDash(ps.dash);
      ctx.lineWidth=ps.vectorEffect==='non-scaling-stroke'?ps.lineWidth/Math.max(.001,scale):ps.lineWidth;ctx.stroke(p.geom)}
  }
  ctx.restore();return true;
}
function renderMobileCanvasCache(wrap){
  const cs=mobileCanvasStates.get(wrap);if(!cs)return false;
  const st=ensureMobileViewBoxState(wrap);if(!st)return false;
  const b=st.baseViewBox,lods=[.25,.5,1];cs.caches=new Map();let total=0;
  for(const lod of lods){
    const w=Math.max(1,Math.ceil(b.w*lod)),h=Math.max(1,Math.ceil(b.h*lod)),cache=document.createElement('canvas');cache.width=w;cache.height=h;
    const ctx=cache.getContext('2d',{alpha:true});ctx.clearRect(0,0,w,h);ctx.save();ctx.translate(-b.x*lod,-b.y*lod);
    let n=0;for(const p of cs.primitives){if(drawCanvasPrimitive(ctx,p,lod,false))n++;}ctx.restore();cs.caches.set(lod,cache);total+=w*h;
  }
  cs.cachePixels=total;cs.cacheVersion=(cs.cacheVersion||0)+1;return true;
}
function chooseMobileCanvasCache(cs,targetDensity){
  const lods=[.25,.5,1];let lod=lods[lods.length-1];for(const x of lods){if(x>=targetDensity*.92){lod=x;break}}
  return {lod,cache:cs.caches?.get(lod)};
}
// v5.11.3: fast selection overlay. The heavy background cache remains untouched for
// the first paint after a tap; only highlighted primitives are drawn on this small layer.
function clearMobileSelectionOverlay(wrap){
  const cs=mobileCanvasStates.get(wrap);if(!cs?.overlayCtx)return false;
  const c=cs.overlay,ctx=cs.overlayCtx;ctx.setTransform(1,0,0,1,0,0);ctx.globalAlpha=1;ctx.shadowBlur=0;ctx.clearRect(0,0,c.width,c.height);cs.overlayDrawn=0;cs.overlaySyntheticDrawn=0;return true;
}
function mobileOverlayNodeClass(id,state){
  if(selectedIds.has(id)) return id===selected?'current-goal':'goal-node';
  if(!state?.ctx?.has(id)) return null;
  if(state.pathMode) return 'pathhl';
  if(state.generic) return 'contexthl';
  const b=state.back?.has(id),f=state.forward?.has(id),c=state.context?.has(id);
  if(b&&f)return 'bothhl'; if(b)return 'backhl'; if(f)return 'forwardhl'; if(c)return 'contexthl';
  return 'hl';
}
function mobileOverlayEdgeClass(key,state){
  if(!key||!state)return null;
  if(state.pathMode) return state.pathEdges?.has(key)?'pathhl':null;
  if(state.generic) return state.contextEdges?.has(key)?'contexthl':null;
  const b=state.backEdges?.has(key),f=state.forwardEdges?.has(key),c=state.contextEdges?.has(key);
  if(b&&f)return 'bothhl'; if(b)return 'backhl'; if(f)return 'forwardhl'; if(c)return 'contexthl';
  return null;
}
function mobileOverlayCategory(p,state){
  const g=p.el.closest('g.node,g.edge,g.dynamic-edge-overlay');if(!g)return null;
  if(g.matches('g.node')) return mobileOverlayNodeClass(gt(g),state);
  // v5.11.4: edge <title> is rewritten to a human-readable tooltip after startup.
  // Keep using the canonical connection key cached on the edge group instead.
  const key=g.dataset?.edgeKey || (typeof window.marvelEdgeKeyFromGroup==='function'?window.marvelEdgeKeyFromGroup(g):'');
  return mobileOverlayEdgeClass(key||null,state);
}
function mobileOverlayColor(category){
  return category==='backhl'?'#38bdf8':category==='forwardhl'?'#34d399':category==='bothhl'||category==='pathhl'?'#a78bfa':category==='contexthl'?'#f59e0b':'#60a5fa';
}
function mobileOverlayCompressedBridges(edgeSet,visible){
  const adj=new Map();
  for(const k of (edgeSet||[])){
    const [a,b]=String(k).split('->');if(!a||!b)continue;
    if(!adj.has(a))adj.set(a,[]);adj.get(a).push(b);
  }
  const ans=[],seenBridge=new Set();
  for(const start of visible){
    for(const first of (adj.get(start)||[])){
      if(visible.has(first))continue;
      const q=[[first,[first]]],seen=new Set([first]);
      while(q.length){
        const [x,hidden]=q.shift();
        for(const y of (adj.get(x)||[])){
          if(visible.has(y)){
            const key=`${start}->${y}`;
            if(start!==y&&!seenBridge.has(key)){seenBridge.add(key);ans.push({source:start,target:y,hidden});}
            continue;
          }
          if(!seen.has(y)){seen.add(y);q.push([y,[...hidden,y]]);}
        }
      }
    }
  }
  return ans;
}
function mobileOverlaySyntheticSpecs(cs,state){
  if(!cs||!state||state.generic)return [];
  const visible=new Set(cs.nodeBoxes.map(n=>n.id));
  const staticKeys=new Set([...cs.svg.querySelectorAll('g.edge:not(.dynamic-edge-overlay)')].map(g=>g.dataset?.edgeKey||(typeof window.marvelEdgeKeyFromGroup==='function'?window.marvelEdgeKeyFromGroup(g):'')).filter(Boolean));
  const specs=[['backhl',state.backEdges],['forwardhl',state.forwardEdges],['contexthl',state.contextEdges],['pathhl',state.pathEdges||new Set()]];
  const out=[],seen=new Set();
  const add=(source,target,category,compressed=false)=>{
    const key=`${source}->${target}`;if(source===target||staticKeys.has(key)||seen.has(`${category}|${key}`))return;
    if(!visible.has(source)||!visible.has(target))return;
    seen.add(`${category}|${key}`);out.push({source,target,category,compressed});
  };
  for(const [category,set] of specs){
    for(const k of (set||[])){const [a,b]=String(k).split('->');if(a&&b)add(a,b,category,false);}
    if(category!=='contexthl')for(const br of mobileOverlayCompressedBridges(set,visible))add(br.source,br.target,category,true);
  }
  return out;
}
function mobileOverlayBoxBoundary(box,from,to){
  const cx=box.x+box.w/2,cy=box.y+box.h/2,dx=to.x-from.x,dy=to.y-from.y,ax=Math.abs(dx)||1e-6,ay=Math.abs(dy)||1e-6;
  const t=Math.min((box.w/2)/ax,(box.h/2)/ay);
  return {x:cx+dx*t,y:cy+dy*t};
}
function drawMobileSyntheticOverlayEdge(ctx,cs,spec,worldScale){
  const a=cs.nodeBoxes.find(n=>n.id===spec.source)?.box,b=cs.nodeBoxes.find(n=>n.id===spec.target)?.box;if(!a||!b)return false;
  const ac={x:a.x+a.w/2,y:a.y+a.h/2},bc={x:b.x+b.w/2,y:b.y+b.h/2};
  const start=mobileOverlayBoxBoundary(a,ac,bc),end=mobileOverlayBoxBoundary(b,bc,ac),dx=end.x-start.x,dy=end.y-start.y;
  const bend=Math.max(-34,Math.min(34,dx*.06));
  const c1={x:start.x+dx*.34,y:start.y+dy*.34-bend},c2={x:start.x+dx*.68,y:start.y+dy*.68-bend};
  const color=mobileOverlayColor(spec.category),w=Math.max(.001,worldScale),line=4.2/w;
  ctx.save();ctx.strokeStyle=color;ctx.fillStyle=color;ctx.lineWidth=line;ctx.lineCap='round';ctx.lineJoin='round';ctx.shadowColor=color;ctx.shadowBlur=9;
  ctx.setLineDash(spec.compressed?[10/w,6/w]:(spec.category==='contexthl'?[7/w,5/w]:[]));
  const path=new Path2D();path.moveTo(start.x,start.y);path.bezierCurveTo(c1.x,c1.y,c2.x,c2.y,end.x,end.y);ctx.stroke(path);
  const ang=Math.atan2(end.y-c2.y,end.x-c2.x),len=8/w,half=4.2/w;
  const tip=end,back={x:end.x-Math.cos(ang)*len,y:end.y-Math.sin(ang)*len},px=-Math.sin(ang),py=Math.cos(ang);
  const arrow=new Path2D();arrow.moveTo(tip.x,tip.y);arrow.lineTo(back.x+px*half,back.y+py*half);arrow.lineTo(back.x-px*half,back.y-py*half);arrow.closePath();ctx.fill(arrow);
  ctx.restore();return true;
}
function drawMobileOverlayPrimitive(ctx,p,category,worldScale){
  const ps=p.style;if(!ps||!ps.display)return false;
  ctx.save();ctx.transform(p.m.a,p.m.b,p.m.c,p.m.d,p.m.e,p.m.f);ctx.globalAlpha=1;
  const shadow=category==='current-goal'?['#ef4444',24]:category==='goal-node'?['#f59e0b',11]:[mobileOverlayColor(category),9];
  ctx.shadowColor=shadow[0];ctx.shadowBlur=shadow[1];
  if(p.tag==='text'){
    ctx.fillStyle=ps.fill||'#111827';ctx.textAlign=ps.textAnchor==='middle'?'center':(ps.textAnchor==='end'?'right':'left');ctx.textBaseline='alphabetic';
    ctx.font=`${ps.fontSize}px ${ps.fontFamily}`;for(const line of p.geom)ctx.fillText(line.text,line.x,line.y);
  }else{
    let fill=ps.fill,stroke=ps.stroke,lineWidth=ps.lineWidth;
    if(p.el.closest('g.edge,g.dynamic-edge-overlay')){
      const c=mobileOverlayColor(category);stroke=c;if(p.tag==='polygon')fill=c;lineWidth=Math.max(lineWidth||1,category==='contexthl'?3.6:4.2)/Math.max(.001,worldScale);
    }
    if(fill){ctx.fillStyle=fill;ctx.fill(p.geom)}
    if(stroke&&lineWidth>0){ctx.strokeStyle=stroke;ctx.lineCap=ps.lineCap;ctx.lineJoin=ps.lineJoin;ctx.setLineDash(ps.dash||[]);ctx.lineWidth=ps.vectorEffect==='non-scaling-stroke'?Math.max(lineWidth,ps.lineWidth/Math.max(.001,worldScale)):lineWidth;ctx.stroke(p.geom)}
  }
  ctx.restore();return true;
}
function drawMobileSelectionOverlay(wrap,state){
  const cs=mobileCanvasStates.get(wrap);if(!cs?.overlayCtx||!mobileChartMotion.matches)return false;
  const st=ensureMobileViewBoxState(wrap),m=mobileViewBoxMetrics(wrap,st),ctx=cs.overlayCtx,dpr=cs.dpr||1;if(!st||!m)return false;
  clearMobileSelectionOverlay(wrap);
  if(!selectedIds.size||!state){cs.overlayActive=false;cs.overlayState=null;return true;}
  ctx.setTransform(dpr*m.pxPerWorld,0,0,dpr*m.pxPerWorld,dpr*(m.offsetX-st.vbX*m.pxPerWorld),dpr*(m.offsetY-st.vbY*m.pxPerWorld));
  let n=0;for(const p of cs.primitives){const category=mobileOverlayCategory(p,state);if(category&&drawMobileOverlayPrimitive(ctx,p,category,m.pxPerWorld))n++;}
  let synthetic=0;for(const spec of mobileOverlaySyntheticSpecs(cs,state))if(drawMobileSyntheticOverlayEdge(ctx,cs,spec,m.pxPerWorld))synthetic++;
  cs.overlayActive=true;cs.overlayState=state;cs.overlayVersion=(cs.overlayVersion||0)+1;cs.overlayDrawn=n+synthetic;cs.overlaySyntheticDrawn=synthetic;return (n+synthetic)>0;
}

// v5.11.2: adaptive pan LOD (.25 at overview, up to .5 when zoomed); pinch stays at .25.
function drawMobileCanvas(wrap){
  const cs=mobileCanvasStates.get(wrap);if(!cs||!mobileChartMotion.matches)return false;
  const st=ensureMobileViewBoxState(wrap),ctx=cs.ctx;if(!st||!ctx||!cs.caches)return false;
  const dpr=cs.dpr||1,m=mobileViewBoxMetrics(wrap,st),b=st.baseViewBox,gesture=wrap.classList.contains('gesture-active'),panPick=chooseMobileCanvasCache(cs,Math.min(.5,m.pxPerWorld*dpr)),pick=gesture?(st.pinching?{lod:.25,cache:cs.caches?.get(.25)}:panPick):chooseMobileCanvasCache(cs,m.pxPerWorld*dpr),cache=pick.cache,lod=pick.lod;if(!cache)return false;
  ctx.setTransform(1,0,0,1,0,0);ctx.globalAlpha=1;ctx.shadowBlur=0;ctx.clearRect(0,0,cs.canvas.width,cs.canvas.height);
  const ix=Math.max(st.vbX,b.x),iy=Math.max(st.vbY,b.y),ix2=Math.min(st.vbX+st.vbW,b.x+b.w),iy2=Math.min(st.vbY+st.vbH,b.y+b.h);
  if(ix2>ix&&iy2>iy){
    const sx=(ix-b.x)*lod,sy=(iy-b.y)*lod,sw=(ix2-ix)*lod,sh=(iy2-iy)*lod;
    const dx=m.offsetX+(ix-st.vbX)*m.pxPerWorld,dy=m.offsetY+(iy-st.vbY)*m.pxPerWorld,dw=(ix2-ix)*m.pxPerWorld,dh=(iy2-iy)*m.pxPerWorld;
    ctx.setTransform(dpr,0,0,dpr,0,0);ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='medium';ctx.drawImage(cache,sx,sy,sw,sh,dx,dy,dw,dh);
  }
  cs.frames++;cs.cullDraws=1;cs.lastLod=lod;
  if(cs.overlayActive&&cs.overlayState) drawMobileSelectionOverlay(wrap,cs.overlayState);
  return true;
}
function mobileCanvasNodeBox(wrap,id){return mobileCanvasStates.get(wrap)?.nodeBoxes.find(x=>x.id===id)?.box||null}
function mobileCanvasHitTest(wrap,clientX,clientY){
  const cs=mobileCanvasStates.get(wrap),st=ensureMobileViewBoxState(wrap);if(!cs||!st)return null;
  const rect=wrap.getBoundingClientRect(),w=mobileClientToWorld(wrap,st,clientX,clientY,rect),m=mobileViewBoxMetrics(wrap,st),pad=8/Math.max(.001,m.pxPerWorld);
  for(let i=cs.nodeBoxes.length-1;i>=0;i--){const n=cs.nodeBoxes[i],b=n.box;if(w.x>=b.x-pad&&w.x<=b.x2+pad&&w.y>=b.y-pad&&w.y<=b.y2+pad)return n.id}
  return null;
}
window.marvelCanvasAudit=()=>{
  const wrap=activeWrap(),cs=wrap&&mobileCanvasStates.get(wrap),st=wrap&&ensureViewState(wrap);
  return {panel:wrap?.closest('.panel')?.id||null,active:!!cs,sourceViewBox:cs?.svg.getAttribute('viewBox')||null,canvas:[cs?.canvas.width||0,cs?.canvas.height||0],primitives:cs?.primitives.length||0,nodeBoxes:cs?.nodeBoxes.length||0,frames:cs?.frames||0,lastDrawn:cs?.cullDraws||0,cacheLod:cs?.lastLod||0,cachePixels:cs?.cachePixels||0,cacheVersion:cs?.cacheVersion||0,overlayVersion:cs?.overlayVersion||0,overlayDrawn:cs?.overlayDrawn||0,overlaySyntheticDrawn:cs?.overlaySyntheticDrawn||0,overlayActive:!!cs?.overlayActive,camera:st&&st.baseViewBox?{x:st.vbX,y:st.vbY,w:st.vbW,h:st.vbH}:null};
};

function applyView(wrap){
  if(!wrap) return;
  const svg=wrap.querySelector('svg'); if(!svg) return;
  const st=ensureViewState(wrap);
  if(mobileChartMotion.matches){
    const ms=ensureMobileViewBoxState(wrap); if(!ms) return;
    if(svg.style.transform!=='none') svg.style.transform='none';
    if(isMobileCanvasWrap(wrap)){initMobileCanvas(wrap);drawMobileCanvas(wrap);return;}
    const value=`${ms.vbX} ${ms.vbY} ${ms.vbW} ${ms.vbH}`;
    if(ms.lastAppliedViewBox!==value){svg.setAttribute('viewBox',value);ms.lastAppliedViewBox=value}
    return;
  }
  svg.style.transform=`translate3d(${st.x}px,${st.y}px,0) scale(${st.scale})`;
}
function scheduleView(wrap){
  if(!wrap) return;
  const st=ensureViewState(wrap);
  if(st.raf) return;
  st.raf=requestAnimationFrame(()=>{st.raf=0;applyView(wrap)});
}
function flushView(wrap){
  if(!wrap) return;
  const st=ensureViewState(wrap);
  if(st.raf){cancelAnimationFrame(st.raf);st.raf=0}
  applyView(wrap);
}
function fitView(wrap){
  if(!wrap) return;
  const svg=wrap.querySelector('svg'); if(!svg) return;
  if(mobileChartMotion.matches){
    const st=ensureMobileViewBoxState(wrap); if(!st) return;
    st.viewportW=Math.max(1,wrap.clientWidth); st.viewportH=Math.max(1,wrap.clientHeight);
    const fitZoom=.96,size=mobileCameraSizeForZoom(wrap,st,fitZoom),nw=size.w,nh=size.h;
    const cx=st.baseViewBox.x+st.baseViewBox.w/2,cy=st.baseViewBox.y+st.baseViewBox.h/2;
    setMobileViewBox(wrap,st,cx-nw/2,cy-nh/2,nw,nh);
    applyView(wrap);
    return;
  }
  // SVGのwidth/heightはptの場合があるため、viewBox値ではなく
  // ブラウザが実際にレイアウトしたCSSピクセル寸法を使ってfitする。
  svg.style.transform='none';
  const raw=svg.getBoundingClientRect();
  const iw=Math.max(1,raw.width), ih=Math.max(1,raw.height);
  const cw=Math.max(100,wrap.clientWidth), ch=Math.max(100,wrap.clientHeight);
  const scale=Math.max(0.05,Math.min(1.4, Math.min(cw/iw,ch/ih)*0.96));
  const st=ensureViewState(wrap);
  st.scale=scale; st.x=(cw-iw*scale)/2; st.y=(ch-ih*scale)/2;
  st.intrinsicW=iw; st.intrinsicH=ih;
  applyView(wrap);
}
function zoomAt(wrap, factor, clientX, clientY){
  if(!wrap) return;
  if(mobileChartMotion.matches){
    const st=ensureMobileViewBoxState(wrap); if(!st) return;
    const rect=wrap.getBoundingClientRect();
    const cx=clientX??(rect.left+rect.width/2), cy=clientY??(rect.top+rect.height/2);
    const anchor=mobileClientToWorld(wrap,st,cx,cy,rect);
    const oldZoom=mobileCameraZoom(wrap,st);
    const nextZoom=Math.max(.85,Math.min(65,oldZoom*factor));
    const size=mobileCameraSizeForZoom(wrap,st,nextZoom),nw=size.w,nh=size.h;
    const nm=mobileViewBoxMetrics(wrap,st,nw,nh);
    const nx=anchor.x-(anchor.px-nm.offsetX)/nm.pxPerWorld;
    const ny=anchor.y-(anchor.py-nm.offsetY)/nm.pxPerWorld;
    setMobileViewBox(wrap,st,nx,ny,nw,nh); applyView(wrap); return;
  }
  const st=ensureViewState(wrap);
  const rect=wrap.getBoundingClientRect();
  const px=(clientX??(rect.left+rect.width/2))-rect.left;
  const py=(clientY??(rect.top+rect.height/2))-rect.top;
  const old=st.scale, next=Math.max(0.08,Math.min(4.5,old*factor));
  const wx=(px-st.x)/old, wy=(py-st.y)/old;
  st.scale=next; st.x=px-wx*next; st.y=py-wy*next;
  applyView(wrap);
}
function centerNodeInView(id){
  const wrap=activeWrap(), svg=activeSvg(); if(!wrap||!svg) return false;
  const g=[...svg.querySelectorAll('g.node')].find(n=>gt(n)===id); if(!g) return false;
  if(mobileChartMotion.matches){
    const st=ensureMobileViewBoxState(wrap); if(!st) return false;
    if(isMobileCanvasWrap(wrap)){
      const b=mobileCanvasNodeBox(wrap,id);if(!b)return false;
      const center={x:b.x+b.w/2,y:b.y+b.h/2},localW=b.w,localH=b.h,aspect=mobileViewportAspect(wrap,st);
      const desiredW=Math.max(localW*5,localH*5*aspect),minSize=mobileCameraSizeForZoom(wrap,st,65);
      const nw=Math.min(st.vbW,Math.max(minSize.w,desiredW)),nh=nw/aspect;
      setMobileViewBox(wrap,st,center.x-nw/2,center.y-nh/2,nw,nh);applyView(wrap);return true;
    }
    applyView(wrap);
    const wr=wrap.getBoundingClientRect(), gr=g.getBoundingClientRect();
    const m=mobileViewBoxMetrics(wrap,st);
    const center=mobileClientToWorld(wrap,st,gr.left+gr.width/2,gr.top+gr.height/2,wr);
    const localW=Math.max(1,gr.width/m.pxPerWorld), localH=Math.max(1,gr.height/m.pxPerWorld);
    const aspect=mobileViewportAspect(wrap,st);
    const desiredW=Math.max(localW*5,localH*5*aspect),minSize=mobileCameraSizeForZoom(wrap,st,65);
    const nw=Math.min(st.vbW,Math.max(minSize.w,desiredW));
    const nh=nw/aspect;
    setMobileViewBox(wrap,st,center.x-nw/2,center.y-nh/2,nw,nh);
    applyView(wrap); return true;
  }
  const st=ensureViewState(wrap), wr=wrap.getBoundingClientRect(), gr=g.getBoundingClientRect();
  const oldScale=Math.max(.0001,st.scale);
  // 現在の描画結果から「SVGの未変換CSS座標」を逆算する。
  // Graphviz内部のY軸反転やgroup transformに依存しない。
  const localCx=(gr.left+gr.width/2-wr.left-st.x)/oldScale;
  const localCy=(gr.top+gr.height/2-wr.top-st.y)/oldScale;
  const localW=Math.max(1,gr.width/oldScale), localH=Math.max(1,gr.height/oldScale);
  const targetScale=Math.max(st.scale,Math.min(2.4,Math.max(.9,Math.min(wr.width/(localW*5),wr.height/(localH*5)))));
  st.scale=targetScale;
  st.x=wr.width/2-localCx*targetScale;
  st.y=wr.height/2-localCy*targetScale;
  applyView(wrap);
  return true;
}
function initSvgInteraction(){
  document.querySelectorAll('.svg-wrap').forEach(wrap=>{
    if(wrap.dataset.zoomInit==='1') return;
    wrap.dataset.zoomInit='1';
    wrap.classList.add('scroll-friendly');

    const hint=document.createElement('div');
    hint.className='zoom-hint';
    hint.textContent=window.matchMedia('(max-width:760px)').matches
      ? '1本指: 図を移動 / 2本指: 図をズーム / タップ: ゴール追加・解除'
      : 'チャート上のホイール: 図をズーム / ドラッグ: 図を移動';
    wrap.appendChild(hint);

    const jump=document.createElement('button');
    jump.type='button';
    jump.className='chart-watch-jump';
    jump.textContent='↓ 予習・視聴プラン';
    jump.setAttribute('aria-label','予習・視聴プランへ移動');
    jump.addEventListener('pointerdown',e=>e.stopPropagation());
    jump.addEventListener('click',e=>{
      e.preventDefault(); e.stopPropagation();
      const target=document.getElementById('watchWorkspace');
      if(!target) return;
      const behavior=window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth';
      target.scrollIntoView({block:'start',behavior});
    });
    wrap.appendChild(jump);

    // PUBLIC v5.12.2: on desktop, wheel over the chart zooms directly.
    // Wheel outside the chart remains normal document scrolling; mobile keeps touch gestures.
    wrap.addEventListener('wheel',e=>{
      if(!wrap.querySelector('svg') || mobileChartMotion.matches) return;
      e.preventDefault();
      const mag=Math.min(3,Math.max(.35,Math.abs(e.deltaY)/90));
      const base=e.deltaY<0?1.10:0.91;
      zoomAt(wrap,Math.pow(base,mag),e.clientX,e.clientY);
    },{passive:false});

    const pointers=new Map();
    const midpoint=()=>{
      const a=[...pointers.values()];
      if(a.length<2) return null;
      return {x:(a[0].x+a[1].x)/2,y:(a[0].y+a[1].y)/2,d:Math.hypot(a[0].x-a[1].x,a[0].y-a[1].y)};
    };

    wrap.addEventListener('pointerdown',e=>{
      if(e.target.closest?.('.chart-watch-jump')) return;
      const st=ensureViewState(wrap);
      pointers.set(e.pointerId,{x:e.clientX,y:e.clientY,type:e.pointerType});

      if(e.pointerType==='touch'){
        try{wrap.setPointerCapture?.(e.pointerId)}catch(_){}
        wrap.classList.add('gesture-active','dragging');
        if(pointers.size<2){
          st.pinching=false; st.drag=true; st.moved=false; st.pointerId=e.pointerId;
          st.startX=e.clientX; st.startY=e.clientY; st.lastX=e.clientX; st.lastY=e.clientY;
          return;
        }
        for(const id of pointers.keys()) try{wrap.setPointerCapture?.(id)}catch(_){}
      }

      if(pointers.size>=2){
        const p=midpoint();
        st.pinching=true; st.moved=true; st.drag=false;
        st.pinchDist=Math.max(1,p.d); st.pinchX=p.x; st.pinchY=p.y;
        st.gestureRect=wrap.getBoundingClientRect();
        wrap.classList.add('dragging');
        return;
      }

      // Mouse / pen keep the familiar one-pointer chart pan.
      st.pinching=false; st.drag=true; st.moved=false; st.pointerId=e.pointerId;
      st.startX=e.clientX; st.startY=e.clientY;
      st.lastX=e.clientX; st.lastY=e.clientY;
    },{passive:false});

    wrap.addEventListener('pointermove',e=>{
      if(pointers.has(e.pointerId)) pointers.set(e.pointerId,{x:e.clientX,y:e.clientY,type:e.pointerType});
      const st=ensureViewState(wrap);
      if(pointers.size>=2){
        e.preventDefault();
        const p=midpoint(); if(!p) return;
        st.moved=true; st.pinching=true; st.drag=false;
        const rect=st.gestureRect||wrap.getBoundingClientRect();
        const factor=Math.max(.7,Math.min(1.45,p.d/Math.max(1,st.pinchDist||p.d)));
        if(mobileChartMotion.matches){
          const ms=ensureMobileViewBoxState(wrap);
          const anchor=mobileClientToWorld(wrap,ms,st.pinchX??p.x,st.pinchY??p.y,rect);
          const oldZoom=mobileCameraZoom(wrap,ms);
          const nextZoom=Math.max(.85,Math.min(65,oldZoom*factor));
          const size=mobileCameraSizeForZoom(wrap,ms,nextZoom),nw=size.w,nh=size.h;
          const nm=mobileViewBoxMetrics(wrap,ms,nw,nh);
          const newPx=p.x-rect.left, newPy=p.y-rect.top;
          const nx=anchor.x-(newPx-nm.offsetX)/nm.pxPerWorld;
          const ny=anchor.y-(newPy-nm.offsetY)/nm.pxPerWorld;
          setMobileViewBox(wrap,ms,nx,ny,nw,nh);
        }else{
          const oldScale=Math.max(.0001,st.scale);
          const nextScale=Math.max(.08,Math.min(4.5,oldScale*factor));
          const oldPx=(st.pinchX??p.x)-rect.left, oldPy=(st.pinchY??p.y)-rect.top;
          const newPx=p.x-rect.left, newPy=p.y-rect.top;
          const wx=(oldPx-st.x)/oldScale, wy=(oldPy-st.y)/oldScale;
          st.scale=nextScale; st.x=newPx-wx*nextScale; st.y=newPy-wy*nextScale;
        }
        st.pinchX=p.x; st.pinchY=p.y; st.pinchDist=Math.max(1,p.d);
        scheduleView(wrap);
        wrap.classList.add('dragging','gesture-active');
        return;
      }

      if(e.pointerType==='touch'){
        if(!st.drag || st.pinching || pointers.size!==1) return;
        e.preventDefault();
        const total=Math.hypot(e.clientX-st.startX,e.clientY-st.startY);
        if(!st.moved && total>5) st.moved=true;
        if(!st.moved) return;
        const dx=e.clientX-st.lastX, dy=e.clientY-st.lastY;
        if(mobileChartMotion.matches){
          const ms=ensureMobileViewBoxState(wrap), m=mobileViewBoxMetrics(wrap,ms);
          setMobileViewBox(wrap,ms,ms.vbX-dx/m.pxPerWorld,ms.vbY-dy/m.pxPerWorld,ms.vbW,ms.vbH);
        }else{ st.x+=dx; st.y+=dy; }
        st.lastX=e.clientX; st.lastY=e.clientY;
        scheduleView(wrap);
        wrap.classList.add('dragging','gesture-active');
        return;
      }

      if(!st.drag || st.pinching) return;
      const total=Math.hypot(e.clientX-st.startX,e.clientY-st.startY);
      if(!st.moved && total>7){
        st.moved=true;
        try{wrap.setPointerCapture?.(e.pointerId)}catch(_){}
      }
      if(!st.moved) return;
      const dx=e.clientX-st.lastX, dy=e.clientY-st.lastY;
      st.x+=dx; st.y+=dy; st.lastX=e.clientX; st.lastY=e.clientY;
      wrap.classList.add('dragging'); applyView(wrap);
    },{passive:false});

    const endPointer=e=>{
      const st=ensureViewState(wrap);
      const wasPinching=st.pinching || pointers.size>=2;
      pointers.delete(e.pointerId);
      try{wrap.releasePointerCapture?.(e.pointerId)}catch(_){}
      if(wasPinching){
        st.moved=true; st.pinching=false; st.drag=false;
      }else if(pointers.size===0){
        st.drag=false;
      }
      if(pointers.size===0){
        flushView(wrap);
        st.gestureRect=null;
        wrap.classList.remove('dragging','gesture-active');
        if(isMobileCanvasWrap(wrap)) drawMobileCanvas(wrap);
      }
    };
    wrap.addEventListener('pointerup',endPointer);
    wrap.addEventListener('pointercancel',endPointer);

    // Node selection is delegated once at document level below.
    // Pan/zoom stays here; no Graphviz node owns a click listener.
    requestAnimationFrame(()=>{if(wrap.offsetParent!==null) fitView(wrap)});
  });
}

function clearSvg(){
  document.querySelectorAll('.panel.active .svg-wrap svg').forEach(s=>{
    s.classList.remove('dim');
    s.querySelectorAll('.dynamic-edge-overlay').forEach(x=>x.remove());
    s.querySelectorAll('.hl,.focus,.backhl,.forwardhl,.bothhl,.contexthl,.pathhl,.goal-node,.current-goal').forEach(x=>x.classList.remove('hl','focus','backhl','forwardhl','bothhl','contexthl','pathhl','goal-node','current-goal'));
  });
  applyCharacterHighlight();
}
function gt(g){let t=g.querySelector(':scope > title');return t?t.textContent.trim():''}
function activePanel(){return document.querySelector('.panel.active')}
function activeWrap(){return activePanel()?.querySelector('.svg-wrap')}
function activeSvg(){return activeWrap()?.querySelector('svg')}
function activeSvgHasNode(id){
  const svg=activeSvg(); if(!svg||!id) return false;
  return [...svg.querySelectorAll('g.node')].some(g=>gt(g)===id);
}
function edgeRank(e){return e.strength==='very strong'?4:e.strength==='strong'?3:e.strength==='medium'?2:1}
function applyCharacterHighlight(){
  document.querySelectorAll('.svg-wrap svg').forEach(svg=>{
    svg.classList.remove('char-mode');
    svg.querySelectorAll('.charhl').forEach(x=>x.classList.remove('charhl'));
    if(!cf.value) return;
    const ids=charWorks[cf.value]||new Set();
    let hits=0;
    svg.querySelectorAll('g.node').forEach(g=>{
      const id=gt(g);
      if(ids.has(id)){g.classList.add('charhl');hits++}
    });
    if(hits && !selected) svg.classList.add('char-mode');
  });
}

function hilite(id){clearSvg();let ctx=neighborhood(id,hop);document.querySelectorAll('.panel.active .svg-wrap svg').forEach(svg=>{let ns=[...svg.querySelectorAll('g.node')],es=[...svg.querySelectorAll('g.edge')],ids=new Set(ns.map(gt));if(!ids.has(id))return;svg.classList.add('dim');ns.forEach(g=>{let x=gt(g);if(x===id)g.classList.add('focus');else if(ctx.has(x))g.classList.add('hl')});es.forEach(g=>{let p=gt(g).split('->');if(p.length===2&&ctx.has(p[0])&&ctx.has(p[1]))g.classList.add('hl')})})}
function ancestors(id){let seen=new Set(),st=[id];while(st.length){let x=st.pop();for(const e of(inc[x]||[])){if((e.strength==='strong'||e.strength==='very strong')&&!seen.has(e.source)){seen.add(e.source);st.push(e.source)}}}return [...seen]}
function select(id){selected=id;render();let n=nm[id],ins=inc[id]||[],outs=out[id]||[],anc=ancestors(id);
let direct=ins.filter(e=>e.strength==='strong'||e.strength==='very strong').map(e=>e.source);
let jpinfo=n.japan_date?`<p><b>日本公開・配信情報：</b><br>${esc(n.japan_date)}　${esc(n.japan_type)}</p>`:'<p class="muted">日本公開・配信日の公式確認データは未登録です。</p>';
let source=n.source_url?`<p><a href="${esc(n.source_url)}" target="_blank" rel="noopener" style="color:#60a5fa">日本向け公式ソースを開く ↗</a><br><span class="muted">${esc(n.source_note)}</span></p>`:'';
detail.innerHTML=`<strong>${esc(n.title)}</strong><div class="muted">現在の図では関連作品だけ点灯中</div><div class="muted">${esc(n.title_en)} / ${esc(n.release)}</div><p><span class="badge">${esc(n.branch)}</span><span class="badge">${esc(n.ja_status)}</span></p>${n.ja_status==='unannounced'?'<p class="warn">日本公式の邦題未発表として扱っています。</p>':''}${jpinfo}${source}<p><b>直接の強い前提候補：</b><br>${direct.length?direct.map(x=>`<span class="badge pre" data-id="${x}" style="cursor:pointer">${esc(nm[x]?.title||x)}</span>`).join(' '):'<span class="muted">なし</span>'}</p><p><b>強い接続を遡った前提候補：</b><br>${anc.length?anc.slice(0,20).map(x=>`<span class="badge pre" data-id="${x}" style="cursor:pointer">${esc(nm[x]?.title||x)}</span>`).join(' '):'<span class="muted">なし</span>'}</p><p><b>接続数：</b>入力 ${ins.length} / 出力 ${outs.length}</p>`;
detail.querySelectorAll('.pre').forEach(x=>x.onclick=()=>select(x.dataset.id));

let prevCand=(ins.filter(e=>edgeRank(e)>=3).sort((a,b)=>edgeRank(b)-edgeRank(a)));
if(!prevCand.length) prevCand=ins.slice().sort((a,b)=>edgeRank(b)-edgeRank(a));
let nextCand=(outs.filter(e=>edgeRank(e)>=3).sort((a,b)=>edgeRank(b)-edgeRank(a)));
if(!nextCand.length) nextCand=outs.slice().sort((a,b)=>edgeRank(b)-edgeRank(a));
prevCand=prevCand.slice(0,8);
nextCand=nextCand.slice(0,8);
flow.innerHTML=`<div><b>← 前に見る候補</b><br>${prevCand.length?prevCand.map(e=>`<span class="badge flowlink" data-id="${e.source}" style="cursor:pointer">${esc(nm[e.source]?.title||e.source)}</span>`).join(' '):'<span class="muted">なし</span>'}</div>
<hr style="border:none;border-top:1px solid #334155;margin:10px 0">
<div><b>→ 次に見る候補</b><br>${nextCand.length?nextCand.map(e=>`<span class="badge flowlink" data-id="${e.target}" style="cursor:pointer">${esc(nm[e.target]?.title||e.target)}</span>`).join(' '):'<span class="muted">なし</span>'}</div>
<p class="muted">※ まず strong / very strong 接続を優先表示し、なければ他の直接接続も候補として表示。</p>`;
flow.querySelectorAll('.flowlink').forEach(x=>x.onclick=()=>select(x.dataset.id));

let rr=[...ins,...outs];
et.innerHTML=rr.map(e=>`<tr><td>${esc(nm[e.source]?.title||e.source)}</td><td>${esc(nm[e.target]?.title||e.target)}</td><td>${esc(displayEdgeType(e))}</td><td>${esc(e.strength)}</td></tr>`).join('')||'<tr><td colspan="4" class="muted">接続なし</td></tr>';
hilite(id);setTimeout(()=>centerNodeInView(id),20)}
[q,bf,sf].forEach(x=>{x.addEventListener('input',render);x.addEventListener('change',render)});
cf.addEventListener('change',()=>{
  if(cf.value && selected && !(charWorks[cf.value]||new Set()).has(selected)){
    selected=null; clearSvg();
    detail.textContent='キャラクターを選択中です。図上で関連作品が点灯します。';
    flow.textContent='作品をクリックすると、「前に見る候補」「次に見る候補」を表示します。';
    et.innerHTML='';
  }
  render(); applyCharacterHighlight();
});document.querySelectorAll('.hop').forEach(b=>b.onclick=()=>{document.querySelectorAll('.hop').forEach(x=>x.classList.remove('active'));b.classList.add('active');hop=Number(b.dataset.hop);if(selected)select(selected)});
document.getElementById('clear').onclick=()=>{selected=null;q.value='';bf.value='';cf.value='';sf.value='';clearSvg();render();detail.textContent='作品を選ぶと前後の接続を表示します。';flow.textContent='作品を選ぶと、「前に見る候補」「次に見る候補」を表示します。';et.innerHTML=''};
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.target).classList.add('active');setTimeout(()=>{if(selected&&activeSvgHasNode(selected)){hilite(selected);centerNodeInView(selected)}else{fitView(activeWrap());clearSvg();applyCharacterHighlight()}},30)});
document.getElementById('zoomIn').onclick=()=>zoomAt(activeWrap(),1.22);
document.getElementById('zoomOut').onclick=()=>zoomAt(activeWrap(),0.82);
document.getElementById('zoomReset').onclick=()=>fitView(activeWrap());
document.getElementById('zoomSelected').onclick=()=>{if(selected)centerNodeInView(selected);else fitView(activeWrap())};
initSvgInteraction();
window.addEventListener('resize',()=>{if(!selected)fitView(activeWrap())});
render();
