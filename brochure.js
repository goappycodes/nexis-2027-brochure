/* Responsive flipbook: desktop spreads and one page on phones. */
(() => {
  const frames=[...document.querySelectorAll('.page-frame')], zoom=document.querySelector('#zoom'), navigation=document.querySelector('#page-select'), previous=document.querySelector('#previous-page'), next=document.querySelector('#next-page'), counter=document.querySelector('#spread-counter');
  const desktop=matchMedia('(min-width: 900px)'), reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
  const main=document.querySelector('.brochure'), toolbar=document.querySelector('.viewer-toolbar');
  let current=1,touchStart;
  const pendingPages=new WeakMap();
  const pendingAssets=new WeakMap();
  const fontsReady=Promise.all([...document.fonts].map(font=>font.load()));
  function loadAsset(asset) {
    if(pendingAssets.has(asset))return pendingAssets.get(asset);
    const source=asset.dataset.src;
    if(!source)return Promise.resolve();
    const object=asset.tagName==='OBJECT';
    const isReady=()=>object
      ? asset.contentDocument?.documentElement?.localName==='svg'&&asset.contentDocument.readyState==='complete'
      : asset.complete&&asset.naturalWidth>0;
    const decode=async()=>{
      // An object's load event includes its SVG's dependent images. Decoding
      // every image in <defs> would also fetch unused extraction leftovers.
      if(!object&&asset.decode)await asset.decode();
    };
    if(asset.getAttribute(object?'data':'src')===source&&isReady())return decode();
    // Replacing a failed object forces a fresh request for the same URL.
    if(asset.getAttribute(object?'data':'src')===source) {
      const replacement=asset.cloneNode(true);replacement.removeAttribute(object?'data':'src');
      asset.replaceWith(replacement);return loadAsset(replacement);
    }
    const promise=new Promise((resolve,reject)=>{
      const cleanup=()=>{clearTimeout(timer);asset.removeEventListener('load',loaded);asset.removeEventListener('error',failed);};
      const failed=()=>{cleanup();reject(new Error(`Could not load ${source}`));};
      const loaded=()=>{
        if(!isReady()){failed();return;}
        cleanup();decode().then(resolve,reject);
      };
      const timer=setTimeout(failed,45000);
      asset.addEventListener('load',loaded);asset.addEventListener('error',failed);
      asset.setAttribute(object?'data':'src',source);
    }).catch(error=>{pendingAssets.delete(asset);throw error;});
    pendingAssets.set(asset,promise);return promise;
  }
  frames.forEach(frame=>{
    const loader=document.createElement('div');loader.className='page-loader';
    const spinner=document.createElement('span');spinner.className='page-loader-spinner';spinner.setAttribute('aria-hidden','true');
    const message=document.createElement('span');message.setAttribute('role','status');
    const retry=document.createElement('button');retry.type='button';retry.textContent='Try again';retry.hidden=true;
    retry.addEventListener('click',()=>loadPage(frame).catch(()=>{}));
    loader.append(spinner,message,retry);frame.append(loader);
  });
  function loadPage(frame) {
    if(pendingPages.has(frame))return pendingPages.get(frame);
    frame.dataset.loadState='loading';frame.setAttribute('aria-busy','true');
    const loader=frame.querySelector('.page-loader'),message=loader.querySelector('[role=status]');
    message.textContent=`Loading page ${frame.dataset.page}…`;loader.querySelector('button').hidden=true;
    const promise=Promise.all([fontsReady,...[...frame.querySelectorAll('object[data-src],img[data-src]')].map(loadAsset)])
      .then(()=>new Promise(resolve=>requestAnimationFrame(resolve)))
      .then(()=>{frame.dataset.loadState='ready';frame.setAttribute('aria-busy','false');})
      .catch(error=>{
        pendingPages.delete(frame);frame.dataset.loadState='error';frame.setAttribute('aria-busy','false');
        message.textContent=`Page ${frame.dataset.page} couldn’t load.`;loader.querySelector('button').hidden=false;
        throw error;
      });
    pendingPages.set(frame,promise);return promise;
  }
  const loadVisiblePages=()=>Promise.allSettled(frames.filter(frame=>frame.classList.contains('is-active')).map(loadPage));
  // Exports and the print button await every page, including deferred artwork.
  window.prepareBrochure=()=>Promise.all(frames.map(loadPage));
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
    loadVisiblePages();
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
    if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='p'){event.preventDefault();printBrochure();return;}
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
  async function printBrochure() {
    const button=document.querySelector('#print');if(button.disabled)return;
    button.disabled=true;const label=button.textContent;button.textContent='Preparing pages…';
    try {
      await window.prepareBrochure();document.documentElement.dataset.view='pages';window.print();
    } catch {
      document.querySelector('#page-announcement').textContent='Some pages could not load. Please try Print / PDF again.';
    } finally {document.documentElement.dataset.view='flipbook';button.disabled=false;button.textContent=label;}
  }
  document.querySelector('#print').addEventListener('click',printBrochure);
  new MutationObserver(()=>{
    if(document.documentElement.dataset.view==='pages')window.prepareBrochure().catch(()=>{});
  }).observe(document.documentElement,{attributes:true,attributeFilter:['data-view']});
  window.addEventListener('beforeprint',()=>{frames.forEach(frame=>frame.inert=false);window.prepareBrochure().catch(()=>{});});window.addEventListener('afterprint',updateNavigation);
  new ResizeObserver(resize).observe(toolbar);
  resize();updateNavigation();loadVisiblePages().then(()=>{resize();document.documentElement.dataset.ready='true';});
})();
