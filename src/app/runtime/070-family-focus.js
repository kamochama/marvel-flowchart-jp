// v5.9.4 — family focus overlay. It deliberately does not rearrange Graphviz nodes.
(()=>{
  const familySelect=document.getElementById('familyFocus');
  if(!familySelect) return;
  function familyOf(id){
    if(['the-avengers-2012','avengers-age-of-ultron-2015','captain-america-civil-war-2016','avengers-infinity-war-2018','avengers-endgame-2019','avengers-doomsday-2026-12-18','avengers-secret-wars-2027-12-17','item-47-2012'].includes(id)) return 'Avengers / 合流点';
    if(id.startsWith('iron-man') || ['the-incredible-hulk-2008','shang-chi-and-the-legend-of-the-ten-rings-2021','she-hulk-attorney-at-law-2022','wonder-man-s1-2026','wonder-man-s2-tba','the-consultant-2011','all-hail-the-king-2014'].includes(id)) return 'Iron Man / Hulk / Ten Rings';
    if(id.startsWith('captain-america') || ['black-widow-2021','the-falcon-and-the-winter-soldier-2021','black-panther-2018','black-panther-wakanda-forever-2022','thunderbolts-new-avengers-2025','ironheart-2025','eyes-of-wakanda-2025','agent-carter-one-shot-2013'].includes(id)) return 'Captain America / Wakanda';
    if(id.startsWith('thor') || id.startsWith('loki-') || id==='a-funny-thing-happened-on-the-way-to-thor-s-hammer-2011') return 'Thor / Loki';
    if(id.startsWith('guardians-of-the-galaxy') || id.startsWith('the-guardians-of-the-galaxy') || id.startsWith('i-am-groot') || ['captain-marvel-2019','the-marvels-2023','ms-marvel-2022','secret-invasion-2023','eternals-2021'].includes(id)) return 'Guardians / Cosmic';
    if(id.startsWith('doctor-strange') || ['wandavision-2021','agatha-all-along-2024','visionquest-2026-10-14','moon-knight-2022','werewolf-by-night-2022','blade-mcu-tba-tba'].includes(id)) return 'Magic / Vision';
    if(id.startsWith('spider-man-') || id.startsWith('your-friendly-neighborhood-spider-man') || ['deadpool-wolverine-2024','the-fantastic-four-first-steps-2025'].includes(id)) return 'Spider-Man / Multiverse';
    if(id.startsWith('ant-man')) return 'Ant-Man';
    if(['hawkeye-2021','echo-2024','daredevil-born-again-s1-2025','daredevil-born-again-s2-2026','daredevil-born-again-s3-tba','the-punisher-one-last-kill-2026-05-12'].includes(id)) return 'Street';
    if(id.startsWith('what-if') || id.startsWith('marvel-zombies') || id.startsWith('x-men-97')) return 'Animation';
    return 'Other';
  }
  window.marvelFamilyOf=familyOf;
  function applyFamilyFocus(){
    const fam=familySelect.value, svg=activeSvg(); if(!svg) return;
    svg.classList.remove('family-mode');
    svg.querySelectorAll('.familyhl,.familyedge').forEach(x=>x.classList.remove('familyhl','familyedge'));
    if(!fam) return;
    let hits=0;
    svg.querySelectorAll('g.node').forEach(g=>{const id=gt(g);if(familyOf(id)===fam){g.classList.add('familyhl');hits++;}});
    svg.querySelectorAll('g.edge').forEach(g=>{const p=(window.marvelEdgeKeyFromGroup?.(g)||'').split('->');if(p.length===2&&familyOf(p[0])===fam&&familyOf(p[1])===fam)g.classList.add('familyedge');});
    // Only dim the active diagram for family browsing when no work selection is active.
    if(hits && (!window.selectedIds || !selectedIds.size)) svg.classList.add('family-mode');
  }
  window.applyFamilyFocus=applyFamilyFocus;
  familySelect.addEventListener('change',()=>{
    if(selectedIds.size) refreshSelection(false); else applyFamilyFocus();
  });
  document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>requestAnimationFrame(()=>{if(!selectedIds.size)applyFamilyFocus();})));
  applyFamilyFocus();
})();
