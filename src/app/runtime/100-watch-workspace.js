(()=>{
  const right=document.getElementById('right');
  if(!right) return;
  const buttons=[...right.querySelectorAll('.side-tab-btn')];
  const panels=[...right.querySelectorAll('.side-tab-panel')];
  function showSideTab(key){
    buttons.forEach(b=>{const on=b.dataset.sideTab===key;b.classList.toggle('active',on);b.setAttribute('aria-selected',on?'true':'false')});
    panels.forEach(p=>p.classList.toggle('active',p.classList.contains('side-tab-'+key)));
  }
  buttons.forEach(b=>b.addEventListener('click',()=>showSideTab(b.dataset.sideTab)));
  window.marvelShowSideTab=showSideTab;
  // The viewing plan is a full-width workspace below the chart in v5.10.12.
  // Changing its target must not disturb the right-side Works / Links tabs.
})();

  requestAnimationFrame(()=>{try{updateOverallWatchProgress()}catch(_){}});
