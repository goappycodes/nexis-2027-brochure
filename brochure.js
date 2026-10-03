/* Both views use the same editable content and original eight pages. */
(() => {
  const frames=[...document.querySelectorAll('.page-frame')], zoom=document.querySelector('#zoom'), navigation=document.querySelector('#page-select'), mode=document.querySelector('#view-mode'), previous=document.querySelector('#previous-page'), next=document.querySelector('#next-page');
  let current=1, manuallySelectedMode=false, touchStart;
  const smallScreen=matchMedia('(max-width: 760px)'), reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
  function resize() {
    const available=Math.max(240,innerWidth-(innerWidth<650?24:64));
    frames.forEach(frame=>frame.style.setProperty('--scale',zoom.value==='fit'?Math.min(.5,available/Number(frame.style.getPropertyValue('--page-width'))):Number(zoom.value)));
  }
  function updateNavigation() {
    navigation.value=String(current); previous.disabled=current===1; next.disabled=current===frames.length;
    frames.forEach((frame,i)=>{ frame.classList.toggle('is-active',i+1===current); frame.inert=mode.value==='flipbook'&&i+1!==current; });
  }
  function goToPage(number,scroll=true) {
    current=Math.max(1,Math.min(frames.length,Number(number))); updateNavigation();
    if(scroll) frames[current-1].scrollIntoView({behavior:reducedMotion.matches?'instant':'smooth',block:'start'});
    document.querySelector('#page-announcement').textContent=navigation.selectedOptions[0].textContent;
  }
  function setMode(value,scroll=false) {
    mode.value=value; document.documentElement.dataset.view=value; zoom.disabled=value==='reading'; updateNavigation(); resize(); if(scroll)goToPage(current);
  }
  mode.addEventListener('change',()=>{ manuallySelectedMode=true;setMode(mode.value,true); });
  zoom.addEventListener('change',resize); window.addEventListener('resize',resize);
  smallScreen.addEventListener('change',()=>{if(!manuallySelectedMode)setMode(smallScreen.matches?'reading':'flipbook',true);});
  navigation.addEventListener('change',()=>goToPage(navigation.value));
  previous.addEventListener('click',()=>goToPage(current-1)); next.addEventListener('click',()=>goToPage(current+1));
  document.querySelector('#print').addEventListener('click',()=>window.print());
  document.addEventListener('keydown',event=>{
    if(mode.value!=='flipbook'||/INPUT|TEXTAREA|SELECT|BUTTON/.test(event.target.tagName))return;
    if(event.key==='ArrowRight'){event.preventDefault();goToPage(current+1);}
    if(event.key==='ArrowLeft'){event.preventDefault();goToPage(current-1);}
  });
  const main=document.querySelector('.brochure');
  main.addEventListener('touchstart',event=>{touchStart=event.touches.length===1?{x:event.touches[0].clientX,y:event.touches[0].clientY}:null;},{passive:true});
  main.addEventListener('touchend',event=>{
    if(!touchStart||mode.value!=='flipbook'||zoom.value!=='fit')return;
    const dx=event.changedTouches[0].clientX-touchStart.x,dy=event.changedTouches[0].clientY-touchStart.y;touchStart=null;
    if(Math.abs(dx)>70&&Math.abs(dx)>Math.abs(dy)*1.5)goToPage(current+(dx<0?1:-1));
  },{passive:true});
  const observer=new IntersectionObserver(entries=>{
    if(document.documentElement.dataset.view!=='reading')return;
    const visible=entries.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];
    if(visible){current=Number(visible.target.dataset.page);updateNavigation();}
  },{rootMargin:'-100px 0px -35% 0px',threshold:[0,.1,.25,.5]});
  frames.forEach(frame=>observer.observe(frame));
  window.addEventListener('beforeprint',()=>frames.forEach(frame=>frame.inert=false));window.addEventListener('afterprint',updateNavigation);
  setMode(document.documentElement.dataset.view||(smallScreen.matches?'reading':'flipbook'));
  document.fonts.ready.then(()=>document.documentElement.dataset.ready='true');
})();
