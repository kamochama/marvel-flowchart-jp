// v5.5 patch: deselect on second click + multi-select with Ctrl/Cmd/Shift
var selectedIds = new Set();
const _origCenterNodeInView = centerNodeInView;
centerNodeInView = function(id){
  if(!selectedIds.size) return false;
  const target = id || selected;
  if(!target || !selectedIds.has(target)) return false;
  return _origCenterNodeInView(target);
};
function orderedSelectedIds(){ return [...selectedIds]; }
function selectionNeighborhood(){ const ctx=new Set(); for(const id of selectedIds){ for(const x of neighborhood(id,hop)) ctx.add(x); } return ctx; }
function normalizeSelection(){ if(selected && selectedIds.has(selected)) return; selected = orderedSelectedIds().slice(-1)[0] || null; }
function orderedGoalIds(){ return [...selectedIds]; }
function focusGoal(id){ if(!selectedIds.has(id)) return false; selected=id; refreshSelection(false); return true; }
function removeGoal(id){ if(!selectedIds.has(id)) return false; selectedIds.delete(id); if(selected===id) normalizeSelection(); refreshSelection(false); return true; }
function resetPanels(message='作品を選ぶと前後の接続を表示します。'){
  detail.textContent=message;
  flow.textContent='作品を選ぶと、「前に見る候補」「次に見る候補」を表示します。';
  et.innerHTML='';
}
function toggleSelectionState(id,multi=false){
  if(multi){
    if(selectedIds.has(id)){ selectedIds.delete(id); if(selected===id) normalizeSelection(); }
    else { selectedIds.add(id); selected=id; }
  }else{
    if(selectedIds.size===1 && selectedIds.has(id)){ selectedIds.clear(); selected=null; }
    else { selectedIds = new Set([id]); selected=id; }
  }
}
function mergeUniqueEdges(arr){ const m=new Map(); for(const e of arr){ m.set(`${e.source}|${e.target}|${e.type}|${e.strength}`, e); } return [...m.values()]; }
function unionEdgesForSelection(kind){ const gathered=[]; for(const id of selectedIds){ const arr = kind==='in' ? (inc[id]||[]) : (out[id]||[]); for(const e of arr) gathered.push(e); } return mergeUniqueEdges(gathered); }
function selectionSummaryHtml(){ const ids=orderedSelectedIds(); if(ids.length<=1) return ''; return `<p><b>複数ゴール中 (${ids.length})：</b><br>${ids.map(x=>`<span class="badge seljump" data-id="${x}" style="cursor:pointer">${esc(nm[x]?.title||x)}</span>`).join(' ')}</p>`; }
render = function(){
  let a=NODES.filter(pass).sort((x,y)=>x.title.localeCompare(y.title,'ja'));
  const hasSel=selectedIds.size>0;
  const ctx=hasSel?selectionNeighborhood():new Set();
  if(hasSel){ const inCtx=a.filter(n=>ctx.has(n.id)); const outCtx=a.filter(n=>!ctx.has(n.id)); a=[...inCtx,...outCtx]; }
  count.textContent=`${a.length} / ${NODES.length} 作品`;
  list.innerHTML=a.map(n=>{
    const isSelected=selectedIds.has(n.id); const isRelated=hasSel && ctx.has(n.id);
    const faded=(hasSel && !isRelated) ? ' style="opacity:.28"' : '';
    const marker=isSelected?'<span class="badge">ゴール</span>':(isRelated?'<span class="badge">関連</span>':'');
    const cls=isSelected?'selected':'';
    return `<div class="node-item ${cls}" data-id="${n.id}"${faded}><strong>${esc(n.title)}</strong>${n.source_url?'<span class="badge">公式ソース</span>':''}${marker}<div class="muted">${esc(n.title_en)} / ${esc(n.release)}</div></div>`;
  }).join('')||'<div class="node-item muted">該当なし</div>';
  list.querySelectorAll('[data-id]').forEach(x=>x.onclick=(e)=>select(x.dataset.id, e.ctrlKey||e.metaKey||e.shiftKey));
  if(cf.value){ let ws=[...(charWorks[cf.value]||[])]; charinfo.innerHTML=`<strong>${esc(cf.value)}</strong><br>主要出演・接続作品：${ws.length}件<br><span class="muted">※網羅的な全カメオ表ではなく、相関図を追うための主要出演・接続索引です。</span>` }
  else { charinfo.textContent='上部のキャラクター欄から選ぶと、主要出演・物語接続作品だけに絞り込みます。' }
  applyCharacterHighlight();
};
applyCharacterHighlight = function(){
  const svg=activeSvg(); if(!svg) return;
  svg.classList.remove('char-mode');
  svg.querySelectorAll('.charhl').forEach(x=>x.classList.remove('charhl'));
  if(!cf.value) return;
  const ids=charWorks[cf.value]||new Set(); let hits=0;
  svg.querySelectorAll('g.node').forEach(g=>{ const id=gt(g); if(ids.has(id)){ g.classList.add('charhl'); hits++; } });
  if(hits && !selectedIds.size) svg.classList.add('char-mode');
};
hilite = function(){
  clearSvg();
  if(!selectedIds.size) return;
  const ctx=selectionNeighborhood();
  document.querySelectorAll('.panel.active .svg-wrap svg').forEach(svg=>{
    const ns=[...svg.querySelectorAll('g.node')], es=[...svg.querySelectorAll('g.edge')], ids=new Set(ns.map(gt));
    const selHere=orderedSelectedIds().some(id=>ids.has(id));
    if(!selHere) return;
    svg.classList.add('dim');
    ns.forEach(g=>{ const x=gt(g); if(selectedIds.has(x)) g.classList.add('focus'); else if(ctx.has(x)) g.classList.add('hl'); });
    es.forEach(g=>{ const p=gt(g).split('->'); if(p.length===2 && ctx.has(p[0]) && ctx.has(p[1])) g.classList.add('hl'); });
  });
};
function refreshSelection(center=true){
  normalizeSelection();
  render();
  if(!selectedIds.size || !selected){ clearSvg(); resetPanels(); return; }
  const ids=orderedSelectedIds(); const n=nm[selected];
  const ins=unionEdgesForSelection('in'); const outs=unionEdgesForSelection('out');
  const ancSet=new Set(); for(const id of ids){ for(const a of ancestors(id)) ancSet.add(a); }
  const anc=[...ancSet]; const direct=[...new Set(ins.filter(e=>e.strength==='strong'||e.strength==='very strong').map(e=>e.source))];
  const jpinfo=n.japan_date?`<p><b>日本公開・配信情報：</b><br>${esc(n.japan_date)}　${esc(n.japan_type)}</p>`:'<p class="muted">日本公開・配信日の公式確認データは未登録です。</p>';
  const source=n.source_url?`<p><a href="${esc(n.source_url)}" target="_blank" rel="noopener" style="color:#60a5fa">日本向け公式ソースを開く ↗</a><br><span class="muted">${esc(n.source_note)}</span></p>`:'';
  detail.innerHTML=`<strong>${esc(n.title)}</strong><div class="muted">現在の図では関連作品だけ点灯中</div><div class="muted">${esc(n.title_en)} / ${esc(n.release)}</div><p><span class="badge">${esc(n.branch)}</span><span class="badge">${esc(n.ja_status)}</span>${selectedIds.size>1?'<span class="badge">複数ゴール</span>':''}</p>${n.ja_status==='unannounced'?'<p class="warn">日本公式の邦題未発表として扱っています。</p>':''}${jpinfo}${source}${selectionSummaryHtml()}<p><b>直接の強い前提候補：</b><br>${direct.length?direct.map(x=>`<span class="badge pre" data-id="${x}" style="cursor:pointer">${esc(nm[x]?.title||x)}</span>`).join(' '):'<span class="muted">なし</span>'}</p><p><b>強い接続を遡った前提候補：</b><br>${anc.length?anc.slice(0,20).map(x=>`<span class="badge pre" data-id="${x}" style="cursor:pointer">${esc(nm[x]?.title||x)}</span>`).join(' '):'<span class="muted">なし</span>'}</p><p><b>ゴール数：</b> ${selectedIds.size} / <b>接続数：</b>入力 ${ins.length} / 出力 ${outs.length}</p>`;
  detail.querySelectorAll('.pre').forEach(x=>x.onclick=(e)=>select(x.dataset.id, e.ctrlKey||e.metaKey||e.shiftKey));
  detail.querySelectorAll('.seljump').forEach(x=>x.onclick=()=>{ selected=x.dataset.id; refreshSelection(true); });
  let prevCand=(ins.filter(e=>edgeRank(e)>=3).sort((a,b)=>edgeRank(b)-edgeRank(a))); if(!prevCand.length) prevCand=ins.slice().sort((a,b)=>edgeRank(b)-edgeRank(a));
  let nextCand=(outs.filter(e=>edgeRank(e)>=3).sort((a,b)=>edgeRank(b)-edgeRank(a))); if(!nextCand.length) nextCand=outs.slice().sort((a,b)=>edgeRank(b)-edgeRank(a));
  prevCand=mergeUniqueEdges(prevCand).slice(0,10); nextCand=mergeUniqueEdges(nextCand).slice(0,10);
  flow.innerHTML=`<div><b>← 前に見る候補</b><br>${prevCand.length?prevCand.map(e=>`<span class="badge flowlink" data-id="${e.source}" style="cursor:pointer">${esc(nm[e.source]?.title||e.source)}</span>`).join(' '):'<span class="muted">なし</span>'}</div><hr style="border:none;border-top:1px solid #334155;margin:10px 0"><div><b>→ 次に見る候補</b><br>${nextCand.length?nextCand.map(e=>`<span class="badge flowlink" data-id="${e.target}" style="cursor:pointer">${esc(nm[e.target]?.title||e.target)}</span>`).join(' '):'<span class="muted">なし</span>'}</div><p class="muted">※ 複数ゴール中は各作品の接続候補をまとめて表示。まず strong / very strong 接続を優先表示。</p>`;
  flow.querySelectorAll('.flowlink').forEach(x=>x.onclick=(e)=>select(x.dataset.id, e.ctrlKey||e.metaKey||e.shiftKey));
  const rr=mergeUniqueEdges([...ins,...outs]);
  et.innerHTML=rr.map(e=>`<tr><td>${esc(nm[e.source]?.title||e.source)}</td><td>${esc(nm[e.target]?.title||e.target)}</td><td>${esc(displayEdgeType(e))}</td><td>${esc(e.strength)}</td></tr>`).join('')||'<tr><td colspan="4" class="muted">接続なし</td></tr>';
  hilite();
  if(center && selected && activeSvgHasNode(selected)) setTimeout(()=>_origCenterNodeInView(selected),20);
}
select = function(id,multi=false){ toggleSelectionState(id,multi); refreshSelection(false); };
function installMultiSelectPatch(){
  document.querySelectorAll('.svg-wrap').forEach(wrap=>{
    const hint=wrap.querySelector('.zoom-hint');
    if(hint) hint.textContent=window.matchMedia('(max-width:760px)').matches ? '1本指: 図を移動 / 2本指: 図をズーム / タップ: ゴール追加・解除' : 'チャート上のホイール: 図をズーム / ドラッグ: 図を移動 / クリック: ゴール追加・解除';
  });
}
cf.addEventListener('change',e=>{
  e.stopImmediatePropagation();
  if(cf.value && selectedIds.size){
    const allowed=charWorks[cf.value]||new Set();
    selectedIds = new Set(orderedSelectedIds().filter(id=>allowed.has(id)));
    normalizeSelection();
    if(!selectedIds.size){ clearSvg(); render(); resetPanels('キャラクターを選択中です。図上で関連作品が点灯します。'); return; }
    refreshSelection(false); return;
  }
  render(); applyCharacterHighlight();
}, true);
document.querySelectorAll('.hop').forEach(b=>b.onclick=()=>{ document.querySelectorAll('.hop').forEach(x=>x.classList.remove('active')); b.classList.add('active'); hop=Number(b.dataset.hop); if(selectedIds.size) refreshSelection(false); else { clearSvg(); render(); } });
document.getElementById('clear').onclick=()=>{ selected=null; selectedIds=new Set(); q.value=''; bf.value=''; cf.value=''; sf.value=''; refreshSelection(false); };
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{ document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active')); document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active')); b.classList.add('active'); document.getElementById(b.dataset.target).classList.add('active'); requestAnimationFrame(()=>{ fitView(activeWrap()); if(selectedIds.size) refreshSelection(false); else { clearSvg(); applyCharacterHighlight(); if(typeof applyFamilyFocus==='function') applyFamilyFocus(); } }); });
document.getElementById('zoomSelected').onclick=()=>{ if(selectedIds.size && selected) _origCenterNodeInView(selected); else fitView(activeWrap()); };
installMultiSelectPatch();
resetPanels();
render();
