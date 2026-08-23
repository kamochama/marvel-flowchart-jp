// v5.6: full connected-component focus + ordered preparation plan
const CURATED_ROUTES_V56 = [{"route": "Spider-Man / Multiverse", "route_ja": "スパイダーマン／マルチバース", "ids": ["captain-america-civil-war-2016", "spider-man-homecoming-2017", "avengers-infinity-war-2018", "avengers-endgame-2019", "spider-man-far-from-home-2019", "spider-man-no-way-home-2021", "doctor-strange-in-the-multiverse-of-madness-2022", "spider-man-brand-new-day-2026-07-31"]}, {"route": "Wanda / Vision / 魔術", "route_ja": "ワンダ／ヴィジョン／魔術", "ids": ["avengers-age-of-ultron-2015", "captain-america-civil-war-2016", "avengers-infinity-war-2018", "avengers-endgame-2019", "wandavision-2021", "doctor-strange-in-the-multiverse-of-madness-2022", "agatha-all-along-2024", "visionquest-2026-10-14"]}, {"route": "Daredevil / Street-level", "route_ja": "デアデビル／ストリート系", "ids": ["daredevil-s1-2015", "daredevil-s2-2016", "the-punisher-s1-2017", "the-defenders-2017", "daredevil-s3-2018", "the-punisher-s2-2019", "hawkeye-2021", "echo-2024", "daredevil-born-again-s1-2025", "daredevil-born-again-s2-2026", "the-punisher-one-last-kill-2026-05-12"]}, {"route": "X-Men / Deadpool", "route_ja": "X-MEN／デッドプール", "ids": ["x-men-2000", "x2-x-men-united-2003", "x-men-the-last-stand-2006", "x-men-first-class-2011", "x-men-days-of-future-past-2014", "the-wolverine-2013", "deadpool-2016", "logan-2017", "deadpool-2-2018", "deadpool-wolverine-2024", "avengers-doomsday-2026-12-18"]}, {"route": "Doomsday 最短準備", "route_ja": "『アベンジャーズ／ドゥームズデイ』最短準備", "ids": ["avengers-endgame-2019", "wandavision-2021", "loki-s1-2021", "loki-s2-2023", "spider-man-no-way-home-2021", "deadpool-wolverine-2024", "thunderbolts-new-avengers-2025", "the-fantastic-four-first-steps-2025", "spider-man-brand-new-day-2026-07-31", "avengers-doomsday-2026-12-18", "avengers-secret-wars-2027-12-17"]}];
const prepplan = document.getElementById('prepplan');
let scopeMode = 'all';

// Simple click is now a toggle. Re-click removes the work.
// Clicking additional works naturally creates a multi-selection.
toggleSelectionState = function(id, multi=false){
  if(selectedIds.has(id)){
    selectedIds.delete(id);
    if(selected===id) normalizeSelection();
  }else{
    selectedIds.add(id);
    selected=id;
  }
};

function connectedComponent(start){
  const seen=new Set([start]), stack=[start];
  while(stack.length){
    const x=stack.pop();
    for(const e of (inc[x]||[])){
      if(!seen.has(e.source)){seen.add(e.source);stack.push(e.source)}
    }
    for(const e of (out[x]||[])){
      if(!seen.has(e.target)){seen.add(e.target);stack.push(e.target)}
    }
  }
  return seen;
}

selectionNeighborhood = function(){
  const ctx=new Set();
  for(const id of selectedIds){
    const part = scopeMode==='all' ? connectedComponent(id) : neighborhood(id, scopeMode==='two'?2:1);
    for(const x of part) ctx.add(x);
  }
  return ctx;
};

// Show the connected set even on a tab where the originally selected node itself
// is not present. This makes the whole relationship visible across diagrams.
hilite = function(){
  clearSvg();
  if(!selectedIds.size) return;
  const ctx=selectionNeighborhood();
  document.querySelectorAll('.panel.active .svg-wrap svg').forEach(svg=>{
    const ns=[...svg.querySelectorAll('g.node')], es=[...svg.querySelectorAll('g.edge')];
    const hasContext=ns.some(g=>ctx.has(gt(g)));
    if(!hasContext) return;
    svg.classList.add('dim');
    ns.forEach(g=>{
      const id=gt(g);
      if(selectedIds.has(id)) g.classList.add('focus');
      else if(ctx.has(id)) g.classList.add('hl');
    });
    es.forEach(g=>{
      const p=gt(g).split('->');
      if(p.length===2 && ctx.has(p[0]) && ctx.has(p[1])) g.classList.add('hl');
    });
  });
};

function releaseKey(id){
  const n=nm[id];
  if(!n) return 99999999;
  const s=n.release_raw||'';
  const m=s.match(/(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?/);
  if(!m) return 99999999;
  return Number(m[1])*10000 + Number(m[2]||1)*100 + Number(m[3]||1);
}
function sortByRelease(ids){
  return [...ids].sort((a,b)=>releaseKey(a)-releaseKey(b) || (nm[a]?.title||a).localeCompare(nm[b]?.title||b,'ja'));
}
function strongAncestorSet(target){
  const seen=new Set(), stack=[target];
  while(stack.length){
    const x=stack.pop();
    for(const e of (inc[x]||[])){
      if(edgeRank(e)>=3 && !seen.has(e.source)){
        seen.add(e.source);
        stack.push(e.source);
      }
    }
  }
  seen.delete(target);
  return seen;
}
function topologicalPreparationOrder(ids){
  const set=new Set(ids);
  const indeg=new Map([...set].map(x=>[x,0]));
  const fwd=new Map([...set].map(x=>[x,[]]));
  for(const e of EDGES){
    if(set.has(e.source)&&set.has(e.target)&&edgeRank(e)>=3){
      fwd.get(e.source).push(e.target);
      indeg.set(e.target,(indeg.get(e.target)||0)+1);
    }
  }
  let ready=sortByRelease([...set].filter(x=>(indeg.get(x)||0)===0));
  const outOrder=[];
  while(ready.length){
    const x=ready.shift(); outOrder.push(x);
    for(const y of fwd.get(x)||[]){
      indeg.set(y,indeg.get(y)-1);
      if(indeg.get(y)===0){ ready.push(y); ready=sortByRelease(ready); }
    }
  }
  if(outOrder.length!==set.size){
    return sortByRelease(set);
  }
  return outOrder;
}
function chooseCuratedRoute(target){
  const candidates=[];
  const title=((nm[target]?.title_en||'')+' '+(nm[target]?.title||'')).toLowerCase();
  function affinity(r){
    const name=(r.route||'').toLowerCase();
    let s=0;
    if((title.includes('spider-man')||title.includes('スパイダーマン')) && name.includes('spider-man')) s+=100;
    if((title.includes('wanda')||title.includes('vision')||title.includes('agatha')||title.includes('doctor strange')||title.includes('ワンダ')||title.includes('ヴィジョン')||title.includes('アガサ')||title.includes('ドクター・ストレンジ')) && name.includes('wanda')) s+=100;
    if((title.includes('daredevil')||title.includes('punisher')||title.includes('hawkeye')||title.includes('echo')||title.includes('デアデビル')||title.includes('パニッシャー')||title.includes('ホークアイ')||title.includes('エコー')) && name.includes('daredevil')) s+=100;
    if((title.includes('x-men')||title.includes('deadpool')||title.includes('logan')||title.includes('wolverine')||title.includes('x-men')||title.includes('デッドプール')||title.includes('ローガン')||title.includes('ウルヴァリン')) && name.includes('x-men')) s+=100;
    if((title.includes('doomsday')||title.includes('secret wars')||title.includes('ドゥームズデイ')) && name.includes('doomsday')) s+=150;
    return s;
  }
  for(const r of CURATED_ROUTES_V56){
    const i=r.ids.indexOf(target);
    if(i>0) candidates.push({route:r,index:i,score:affinity(r)});
  }
  if(!candidates.length) return null;
  candidates.sort((a,b)=>b.score-a.score || b.index-a.index || a.route.ids.length-b.route.ids.length);
  return candidates[0];
}
function buildPreparationPlan(target){
  const curated=chooseCuratedRoute(target);
  if(curated){
    return {
      ids: curated.route.ids.slice(0,curated.index),
      source: `監査済み推奨ルート「${curated.route.route_ja}」を使用`,
      kind:'curated'
    };
  }
  const strong=strongAncestorSet(target);
  let ids=topologicalPreparationOrder(strong);

  // If there is no strong lineage, add direct medium connections as useful context.
  if(!ids.length){
    ids=sortByRelease((inc[target]||[]).filter(e=>edgeRank(e)>=2).map(e=>e.source));
  }
  return {
    ids,
    source:'監査済み接続表の strong / very strong 接続から自動生成',
    kind:'graph'
  };
}
function updatePreparationPlan(){
  if(!selectedIds.size || !selected){
    prepplan.textContent='見たい作品を選ぶと、予習した方がよい作品をおすすめ順に並べます。';
    return;
  }
  const target=selected;
  const plan=buildPreparationPlan(target);
  const targetNode=nm[target];
  if(!plan.ids.length){
    prepplan.innerHTML=`<strong>${esc(targetNode?.title||target)}</strong><p class="muted">監査済みデータ上、事前に見ることを強く勧める作品はありません。</p><div class="prep-goal">🎯 視聴目標：${esc(targetNode?.title||target)}</div><div class="prep-source">${esc(plan.source)}</div>`;
    return;
  }
  prepplan.innerHTML=`<div><strong>${esc(targetNode?.title||target)} の予習順</strong>${selectedIds.size>1?'<div class="muted">※複数ゴールは統合予習プランとして扱います。</div>':''}</div>
  <ol class="prep-list">${plan.ids.map((id,i)=>`<li class="prep-item"><span class="prep-num">${i+1}</span><div><a href="#" class="prep-link" data-id="${id}" style="color:#e5e7eb;text-decoration:none"><strong>${esc(nm[id]?.title||id)}</strong></a><div class="muted">${esc(nm[id]?.release||'')}</div></div></li>`).join('')}</ol>
  <div class="prep-goal">🎯 ${plan.ids.length+1}. 視聴目標：<strong>${esc(targetNode?.title||target)}</strong></div>
  <div class="prep-source">${esc(plan.source)}。これは「絶対必須」ではなく、物語を追いやすくするための予習順です。</div>`;
  prepplan.querySelectorAll('.prep-link').forEach(x=>x.onclick=e=>{
    e.preventDefault();
    const id=x.dataset.id;
    if(!selectedIds.has(id)) selectedIds.add(id);
    selected=id;
    refreshSelection(true);
  });
}

const _resetPanels_v55 = resetPanels;
resetPanels = function(message='作品を選ぶと前後の接続を表示します。'){
  _resetPanels_v55(message);
  if(prepplan) prepplan.textContent='見たい作品を選ぶと、予習した方がよい作品をおすすめ順に並べます。';
};

document.querySelectorAll('.scope-btn').forEach(btn=>{
  btn.onclick=()=>{
    document.querySelectorAll('.scope-btn').forEach(x=>x.classList.remove('active'));
    btn.classList.add('active');
    scopeMode=btn.dataset.scope;
    if(selectedIds.size) refreshSelection(false);
    else {clearSvg();render();}
  };
});

// Tabs use the same selection recompute/render route as graph clicks.
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  document.getElementById(b.dataset.target).classList.add('active');
  requestAnimationFrame(()=>{
    fitView(activeWrap());
    if(selectedIds.size) refreshSelection(false);
    else { clearSvg(); applyCharacterHighlight(); if(typeof applyFamilyFocus==='function') applyFamilyFocus(); }
  });
});

installMultiSelectPatch();
updatePreparationPlan();
render();
