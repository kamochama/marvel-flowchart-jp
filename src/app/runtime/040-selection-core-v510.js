// v5.10.0 core selection module: one state computation and one renderer, while preserving stable pan/zoom.
(()=>{
  let combineMode='or';
  let pathPreference='main';
  let prepTier='recommended';
  let importanceMode='reference';
  const IMPORTANCE_RANK={core:3,recommended:2,reference:1};
  const IMPORTANCE_MIN={core:3,recommended:2,reference:1};
  let prepTargetId=null;
  let prepTargetLocked=false;
  const selectBeforeV57=select;
  select = function(id,multi=false){
    const removing=selectedIds.has(id);
    if(!removing && !prepTargetLocked) prepTargetId=id;
    selectBeforeV57(id,multi);
    if(removing && prepTargetId===id && !prepTargetLocked){
      prepTargetId=selected;
      updatePreparationPlan();
    }
  };

  function edgeKey(e){ return `${e.source}->${e.target}`; }
  function edgeKeyFromSvgGroup(g){
    if(!g) return '';
    if(g.dataset?.edgeKey) return g.dataset.edgeKey;
    const raw=(g.querySelector(':scope > title')?.textContent||'').replace(/\s+/g,'').trim();
    if(raw.includes('->')){
      const [a,b]=raw.split('->');
      if(a&&b && EDGES.some(e=>e.source===a&&e.target===b)){
        g.dataset.edgeKey=`${a}->${b}`;
        return g.dataset.edgeKey;
      }
    }
    return '';
  }
  window.marvelEdgeKeyFromGroup=edgeKeyFromSvgGroup;
  document.querySelectorAll('.svg-wrap svg g.edge:not(.dynamic-edge-overlay)').forEach(edgeKeyFromSvgGroup);

  const EDGE_TYPE_JA={
    'character continuity':'キャラクター継続',
    'direct anthology continuation':'アンソロジーの直接継続',
    'direct lead-in':'直接の導入',
    'Spider-Man film continuation':'スパイダーマン映画の継続',
    'direct sequel/character continuation':'直接続編／キャラクター継続',
    'direct character spin-off':'キャラクターの直接スピンオフ',
    'Yelena/Natasha legacy':'エレーナ／ナターシャの継承',
    'character/plot callback':'キャラクター／物語の再接続',
    'character continuation short':'短編でのキャラクター継続',
    'direct short-series continuation':'短編シリーズの直接継続',
    'legacy character continuity':'旧シリーズからのキャラクター継続'
  };
  function displayEdgeType(e){ const t=(e&&(e.type||e.type_en))||'接続'; return EDGE_TYPE_JA[t]||t; }
  window.displayEdgeType=displayEdgeType;

  function importanceOf(e){ return e.importance||'recommended'; }
  function importanceAllowed(e){ return (IMPORTANCE_RANK[importanceOf(e)]||1) >= (IMPORTANCE_MIN[importanceMode]||2); }
  function limitedPart(id,hops){
    const nodes=new Set([id]), usedEdges=new Set();
    const q=[[id,0]];
    while(q.length){
      const [x,d]=q.shift();
      if(d>=hops) continue;
      const incident=[...(inc[x]||[]),...(out[x]||[])];
      for(const e of incident){
        if(!importanceAllowed(e)) continue;
        const y=e.source===x?e.target:e.source;
        usedEdges.add(edgeKey(e));
        if(!nodes.has(y)){ nodes.add(y); q.push([y,d+1]); }
      }
    }
    return {nodes,backNodes:new Set(),forwardNodes:new Set(),contextNodes:new Set(nodes),backEdges:new Set(),forwardEdges:new Set(),contextEdges:usedEdges,generic:true};
  }

  function tagEdgeImportance(){
    const byKey=new Map(EDGES.map(e=>[edgeKey(e),importanceOf(e)]));
    document.querySelectorAll('.svg-wrap svg g.edge:not(.dynamic-edge-overlay)').forEach(g=>{
      const k=edgeKeyFromSvgGroup(g);
      g.classList.remove('imp-core','imp-recommended','imp-reference','importance-hidden');
      const imp=byKey.get(k);
      if(!imp) return;
      g.classList.add(`imp-${imp}`);
      const fake={importance:imp};
      if(!importanceAllowed(fake)) g.classList.add('importance-hidden');
    });
  }

  // v5.7.7: compute two independent directed closures from the selected work.
  // Backward traversal only follows incoming arrows; forward traversal only
  // follows outgoing arrows.  A walk never changes direction midway.
  function directedPartAll(id){
    const backNodes=new Set([id]), forwardNodes=new Set([id]), contextNodes=new Set();
    const backEdges=new Set(), forwardEdges=new Set(), contextEdges=new Set();
    const propagates=e=>edgeRank(e)>=3; // traversal is independent from viewing importance

    let stack=[id];
    while(stack.length){
      const x=stack.pop();
      for(const e of (inc[x]||[])){
        if(!propagates(e)) continue;
        backEdges.add(edgeKey(e));
        if(!backNodes.has(e.source)){ backNodes.add(e.source); stack.push(e.source); }
      }
    }
    stack=[id];
    while(stack.length){
      const x=stack.pop();
      for(const e of (out[x]||[])){
        if(!propagates(e)) continue;
        forwardEdges.add(edgeKey(e));
        if(!forwardNodes.has(e.target)){ forwardNodes.add(e.target); stack.push(e.target); }
      }
    }

    // Medium/weak/reference links are one-hop context only. Importance changes
    // what context is shown, never where recursive history stops.
    for(const e of (inc[id]||[])) if(importanceAllowed(e) && !propagates(e)){ contextNodes.add(e.source); contextEdges.add(edgeKey(e)); }
    for(const e of (out[id]||[])) if(importanceAllowed(e) && !propagates(e)){ contextNodes.add(e.target); contextEdges.add(edgeKey(e)); }
    const nodes=new Set([...backNodes,...forwardNodes,...contextNodes]);
    return {nodes,backNodes,forwardNodes,contextNodes,backEdges,forwardEdges,contextEdges,generic:false};
  }
  function directedPart(id){
    return scopeMode==='all' ? directedPartAll(id) : limitedPart(id, scopeMode==='two'?2:1);
  }

  function pathEdgeCost(e,profile=pathPreference){
    const imp=importanceOf(e);
    if(profile==='shortest') return imp==='core'?100:(imp==='recommended'?101:103);
    return imp==='core'?1:(imp==='recommended'?3:7);
  }
  function shortestDirectedPath(source,target,profile=pathPreference){
    if(source===target) return {nodes:[source],edges:[],cost:0};
    const dist=new Map([[source,0]]), prev=new Map(), prevEdge=new Map(), done=new Set();
    while(true){
      let x=null,best=Infinity;
      for(const [id,d] of dist){ if(!done.has(id)&&d<best){best=d;x=id;} }
      if(x===null) break;
      if(x===target) break;
      done.add(x);
      for(const e of (out[x]||[])){
        if(!importanceAllowed(e)) continue;
        const nd=best+pathEdgeCost(e,profile);
        if(nd<(dist.get(e.target)??Infinity)){dist.set(e.target,nd);prev.set(e.target,x);prevEdge.set(e.target,e);}
      }
    }
    if(!dist.has(target)) return null;
    const nodes=[target], edges=[]; let cur=target;
    while(cur!==source){ const e=prevEdge.get(cur), p=prev.get(cur); if(!e||!p) return null; edges.push(edgeKey(e)); nodes.push(p); cur=p; }
    nodes.reverse(); edges.reverse();
    return {nodes,edges,cost:dist.get(target)};
  }
  function bestDirectedPairPath(a,b,profile=pathPreference){
    const ab=shortestDirectedPath(a,b,profile), ba=shortestDirectedPath(b,a,profile);
    if(!ab) return ba; if(!ba) return ab;
    if(ab.cost!==ba.cost) return ab.cost<ba.cost?ab:ba;
    return ab.edges.length<=ba.edges.length?ab:ba;
  }
  function pathSelectionState(){
    const ids=[...selectedIds];
    if(ids.length<2) return directedPart(ids[0]);
    const nodes=new Set(ids), pathEdges=new Set(), disconnected=[];
    for(let i=0;i<ids.length;i++) for(let j=i+1;j<ids.length;j++){
      const p=bestDirectedPairPath(ids[i],ids[j],pathPreference);
      if(!p){disconnected.push([ids[i],ids[j]]);continue;}
      for(const x of p.nodes) nodes.add(x);
      for(const k of p.edges) pathEdges.add(k);
    }
    return {ctx:nodes,nodes,back:new Set(),forward:new Set(),context:new Set(),backNodes:new Set(),forwardNodes:new Set(),contextNodes:new Set(),backEdges:new Set(),forwardEdges:new Set(),contextEdges:new Set(),pathEdges,pathMode:true,generic:false,disconnected};
  }

  function selectedParts(){
    return [...selectedIds].map(id=>directedPart(id));
  }

  function computeSelectionState(){
    if(!selectedIds.size) return {ctx:new Set(),back:new Set(),forward:new Set(),context:new Set(),backEdges:new Set(),forwardEdges:new Set(),contextEdges:new Set(),pathEdges:new Set(),generic:scopeMode!=='all'};
    if(combineMode==='path' && selectedIds.size>1) return pathSelectionState();
    const parts=selectedParts();
    let ctx;
    if(combineMode==='and' && parts.length>1){
      ctx=new Set(parts[0].nodes);
      for(const p of parts.slice(1)) for(const x of [...ctx]) if(!p.nodes.has(x)) ctx.delete(x);
    }else{
      ctx=new Set();
      for(const p of parts) for(const x of p.nodes) ctx.add(x);
    }
    for(const id of selectedIds) ctx.add(id);

    const back=new Set(), forward=new Set(), context=new Set();
    const backEdges=new Set(), forwardEdges=new Set(), contextEdges=new Set();
    const stateEdgeByKey=new Map(EDGES.map(e=>[edgeKey(e),e]));
    const edgeSurvivesCtx=k=>{
      const e=stateEdgeByKey.get(k);
      return !!e && ctx.has(e.source) && ctx.has(e.target);
    };
    for(const p of parts){
      for(const x of p.backNodes) if(ctx.has(x)) back.add(x);
      for(const x of p.forwardNodes) if(ctx.has(x)) forward.add(x);
      for(const x of p.contextNodes) if(ctx.has(x)) context.add(x);
      for(const k of p.backEdges) if(edgeSurvivesCtx(k)) backEdges.add(k);
      for(const k of p.forwardEdges) if(edgeSurvivesCtx(k)) forwardEdges.add(k);
      for(const k of p.contextEdges) if(edgeSurvivesCtx(k)) contextEdges.add(k);
    }
    return {ctx,back,forward,context,backEdges,forwardEdges,contextEdges,pathEdges:new Set(),generic:scopeMode!=='all'};
  }
  window.computeSelectionState=computeSelectionState;
  let selectionStateCache=null;
  function currentSelectionState(){ return selectionStateCache || computeSelectionState(); }

  selectionNeighborhood = function(){ return currentSelectionState().ctx; };

  selectionSummaryHtml = function(){
    const ids=orderedSelectedIds();
    if(!ids.length) return '';
    const pathState=(combineMode==='path'&&ids.length>1)?computeSelectionState():null;
    const combLabel=combineMode==='and'?'AND（全ゴールに共通）':combineMode==='path'?`PATH（${pathPreference==='shortest'?'最短':'本流優先'}）`:'OR（いずれかのゴール）';
    const disconnectedNote=pathState?.disconnected?.length?`　※有向経路なし：${pathState.disconnected.length}組`:'';
    const mode=ids.length>1 ? `<div class="selection-mode-note${combineMode==='path'?' path-note':''}">点灯条件：${combLabel} / ${scopeMode==='all'?'関連全体':scopeMode==='two'?'2段階':'1段階'} / 接続層：${importanceMode==='core'?'中核のみ':importanceMode==='recommended'?'中核＋推奨':'中核＋推奨＋参照'}${combineMode==='and'&&scopeMode==='all'?'　※有向の共通範囲を表示します。':''}${disconnectedNote}</div>` : '';
    if(ids.length===1) return mode;
    const target=selected;
    return `<p><b>複数ゴール中 (${ids.length})：</b><br>${ids.map(x=>`<span class="badge selbadge"${x===target?' style="outline:1px solid #f59e0b"':''}><span class="seljump" data-id="${x}" title="このゴールを基準に表示">${x===target?'🎯 ':''}${esc(nm[x]?.title||x)}</span><button class="selremove" data-id="${x}" title="このゴールだけ解除" aria-label="${esc(nm[x]?.title||x)}をゴールから解除">×</button></span>`).join(' ')}</p>${mode}`;
  };


  // v5.7.10: the embedded Graphviz SVGs predate part of the current edge table.
  // When a traversed edge is absent from the active SVG, draw it dynamically.
  // If a path runs through nodes that live on another tab, compress only that
  // hidden run into one dashed bridge; the tooltip lists the omitted works.
  function svgNodeMap(svg){
    return new Map([...svg.querySelectorAll('g.node')].map(g=>[gt(g),g]));
  }
  function svgStaticEdgeKeys(svg){
    return new Set([...svg.querySelectorAll('g.edge:not(.dynamic-edge-overlay)')].map(edgeKeyFromSvgGroup).filter(Boolean));
  }
  function ensureDynamicMarkers(svg){
    const NS='http://www.w3.org/2000/svg';
    let defs=svg.querySelector('defs');
    if(!defs){ defs=document.createElementNS(NS,'defs'); svg.insertBefore(defs,svg.firstChild); }
    const panel=(svg.closest('.panel')?.id||'svg').replace(/[^a-zA-Z0-9_-]/g,'_');
    const specs={backhl:'#60a5fa',forwardhl:'#34d399',contexthl:'#f59e0b',bothhl:'#a78bfa',pathhl:'#c4b5fd'};
    const ids={};
    for(const [cls,color] of Object.entries(specs)){
      const id=`dynArrow_${panel}_${cls}`; ids[cls]=id;
      if(svg.querySelector(`#${id}`)) continue;
      const marker=document.createElementNS(NS,'marker');
      marker.setAttribute('id',id); marker.setAttribute('viewBox','0 0 10 10');
      marker.setAttribute('refX','9'); marker.setAttribute('refY','5');
      marker.setAttribute('markerWidth','7'); marker.setAttribute('markerHeight','7');
      marker.setAttribute('orient','auto-start-reverse');
      const p=document.createElementNS(NS,'path');
      p.setAttribute('d','M 0 0 L 10 5 L 0 10 z'); p.setAttribute('fill',color);
      marker.appendChild(p); defs.appendChild(marker);
    }
    return ids;
  }
  function edgeBoundaryPoints(a,b){
    const A=a.getBBox(), B=b.getBBox();
    const ac={x:A.x+A.width/2,y:A.y+A.height/2}, bc={x:B.x+B.width/2,y:B.y+B.height/2};
    const dx=bc.x-ac.x, dy=bc.y-ac.y;
    const boundary=(box,cx,cy,vx,vy,sign)=>{
      const ax=Math.abs(vx)||1e-6, ay=Math.abs(vy)||1e-6;
      const tx=(box.width/2)/ax, ty=(box.height/2)/ay;
      const t=Math.min(tx,ty);
      return {x:cx+sign*vx*t,y:cy+sign*vy*t};
    };
    return {start:boundary(A,ac.x,ac.y,dx,dy,1),end:boundary(B,bc.x,bc.y,dx,dy,-1)};
  }
  function drawDynamicEdge(svg,nodeMap,source,target,cls,compressed=false,hidden=[]){
    const a=nodeMap.get(source), b=nodeMap.get(target); if(!a||!b||source===target) return;
    const NS='http://www.w3.org/2000/svg', marks=ensureDynamicMarkers(svg);
    const pts=edgeBoundaryPoints(a,b), dx=pts.end.x-pts.start.x, dy=pts.end.y-pts.start.y;
    // Gentle bend keeps a synthetic bridge distinguishable from a native Graphviz edge.
    const bend=Math.max(-34,Math.min(34,dx*.06));
    const c1x=pts.start.x+dx*.34, c1y=pts.start.y+dy*.34-bend;
    const c2x=pts.start.x+dx*.68, c2y=pts.start.y+dy*.68-bend;
    const g=document.createElementNS(NS,'g');
    g.classList.add('edge','hl','dynamic-edge-overlay',cls); if(compressed) g.classList.add('compressed');
    g.dataset.edgeKey=`${source}->${target}`;
    const title=document.createElementNS(NS,'title');
    const hiddenNames=hidden.map(x=>nm[x]?.title||x);
    title.textContent=compressed ? `${nm[source]?.title||source} → ${nm[target]?.title||target}（${hiddenNames.join(' → ')} 経由）` : `${nm[source]?.title||source} → ${nm[target]?.title||target}`;
    g.appendChild(title);
    const path=document.createElementNS(NS,'path');
    path.setAttribute('d',`M ${pts.start.x} ${pts.start.y} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${pts.end.x} ${pts.end.y}`);
    path.setAttribute('marker-end',`url(#${marks[cls]||marks.contexthl})`);
    g.appendChild(path);
    const parent=a.parentNode;
    const firstNode=[...parent.children].find(x=>x.classList?.contains('node'));
    if(firstNode) parent.insertBefore(g,firstNode); else parent.appendChild(g);
  }

  function drawMasterOverlayEdge(svg,nodeMap,edge){
    const a=nodeMap.get(edge.source), b=nodeMap.get(edge.target); if(!a||!b||edge.source===edge.target) return;
    const NS='http://www.w3.org/2000/svg', pts=edgeBoundaryPoints(a,b), dx=pts.end.x-pts.start.x, dy=pts.end.y-pts.start.y;
    const bend=Math.max(-28,Math.min(28,dx*.05));
    const c1x=pts.start.x+dx*.34, c1y=pts.start.y+dy*.34-bend;
    const c2x=pts.start.x+dx*.68, c2y=pts.start.y+dy*.68-bend;
    const g=document.createElementNS(NS,'g'); g.classList.add('edge','master-edge-overlay');
    g.dataset.edgeKey=`${edge.source}->${edge.target}`;
    const title=document.createElementNS(NS,'title'); title.textContent=`${nm[edge.source]?.title||edge.source} → ${nm[edge.target]?.title||edge.target}：${edge.reason||''}`; g.appendChild(title);
    const path=document.createElementNS(NS,'path'); path.setAttribute('d',`M ${pts.start.x} ${pts.start.y} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${pts.end.x} ${pts.end.y}`); g.appendChild(path);
    const len=Math.hypot(dx,dy)||1, ux=dx/len, uy=dy/len, px=-uy, py=ux, back=7.5, half=3.8;
    const bx=pts.end.x-ux*back, by=pts.end.y-uy*back;
    const poly=document.createElementNS(NS,'polygon'); poly.setAttribute('points',`${pts.end.x},${pts.end.y} ${bx+px*half},${by+py*half} ${bx-px*half},${by-py*half}`); g.appendChild(poly);
    const parent=a.parentNode, firstNode=[...parent.children].find(x=>x.classList?.contains('node'));
    if(firstNode) parent.insertBefore(g,firstNode); else parent.appendChild(g);
  }
  function materializeMissingMasterEdges(){
    document.querySelectorAll('.panel .svg-wrap svg').forEach(svg=>{
      if(svg.closest('.panel')?.dataset.selectionScope==='independent') return;
      const nodeMap=svgNodeMap(svg), visible=new Set(nodeMap.keys()), present=svgStaticEdgeKeys(svg);
      for(const edge of EDGES){
        const k=`${edge.source}->${edge.target}`;
        if(visible.has(edge.source)&&visible.has(edge.target)&&!present.has(k)){ drawMasterOverlayEdge(svg,nodeMap,edge); present.add(k); }
      }
    });
  }

  function compressedBridges(edgeSet,visible){
    const adj=new Map();
    for(const k of edgeSet){
      const [a,b]=k.split('->'); if(!a||!b) continue;
      if(!adj.has(a)) adj.set(a,[]); adj.get(a).push(b);
    }
    const ans=[], seenBridge=new Set();
    for(const start of visible){
      for(const first of (adj.get(start)||[])){
        if(visible.has(first)) continue;
        const q=[[first,[first]]], seen=new Set([first]);
        while(q.length){
          const [x,hidden]=q.shift();
          for(const y of (adj.get(x)||[])){
            if(visible.has(y)){
              const key=`${start}->${y}`;
              if(start!==y && !seenBridge.has(key)){ seenBridge.add(key); ans.push({source:start,target:y,hidden}); }
              continue;
            }
            if(!seen.has(y)){ seen.add(y); q.push([y,[...hidden,y]]); }
          }
        }
      }
    }
    return ans;
  }
  materializeMissingMasterEdges();

  function addMissingDirectedEdges(svg,state){
    if(state.generic) return;
    const nodeMap=svgNodeMap(svg), visible=new Set(nodeMap.keys()), staticKeys=svgStaticEdgeKeys(svg);
    const specs=[['backhl',state.backEdges],['forwardhl',state.forwardEdges],['contexthl',state.contextEdges],['pathhl',state.pathEdges||new Set()]];
    for(const [cls,set] of specs){
      for(const k of set){
        const [a,b]=k.split('->');
        if(visible.has(a)&&visible.has(b)&&!staticKeys.has(k.replace(/\\s+/g,''))) drawDynamicEdge(svg,nodeMap,a,b,cls,false,[]);
      }
      if(cls!=='contexthl'){
        for(const br of compressedBridges(set,visible)){
          const k=`${br.source}->${br.target}`;
          if(!staticKeys.has(k.replace(/\\s+/g,''))) drawDynamicEdge(svg,nodeMap,br.source,br.target,cls,true,br.hidden);
        }
      }
    }
  }

  // Unlike the old behavior, allow context to remain lit on a tab even if the
  // selected work itself is absent, as long as matching context nodes exist.
  function renderSelectionState(svg,state){
    svg.querySelectorAll('.dynamic-edge-overlay').forEach(x=>x.remove());
    svg.querySelectorAll('.hl,.focus,.backhl,.forwardhl,.bothhl,.contexthl,.pathhl,.goal-node,.current-goal').forEach(x=>x.classList.remove('hl','focus','backhl','forwardhl','bothhl','contexthl','pathhl','goal-node','current-goal'));
    // Reference/curated charts (e.g. tab ⑥) are intentionally independent of
    // work selection made in the main graph. They must stay fully readable.
    if(svg.closest('.panel')?.dataset.selectionScope==='independent'){
      svg.classList.remove('dim','family-mode','char-mode');
      return;
    }
    if(!selectedIds.size){ svg.classList.remove('dim'); return; }
    svg.classList.remove('family-mode','char-mode');
    svg.classList.add('dim');
    const ctx=state.ctx;
    for(const g of svg.querySelectorAll('g.node')){
      const id=gt(g);
      if(selectedIds.has(id)){ g.classList.add('focus',id===selected?'current-goal':'goal-node'); continue; }
      if(!ctx.has(id)) continue;
      g.classList.add('hl');
      if(state.pathMode){ g.classList.add('pathhl'); continue; }
      if(state.generic) continue;
      const b=state.back.has(id), f=state.forward.has(id), c=state.context.has(id);
      if(b&&f) g.classList.add('bothhl');
      else if(b) g.classList.add('backhl');
      else if(f) g.classList.add('forwardhl');
      else if(c) g.classList.add('contexthl');
    }
    for(const g of svg.querySelectorAll('g.edge:not(.dynamic-edge-overlay)')){
      const k=edgeKeyFromSvgGroup(g); if(!k) continue;
      if(state.pathMode){ if(state.pathEdges.has(k)) g.classList.add('hl','pathhl'); continue; }
      if(state.generic){ if(state.contextEdges.has(k)) g.classList.add('hl','contexthl'); continue; }
      if(state.backEdges.has(k)) g.classList.add('hl','backhl');
      if(state.forwardEdges.has(k)) g.classList.add('hl','forwardhl');
      if(state.contextEdges.has(k)) g.classList.add('hl','contexthl');
    }
    addMissingDirectedEdges(svg,state);
  }
  window.renderSelectionState=renderSelectionState;
  window.marvelDirectedPartAll=directedPartAll;
  window.marvelImportanceAllowed=importanceAllowed;
  window.marvelEdgeKey=edgeKey;
  window.marvelAddMissingDirectedEdges=addMissingDirectedEdges;
  hilite = function(){
    clearSvg();
    if(!selectedIds.size) return;
    const state=currentSelectionState();
    document.querySelectorAll('.panel.active .svg-wrap svg').forEach(svg=>renderSelectionState(svg,state));
  };

  function ancestorSetAtRank(target,minRank){
    const seen=new Set(), stack=[target];
    while(stack.length){
      const x=stack.pop();
      for(const e of (inc[x]||[])){
        if(edgeRank(e)>=minRank && !seen.has(e.source)){
          seen.add(e.source); stack.push(e.source);
        }
      }
    }
    seen.delete(target);
    return seen;
  }

  function topologicalOrderAtRank(ids,minRank){
    const set=new Set(ids);
    const indeg=new Map([...set].map(x=>[x,0]));
    const fwd=new Map([...set].map(x=>[x,[]]));
    for(const e of EDGES){
      if(set.has(e.source)&&set.has(e.target)&&edgeRank(e)>=minRank){
        fwd.get(e.source).push(e.target);
        indeg.set(e.target,(indeg.get(e.target)||0)+1);
      }
    }
    let ready=sortByRelease([...set].filter(x=>(indeg.get(x)||0)===0));
    const ordered=[];
    while(ready.length){
      const x=ready.shift(); ordered.push(x);
      for(const y of (fwd.get(x)||[])){
        indeg.set(y,indeg.get(y)-1);
        if(indeg.get(y)===0){ ready.push(y); ready=sortByRelease(ready); }
      }
    }
    return ordered.length===set.size ? ordered : sortByRelease(set);
  }

  function ancestorSetByImportance(target, includeRecommended=false){
    const seen=new Set(), stack=[target];
    while(stack.length){
      const x=stack.pop();
      for(const e of (inc[x]||[])){
        const ok=importanceOf(e)==='core' || (includeRecommended && importanceOf(e)==='recommended');
        if(ok && !seen.has(e.source)){ seen.add(e.source); stack.push(e.source); }
      }
    }
    seen.delete(target); return seen;
  }
  function topologicalOrderByImportance(ids, includeRecommended=false){
    const set=new Set(ids), indeg=new Map([...set].map(x=>[x,0])), fwd=new Map([...set].map(x=>[x,[]]));
    for(const e of EDGES){
      const ok=importanceOf(e)==='core' || (includeRecommended && importanceOf(e)==='recommended');
      if(ok && set.has(e.source)&&set.has(e.target)){ fwd.get(e.source).push(e.target); indeg.set(e.target,(indeg.get(e.target)||0)+1); }
    }
    let ready=sortByRelease([...set].filter(x=>(indeg.get(x)||0)===0)), ordered=[];
    while(ready.length){ const x=ready.shift(); ordered.push(x); for(const y of fwd.get(x)||[]){ indeg.set(y,indeg.get(y)-1); if(indeg.get(y)===0){ready.push(y);ready=sortByRelease(ready);} } }
    return ordered.length===set.size?ordered:sortByRelease(set);
  }

  const buildRecommendedPlan=buildPreparationPlan;
  function buildTieredPlan(target){
    const rec=buildRecommendedPlan(target);
    const recIds=[...new Set(rec.ids)];

    if(prepTier==='minimum'){
      const directCore=(inc[target]||[]).filter(e=>importanceOf(e)==='core').map(e=>e.source);
      let ids=sortByRelease(new Set(directCore));
      if(!ids.length && recIds.length) ids=recIds.slice(-Math.min(3,recIds.length));
      return {ids,source:'接続重要度「中核」の直接前史',kind:'minimum',tierLabel:'最低限',tierNote:'視聴目標へ直接入る「中核」接続だけを優先します。中核が無い場合のみ推奨ルート直前を最大3作品提示します。'};
    }

    if(prepTier==='recommended'){
      const core=ancestorSetByImportance(target,false);
      for(const id of recIds) core.add(id);
      const ids=topologicalOrderByImportance(core,false);
      return {ids,source:`${rec.source} ＋ 接続重要度「中核」`,kind:rec.kind,tierLabel:'おすすめ',tierNote:'監査済み推奨ルートを優先しつつ、同系列・直接前提などの「中核」前史を補います。客演や参照だけの接続は自動では広げません。'};
    }

    const broad=ancestorSetByImportance(target,true);
    for(const id of recIds) broad.add(id);
    // Reference edges are direct context only, never recursive even in complete mode.
    for(const e of (inc[target]||[])) if(importanceOf(e)==='reference') broad.add(e.source);
    const ids=topologicalOrderByImportance(broad,true);
    return {ids,source:`${rec.source} ＋ 「中核／推奨」を再帰追跡 ＋ 直接参照`,kind:'complete',tierLabel:'完全版',tierNote:'「中核」と「推奨」を再帰的に遡り、視聴目標へ直接つながる「参照」も加えます。参照を踏み台に別系列へは拡散しません。'};
  }

  function buildMultiGoalPlan(goalIds,tier=prepTier){
    const goals=[...new Set((goalIds||[]).filter(id=>nm[id]))];
    const goalSet=new Set(goals), union=new Set(goals), sourceByGoal={};
    const rolesById={};
    const previousTier=prepTier;
    try{
      prepTier=tier;
      for(const goal of goals){
        const plan=buildTieredPlan(goal);
        sourceByGoal[goal]=[...plan.ids];
        for(const id of plan.ids){
          union.add(id);
          if(!rolesById[id]) rolesById[id]=[];
          if(!rolesById[id].includes('prep')) rolesById[id].push('prep');
        }
        if(!rolesById[goal]) rolesById[goal]=[];
        if(!rolesById[goal].includes('goal')) rolesById[goal].push('goal');
      }
    }finally{ prepTier=previousTier; }
    const indeg=new Map([...union].map(id=>[id,0]));
    const fwd=new Map([...union].map(id=>[id,[]]));
    for(const e of EDGES){
      if(importanceOf(e)==='reference') continue;
      if(!union.has(e.source)||!union.has(e.target)) continue;
      if(!fwd.get(e.source).includes(e.target)){
        fwd.get(e.source).push(e.target);
        indeg.set(e.target,(indeg.get(e.target)||0)+1);
      }
    }
    let ready=sortByRelease([...union].filter(id=>(indeg.get(id)||0)===0));
    const ordered=[];
    while(ready.length){
      const id=ready.shift(); ordered.push(id);
      for(const next of fwd.get(id)||[]){
        indeg.set(next,indeg.get(next)-1);
        if(indeg.get(next)===0){ ready.push(next); ready=sortByRelease(ready); }
      }
    }
    const orderedIds=ordered.length===union.size?ordered:sortByRelease(union);
    const prepIds=orderedIds.filter(id=>!goalSet.has(id));
    return {orderedIds,goalIds:goals,prepIds,rolesById,sourceByGoal,unknownOrderingPairs:[]};
  }
  window.marvelBuildMultiGoalPlan=buildMultiGoalPlan;
  window.marvelMultiGoalAudit=()=>({goals:orderedGoalIds(),tier:prepTier,plan:buildMultiGoalPlan(orderedGoalIds(),prepTier)});

  function prepImportanceLabel(imp){ return ({core:'中核',recommended:'推奨',reference:'参照'})[imp]||imp; }
  function prepAllowedEdge(e){
    const imp=importanceOf(e);
    if(prepTier==='minimum') return imp==='core';
    if(prepTier==='recommended') return imp==='core' || imp==='recommended';
    return imp==='core' || imp==='recommended' || imp==='reference';
  }
  function prepPath(source,target,allowedIds){
    if(source===target) return {nodes:[source],edges:[]};
    const allowed=new Set([...(allowedIds||[]),source,target]);
    const dist=new Map([[source,0]]), prev=new Map(), prevEdge=new Map(), done=new Set();
    while(true){
      let x=null,best=Infinity;
      for(const [id,d] of dist){ if(!done.has(id)&&d<best){best=d;x=id;} }
      if(x===null||x===target) break;
      done.add(x);
      for(const e of (out[x]||[])){
        if(!prepAllowedEdge(e) || !allowed.has(e.target)) continue;
        // In complete mode a reference edge is context only unless it lands directly on the viewing target.
        if(prepTier==='complete' && importanceOf(e)==='reference' && e.target!==target) continue;
        const w=importanceOf(e)==='core'?1:(importanceOf(e)==='recommended'?3:7), nd=best+w;
        if(nd<(dist.get(e.target)??Infinity)){dist.set(e.target,nd);prev.set(e.target,x);prevEdge.set(e.target,e);}
      }
    }
    if(!dist.has(target)) return null;
    const nodes=[target],edges=[]; let cur=target;
    while(cur!==source){ const e=prevEdge.get(cur),p=prev.get(cur); if(!e||!p) return null; edges.push(e);nodes.push(p);cur=p; }
    nodes.reverse();edges.reverse();return {nodes,edges};
  }
  function prepItemExplanation(id,target,plan){
    const direct=(out[id]||[]).filter(e=>e.target===target).sort((a,b)=>(IMPORTANCE_RANK[importanceOf(b)]||0)-(IMPORTANCE_RANK[importanceOf(a)]||0))[0];
    if(direct){
      const imp=importanceOf(direct), type=displayEdgeType(direct);
      return {imp, html:`<span class="prep-next">視聴目標へ直接</span> — ${esc(type)}`, title:direct.reason||''};
    }
    const path=prepPath(id,target,plan.ids);
    if(path && path.edges.length){
      const first=path.edges[0], imp=importanceOf(first), next=path.nodes[1], type=displayEdgeType(first);
      const hopNote=path.edges.length>1?`（あと${path.edges.length-1}段階）`:'';
      return {imp, html:`次は <span class="prep-next">${esc(nm[next]?.title||next)}</span> — ${esc(type)} ${hopNote}`, title:first.reason||''};
    }
    // Curated route entries can intentionally exist without an edge chain in the selected layer.
    return {imp:'recommended', html:'監査済み推奨ルート上の予習作品', title:''};
  }


  const WATCHED_STORAGE_KEY='marvelJapanWatchedIds.v1';
  const WATCHED_DIM_STORAGE_KEY='marvelJapanDimWatched.v1';
  function storageRead(key,fallback){
    try{const v=localStorage.getItem(key);return v===null?fallback:v}catch(_){return fallback}
  }
  function loadWatchedIds(){
    try{
      const raw=storageRead(WATCHED_STORAGE_KEY,'[]'), arr=JSON.parse(raw||'[]');
      return new Set(Array.isArray(arr)?arr.filter(id=>nm[id]):[]);
    }catch(_){return new Set()}
  }
  let watchedIds=loadWatchedIds();
  let dimWatchedOnChart=storageRead(WATCHED_DIM_STORAGE_KEY,'0')==='1';
  function saveWatchedState(){
    try{localStorage.setItem(WATCHED_STORAGE_KEY,JSON.stringify([...watchedIds]));localStorage.setItem(WATCHED_DIM_STORAGE_KEY,dimWatchedOnChart?'1':'0')}catch(_){}
  }
  function applyWatchedDimming(){
    document.querySelectorAll('.svg-wrap svg g.node').forEach(g=>{
      const id=gt(g); g.classList.toggle('watched-dim',!!(dimWatchedOnChart&&watchedIds.has(id)));
    });
  }
  function setWatched(id,on){
    if(!nm[id]) return;
    if(on) watchedIds.add(id); else watchedIds.delete(id);
    saveWatchedState(); applyWatchedDimming();
  }
  function prepWatchedCheckbox(id,label='視聴済み'){
    const checked=watchedIds.has(id)?' checked':'';
    return `<input class="prep-watched-check" type="checkbox" data-id="${esc(id)}"${checked} aria-label="${esc(nm[id]?.title||id)}を${label}にする" title="${label}として記録">`;
  }
  function prepProgressTools(ids){
    const items=[...ids], done=items.filter(id=>watchedIds.has(id)).length;
    return `<div class="prep-progress-tools"><div class="prep-progress-head"><span class="prep-progress-count">✓ プランの視聴済み ${done}/${items.length}</span><label class="prep-dim-toggle"><input id="prepDimWatched" type="checkbox"${dimWatchedOnChart?' checked':''}> 視聴済みを図で消灯</label></div>${items.length?`<div class="prep-progress-actions"><button type="button" id="prepMarkAllWatched">プランを全部チェック</button><button type="button" id="prepClearPlanWatched">このプランだけチェック解除</button></div>`:''}<div class="prep-progress-note">チェックはこのブラウザに保存され、別の作品の予習プランにも引き継がれます。</div></div>`;
  }
  function updatePreparationPlanPreservingView(anchorId=null){
    const pageX=window.scrollX,pageY=window.scrollY;
    const oldList=prepplan.querySelector('.prep-list');
    const oldListScroll=oldList?oldList.scrollTop:0;
    const oldAnchor=anchorId?[...prepplan.querySelectorAll('.prep-watched-check')].find(x=>x.dataset.id===anchorId):null;
    const oldAnchorTop=oldAnchor?oldAnchor.getBoundingClientRect().top:null;
    updatePreparationPlan();
    const restore=()=>{
      const newList=prepplan.querySelector('.prep-list');
      if(newList) newList.scrollTop=oldListScroll;
      if(anchorId && oldAnchorTop!==null){
        const next=[...prepplan.querySelectorAll('.prep-watched-check')].find(x=>x.dataset.id===anchorId);
        if(next){
          const delta=next.getBoundingClientRect().top-oldAnchorTop;
          if(Math.abs(delta)>.5) window.scrollBy(0,delta);
          return;
        }
      }
      if(Math.abs(window.scrollY-pageY)>.5 || Math.abs(window.scrollX-pageX)>.5) window.scrollTo(pageX,pageY);
    };
    restore();
    requestAnimationFrame(restore);
  }
  function wirePreparationProgress(ids,target){
    const planIds=[...ids];
    prepplan.querySelectorAll('.prep-watched-check').forEach(box=>box.onchange=()=>{
      const id=box.dataset.id;
      setWatched(id,box.checked);
      updatePreparationPlanPreservingView(id);
    });
    const dim=prepplan.querySelector('#prepDimWatched');
    if(dim) dim.onchange=()=>{dimWatchedOnChart=dim.checked;saveWatchedState();applyWatchedDimming();};
    const all=prepplan.querySelector('#prepMarkAllWatched');
    if(all) all.onclick=()=>{planIds.forEach(id=>watchedIds.add(id));saveWatchedState();applyWatchedDimming();updatePreparationPlanPreservingView();};
    const clear=prepplan.querySelector('#prepClearPlanWatched');
    if(clear) clear.onclick=()=>{planIds.forEach(id=>watchedIds.delete(id));saveWatchedState();applyWatchedDimming();updatePreparationPlanPreservingView();};
  }
  window.marvelWatchProgress={
    get watched(){return [...watchedIds]},
    isWatched:id=>watchedIds.has(id),
    set:(id,on=true)=>{setWatched(id,!!on);updatePreparationPlanPreservingView(id);},
    clear:()=>{watchedIds.clear();saveWatchedState();applyWatchedDimming();updatePreparationPlanPreservingView();},
    get dimOnChart(){return dimWatchedOnChart},
    setDim:on=>{dimWatchedOnChart=!!on;saveWatchedState();applyWatchedDimming();updatePreparationPlanPreservingView();}
  };

  const WATCH_TIME_MINUTES=Object.freeze({"iron-man-2008":126,"the-incredible-hulk-2008":112,"iron-man-2-2010":125,"thor-2011":114,"captain-america-the-first-avenger-2011":124,"the-avengers-2012":143,"iron-man-3-2013":130,"thor-the-dark-world-2013":112,"captain-america-the-winter-soldier-2014":136,"guardians-of-the-galaxy-2014":122,"avengers-age-of-ultron-2015":141,"ant-man-2015":117,"captain-america-civil-war-2016":147,"doctor-strange-2016":115,"guardians-of-the-galaxy-vol-2-2017":136,"spider-man-homecoming-2017":133,"thor-ragnarok-2017":130,"black-panther-2018":134,"avengers-infinity-war-2018":149,"ant-man-and-the-wasp-2018":118,"captain-marvel-2019":124,"avengers-endgame-2019":181,"spider-man-far-from-home-2019":129,"black-widow-2021":134,"shang-chi-and-the-legend-of-the-ten-rings-2021":132,"eternals-2021":156,"spider-man-no-way-home-2021":148,"doctor-strange-in-the-multiverse-of-madness-2022":126,"thor-love-and-thunder-2022":119,"black-panther-wakanda-forever-2022":161,"ant-man-and-the-wasp-quantumania-2023":124,"guardians-of-the-galaxy-vol-3-2023":150,"the-marvels-2023":105,"deadpool-wolverine-2024":128,"captain-america-brave-new-world-2025":118,"thunderbolts-new-avengers-2025":127,"the-fantastic-four-first-steps-2025":114,"spider-man-brand-new-day-2026-07-31":145,"wandavision-2021":363,"the-falcon-and-the-winter-soldier-2021":330,"loki-s1-2021":302,"what-if-s1-2021":322,"hawkeye-2021":297,"moon-knight-2022":303,"ms-marvel-2022":289,"she-hulk-attorney-at-law-2022":309,"werewolf-by-night-2022":54,"the-guardians-of-the-galaxy-holiday-special-2022":44,"secret-invasion-2023":272,"loki-s2-2023":313,"what-if-s2-2023":292,"echo-2024":215,"x-men-97-s1-2024":344,"agatha-all-along-2024":379,"what-if-s3-2024":254,"your-friendly-neighborhood-spider-man-s1-2025":317,"daredevil-born-again-s1-2025":454,"eyes-of-wakanda-2025":125,"ironheart-2025":289,"i-am-groot-s1-2022":20,"i-am-groot-s2-2023":20,"daredevil-born-again-s2-2026":389,"daredevil-s1-2015":704,"daredevil-s2-2016":702,"daredevil-s3-2018":655,"spider-man-2002":121,"spider-man-2-2004":127,"spider-man-3-2007":139,"the-amazing-spider-man-2012":136,"the-amazing-spider-man-2-2014":142,"spider-man-into-the-spider-verse-2018":117,"spider-man-across-the-spider-verse-2023":140,"x-men-2000":104,"x2-x-men-united-2003":134,"x-men-the-last-stand-2006":104,"x-men-origins-wolverine-2009":107,"x-men-first-class-2011":131,"the-wolverine-2013":126,"x-men-days-of-future-past-2014":132,"deadpool-2016":108,"x-men-apocalypse-2016":144,"logan-2017":137,"deadpool-2-2018":119,"dark-phoenix-2019":113,"the-new-mutants-2020":94,"the-consultant-2011":4,"a-funny-thing-happened-on-the-way-to-thor-s-hammer-2011":4,"item-47-2012":12,"agent-carter-one-shot-2013":15,"all-hail-the-king-2014":14,"the-punisher-one-last-kill-2026-05-12":50});
  function watchTimeMinutes(id){
    const v=WATCH_TIME_MINUTES[id];
    return Number.isFinite(v)&&v>0?v:null;
  }
  function formatWatchMinutes(min){
    if(!Number.isFinite(min)||min<=0) return '';
    const h=Math.floor(min/60),m=Math.round(min%60);
    return h?`${h}時間${m?m+'分':''}`:`${m}分`;
  }
  function prepRuntimeBadge(id){
    const min=watchTimeMinutes(id);
    return min?`<span class="prep-runtime" title="標準版・シーズン全話などの視聴時間目安">⏱ ${formatWatchMinutes(min)}</span>`:'';
  }
  function overallWatchProgressState(){
    const ids=NODES.map(n=>n.id);
    const total=ids.length;
    const watched=ids.filter(id=>watchedIds.has(id));
    const known=ids.filter(id=>watchTimeMinutes(id)!==null);
    const unseenKnown=known.filter(id=>!watchedIds.has(id));
    const totalKnownMinutes=known.reduce((a,id)=>a+watchTimeMinutes(id),0);
    const remainingKnownMinutes=unseenKnown.reduce((a,id)=>a+watchTimeMinutes(id),0);
    const percent=total?watched.length/total*100:0;
    return {total,watched:watched.length,known:known.length,unknown:total-known.length,totalKnownMinutes,remainingKnownMinutes,percent};
  }
  function updateOverallWatchProgress(){
    const el=document.getElementById('overallWatchProgress');
    if(!el) return;
    const st=overallWatchProgressState();
    const pct=Math.round(st.percent*10)/10;
    const days=st.remainingKnownMinutes?Math.max(1,Math.ceil(st.remainingKnownMinutes/120)):0;
    const remaining=st.remainingKnownMinutes?`時間登録済みの未視聴分：<strong>約 ${formatWatchMinutes(st.remainingKnownMinutes)}</strong>${days?` <span class="muted">（1日2時間なら約${days}日）</span>`:''}`:'時間登録済み作品はすべて視聴済み ✓';
    el.innerHTML=`<div class="overall-watch-head"><span class="overall-watch-title">📺 全131作品の視聴進捗</span><span class="overall-watch-percent">${pct}%</span></div><div class="overall-watch-bar" role="progressbar" aria-label="全作品の視聴進捗" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${pct}"><div class="overall-watch-fill" style="width:${Math.max(0,Math.min(100,pct))}%"></div></div><div class="overall-watch-stats"><span class="overall-watch-stat">視聴済み <strong>${st.watched}/${st.total}</strong></span><span class="overall-watch-stat">時間登録 <strong>${st.known}/${st.total}</strong></span><span class="overall-watch-stat">未登録 <strong>${st.unknown}</strong></span></div><div class="overall-watch-remaining">⏱ ${remaining}</div><div class="overall-watch-note">残り時間は上映・配信時間を登録済みの作品だけで計算します。未公開作・時間未登録作は推測して足しません。</div>`;
  }
  window.marvelOverallWatchProgress=()=>overallWatchProgressState();

  function prepWatchTimeSummary(ids,target){
    const items=[...ids];
    const unseen=items.filter(id=>!watchedIds.has(id));
    const known=unseen.filter(id=>watchTimeMinutes(id)!==null);
    const unknown=unseen.filter(id=>watchTimeMinutes(id)===null);
    const remaining=known.reduce((a,id)=>a+watchTimeMinutes(id),0);
    const allKnown=items.filter(id=>watchTimeMinutes(id)!==null);
    const allTotal=allKnown.reduce((a,id)=>a+watchTimeMinutes(id),0);
    const watchedCount=items.length-unseen.length;
    const targetMin=watchTimeMinutes(target);
    const targetRemaining=watchedIds.has(target)?0:targetMin;
    let main='';
    if(items.length===0){
      main=watchedIds.has(target)?'視聴目標は視聴済み ✓':targetMin?`目標作は約 ${formatWatchMinutes(targetMin)}`:'視聴時間は未集計';
    }else if(unseen.length===0){
      main='予習はすべて視聴済み ✓';
    }else if(unknown.length===0){
      main=`未視聴 ${unseen.length}本を見ると 残り 約 ${formatWatchMinutes(remaining)}`;
    }else if(known.length){
      main=`未視聴 ${unseen.length}本中、時間登録済み${known.length}本で 残り 約 ${formatWatchMinutes(remaining)}`;
    }else{
      main=`未視聴 ${unseen.length}本（視聴時間は未集計）`;
    }
    const chips=[];
    if(items.length) chips.push(`<span class="prep-time-chip">視聴済み ${watchedCount}/${items.length}</span>`);
    if(items.length && allKnown.length===items.length) chips.push(`<span class="prep-time-chip">予習全体 約${formatWatchMinutes(allTotal)}</span>`);
    if(unseen.length && unknown.length===0){
      const days=Math.max(1,Math.ceil(remaining/120)); chips.push(`<span class="prep-time-chip">残りを1日2時間なら約${days}日</span>`);
    }
    if(targetMin!==null && unknown.length===0){
      const toGoal=remaining+(targetRemaining||0);
      chips.push(`<span class="prep-time-chip">目標作まで残り ${toGoal?`約${formatWatchMinutes(toGoal)}`:'0分 ✓'}</span>`);
    }
    if(unknown.length) chips.push(`<span class="prep-time-chip prep-time-missing">未視聴・時間未登録 ${unknown.length}件</span>`);
    const doneClass=unseen.length===0?' prep-time-done':'';
    return `<div class="prep-time-summary"><div class="prep-time-main"><span class="prep-time-icon">⏱</span><strong class="${doneClass.trim()}">${main}</strong></div>${chips.length?`<div class="prep-time-sub">${chips.join('')}</div>`:''}<div class="prep-time-note">チェック済み作品を除いた残り時間です。上映時間・配信時間は目安で、未公開作や時間未登録作は推測せず集計から外します。</div></div>`;
  }

  function multiGoalWatchTimeSummary(plan){
    const ids=plan.orderedIds;
    const unseen=ids.filter(id=>!watchedIds.has(id));
    const known=unseen.filter(id=>watchTimeMinutes(id)!==null);
    const unknown=unseen.filter(id=>watchTimeMinutes(id)===null);
    const remaining=known.reduce((sum,id)=>sum+watchTimeMinutes(id),0);
    const watchedCount=ids.length-unseen.length;
    const days=remaining?Math.max(1,Math.ceil(remaining/120)):0;
    const main=unseen.length===0?'統合プランはすべて視聴済み ✓':known.length?`未視聴 ${unseen.length}作品 / 残り 約 ${formatWatchMinutes(remaining)}`:`未視聴 ${unseen.length}作品（視聴時間は未集計）`;
    return `<div class="prep-time-summary multi-goal-time"><div class="prep-time-main"><span class="prep-time-icon">⏱</span><strong>${main}</strong></div><div class="prep-time-sub"><span class="prep-time-chip">ゴール ${plan.goalIds.length}</span><span class="prep-time-chip">ユニーク作品 ${ids.length}</span><span class="prep-time-chip">視聴済み ${watchedCount}/${ids.length}</span>${days?`<span class="prep-time-chip">1日2時間なら約${days}日</span>`:''}${unknown.length?`<span class="prep-time-chip prep-time-missing">時間未登録 ${unknown.length}件</span>`:''}</div><div class="prep-time-note">複数ゴールの前提作品を重複除去し、チェック済みを除いた残り時間です。時間未登録作は推測しません。</div></div>`;
  }

  updatePreparationPlan = function(){
    updateOverallWatchProgress();
    const goals=orderedGoalIds();
    if(!goals.length){
      prepplan.innerHTML='<div class="prep-plan-empty">チャートで見たい作品を選ぶと、ここに統合予習プランを作ります。</div>';
      applyWatchedDimming();
      return;
    }
    const plan=buildMultiGoalPlan(goals,prepTier);
    const multi=goals.length>1;
    const goalIndex=new Map(goals.map((id,i)=>[id,i+1]));
    const heading=`<div class="prep-plan-heading"><strong>${multi?'複数ゴールの統合予習プラン':`${esc(nm[goals[0]]?.title||goals[0])} の予習プラン`}</strong><span class="prep-tier-label">${({minimum:'最低限',recommended:'おすすめ',complete:'完全版'})[prepTier]||prepTier}</span></div>`;
    const goalBadges=`<div class="multi-goal-summary"><span>🎯 ${goals.length}作品をゴール中</span>${goals.map((id,i)=>`<span class="multi-goal-badge-wrap"><button type="button" class="multi-goal-badge" data-goal-focus="${esc(id)}">ゴール ${i+1}：${esc(nm[id]?.title||id)}</button><button type="button" class="prep-goal-remove" data-id="${esc(id)}" title="このゴールを解除" aria-label="${esc(nm[id]?.title||id)}をゴールから解除">×</button></span>`).join('')}</div>`;
    const progress=prepProgressTools(plan.orderedIds);
    const timeSummary=multiGoalWatchTimeSummary(plan);
    const rows=plan.orderedIds.map((id,i)=>{
      const done=watchedIds.has(id), roles=plan.rolesById[id]||[];
      const goalNo=goalIndex.get(id);
      const usedBy=goals.filter(g=>(plan.sourceByGoal[g]||[]).includes(id));
      let why='';
      if(goalNo && roles.includes('prep')) why=`この作品自体がゴールで、後のゴールにもつながります。`;
      else if(goalNo) why='選択した視聴ゴールです。';
      else if(usedBy.length>1) why=`${usedBy.length}ゴールで共通する予習作品です。`;
      else if(usedBy.length===1){ const g=usedBy[0]; const x=prepItemExplanation(id,g,{ids:plan.sourceByGoal[g]}); why=x.html; }
      else why='統合予習ルート上の作品です。';
      return `<li class="prep-item${done?' is-watched':''}${goalNo?' is-goal':''}" data-plan-id="${esc(id)}"><span class="prep-num">${i+1}</span><div class="prep-item-main"><div class="prep-title-row">${prepWatchedCheckbox(id)}<a href="#" class="prep-link" data-id="${esc(id)}" style="color:#e5e7eb;text-decoration:none"><strong>${esc(nm[id]?.title||id)}</strong></a>${goalNo?`<span class="prep-goal-badge">🎯 ゴール ${goalNo}</span>`:''}${done?'<span class="prep-done-badge">視聴済み</span>':''}</div><div class="prep-item-meta"><span class="muted">${esc(nm[id]?.release||'')}</span>${prepRuntimeBadge(id)}</div><div class="prep-why">${why}</div></div></li>`;
    }).join('');
    prepplan.innerHTML=`${heading}${goalBadges}${progress}${timeSummary}<ol class="prep-list multi-goal-list">${rows}</ol><div class="prep-source">各ゴールの予習候補を統合し、重複を除いて有向接続順に並べています。参照のみの接続は並び順を強制しません。</div>`;
    prepplan.querySelectorAll('[data-goal-focus]').forEach(b=>b.onclick=()=>focusGoal(b.dataset.goalFocus));
    prepplan.querySelectorAll('.prep-goal-remove').forEach(b=>b.onclick=e=>{
      e.preventDefault(); e.stopPropagation(); removeGoal(b.dataset.id);
    });
    prepplan.querySelectorAll('.prep-link').forEach(x=>x.onclick=e=>{
      e.preventDefault(); const id=x.dataset.id;
      if(selectedIds.has(id)) focusGoal(id);
    });
    wirePreparationProgress(plan.orderedIds,null);
    applyWatchedDimming();
  };

  function updateModeButtons(){
    document.querySelectorAll('.combine-btn').forEach(b=>b.classList.toggle('active',b.dataset.combine===combineMode));
    document.querySelectorAll('.path-pref-btn').forEach(b=>b.classList.toggle('active',b.dataset.pathPref===pathPreference));
    document.querySelectorAll('.prep-tier').forEach(b=>b.classList.toggle('active',b.dataset.tier===prepTier));
    document.querySelectorAll('.importance-btn').forEach(b=>b.classList.toggle('active',b.dataset.importanceMode===importanceMode));
    tagEdgeImportance();
  }

  function wireSelectionRemovers(){
    detail.querySelectorAll('.selremove').forEach(btn=>btn.onclick=e=>{
      e.preventDefault(); e.stopPropagation(); removeGoal(btn.dataset.id);
    });
    detail.querySelectorAll('.seljump').forEach(x=>x.onclick=e=>{
      e.preventDefault(); e.stopPropagation(); focusGoal(x.dataset.id);
    });
  }

  const refreshBaseSelectionUI=refreshSelection;
  function fullPastIds(){
    const ids=new Set();
    for(const selectedId of selectedIds){
      const p=directedPartAll(selectedId);
      for(const x of p.backNodes) if(!selectedIds.has(x)) ids.add(x);
    }
    return sortByRelease(ids);
  }
  function renderFullDirectedHistory(){
    if(!selectedIds.size || !flow) return;
    const ids=fullPastIds();
    const box=document.createElement('div');
    box.id='fullDirectedHistory';
    box.style.cssText='margin:0 0 10px;padding:8px;border:1px solid #334155;border-radius:8px;background:#0b1220';
    box.innerHTML=`<b>← 前史（全段階）</b><br>${ids.length?ids.map(x=>`<span class="badge fullpast-link" data-id="${x}" style="cursor:pointer">${esc(nm[x]?.title||x)}</span>`).join(' '):'<span class="muted">なし</span>'}<div class="muted" style="margin-top:5px;font-size:11px">strong / very strong の矢印を incoming 方向だけに最後まで辿ります。途中で outgoing へ折り返しません。</div>`;
    flow.prepend(box);
    box.querySelectorAll('.fullpast-link').forEach(x=>x.onclick=e=>select(x.dataset.id,e.ctrlKey||e.metaKey||e.shiftKey));
  }
  refreshSelection = function(center=true){
    normalizeSelection();
    updateModeButtons();
    selectionStateCache=computeSelectionState();
    if(typeof applyFamilyFocus==='function') applyFamilyFocus();
    refreshBaseSelectionUI(center);
    renderFullDirectedHistory();
    updatePreparationPlan();
    wireSelectionRemovers();
    syncTargetControl();
    enhanceEdgeTooltips();
    updatePathExplanation();
    applyWatchedDimming();
    renderGoalBar();
    window.__marvelLastSelectionState=selectionStateCache;
  };

  // v5.11.3: on mobile Canvas, paint the selection overlay immediately and
  // defer the full DOM/UI/cache refresh by one painted frame. Desktop remains synchronous.
  const selectBeforeImmediateOverlay=select;
  let mobileSelectRafA=0,mobileSelectRafB=0;
  function queueMobileFullSelectionRefresh(){
    if(mobileSelectRafA)cancelAnimationFrame(mobileSelectRafA);if(mobileSelectRafB)cancelAnimationFrame(mobileSelectRafB);
    mobileSelectRafA=requestAnimationFrame(()=>{mobileSelectRafA=0;mobileSelectRafB=requestAnimationFrame(()=>{mobileSelectRafB=0;refreshSelection(false);});});
  }
  select=function(id,multi=false){
    const wrap=activeWrap();
    if(!(mobileChartMotion.matches&&isMobileCanvasWrap(wrap))) return selectBeforeImmediateOverlay(id,multi);
    toggleSelectionState(id,multi);normalizeSelection();selectionStateCache=computeSelectionState();
    initMobileCanvas(wrap);drawMobileSelectionOverlay(wrap,selectionStateCache);
    queueMobileFullSelectionRefresh();
  };

  document.querySelectorAll('.combine-btn').forEach(btn=>{
    btn.onclick=()=>{
      combineMode=['and','path'].includes(btn.dataset.combine)?btn.dataset.combine:'or';
      selectionStateCache=null;
      updateModeButtons();
      if(selectedIds.size) refreshSelection(false); else {render();updatePathExplanation();}
    };
  });
  document.querySelectorAll('.path-pref-btn').forEach(btn=>{
    btn.onclick=()=>{
      pathPreference=btn.dataset.pathPref==='shortest'?'shortest':'main';
      selectionStateCache=null;
      updateModeButtons();
      if(combineMode==='path' && selectedIds.size>1) refreshSelection(false);
      else updatePathExplanation();
    };
  });
  document.querySelectorAll('.importance-btn').forEach(btn=>{
    btn.onclick=()=>{
      importanceMode=btn.dataset.importanceMode||'recommended';
      selectionStateCache=null;
      updateModeButtons();
      if(selectedIds.size) refreshSelection(false); else {render();updatePathExplanation();}
    };
  });
  document.querySelectorAll('.prep-tier').forEach(btn=>{
    btn.onclick=()=>{
      prepTier=btn.dataset.tier||'recommended';
      updateModeButtons();
      updatePreparationPlan();
    };
  });

  function pathRouteHtml(a,b,p,profileLabel='',active=false){
    if(!p) return `<div class="path-missing">${esc(nm[a]?.title||a)} と ${esc(nm[b]?.title||b)} の間に、現在の接続層で向きを守った経路はありません。</div>`;
    const eMap=new Map(EDGES.map(e=>[edgeKey(e),e]));
    const impJa={core:'中核',recommended:'推奨',reference:'参照'};
    const title=`${esc(nm[p.nodes[0]]?.title||p.nodes[0])} → ${esc(nm[p.nodes[p.nodes.length-1]]?.title||p.nodes[p.nodes.length-1])}`;
    const badge=profileLabel?`<span class="path-route-profile${active?' active':''}">${esc(profileLabel)}</span>`:'';
    let body=`<div class="path-route${active?' active-route':''}"><div class="path-route-title">${title}${badge}</div>`;
    for(let i=0;i<p.edges.length;i++){
      const e=eMap.get(p.edges[i]), s=p.nodes[i], t=p.nodes[i+1], imp=importanceOf(e||{});
      body+=`<div class="path-step"><span>${esc(nm[s]?.title||s)}</span><span class="path-arrow">→</span><span><b>${esc(nm[t]?.title||t)}</b><span class="path-imp ${imp}">${impJa[imp]||imp}</span><div class="path-edge-meta">${esc(displayEdgeType(e))} / ${esc(e?.strength||'')}</div></span></div>`;
    }
    return body+'</div>';
  }
  function updatePathExplanation(){
    const card=document.getElementById('pathExplainCard'), box=document.getElementById('pathExplain'); if(!card||!box) return;
    const ids=[...selectedIds];
    if(combineMode!=='path'||ids.length<2){ card.classList.remove('active'); return; }
    card.classList.add('active');
    const chunks=[];
    for(let i=0;i<ids.length;i++) for(let j=i+1;j<ids.length;j++){
      const a=ids[i], b=ids[j];
      const main=bestDirectedPairPath(a,b,'main'), shortest=bestDirectedPairPath(a,b,'shortest');
      const same=main&&shortest&&main.edges.join('|')===shortest.edges.join('|')&&main.nodes.join('|')===shortest.nodes.join('|');
      if(same){
        chunks.push(pathRouteHtml(a,b,pathPreference==='shortest'?shortest:main,pathPreference==='shortest'?'最短＝本流優先':'本流優先＝最短',true));
      }else{
        chunks.push(pathRouteHtml(a,b,main,'本流優先',pathPreference==='main'));
        chunks.push(pathRouteHtml(a,b,shortest,'最短',pathPreference==='shortest'));
        if(main&&shortest) chunks.push(`<div class="path-route-alt-note">本流優先：${main.edges.length}本 / 最短：${shortest.edges.length}本。上部のPATH切替で図上の強調経路を選べます。</div>`);
      }
    }
    box.innerHTML=chunks.join('')||'<div class="muted">経路を表示できません。</div>';
  }

  let mobileUndoSnapshot=null;
  let mobileUndoTimer=null;
  function mobileWidth(){ return window.matchMedia('(max-width:760px)').matches; }
  function ensureMobileFocusShell(){
    let shell=document.getElementById('mobileFocusShell');
    if(shell) return shell;
    const left=document.getElementById('left'); if(!left) return null;
    shell=document.createElement('section'); shell.id='mobileFocusShell'; shell.className='mobile-goal-shell';
    shell.innerHTML=`<div id="mobileGoalBar" class="mobile-goal-bar"></div><div id="mobileGoalUndo" aria-live="polite"></div>`;
    const firstPanel=left.querySelector('.panel'); left.insertBefore(shell,firstPanel);
    return shell;
  }
  function renderGoalBar(){
    const shell=ensureMobileFocusShell(); if(!shell) return;
    const bar=shell.querySelector('#mobileGoalBar'), ids=orderedGoalIds();
    const watch=document.getElementById('watchWorkspace'), hint=watch?.querySelector('.watch-card-target'), hasGoal=ids.length>0;
    if(hint) hint.hidden=hasGoal;
    watch?.classList.toggle('has-goal',hasGoal);
    if(!ids.length){ bar.innerHTML='<div class="mobile-goal-count">🎯 ゴールはまだありません</div><div class="muted" style="font-size:11px;margin-top:4px">作品をタップして詳細を開き、「ゴールに追加」を押してください。</div>'; return; }
    bar.innerHTML=`<div class="mobile-goal-head"><span class="mobile-goal-count">🎯 ${ids.length}作品をゴール中</span></div><div class="mobile-goal-chips">${ids.map((id,i)=>`<div class="mobile-goal-chip${id===selected?' current':''}" data-id="${esc(id)}"><button type="button" class="mobile-goal-chip-main" title="このゴールを基準に表示">${i+1}. ${esc(nm[id]?.title||id)}</button><button type="button" class="mobile-goal-chip-remove" aria-label="${esc(nm[id]?.title||id)}をゴールから解除">×</button></div>`).join('')}</div><div class="mobile-goal-actions"><button type="button" id="mobileClearGoals">すべて解除</button><button type="button" id="mobilePrepJump">予習プランを見る</button></div>`;
    bar.querySelectorAll('.mobile-goal-chip-main').forEach(b=>b.onclick=()=>focusGoal(b.closest('.mobile-goal-chip').dataset.id));
    bar.querySelectorAll('.mobile-goal-chip-remove').forEach(b=>b.onclick=e=>{e.stopPropagation();removeGoal(b.closest('.mobile-goal-chip').dataset.id);});
    bar.querySelector('#mobileClearGoals').onclick=clearAllGoalsWithUndo;
    bar.querySelector('#mobilePrepJump').onclick=()=>window.showWatchWorkspace?.();
  }
  function clearAllGoalsWithUndo(){
    if(!selectedIds.size) return;
    mobileUndoSnapshot={ids:orderedGoalIds(),focus:selected};
    selectedIds=new Set(); selected=null; refreshSelection(false);
    const undo=ensureMobileFocusShell()?.querySelector('#mobileGoalUndo'); if(!undo) return;
    undo.innerHTML='ゴールを解除しました <button type="button">元に戻す</button>'; undo.classList.add('show');
    undo.querySelector('button').onclick=undoClearGoals;
    clearTimeout(mobileUndoTimer); mobileUndoTimer=setTimeout(()=>{undo.classList.remove('show');mobileUndoSnapshot=null;},5000);
  }
  function undoClearGoals(){
    if(!mobileUndoSnapshot) return;
    const snap=mobileUndoSnapshot; mobileUndoSnapshot=null; clearTimeout(mobileUndoTimer);
    selectedIds=new Set(snap.ids); selected=(snap.focus&&selectedIds.has(snap.focus))?snap.focus:(snap.ids.at(-1)||null);
    refreshSelection(false); ensureMobileFocusShell()?.querySelector('#mobileGoalUndo')?.classList.remove('show');
  }
  window.clearAllGoalsWithUndo=clearAllGoalsWithUndo; window.undoClearGoals=undoClearGoals;

  function syncTargetControl(){}
  function wireTargetControl(){}
  function enhanceEdgeTooltips(){
    const byKey=new Map(EDGES.map(e=>[edgeKey(e),e]));
    const impJa={core:'中核',recommended:'推奨',reference:'参照'};
    document.querySelectorAll('.svg-wrap svg g.edge:not(.dynamic-edge-overlay)').forEach(g=>{
      const k=edgeKeyFromSvgGroup(g), e=byKey.get(k); if(!e) return;
      let t=g.querySelector(':scope > title'); if(!t){t=document.createElementNS('http://www.w3.org/2000/svg','title');g.insertBefore(t,g.firstChild);}
      const reason=e.reason?`\n根拠：${e.reason}`:'';
      t.textContent=`${nm[e.source]?.title||e.source} → ${nm[e.target]?.title||e.target}\n接続：${displayEdgeType(e)} / 重要度：${impJa[importanceOf(e)]||importanceOf(e)} / 強さ：${e.strength||''}${reason}`;
    });
  }

  // Exactly one graph click path: click -> select state -> compute -> render.
  document.addEventListener('click',e=>{
    const canvas=e.target?.closest?.('canvas[data-marvel-mobile-canvas]');
    if(canvas){
      const wrap=canvas.closest('.svg-wrap'),st=typeof ensureViewState==='function'?ensureViewState(wrap):null;
      if(st?.moved){st.moved=false;e.preventDefault();e.stopImmediatePropagation();return;}
      const id=mobileCanvasHitTest(wrap,e.clientX,e.clientY);if(!id||!nm[id])return;
      e.preventDefault();e.stopImmediatePropagation();select(id,!!(e.ctrlKey||e.metaKey||e.shiftKey));return;
    }
    const node=e.target?.closest?.('.svg-wrap svg g.node');
    if(!node) return;
    const wrap=node.closest('.svg-wrap');
    const st=typeof ensureViewState==='function'?ensureViewState(wrap):null;
    if(st?.moved){ st.moved=false; e.preventDefault(); e.stopImmediatePropagation(); return; }
    const id=gt(node); if(!id || !nm[id]) return;
    e.preventDefault(); e.stopImmediatePropagation();
    select(id,!!(e.ctrlKey||e.metaKey||e.shiftKey));
  },true);

  document.querySelectorAll('.svg-wrap .zoom-hint').forEach(h=>{
    h.textContent=window.matchMedia('(max-width:760px)').matches ? '1本指: 図を移動 / 2本指: 図をズーム / タップ: ゴール追加・解除' : 'チャート上のホイール: 図をズーム / ドラッグ: 図を移動 / クリック: ゴール追加・解除';
  });

  // v5.13.0: desktop detail panel can give its width back to the chart.
  (()=>{
    const main=document.querySelector('main'), btn=document.getElementById('desktopSideToggle');
    if(!main||!btn) return;
    btn.addEventListener('click',()=>{
      const collapsed=main.dataset.sideCollapsed!=='true';
      main.dataset.sideCollapsed=collapsed?'true':'false';
      btn.setAttribute('aria-expanded',collapsed?'false':'true');
      btn.textContent=collapsed?'詳細':'詳細を隠す';
      btn.title=collapsed?'詳細パネルを開く':'詳細パネルを折り畳む';
      requestAnimationFrame(()=>activeWrap()&&applyView(activeWrap()));
    });
  })();

  // v5.13.0: graph-only mobile actions. Keep the floating controls off the watch plan/about area.
  (()=>{
    let raf=0;
    const sync=()=>{
      raf=0;
      const wrap=document.querySelector('.panel.active .svg-wrap');
      const r=wrap?.getBoundingClientRect();
      const visible=!!r && Math.max(0,Math.min(r.bottom,innerHeight)-Math.max(r.top,0))>Math.min(180,r.height*.25);
      document.body.classList.toggle('mobile-chart-in-view',visible);
    };
    const queue=()=>{if(!raf)raf=requestAnimationFrame(sync)};
    addEventListener('scroll',queue,{passive:true});
    addEventListener('resize',queue,{passive:true});
    document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>requestAnimationFrame(sync)));
    sync();
  })();

  ensureMobileFocusShell();
  renderGoalBar();
  document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>requestAnimationFrame(()=>{
    if(mobileWidth()) renderGoalBar();
  })));
  wireTargetControl();
  enhanceEdgeTooltips();
  updateModeButtons();
  if(selectedIds.size) refreshSelection(false); else { selectionStateCache=computeSelectionState(); updatePreparationPlan(); }
  syncTargetControl();
  updatePathExplanation();
  window.marvelSelectionAudit=function(){
    const state=selectedIds.size ? (window.__marvelLastSelectionState||computeSelectionState()) : null;
    const svg=document.querySelector('.panel.active .svg-wrap svg');
    return {
      version:'5.15.0-public', selected:[...selectedIds], scope:scopeMode, importance:importanceMode, combine:combineMode,
      dim:!!svg?.classList.contains('dim'),
      litNodes:svg?.querySelectorAll('g.node.hl,g.node.focus').length||0,
      litEdges:svg?.querySelectorAll('g.edge.hl').length||0,
      back:[...(state?.back||[])].filter(x=>!selectedIds.has(x)),
      forward:[...(state?.forward||[])].filter(x=>!selectedIds.has(x)),
      fullPast:fullPastIds(),
      staticEdgeKeys:[...document.querySelectorAll('.panel.active .svg-wrap svg g.edge:not(.dynamic-edge-overlay)')].map(edgeKeyFromSvgGroup).filter(Boolean).length
    };
  };

  // PUBLIC v5.12.0: project shared room state into the existing watch-plan UI.
  (()=>{
    if(!window.marvelSharedRoom)return;
    const room=window.marvelSharedRoom;
    const bar=document.getElementById('sharedRoomBar'), openBtn=document.getElementById('sharedRoomOpen');
    const dialog=document.getElementById('sharedRoomDialog'), nameInput=document.getElementById('sharedRoomName');
    const submitBtn=document.getElementById('sharedRoomSubmit'), cancelBtn=document.getElementById('sharedRoomCancel');
    const dialogTitle=document.getElementById('sharedRoomDialogTitle'), dialogText=document.getElementById('sharedRoomDialogText'), errorBox=document.getElementById('sharedRoomError');
    let roomViewState=null, applyingRoomState=false, lastSentPlan='', joiningRoomId='';
  
    function escRoom(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
    function memberSet(memberId){return new Set(roomViewState?.watched?.[memberId]||[])}
    function ownSet(){return memberSet(room.memberId)}
    function currentPlanSignature(){return JSON.stringify({tier:prepTier,goalIds:orderedGoalIds()})}
    function serverPlanSignature(){const p=roomViewState?.plan||{};return JSON.stringify({tier:p.tier||'recommended',goalIds:[...(p.goalIds||[])]})}
    function maybePushPlan(){
      if(!room.active||applyingRoomState)return;
      const sig=currentPlanSignature();if(sig===serverPlanSignature()||sig===lastSentPlan)return;
      if(room.setPlan(orderedGoalIds(),prepTier))lastSentPlan=sig;
    }
    function renderRoomBar(){
      if(!bar)return;
      if(!room.active||!roomViewState){bar.classList.remove('active');bar.innerHTML='';if(openBtn)openBtn.textContent='👥 一緒に見る';return}
      const members=roomViewState.members||[];
      bar.classList.add('active');
      bar.innerHTML=`<div class="shared-room-head"><span class="shared-room-title">👥 共有中 · ${members.length}人</span><div class="shared-room-actions"><button id="sharedRoomCopy" type="button">招待リンクをコピー</button><button id="sharedRoomLeave" type="button">退出</button></div></div><div class="shared-room-members">${members.map(m=>`<span class="shared-room-member${m.id===room.memberId?' me':''}">${escRoom(m.name)}${m.id===room.memberId?'（自分）':''}</span>`).join('')}</div><div class="shared-room-note">チェックは参加者ごとに共有されます。30日間使われないルームは自動で削除されます。</div>`;
      if(openBtn)openBtn.textContent='👥 共有中';
      bar.querySelector('#sharedRoomCopy')?.addEventListener('click',async()=>{
        const url=room.inviteUrl();try{await navigator.clipboard?.writeText(url);bar.querySelector('#sharedRoomCopy').textContent='コピーしました ✓'}catch(_){prompt('このリンクを共有してください',url)}
      });
      bar.querySelector('#sharedRoomLeave')?.addEventListener('click',()=>room.leave());
    }
    function decorateSharedPlan(){
      if(!room.active||!roomViewState)return;
      const members=roomViewState.members||[];
      prepplan.querySelectorAll('.prep-item[data-plan-id]').forEach(row=>{
        const id=row.dataset.planId;row.querySelector('.prep-room-members')?.remove();row.querySelector('.prep-all-done-badge')?.remove();
        const states=members.map(m=>({m,done:memberSet(m.id).has(id)}));
        const allDone=states.length>0&&states.every(x=>x.done);row.classList.toggle('is-room-all-watched',allDone);
        const box=document.createElement('div');box.className='prep-room-members';
        box.innerHTML=states.map(({m,done})=>`<span class="prep-room-member${done?' done':''}${m.id===room.memberId?' me':''}">${escRoom(m.name)} ${done?'✓':'—'}</span>`).join('');
        row.querySelector('.prep-item-main')?.appendChild(box);
        if(allDone){const badge=document.createElement('span');badge.className='prep-all-done-badge';badge.textContent='全員完了';row.querySelector('.prep-title-row')?.appendChild(badge)}
      });
      const all=prepplan.querySelector('#prepMarkAllWatched'),clear=prepplan.querySelector('#prepClearPlanWatched');
      for(const b of [all,clear])if(b){b.disabled=true;b.title='共有中は1作品ずつチェックしてください';}
    }
  
    const saveWatchedStateLocal=saveWatchedState;
    saveWatchedState=function(){
      if(room.active){try{localStorage.setItem(WATCHED_DIM_STORAGE_KEY,dimWatchedOnChart?'1':'0')}catch(_){}return}
      return saveWatchedStateLocal();
    };
    const setWatchedLocal=setWatched;
    setWatched=function(id,on){
      if(!room.active)return setWatchedLocal(id,on);
      if(!nm[id])return;
      if(on)watchedIds.add(id);else watchedIds.delete(id);
      if(roomViewState){roomViewState.watched=roomViewState.watched||{};roomViewState.watched[room.memberId]=[...watchedIds].sort()}
      room.setWatched(id,!!on);applyWatchedDimming();
    };
    const updatePreparationPlanRoomBase=updatePreparationPlan;
    updatePreparationPlan=function(){
      updatePreparationPlanRoomBase();decorateSharedPlan();renderRoomBar();maybePushPlan();
    };
  
    function applyIncomingState(next,kind){
      if(!next)return;
      roomViewState=JSON.parse(JSON.stringify(next));
      applyingRoomState=true;
      try{
        watchedIds=ownSet();
        const rp=roomViewState.plan||{};
        const goals=(rp.goalIds||[]).filter(id=>nm[id]);
        const tier=['minimum','recommended','complete'].includes(rp.tier)?rp.tier:'recommended';
        const creating=kind==='created';
        const differs=tier!==prepTier||JSON.stringify(goals)!==JSON.stringify(orderedGoalIds());
        if(!creating&&differs){selectedIds=new Set(goals);selected=goals.slice(-1)[0]||null;prepTier=tier;selectionStateCache=null;refreshSelection(false)}
        else updatePreparationPlanPreservingView();
        applyWatchedDimming();renderRoomBar();
        lastSentPlan=serverPlanSignature();
        if(creating)requestAnimationFrame(()=>{lastSentPlan='';maybePushPlan()});
      }finally{applyingRoomState=false}
    }
    window.addEventListener('marvelroomstate',e=>{
      const d=e.detail||{};
      if(d.active&&d.state)applyIncomingState(d.state,d.kind);
      else if(d.kind==='left'){
        roomViewState=null;applyingRoomState=true;
        try{watchedIds=loadWatchedIds();updatePreparationPlanPreservingView();applyWatchedDimming();renderRoomBar()}finally{applyingRoomState=false}
      }else renderRoomBar();
    });
  
    function openRoomDialog(roomId=''){
      joiningRoomId=roomId||'';errorBox.textContent='';
      dialogTitle.textContent=joiningRoomId?'共有ルームに参加':'一緒に見るルームを作る';
      dialogText.textContent=joiningRoomId?'表示名を入れると、このルームの予習プランとチェック状況を共有できます。':'共有リンクを送った相手と、参加者別の視聴済みをリアルタイムで共有できます。';
      submitBtn.textContent=joiningRoomId?'参加する':'ルームを作る';
      const saved=joiningRoomId?room.loadCredential(joiningRoomId):null;if(saved?.displayName)nameInput.value=saved.displayName;
      if(dialog.showModal)dialog.showModal();else dialog.setAttribute('open','');setTimeout(()=>nameInput.focus(),20);
    }
    openBtn?.addEventListener('click',()=>room.active?renderRoomBar():openRoomDialog(room.roomIdFromHash()));
    cancelBtn?.addEventListener('click',()=>dialog.close?.());
    submitBtn?.addEventListener('click',async()=>{
      const name=nameInput.value.trim();if(!name){errorBox.textContent='表示名を入力してください。';return}
      submitBtn.disabled=true;errorBox.textContent='';
      try{if(joiningRoomId)await room.join(joiningRoomId,name);else await room.create(name);dialog.close?.()}
      catch(e){errorBox.textContent=e?.code==='room_full'?'このルームは満員です。':e?.code==='room_not_found'?'このルームは期限切れか、見つかりません。':`接続できませんでした：${e?.message||'通信エラー'}`}
      finally{submitBtn.disabled=false}
    });
    renderRoomBar();
    const inviteRoomId=room.roomIdFromHash();
    if(inviteRoomId){
      const saved=room.loadCredential(inviteRoomId);
      if(saved?.displayName){
        room.join(inviteRoomId,saved.displayName).catch(e=>{
          openRoomDialog(inviteRoomId);
          errorBox.textContent=e?.code==='room_not_found'?'このルームは期限切れか、見つかりません。':e?.code==='room_full'?'このルームは満員です。':'再接続できませんでした。表示名を確認してもう一度お試しください。';
        });
      }else requestAnimationFrame(()=>openRoomDialog(inviteRoomId));
    }
    window.marvelSharedRoomUI={openDialog:openRoomDialog,get viewState(){return roomViewState},decorate:decorateSharedPlan};
  })();


  // PUBLIC v5.12.0: render the current watch plan to a standalone PNG.
  (()=>{
    const shareButton=document.getElementById('sharePlanImage');
    const TIER_LABEL={minimum:'最低限',recommended:'おすすめ',complete:'完全版'};
    function wrapChars(ctx,text,maxWidth){
      const out=[];let line='';
      for(const ch of String(text||'')){
        const next=line+ch;
        if(line&&ctx.measureText(next).width>maxWidth){out.push(line);line=ch}else line=next;
      }
      if(line)out.push(line);return out.length?out:[''];
    }
    function roomView(){return window.marvelSharedRoomUI?.viewState||null}
    function currentImageData(){
      const goals=orderedGoalIds();
      if(!goals.length)throw new Error('予習プランを作るには、先に見たい作品を選んでください。');
      const plan=buildMultiGoalPlan(goals,prepTier);
      const rv=roomView(),members=rv?.members||[];
      return {goals,plan,tier:prepTier,members,roomWatched:rv?.watched||{}};
    }
    async function createBlob(){
      const data=currentImageData(), rows=data.plan.orderedIds;
      const sharedExtra=data.members.length?34:0;
      const rowH=92+sharedExtra, width=1080, height=Math.max(620,300+rows.length*rowH+110);
      const canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;
      const ctx=canvas.getContext('2d');
      ctx.fillStyle='#0b1020';ctx.fillRect(0,0,width,height);
      ctx.fillStyle='#e5e7eb';ctx.font='800 44px sans-serif';ctx.fillText('マーベル予習プラン',58,70);
      ctx.fillStyle='#94a3b8';ctx.font='500 24px sans-serif';ctx.fillText(`${TIER_LABEL[data.tier]||data.tier} · ${rows.length}作品`,58,110);
      const goalText=data.goals.map(id=>nm[id]?.title||id).join(' ／ ');
      ctx.font='700 27px sans-serif';ctx.fillStyle='#fde68a';
      const goalLines=wrapChars(ctx,`🎯 ${goalText}`,width-116).slice(0,3);let y=154;
      for(const line of goalLines){ctx.fillText(line,58,y);y+=36}
      y=Math.max(y+24,248);
      const goalSet=new Set(data.goals);
      rows.forEach((id,i)=>{
        const top=y+i*rowH;
        ctx.fillStyle=i%2?'#0f172a':'#111827';ctx.fillRect(42,top-34,width-84,rowH-8);
        ctx.fillStyle='#2563eb';ctx.beginPath();ctx.arc(76,top,21,0,Math.PI*2);ctx.fill();
        ctx.fillStyle='#fff';ctx.font='800 20px sans-serif';ctx.textAlign='center';ctx.fillText(String(i+1),76,top+7);ctx.textAlign='left';
        const title=nm[id]?.title||id;
        ctx.font='700 25px sans-serif';ctx.fillStyle='#e5e7eb';
        const titleLines=wrapChars(ctx,title,goalSet.has(id)?720:815).slice(0,2);let ty=top-6;
        for(const line of titleLines){ctx.fillText(line,112,ty);ty+=30}
        if(goalSet.has(id)){ctx.fillStyle='#f59e0b';ctx.font='800 17px sans-serif';ctx.fillText('🎯 ゴール',850,top-5)}
        ctx.fillStyle='#94a3b8';ctx.font='500 18px sans-serif';ctx.fillText(nm[id]?.release||'',112,top+45);
        if(data.members.length){
          let sx=112;const sy=top+73;
          for(const m of data.members){
            const done=(data.roomWatched[m.id]||[]).includes(id);ctx.font='700 16px sans-serif';
            const label=`${m.name} ${done?'✓':'—'}`, w=Math.min(230,ctx.measureText(label).width+24);
            ctx.fillStyle=done?'#052e20':'#0b1220';ctx.fillRect(sx,sy-20,w,27);ctx.strokeStyle=done?'#166534':'#374151';ctx.strokeRect(sx,sy-20,w,27);ctx.fillStyle=done?'#86efac':'#94a3b8';ctx.fillText(label,sx+10,sy);sx+=w+10;if(sx>930)break;
          }
        }else{
          const done=watchedIds.has(id);ctx.fillStyle=done?'#86efac':'#64748b';ctx.font='700 16px sans-serif';ctx.fillText(done?'視聴済み ✓':'未視聴',850,top+45);
        }
      });
      ctx.fillStyle='#64748b';ctx.font='500 16px sans-serif';ctx.fillText('非公式ファン制作 · マーベル作品相関図 日本版',58,height-48);
      return await new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(new Error('PNG生成に失敗しました')),'image/png'));
    }
    async function share(){
      const blob=await createBlob();const file=new File([blob],'marvel-watch-plan.png',{type:'image/png'});
      if(navigator.share&&navigator.canShare?.({files:[file]})){
        await navigator.share({title:'マーベル予習プラン',files:[file]});return {method:'share'};
      }
      const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=file.name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);return {method:'download'};
    }
    shareButton?.addEventListener('click',async()=>{
      const old=shareButton.textContent;shareButton.disabled=true;shareButton.textContent='画像を作成中…';
      try{await share()}catch(e){alert(e?.message||'画像を作成できませんでした。')}finally{shareButton.disabled=false;shareButton.textContent=old}
    });
    window.marvelPlanShare={createBlob,share,currentImageData};
  })();
  

})();
