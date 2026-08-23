// PUBLIC v5.15.0: inspection focus is independent from viewing-plan goals.
(()=>{
  const legacyGoalSelect=select;
  let detailFocusId=null;
  let focusPaintRaf=0;

  const activeGoalIds=()=>[...selectedIds];
  const edgeKey=e=>window.marvelEdgeKey?window.marvelEdgeKey(e):`${e.source}->${e.target}`;
  const scopeNow=()=>window.marvelSelectionAudit?.().scope||'all';

  function limitedFocusPart(id,hops){
    const nodes=new Set([id]), usedEdges=new Set(), q=[[id,0]];
    while(q.length){
      const [x,d]=q.shift(); if(d>=hops)continue;
      for(const e of [...(inc[x]||[]),...(out[x]||[])]){
        if(window.marvelImportanceAllowed&&!window.marvelImportanceAllowed(e))continue;
        const y=e.source===x?e.target:e.source;
        usedEdges.add(edgeKey(e));
        if(!nodes.has(y)){nodes.add(y);q.push([y,d+1]);}
      }
    }
    return {nodes,backNodes:new Set(),forwardNodes:new Set(),contextNodes:new Set(nodes),backEdges:new Set(),forwardEdges:new Set(),contextEdges:usedEdges,generic:true};
  }

  function focusPart(id){
    const scope=scopeNow();
    if(scope==='all'&&window.marvelDirectedPartAll)return window.marvelDirectedPartAll(id);
    return limitedFocusPart(id,scope==='two'?2:1);
  }

  const attrEsc=s=>esc(s).replaceAll('"','&quot;').replaceAll("'",'&#39;');

  function sortedDirect(id,kind){
    const arr=(kind==='in'?(inc[id]||[]):(out[id]||[])).slice();
    return arr.sort((a,b)=>edgeRank(b)-edgeRank(a)).slice(0,8);
  }

  window.marvelRenderFocusedDetail=function(id){
    const n=nm[id],info=window.WORK_DETAILS?.[id]; if(!n||!detail)return false;
    const goals=activeGoalIds(),isGoal=selectedIds.has(id);
    const prev=sortedDirect(id,'in'),next=sortedDirect(id,'out');
    const link=(wid,label)=>`<button type="button" class="v515-work-link" data-v515-focus="${attrEsc(wid)}">${esc(label)}</button>`;
    const jpinfo=n.japan_date?`${esc(n.japan_date)} ${esc(n.japan_type||'')}`:'公式確認データ未登録';
    const source=n.source_url?`<a href="${attrEsc(n.source_url)}" target="_blank" rel="noopener">日本向け公式ソースを開く ↗</a>${n.source_note?`<div class="muted">${esc(n.source_note)}</div>`:''}`:'<span class="muted">公式ソース登録なし</span>';
    detail.classList.add('v515-detail');
    detail.innerHTML=`
      <div class="v515-detail-title"><strong>${esc(n.title)}</strong><div class="muted">${esc(n.title_en)} / ${esc(n.release)}</div><div class="v515-detail-badges"><span class="badge">${esc(n.branch)}</span>${goals.length?`<span class="badge">ゴール ${goals.length}件保持中</span>`:''}</div></div>
      <section class="v515-detail-section v515-synopsis"><h4>あらすじ</h4><p>${esc(info?.synopsis_ja||'詳細未登録')}</p></section>
      <section class="v515-detail-section v515-map-role"><h4>相関図では</h4><p>${esc(info?.map_role_ja||'接続上の説明は未登録です。')}</p></section>
      <div class="v515-detail-actions"><button type="button" data-v515-goal-toggle class="v515-goal-cta ${isGoal?'is-goal':''}">${isGoal?'ゴールから外す':'🎯 ゴールに追加'}</button>${goals.length?'<button type="button" data-v515-return-goals class="v515-return-goals">ゴール表示に戻る</button>':''}</div>
      <div class="v515-prevnext"><div><b>← 前に見る候補</b><div class="v515-work-links">${prev.length?prev.map(e=>link(e.source,nm[e.source]?.title||e.source)).join(''):'<span class="muted">なし</span>'}</div></div><div><b>→ 次に見る候補</b><div class="v515-work-links">${next.length?next.map(e=>link(e.target,nm[e.target]?.title||e.target)).join(''):'<span class="muted">なし</span>'}</div></div></div>
      <details class="v515-meta"><summary>公開情報・分類・接続数</summary><div class="v515-meta-body"><div><b>系統：</b>${esc(n.branch)}</div><div><b>日本公開・配信：</b>${jpinfo}</div><div><b>接続数：</b>入力 ${(inc[id]||[]).length} / 出力 ${(out[id]||[]).length}</div><div>${source}</div></div></details>`;
    detail.querySelector('[data-v515-goal-toggle]')?.addEventListener('click',()=>{window.marvelToggleGoal(id);window.marvelRenderFocusedDetail(id);});
    detail.querySelector('[data-v515-return-goals]')?.addEventListener('click',()=>window.marvelReturnToGoalView());
    detail.querySelectorAll('[data-v515-focus]').forEach(btn=>btn.addEventListener('click',()=>window.marvelFocusWork(btn.dataset.v515Focus,{center:true})));
    return true;
  };

  function renderFocusHighlight(id){
    if(!id||!nm[id])return false;
    clearSvg();
    const svg=activeSvg(); if(!svg)return false;
    const nodeMap=new Map([...svg.querySelectorAll('g.node')].map(g=>[gt(g),g]));
    if(!nodeMap.has(id))return false;
    const part=focusPart(id),ctx=part.nodes||new Set([id]);
    svg.classList.add('dim');
    for(const [wid,g] of nodeMap){
      if(wid===id){g.classList.add('focus','detail-focus');continue;}
      if(!ctx.has(wid))continue;
      g.classList.add('hl');
      if(part.generic){g.classList.add('contexthl');continue;}
      const b=part.backNodes?.has(wid),f=part.forwardNodes?.has(wid),c=part.contextNodes?.has(wid);
      if(b&&f)g.classList.add('bothhl');
      else if(b)g.classList.add('backhl');
      else if(f)g.classList.add('forwardhl');
      else if(c)g.classList.add('contexthl');
    }
    for(const g of svg.querySelectorAll('g.edge:not(.dynamic-edge-overlay)')){
      const k=window.marvelEdgeKeyFromGroup?.(g); if(!k)continue;
      if(part.generic){if(part.contextEdges?.has(k))g.classList.add('hl','contexthl');continue;}
      if(part.backEdges?.has(k))g.classList.add('hl','backhl');
      if(part.forwardEdges?.has(k))g.classList.add('hl','forwardhl');
      if(part.contextEdges?.has(k))g.classList.add('hl','contexthl');
    }
    if(typeof window.marvelRenderFocusedDetail==='function')window.marvelRenderFocusedDetail(id);
    else if(detail){
      const goals=activeGoalIds().length?`<div class="muted">ゴール${activeGoalIds().length}件は保持中</div>`:'';
      detail.innerHTML=`<strong>${esc(nm[id].title)}</strong><div class="muted">詳細表示中（ゴールには追加していません）</div>${goals}`;
    }
    return true;
  }

  function queueFocusPaint(){
    if(!detailFocusId||focusPaintRaf)return;
    focusPaintRaf=requestAnimationFrame(()=>{focusPaintRaf=0;if(detailFocusId)renderFocusHighlight(detailFocusId);});
  }

  window.marvelFocusWork=function(id,{center=true}={}){
    if(!nm[id])return false;
    if(window.marvelFeaturedRouteAudit?.().active)window.exitFeaturedRoutePreview?.({restore:false});
    detailFocusId=id; window.marvelDetailFocusId=id;
    renderFocusHighlight(id);
    if(window.matchMedia('(max-width:760px)').matches)document.getElementById('mobileDetailsBtn')?.click();
    if(center&&activeSvgHasNode(id))requestAnimationFrame(()=>_origCenterNodeInView(id));
    return true;
  };

  window.marvelToggleGoal=function(id){
    if(!nm[id])return false;
    if(window.marvelFeaturedRouteAudit?.().active)window.exitFeaturedRoutePreview?.({restore:false});
    legacyGoalSelect(id,true);
    if(detailFocusId)queueFocusPaint();
    return selectedIds.has(id);
  };

  window.marvelReturnToGoalView=function(){
    detailFocusId=null; window.marvelDetailFocusId=null;
    if(selectedIds.size)refreshSelection(false);
    else{clearSvg();render();resetPanels();}
    return true;
  };

  window.marvelDetailFocusAudit=()=>({focus:detailFocusId,goals:activeGoalIds(),scope:scopeNow(),active:!!detailFocusId});

  // All legacy graph/list/predecessor clicks now inspect instead of changing goals.
  select=function(id){return window.marvelFocusWork(id,{center:false});};

  // Keep focus visually above normal goal redraws.
  const renderBeforeDetailFocus=render;
  render=function(...args){const r=renderBeforeDetailFocus(...args);queueFocusPaint();return r;};
  const refreshBeforeDetailFocus=refreshSelection;
  refreshSelection=function(...args){const r=refreshBeforeDetailFocus(...args);queueFocusPaint();return r;};

  const navigateBeforeDetailFocus=window.navigateSearchResult;
  if(navigateBeforeDetailFocus)window.navigateSearchResult=function(id){
    const ok=navigateBeforeDetailFocus(id);
    if(ok)requestAnimationFrame(()=>window.marvelFocusWork(id,{center:true}));
    return ok;
  };

  // Featured preview is the only state above detail focus. On exit, restore focus first.
  const exitFeaturedBeforeDetailFocus=window.exitFeaturedRoutePreview;
  if(exitFeaturedBeforeDetailFocus)window.exitFeaturedRoutePreview=function(opts={}){
    const restore=opts?.restore!==false;
    const r=exitFeaturedBeforeDetailFocus(opts);
    if(r&&restore&&detailFocusId)queueFocusPaint();
    return r;
  };
  if(window.FEATURED_ROUTE)window.addFeaturedRouteGoal=function(){
    const id=window.FEATURED_ROUTE.targetId;
    if(window.marvelFeaturedRouteAudit?.().active)window.exitFeaturedRoutePreview({restore:false});
    window.marvelFocusWork(id,{center:false});
    if(!selectedIds.has(id))window.marvelToggleGoal(id);
    return true;
  };

  const featuredGoalButton=document.querySelector('[data-featured-action="goal"]');
  if(featuredGoalButton)featuredGoalButton.onclick=()=>window.addFeaturedRouteGoal();

  // PC-only contextmenu shortcut. Blank chart space keeps the browser menu.
  document.addEventListener('contextmenu',e=>{
    if(window.matchMedia('(max-width:760px)').matches)return;
    const node=e.target?.closest?.('.svg-wrap svg g.node'); if(!node)return;
    const id=gt(node); if(!id||!nm[id])return;
    e.preventDefault();
    window.marvelToggleGoal(id);
  },true);

  // All-clear also clears inspection; scope/importance changes repaint inspection afterwards.
  document.addEventListener('click',e=>{
    if(e.target?.closest?.('#clear')){detailFocusId=null;window.marvelDetailFocusId=null;return;}
    if(detailFocusId&&e.target?.closest?.('.scope-btn,.importance-btn'))requestAnimationFrame(()=>renderFocusHighlight(detailFocusId));
  },true);

  document.querySelectorAll('.svg-wrap .zoom-hint').forEach(h=>{
    h.textContent=window.matchMedia('(max-width:760px)').matches
      ? '1本指: 図を移動 / 2本指: 図をズーム / タップ: 詳細'
      : 'ホイール: ズーム / ドラッグ: 移動 / 左クリック: 詳細 / 右クリック: ゴール';
  });
  const detailCard=detail?.closest('.card'),listCard=list?.closest('.card');
  if(detailCard&&listCard&&detailCard.parentElement===listCard.parentElement){
    detailCard.parentElement.insertBefore(detailCard,listCard);
    const h=detailCard.querySelector('h3');if(h)h.textContent='作品詳細';
  }
  const mobileSub=document.querySelector('.mobile-sheet-sub');if(mobileSub)mobileSub.textContent='あらすじ・相関図上の役割・ゴール操作';
  const emptyHint=document.querySelector('[data-ui-role="empty-goal-hint"]');
  if(emptyHint){
    const strong=emptyHint.querySelector('strong');if(strong)strong.textContent='見たい作品をゴールに追加する';
    const muted=emptyHint.querySelector('.muted');if(muted)muted.textContent='作品をタップして詳細を開き、「ゴールに追加」を押してください。';
  }
  window.marvelDetailFocusId=null;
})();
