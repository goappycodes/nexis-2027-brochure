/* Responsive flipbook: desktop spreads and one page on phones. */
(() => {
  const frames=[...document.querySelectorAll('.page-frame')], zoom=document.querySelector('#zoom'), navigation=document.querySelector('#page-select'), previous=document.querySelector('#previous-page'), next=document.querySelector('#next-page'), counter=document.querySelector('#spread-counter');
  const desktop=matchMedia('(min-width: 900px)'), reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
  const main=document.querySelector('.brochure'), toolbar=document.querySelector('.viewer-toolbar');
  let current=1,touchStart;
  const spreadSize=()=>desktop.matches?2:1;
  const spreadStart=()=>Math.floor((current-1)/spreadSize())*spreadSize()+1;
  function resize() {
    const columns=spreadSize();
    document.documentElement.dataset.spread=String(columns);
    if(!desktop.matches)zoom.value='fit';
    const layout=getComputedStyle(main), gap=columns===2?parseFloat(layout.columnGap):0;
    const availableWidth=Math.max(1,innerWidth-(columns===2?120:24)-gap);
    const availableHeight=Math.max(1,innerHeight-toolbar.getBoundingClientRect().height-parseFloat(layout.paddingTop)-parseFloat(layout.paddingBottom));
    frames.forEach(frame=>{
      const style=getComputedStyle(frame), width=Number(style.getPropertyValue('--page-width')), height=Number(style.getPropertyValue('--page-height'));
      const fitScale=Math.min(availableWidth/(width*columns),desktop.matches?availableHeight/height:Infinity);
      frame.style.setProperty('--scale',zoom.value==='fit'?fitScale:Number(zoom.value));
    });
  }
  function updateNavigation() {
    const start=spreadStart(),end=Math.min(frames.length,start+spreadSize()-1);
    navigation.value=String(current);previous.disabled=start===1;next.disabled=end===frames.length;
    counter.textContent=start===end?`${start} / ${frames.length}`:`${start}–${end} / ${frames.length}`;
    frames.forEach((frame,i)=>{const active=i+1>=start&&i+1<=end;frame.classList.toggle('is-active',active);frame.inert=false;});
  }
  function goToPage(number,scroll=true) {
    current=Math.max(1,Math.min(frames.length,Number(number)));updateNavigation();
    if(scroll)window.scrollTo({top:0,behavior:reducedMotion.matches?'instant':'smooth'});
    document.querySelector('#page-announcement').textContent=`Pages ${counter.textContent}`;
  }
  zoom.addEventListener('change',resize);
  window.addEventListener('resize',()=>{resize();updateNavigation();});
  navigation.addEventListener('change',()=>goToPage(navigation.value));
  previous.addEventListener('click',()=>goToPage(spreadStart()-spreadSize()));next.addEventListener('click',()=>goToPage(spreadStart()+spreadSize()));
  document.addEventListener('keydown',event=>{
    if(/INPUT|TEXTAREA|SELECT|BUTTON/.test(event.target.tagName))return;
    if(event.key==='ArrowRight'){event.preventDefault();goToPage(spreadStart()+spreadSize());}
    if(event.key==='ArrowLeft'){event.preventDefault();goToPage(spreadStart()-spreadSize());}
  });
  main.addEventListener('touchstart',event=>{touchStart=event.touches.length===1?{x:event.touches[0].clientX,y:event.touches[0].clientY}:null;},{passive:true});
  main.addEventListener('touchend',event=>{
    if(!touchStart||zoom.value!=='fit'||(window.visualViewport?.scale||1)>1.01)return;
    const dx=event.changedTouches[0].clientX-touchStart.x,dy=event.changedTouches[0].clientY-touchStart.y;touchStart=null;
    if(Math.abs(dx)>70&&Math.abs(dx)>Math.abs(dy)*1.5)goToPage(spreadStart()+(dx<0?spreadSize():-spreadSize()));
  },{passive:true});
  document.querySelector('#print').addEventListener('click',async()=>{
    const button=document.querySelector('#print');button.disabled=true;document.documentElement.dataset.view='pages';
    await document.fonts.ready;
    await Promise.all([...document.querySelectorAll('object')].map(object=>object.contentDocument?.readyState==='complete'?Promise.resolve():new Promise(resolve=>{
      const timer=setTimeout(resolve,15000);object.addEventListener('load',()=>{clearTimeout(timer);resolve();},{once:true});object.addEventListener('error',()=>{clearTimeout(timer);resolve();},{once:true});
    })));
    window.print();document.documentElement.dataset.view='flipbook';button.disabled=false;
  });
  window.addEventListener('beforeprint',()=>frames.forEach(frame=>frame.inert=false));window.addEventListener('afterprint',updateNavigation);
  new ResizeObserver(resize).observe(toolbar);
  resize();updateNavigation();document.fonts.ready.then(()=>{resize();document.documentElement.dataset.ready='true';});
})();
