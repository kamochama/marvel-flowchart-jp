// v5.8.1 — fan-verified edges are already in regenerated Graphviz SVGs; toggle only.
(function(){
  let visible=true; const fanEdges=EDGES.filter(e=>e.audit_added==='v5.7.2'&&e.fan_verified);
  function addControls(){
    const controls=document.querySelector('header .controls');if(!controls||document.getElementById('toggleFanVerifiedEdges'))return;
    const key=document.createElement('span');key.className='fan-edge-key';key.innerHTML='<b>ファン図起点・裏取り済み '+fanEdges.length+'本：</b><span class="fan-edge-swatch"></span>検証採用';controls.appendChild(key);
    const btn=document.createElement('button');btn.id='toggleFanVerifiedEdges';btn.className='active';btn.textContent='ファン検証線 ON';btn.title='ファン作成相関図から候補化し、独立検証できた接続を表示／非表示';
    btn.addEventListener('click',()=>{visible=!visible;document.querySelectorAll('g.edge.fan-verified').forEach(g=>g.classList.toggle('fan-hidden',!visible));btn.classList.toggle('active',visible);btn.textContent=visible?'ファン検証線 ON':'ファン検証線 OFF';if(typeof updateSelectionHighlight==='function')updateSelectionHighlight();});controls.appendChild(btn);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',addControls,{once:true});else addControls();
})();
