// PUBLIC v5.14.0 — one panel activation path plus mobile hierarchical navigation.
(()=>{
  const AREA_LABELS={overview:'主要フロー',mcu:'MCU本流',legacy:'マルチバース',road:'ストリート／旧TV',doomsday:'イベント合流',characters:'人物・組織',watch:'予習プラン'};
  const areaButton=document.getElementById('mobileAreaButton');
  const areaSheet=document.getElementById('mobileAreaSheet');
  if(areaSheet&&areaSheet.parentElement!==document.body)document.body.appendChild(areaSheet);
  const desktopSearchHost=document.querySelector('.control-search');
  const mobileSearchHost=document.getElementById('mobileSearchHost');
  const searchInput=document.getElementById('q');

  window.currentPanelId=function(){return document.querySelector('.panel.active')?.id||'overview'};
  window.syncMobileAreaLabel=function(target=currentPanelId()){
    if(!areaButton)return;
    const label=AREA_LABELS[target]||'主要フロー';
    areaButton.innerHTML=`${label} <span aria-hidden="true">▼</span>`;
    document.querySelectorAll('[data-mobile-target]').forEach(b=>b.classList.toggle('active',b.dataset.mobileTarget===target));
  };
  window.openMobileAreaMenu=function(){if(!areaSheet)return;areaSheet.hidden=false;areaButton?.setAttribute('aria-expanded','true');syncMobileAreaLabel();};
  window.closeMobileAreaMenu=function(){if(!areaSheet)return;areaSheet.hidden=true;areaButton?.setAttribute('aria-expanded','false');};
  let mobileSearchResults=document.getElementById('mobileSearchResults');
  if(!mobileSearchResults&&mobileSearchHost){
    mobileSearchResults=document.createElement('div');mobileSearchResults.id='mobileSearchResults';mobileSearchResults.className='mobile-search-results';mobileSearchResults.hidden=true;mobileSearchHost.appendChild(mobileSearchResults);
  }
  window.closeMobileSearchResults=function(){if(mobileSearchResults)mobileSearchResults.hidden=true;};
  window.mountSearchForViewport=function(){
    if(!searchInput)return;
    const mobile=window.matchMedia('(max-width:760px)').matches;
    const host=mobile?mobileSearchHost:desktopSearchHost;
    if(host&&searchInput.parentElement!==host)host.prepend(searchInput);
    searchInput.placeholder=mobile?'作品を検索…':'邦題・英題・シリーズ名で検索';
    if(!mobile)closeMobileSearchResults();
  };
  const SEARCH_PANEL_ORDER=['overview','mcu','road','legacy','doomsday'];
  window.panelHasWork=function(panelId,id){
    const svg=document.querySelector(`#${CSS.escape(panelId)} .svg-wrap svg`);
    return !!svg&&[...svg.querySelectorAll('g.node')].some(g=>gt(g)===id);
  };
  window.preferredPanelForWork=function(id){
    const current=currentPanelId();
    if(SEARCH_PANEL_ORDER.includes(current)&&panelHasWork(current,id))return current;
    return SEARCH_PANEL_ORDER.find(panel=>panelHasWork(panel,id))||null;
  };
  window.flashSearchFocus=function(id){
    const svg=activeSvg();if(!svg)return;
    const node=[...svg.querySelectorAll('g.node')].find(g=>gt(g)===id);if(!node)return;
    node.classList.add('search-focus');setTimeout(()=>node.classList.remove('search-focus'),1100);
  };
  const watchWorkspace=document.getElementById('watchWorkspace');
  window.showWatchWorkspace=function(){
    if(!watchWorkspace)return false;
    document.body.classList.add('mobile-watch-in-view');
    syncMobileAreaLabel('watch');
    watchWorkspace.scrollIntoView({behavior:'smooth',block:'start'});
    return true;
  };
  window.returnToGraphFromWatch=function(){
    document.body.classList.remove('mobile-watch-in-view');
    syncMobileAreaLabel(currentPanelId());
    (document.querySelector('.panel.active .svg-wrap')||document.getElementById('left'))?.scrollIntoView({behavior:'smooth',block:'start'});
    return true;
  };
  let mobileWatchSyncRaf=0;
  window.syncMobileWorkspaceStatus=function(){
    mobileWatchSyncRaf=0;
    if(!watchWorkspace||!window.matchMedia('(max-width:760px)').matches){document.body.classList.remove('mobile-watch-in-view');return;}
    const r=watchWorkspace.getBoundingClientRect();
    const inView=r.top<=innerHeight*.45&&r.bottom>120;
    document.body.classList.toggle('mobile-watch-in-view',inView);
    syncMobileAreaLabel(inView?'watch':currentPanelId());
  };
  const queueMobileWorkspaceSync=()=>{if(!mobileWatchSyncRaf)mobileWatchSyncRaf=requestAnimationFrame(syncMobileWorkspaceStatus);};
  window.addEventListener('scroll',queueMobileWorkspaceSync,{passive:true});
  window.addEventListener('resize',queueMobileWorkspaceSync,{passive:true});

  window.navigateSearchResult=function(id){
    if(!nm[id])return false;
    if(typeof window.exitFeaturedRoutePreview==='function')window.exitFeaturedRoutePreview({restore:true});
    const panel=preferredPanelForWork(id);if(!panel)return false;
    activatePanel(panel,{fit:false,restoreSelection:true,exitFeatured:false});
    requestAnimationFrame(()=>{_origCenterNodeInView(id);flashSearchFocus(id);});
    closeMobileSearchResults();
    return true;
  };
  window.renderMobileSearchResults=function(){
    if(!mobileSearchResults||!window.matchMedia('(max-width:760px)').matches){closeMobileSearchResults();return;}
    const query=(searchInput?.value||'').trim().toLowerCase();
    if(!query){mobileSearchResults.innerHTML='';closeMobileSearchResults();return;}
    const hits=NODES.filter(n=>[n.title,n.title_official,n.title_en,n.branch,n.branch_en].join(' ').toLowerCase().includes(query)).slice(0,6);
    if(!hits.length){mobileSearchResults.innerHTML='<div class="muted" style="padding:8px;font-size:11px">該当する作品がありません</div>';mobileSearchResults.hidden=false;return;}
    mobileSearchResults.innerHTML=hits.map(n=>`<button type="button" class="mobile-search-result" data-search-result="${esc(n.id)}"><strong>${esc(n.title)}</strong><small>${esc(n.title_en)} · ${esc(n.release)}</small></button>`).join('');
    mobileSearchResults.querySelectorAll('[data-search-result]').forEach(btn=>btn.onclick=()=>navigateSearchResult(btn.dataset.searchResult));
    mobileSearchResults.hidden=false;
  };
  window.activatePanel=function(target,{fit=true,restoreSelection=true,exitFeatured=true}={}){
    const panel=document.getElementById(target);
    if(!panel)return false;
    if(exitFeatured&&typeof window.exitFeaturedRoutePreview==='function')window.exitFeaturedRoutePreview({restore:false});
    const tab=document.querySelector(`.tab[data-target="${CSS.escape(target)}"]`);
    document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x===tab));
    document.querySelectorAll('.panel').forEach(x=>x.classList.toggle('active',x===panel));
    syncMobileAreaLabel(target);
    requestAnimationFrame(()=>{
      const wrap=activeWrap();
      if(fit&&wrap)fitView(wrap);
      if(restoreSelection&&selectedIds.size)refreshSelection(false);
      else{clearSvg();applyCharacterHighlight();if(typeof window.applyFamilyFocus==='function')window.applyFamilyFocus();}
    });
    return true;
  };

  document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>activatePanel(b.dataset.target));
  document.querySelectorAll('[data-mobile-target]').forEach(btn=>btn.onclick=()=>{
    activatePanel(btn.dataset.mobileTarget);closeMobileAreaMenu();
    if(window.matchMedia('(max-width:760px)').matches&&document.body.classList.contains('mobile-watch-in-view'))returnToGraphFromWatch();
  });
  areaButton?.addEventListener('click',()=>areaSheet?.hidden?openMobileAreaMenu():closeMobileAreaMenu());
  document.getElementById('mobileAreaClose')?.addEventListener('click',closeMobileAreaMenu);
  areaSheet?.addEventListener('click',e=>{if(e.target===areaSheet)closeMobileAreaMenu();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeMobileAreaMenu();closeMobileSearchResults();}});
  searchInput?.addEventListener('input',renderMobileSearchResults);
  searchInput?.addEventListener('focus',renderMobileSearchResults);
  document.addEventListener('pointerdown',e=>{if(mobileSearchHost&&!mobileSearchHost.contains(e.target))closeMobileSearchResults();});
  const mq=window.matchMedia('(max-width:760px)');
  mq.addEventListener?.('change',()=>{mountSearchForViewport();closeMobileAreaMenu();closeMobileSearchResults();syncMobileWorkspaceStatus();});
  mountSearchForViewport();
  syncMobileAreaLabel();
  queueMobileWorkspaceSync();
})();
