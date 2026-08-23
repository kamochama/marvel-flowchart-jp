// v5.9.8 mobile UI: collapsible controls + bottom details sheet + mobile graph actions.
(()=>{
  const mq=window.matchMedia('(max-width:760px)');
  const header=document.querySelector('header');
  const controlsBtn=document.getElementById('mobileControlsBtn');
  const detailsBtn=document.getElementById('mobileDetailsBtn');
  const detailsFloat=document.getElementById('mobileDetailsFloat');
  const detailsClose=document.getElementById('mobileDetailsClose');
  const backdrop=document.getElementById('mobileBackdrop');
  const fitBtn=document.getElementById('mobileFitBtn');
  const selectedBtn=document.getElementById('mobileSelectedBtn');
  function setControls(open){
    header?.classList.toggle('controls-open',!!open);
    controlsBtn?.setAttribute('aria-expanded',open?'true':'false');
    if(controlsBtn) controlsBtn.textContent=open?'× 閉じる':'☰ 操作';
  }
  function setDetails(open){
    if(!mq.matches) open=false;
    document.body.classList.toggle('mobile-details-open',!!open);
    detailsBtn?.setAttribute('aria-expanded',open?'true':'false');
    backdrop?.setAttribute('aria-hidden',open?'false':'true');
  }
  controlsBtn?.addEventListener('click',()=>setControls(!header?.classList.contains('controls-open')));
  [detailsBtn,detailsFloat].forEach(b=>b?.addEventListener('click',()=>setDetails(true)));
  [detailsClose,backdrop].forEach(b=>b?.addEventListener('click',()=>setDetails(false)));
  fitBtn?.addEventListener('click',()=>{fitView(activeWrap());});
  selectedBtn?.addEventListener('click',()=>{
    if(selected && activeSvgHasNode(selected)) centerNodeInView(selected);
    else fitView(activeWrap());
  });
  document.querySelectorAll('.tab').forEach(tab=>tab.addEventListener('click',()=>{
    if(mq.matches){ setControls(false); setDetails(false); }
  }));
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){setDetails(false);setControls(false)}});
  mq.addEventListener?.('change',e=>{
    if(!e.matches){setDetails(false);setControls(false)}
    setTimeout(()=>fitView(activeWrap()),80);
  });
  window.addEventListener('orientationchange',()=>setTimeout(()=>fitView(activeWrap()),180));
})();
