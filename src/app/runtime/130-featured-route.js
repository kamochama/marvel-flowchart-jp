(()=>{
  const cfg=window.FEATURED_ROUTE;
  let featuredRouteState=null;
  const desktopHost=document.getElementById('desktopFeaturedHost');
  const mobileHost=document.getElementById('mobileFeaturedHost');
  const control=document.createElement('div');
  control.id='featuredRouteControl';control.className='featured-route-control';
  control.innerHTML=`<div class="featured-route-copy"><span class="featured-eyebrow">🔥 ${esc(cfg.eyebrow)}</span><strong>${esc(cfg.label)}</strong><small>${esc(cfg.description)}</small></div><button type="button" class="featured-route-preview" data-featured-action="preview">流れを見る</button><button type="button" class="featured-route-goal" data-featured-action="goal">ゴールに追加</button><button type="button" class="featured-route-close" data-featured-action="close" aria-label="特集表示を閉じる">×</button>`;

  window.mountFeaturedForViewport=function(){
    if(!cfg.enabled){control.remove();return;}
    const host=window.matchMedia('(max-width:760px)').matches?mobileHost:desktopHost;
    if(host&&control.parentElement!==host)host.appendChild(control);
  };
  window.buildFeaturedRouteState=function(targetId){
    const all=window.marvelDirectedPartAll(targetId);
    const back=new Set(all.backNodes);back.delete(targetId);
    const backEdges=new Set(all.backEdges),context=new Set(),contextEdges=new Set();
    for(const e of (inc[targetId]||[])){
      if(edgeRank(e)>=3||!window.marvelImportanceAllowed(e))continue;
      context.add(e.source);contextEdges.add(window.marvelEdgeKey(e));
    }
    const ctx=new Set([targetId,...back,...context]);
    return {ctx,back,forward:new Set(),context,backEdges,forwardEdges:new Set(),contextEdges,pathEdges:new Set(),generic:false,pathMode:false};
  };
  function clearFeaturedPaint(svg){
    if(!svg)return;
    svg.querySelectorAll('.dynamic-edge-overlay').forEach(x=>x.remove());
    svg.querySelectorAll('.featured-target,.hl,.focus,.backhl,.forwardhl,.bothhl,.contexthl,.pathhl,.goal-node,.current-goal').forEach(x=>x.classList.remove('featured-target','hl','focus','backhl','forwardhl','bothhl','contexthl','pathhl','goal-node','current-goal'));
    svg.classList.remove('dim');
  }
  window.renderFeaturedRoutePreview=function(){
    if(!featuredRouteState)return false;
    const svg=activeSvg();if(!svg)return false;
    clearFeaturedPaint(svg);svg.classList.remove('family-mode','char-mode');svg.classList.add('dim');
    const {targetId,state}=featuredRouteState;
    for(const g of svg.querySelectorAll('g.node')){
      const id=gt(g);
      if(id===targetId){g.classList.add('focus','featured-target');continue;}
      if(state.back.has(id))g.classList.add('hl','backhl');
      else if(state.context.has(id))g.classList.add('hl','contexthl');
    }
    for(const g of svg.querySelectorAll('g.edge:not(.dynamic-edge-overlay)')){
      const k=window.marvelEdgeKeyFromGroup(g);if(!k)continue;
      if(state.backEdges.has(k))g.classList.add('hl','backhl');
      else if(state.contextEdges.has(k))g.classList.add('hl','contexthl');
    }
    window.marvelAddMissingDirectedEdges(svg,state);
    control.classList.add('is-previewing');
    return true;
  };
  window.startFeaturedRoutePreview=function(){
    if(!cfg.enabled||!nm[cfg.targetId])return false;
    featuredRouteState={targetId:cfg.targetId,state:buildFeaturedRouteState(cfg.targetId)};
    activatePanel('overview',{fit:false,restoreSelection:false,exitFeatured:false});
    requestAnimationFrame(()=>{
      // v5.14.1: activatePanel also queues a paint. If the user exits the
      // preview before this frame, that older paint must not erase the
      // selection we just restored.
      if(!featuredRouteState){
        if(selectedIds.size)refreshSelection(false);
        else{clearSvg();render();}
        return;
      }
      if(renderFeaturedRoutePreview())_origCenterNodeInView(cfg.targetId);
    });
    return true;
  };
  window.exitFeaturedRoutePreview=function({restore=true}={}){
    if(!featuredRouteState)return false;
    featuredRouteState=null;control.classList.remove('is-previewing');
    document.querySelectorAll('.svg-wrap svg').forEach(svg=>{svg.querySelectorAll('.featured-target').forEach(x=>x.classList.remove('featured-target'));});
    clearSvg();
    if(restore){if(selectedIds.size)refreshSelection(false);else render();}
    return true;
  };
  window.addFeaturedRouteGoal=function(){
    if(featuredRouteState)exitFeaturedRoutePreview({restore:false});
    if(selectedIds.has(cfg.targetId)){focusGoal(cfg.targetId);return true;}
    select(cfg.targetId);return true;
  };
  window.marvelFeaturedRouteAudit=()=>({
    active:!!featuredRouteState,
    target:featuredRouteState?.targetId||null,
    nodes:[...(featuredRouteState?.state?.ctx||[])],
    forward:[...(featuredRouteState?.state?.forward||[])]
  });

  // v5.14.1: featured preview is exclusive. Any normal render path first
  // retires the temporary preview state, then performs the requested repaint.
  const renderBeforeFeaturedRoute=render;
  render=function(...args){
    if(featuredRouteState)exitFeaturedRoutePreview({restore:true});
    return renderBeforeFeaturedRoute(...args);
  };
  const refreshSelectionBeforeFeaturedRoute=refreshSelection;
  refreshSelection=function(...args){
    if(featuredRouteState)exitFeaturedRoutePreview({restore:false});
    return refreshSelectionBeforeFeaturedRoute(...args);
  };

  const retireFeaturedBeforeNormalAction=()=>{
    if(featuredRouteState)exitFeaturedRoutePreview({restore:true});
  };
  const featuredExitFieldSelector='#q,#branch,#status,#character,#familyFocus';
  document.addEventListener('input',e=>{
    if(e.target?.matches?.(featuredExitFieldSelector))retireFeaturedBeforeNormalAction();
  },true);
  document.addEventListener('change',e=>{
    if(e.target?.matches?.(featuredExitFieldSelector))retireFeaturedBeforeNormalAction();
  },true);
  document.addEventListener('pointerdown',e=>{
    if(e.target?.closest?.('#clear,.scope-btn,.importance-btn,.combine-btn,.path-pref-btn,.prep-tier'))retireFeaturedBeforeNormalAction();
  },true);

  const selectBeforeFeaturedRoute=select;
  select=function(id,multi=false){
    if(featuredRouteState)exitFeaturedRoutePreview({restore:false});
    return selectBeforeFeaturedRoute(id,multi);
  };
  control.querySelector('[data-featured-action="preview"]').onclick=startFeaturedRoutePreview;
  control.querySelector('[data-featured-action="goal"]').onclick=addFeaturedRouteGoal;
  control.querySelector('[data-featured-action="close"]').onclick=()=>exitFeaturedRoutePreview({restore:true});
  const mq=window.matchMedia('(max-width:760px)');mq.addEventListener?.('change',mountFeaturedForViewport);
  mountFeaturedForViewport();
})();
