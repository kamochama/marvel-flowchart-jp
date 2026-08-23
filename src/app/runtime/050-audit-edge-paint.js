// v5.8.1 — audit-added edges are already in regenerated Graphviz SVGs; toggle only.
(function(){
  let visible=true;
  function addControls(){
    const controls=document.querySelector('header .controls'); if(!controls||document.getElementById('toggleAuditEdges'))return;
    const key=document.createElement('span');key.className='audit-edge-key';key.innerHTML='<b>追加監査線 66本：</b><span class="audit-dot story"></span>物語 <span class="audit-dot character"></span>人物 <span class="audit-dot legacy"></span>旧映像 <span class="audit-dot return"></span>Doomsday帰還';controls.appendChild(key);
    const btn=document.createElement('button');btn.id='toggleAuditEdges';btn.className='active';btn.textContent='追加線 ON';btn.title='v5.7.1で再監査追加した66接続を表示／非表示';
    btn.addEventListener('click',()=>{visible=!visible;document.querySelectorAll('g.edge.audit-added').forEach(g=>g.classList.toggle('audit-hidden',!visible));btn.classList.toggle('active',visible);btn.textContent=visible?'追加線 ON':'追加線 OFF';if(typeof updateSelectionHighlight==='function')updateSelectionHighlight();});controls.appendChild(btn);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',addControls,{once:true});else addControls();
})();
