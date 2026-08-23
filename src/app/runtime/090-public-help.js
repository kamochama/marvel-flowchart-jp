(()=>{
  const dialog=document.getElementById('publicHelpDialog');
  const open=document.getElementById('publicHelpBtn');
  const close=document.getElementById('publicHelpClose');
  const showHelp=()=>{ if(!dialog)return; if(typeof dialog.showModal==='function') dialog.showModal(); else dialog.setAttribute('open',''); };
  const hideHelp=()=>{ if(!dialog)return; if(typeof dialog.close==='function') dialog.close(); else dialog.removeAttribute('open'); };
  open?.addEventListener('click',showHelp);
  close?.addEventListener('click',hideHelp);
  dialog?.addEventListener('click',e=>{ if(e.target===dialog) hideHelp(); });
  const organizeDynamicControls=()=>{
    const grid=document.querySelector('.advanced-grid'); if(!grid)return;
    const moving=[document.querySelector('.audit-edge-key'),document.getElementById('toggleAuditEdges'),document.querySelector('.fan-edge-key'),document.getElementById('toggleFanVerifiedEdges')].filter(Boolean);
    if(!moving.length)return;
    let group=grid.querySelector('.control-data');
    if(!group){ group=document.createElement('div');group.className='control-group control-data';group.innerHTML='<span class="muted">データ線</span>';grid.appendChild(group); }
    moving.forEach(el=>group.appendChild(el));
  };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',organizeDynamicControls,{once:true}); else organizeDynamicControls();
  document.addEventListener('keydown',e=>{
    if(e.key==='/' && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName||'')){
      e.preventDefault(); const q=document.getElementById('q');
      const header=document.querySelector('header'); if(innerWidth<=760) header?.classList.add('controls-open');
      q?.focus();
    }
  });
})();
