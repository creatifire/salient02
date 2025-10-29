(function(){
  if (typeof window === 'undefined') return;
  if (window.__salientWidgetLoaded) return; // guard
  window.__salientWidgetLoaded = true;

  // Check for global config first (set via inline script before widget loads)
  const globalConfig = window.__SALIENT_WIDGET_CONFIG || {};
  
  const script = document.currentScript || (function(){
    const all = document.querySelectorAll('script');
    for (let i=all.length-1;i>=0;i--){ if (String(all[i].src||'').includes('chat-widget.js')) return all[i]; }
    return null;
  })();
  const dataSource = globalConfig.source || (script && script.getAttribute('data-source')) || '/';
  const dataBackend = globalConfig.backend || (script && script.getAttribute('data-backend')) || window.location.origin;
  const chatPath = (script && script.getAttribute('data-chat-path')) || '/chat'; // Deprecated: use data-account + data-agent instead
  const allowCross = globalConfig.allowCross || (script && script.getAttribute('data-allow-cross')) === '1';
  const ssePreferred = globalConfig.sse !== false && (script && script.getAttribute('data-sse')) !== '0'; // default on
  const copyIconSrc = (script && script.getAttribute('data-copy-icon')) || '/widget/chat-copy.svg';
  
  // SVG icon paths for maximize/minimize/close
  const maximizeIconSrc = '/widget/chat-maximize.svg';
  const minimizeIconSrc = '/widget/chat-minimize.svg';
  const closeIconSrc = '/widget/chat-close.svg';
  
  // Multi-tenant configuration attributes
  const accountSlug = globalConfig.account || (script && script.getAttribute('data-account')) || 'default_account';
  const agentInstanceSlug = globalConfig.agent || (script && script.getAttribute('data-agent')) || 'simple_chat1';
  
  // Debug mode - enable verbose console logging
  const debugMode = globalConfig.debug !== undefined ? globalConfig.debug : false;
  function debugLog(...args) {
    if (debugMode) console.debug('[SalientWidget]', ...args);
  }
  
  let backend;
  try { backend = new URL(dataSource, dataBackend); } catch { backend = new URL('/', window.location.origin); }

  function isSameOrigin(u){ try { return new URL(u).origin === window.location.origin; } catch { return false; } }

  async function loadGlobal(url, globalName){
    return new Promise((resolve)=>{
      if (window[globalName]) return resolve(window[globalName]);
      const s = document.createElement('script');
      s.src = url; s.async = true; s.onload = ()=> resolve(window[globalName]); s.onerror = ()=> resolve(undefined);
      document.head.appendChild(s);
    });
  }
  async function renderMarkdownInto(element, raw){
    debugLog('renderMarkdownInto called, loading libraries...');
    const [marked, DOMPurify] = await Promise.all([
      loadGlobal('https://cdn.jsdelivr.net/npm/marked/marked.min.js', 'marked'),
      loadGlobal('https://cdn.jsdelivr.net/npm/dompurify@3.1.7/dist/purify.min.js', 'DOMPurify')
    ]);
    debugLog('Libraries loaded:', { marked: !!marked, DOMPurify: !!DOMPurify });
    if (marked && DOMPurify){
      const trimmed = String(raw || '').trim();
      const html = DOMPurify.sanitize(marked.parse(trimmed, { 
        breaks: true,
        gfm: true  // GitHub Flavored Markdown - enables tables
      }));
      debugLog('Markdown parsed, html length:', html.length);
      if (!html || html.replace(/\s/g,'') === ''){
        element.textContent = trimmed || '[no response]';
      } else {
        element.innerHTML = html;
      }
    } else {
      console.warn('[SalientWidget] Libraries failed to load, falling back to plain text');
      const trimmed = String(raw || '').trim();
      element.textContent = trimmed || '[no response]';
    }
  }

  function createWidget(){
    const host = document.createElement('div');
    host.id = 'salient-chat-widget-host';
    host.style.all = 'initial';
    document.body.appendChild(host);
    const root = host.attachShadow({ mode: 'open' });

    const style = document.createElement('style');
    style.textContent = `
      :host{ all: initial; }
      *, *::before, *::after { box-sizing: border-box; }
      #overlay{ position: fixed; inset: 0; background: rgba(0,0,0,.2); opacity: 0; pointer-events: none; transition: opacity .2s ease; z-index: 2147483630; }
      :host([data-open="1"]) #overlay{ opacity: 1; pointer-events: auto; }
      #fab{ position: fixed; right: 16px; bottom: 16px; z-index: 2147483646; border: 0; border-radius: 9999px; padding: .65rem .9rem; background: #108D43; color: #fff; cursor: pointer; box-shadow: 0 6px 16px rgba(0,0,0,.2); font: 600 14px/1 system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
      #pane{ position: fixed; right: 16px; bottom: 72px; width: min(92vw, 380px); height: 480px; background: #fff; color: #111; border-radius: 12px; box-shadow: 0 12px 28px rgba(0,0,0,.25); transform: translateX(120%); transition: transform .25s ease, width .5s cubic-bezier(0.4, 0, 0.2, 1), height .5s cubic-bezier(0.4, 0, 0.2, 1); overflow: hidden; z-index: 2147483645; display: flex; flex-direction: column; }
      :host([data-open="1"]) #pane{ transform: translateX(0); }
      #pane.maximized{ width: calc(100vw - 66px); height: calc(100vh - 97px); }
      header{ padding: .6rem .85rem; background: #169CB5; color: #fff; font: 600 14px/1.2 system-ui, -apple-system, Segoe UI, Roboto, sans-serif; display:flex; justify-content:space-between; align-items:center; gap:.5rem; }
      .header-title{ flex:1; text-align:center; }
      .header-btn{ background:transparent; border:none; color:#fff; cursor:pointer; padding:4px; width:24px; height:24px; display:flex; align-items:center; justify-content:center; opacity:.9; transition:opacity .15s ease; }
      .header-btn:hover{ opacity:1; }
      .header-btn img{ width:18px; height:18px; display:block; }
      @media (max-width: 767px){ #maximize-btn{ display:none !important; } #pane.maximized{ top:auto; left:auto; right:16px; bottom:72px; width:min(92vw, 380px); max-height:72vh; } }
      .body{ padding: .75rem; overflow: auto; display:flex; flex-direction:column; gap:.5rem; }
      .chat{ border:1px solid #eee; border-radius:8px; padding:.5rem; height: 240px; overflow:auto; display:flex; flex-direction:column; gap:.4rem; background:#fff; }
      #pane.maximized .body{ flex: 1; overflow: hidden; }
      #pane.maximized .chat{ flex: 1; height: auto; }
      .msg{ position: relative; padding:.6rem .8rem; border-radius:6px; max-width:85%; word-wrap:break-word; }
      .msg.user{ background:#eef6ff; align-self:flex-end; margin-left:auto; }
      .msg.bot{ background:#fffbe6; align-self:flex-start; margin-right:auto; }
      .msg.user .content{ white-space:pre-wrap; }
      
      /* Table styles for markdown tables */
      .msg.bot table { 
        border-collapse: collapse; 
        width: 100%; 
        margin: 0.5rem 0; 
        font-size: 0.9rem;
      }
      .msg.bot th, .msg.bot td { 
        border: 1px solid #ddd; 
        padding: 0.5rem 0.75rem; 
        text-align: left; 
      }
      .msg.bot th { 
        background-color: #f8f9fa; 
        font-weight: 600; 
        border-bottom: 2px solid #ccc;
      }
      .msg.bot tr:nth-child(even) { 
        background-color: #f9f9f9; 
      }
      .msg.bot tr:hover { 
        background-color: #f0f8ff; 
      }
      
      /* Proper paragraph spacing for bot messages */
      .msg.bot p {
        margin: 0.5rem 0;
        line-height: 1.5;
      }
      .msg.bot p:first-child {
        margin-top: 0;
      }
      .msg.bot p:last-child {
        margin-bottom: 0;
      }
      
      .copy{ position:absolute; bottom:6px; right:6px; background:rgba(255,255,255,.9); border:1px solid #ddd; border-radius:6px; padding:4px; width:22px; height:22px; display:flex; align-items:center; justify-content:center; opacity:.2; transition:opacity .15s ease, transform .1s ease; cursor:pointer; }
      .copy img{ width:14px; height:14px; display:block; }
      .msg.bot:hover .copy, .copy:focus{ opacity:1; }
      .copy:active{ transform: scale(.96); }
      textarea{ width:100%; min-height:64px; padding:.5rem; border:1px solid #ddd; border-radius:6px; resize:vertical; }
      .row{ display:flex; align-items:center; gap:.5rem; }
      .btn{ padding:.45rem .7rem; border:1px solid #ccc; border-radius:6px; background:#f6f6f6; cursor:pointer; }
      .btn.primary{ background:#108D43; color:#fff; border-color:#108D43; }
      .hint{ font-size:.85rem; color:#666; }
      #toast{ position: fixed; right: 16px; bottom: 90px; background:#111; color:#fff; padding:6px 8px; border-radius:6px; font-size:12px; opacity:0; transition:opacity .15s ease; z-index:2147483646; }
      :host([data-toast="1"]) #toast{ opacity:.9; }
      
      /* Loading indicator for chat history */
      .loading-indicator{ display:flex; align-items:center; justify-content:center; padding:1rem; color:#666; font-size:0.9rem; }
      .loading-text{ margin-left:0.5rem; }
      .loading-indicator::before{ content:''; width:16px; height:16px; border:2px solid #ddd; border-top:2px solid #666; border-radius:50%; animation:spin 1s linear infinite; }
      @keyframes spin{ 0%{ transform:rotate(0deg); } 100%{ transform:rotate(360deg); } }
      
      /* Typing indicator for bot messages */
      .typing-indicator{ display:flex; align-items:center; justify-content:center; gap:4px; padding:8px 0; min-height:32px; }
      .typing-indicator span{ width:8px; height:8px; border-radius:50%; background:#999; animation:typing-bounce 1.4s infinite ease-in-out; }
      .typing-indicator span:nth-child(1){ animation-delay:0s; }
      .typing-indicator span:nth-child(2){ animation-delay:0.2s; }
      .typing-indicator span:nth-child(3){ animation-delay:0.4s; }
      @keyframes typing-bounce{ 0%, 60%, 100%{ transform:translateY(0); opacity:0.7; } 30%{ transform:translateY(-8px); opacity:1; } }
      
      @media (max-width: 480px){ #pane{ bottom: 82px; width: 92vw; } }
    `;

    const overlay = document.createElement('div');
    overlay.id = 'overlay';

    const fab = document.createElement('button');
    fab.id = 'fab';
    fab.type = 'button';
    fab.setAttribute('aria-expanded', 'false');
    fab.setAttribute('aria-controls', 'pane');
    fab.textContent = 'Chat';

    const pane = document.createElement('div');
    pane.id = 'pane';
    pane.setAttribute('role', 'dialog');
    pane.setAttribute('aria-modal', 'true');
    pane.setAttribute('aria-hidden', 'true');

    // Helper function to create header button with SVG icon
    function createHeaderButton(iconSrc, ariaLabel, clickHandler) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'header-btn';
      btn.setAttribute('aria-label', ariaLabel);
      btn.title = ariaLabel;
      
      const img = document.createElement('img');
      img.src = iconSrc;
      img.alt = '';
      btn.appendChild(img);
      
      if (clickHandler) {
        btn.addEventListener('click', clickHandler);
      }
      
      return btn;
    }

    const header = document.createElement('header');
    
    // Create maximize/minimize button (left side)
    // Note: Handler is assigned later after toggleMaximize function is defined
    const maximizeBtn = createHeaderButton(maximizeIconSrc, 'Maximize chat', null);
    maximizeBtn.id = 'maximize-btn';
    maximizeBtn.setAttribute('aria-expanded', 'false');
    
    // Create title (center)
    const headerTitle = document.createElement('span');
    headerTitle.className = 'header-title';
    headerTitle.textContent = 'Salient Chat';
    
    // Create close button (right side) - now with SVG
    const closeBtn = createHeaderButton(closeIconSrc, 'Close chat', close);
    closeBtn.id = 'close-btn';
    
    // Assemble header: [Maximize] [Title] [Close]
    header.appendChild(maximizeBtn);
    header.appendChild(headerTitle);
    header.appendChild(closeBtn);

    const body = document.createElement('div');
    body.className = 'body';

    const toast = document.createElement('div'); toast.id='toast'; toast.textContent='Copied';

    // Chat UI
    const chat = document.createElement('div'); chat.className='chat';
    const input = document.createElement('textarea'); input.placeholder = 'Type your message… (Ctrl/Cmd+Enter to send)';
    const row = document.createElement('div'); row.className='row';
    const send = document.createElement('button'); send.className='btn primary'; send.textContent='Send';
    const clear = document.createElement('button'); clear.className='btn'; clear.textContent='Clear';
    const hint = document.createElement('div'); hint.className='hint'; hint.textContent='Receiving…'; hint.style.display='none';

    body.appendChild(chat); body.appendChild(input); row.appendChild(send); row.appendChild(clear); row.appendChild(hint); body.appendChild(row);

    pane.appendChild(header); pane.appendChild(body);

    function showToast(msg){ toast.textContent = msg || 'Copied'; host.setAttribute('data-toast','1'); setTimeout(()=>{ host.removeAttribute('data-toast'); }, 1000); }

    function addCopyButton(container){
      const btn = document.createElement('button');
      btn.className = 'copy';
      btn.type = 'button';
      btn.setAttribute('aria-label', 'Copy message');
      btn.title = 'Copy';
      const img = document.createElement('img');
      img.src = copyIconSrc;
      img.alt = '';
      btn.appendChild(img);
      btn.addEventListener('click', async ()=>{
        const raw = container.dataset.raw || container.textContent || '';
        try{
          if (navigator.clipboard && navigator.clipboard.writeText){
            await navigator.clipboard.writeText(raw);
          } else {
            const ta = document.createElement('textarea'); ta.value = raw; ta.style.position='fixed'; ta.style.opacity='0'; root.appendChild(ta); ta.select(); document.execCommand && document.execCommand('copy'); ta.remove();
          }
          showToast('Copied');
        }catch{ showToast('Copy failed'); }
      });
      container.appendChild(btn);
    }

    function createMessage(role, text){
      const container = document.createElement('div'); container.className = 'msg '+role;
      const content = document.createElement('div'); content.className = 'content'; content.textContent = text || '';
      container.appendChild(content);
      
      // Add copy button for bot messages
      if (role === 'bot') {
        addCopyButton(container);
      }
      
      chat.appendChild(container); chat.scrollTop = chat.scrollHeight;
      return container;
    }
    function setMessage(container, raw){ const content = container.querySelector('.content') || container; content.textContent = raw; container.dataset.raw = raw; chat.scrollTop = chat.scrollHeight; }
    
    // Typing indicator helper functions
    function showTypingIndicator(container) {
      if (!container) return;
      const content = container.querySelector('.content');
      if (content) {
        // Insert typing indicator HTML directly into content
        content.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        chat.scrollTop = chat.scrollHeight;
      }
    }
    
    function hideTypingIndicator(container) {
      if (!container) return;
      const content = container.querySelector('.content');
      // Check if content contains typing indicator
      if (content && content.querySelector('.typing-indicator')) {
        content.innerHTML = ''; // Clear typing indicator
      }
    }

    let busy=false; let activeSSE=null; let activeBotDiv=null; let accumulated='';
    let typingTimeout=null; // Track typing indicator timeout
    let configCache = null;
    let historyLoaded = false;
    
    // Maximize/minimize state management
    // TODO: Migrate to per-agent localStorage when Epic 0017-007 (per-agent cookies) is implemented
    const STORAGE_KEY = 'salient_chat_widget_maximized';
    let isMaximized = false;
    
    // Mobile detection
    const isMobile = () => window.matchMedia('(max-width: 767px)').matches;
    
    async function loadHistory(){
      if (historyLoaded) return;
      
      // Create and show loading indicator
      const indicator = document.createElement('div');
      indicator.className = 'loading-indicator';
      indicator.innerHTML = '<span class="loading-text">Loading chat history...</span>';
      chat.appendChild(indicator);
      
      try{
        // Use multi-tenant history endpoint
        const historyUrl = new URL(`/accounts/${accountSlug}/agents/${agentInstanceSlug}/history`, backend);
        const r = await fetch(historyUrl.toString(), { 
          mode: allowCross ? 'cors' : 'same-origin',
          credentials: allowCross ? 'include' : 'same-origin'
        });
        
        if (!r.ok) {
          if (r.status === 401) {
            debugLog(`No session found for ${accountSlug}/${agentInstanceSlug}`);
          } else {
            console.warn('[SalientWidget] History load failed:', r.status, r.statusText);
          }
          return;
        }
        
        const data = await r.json();
        const msgs = data.messages || [];
        
        if (msgs.length === 0) {
          debugLog(`No history found for ${accountSlug}/${agentInstanceSlug}`);
          return;
        }
        
        // Load messages into chat
        for (const m of msgs) {
          const role = m.role; // API already maps roles correctly
          const container = createMessage(role, '');
          container.dataset.raw = m.raw_content || m.content || '';
          
          const content = container.querySelector('.content') || container;
          if (role === 'bot') {
            // Bot messages are raw markdown that need to be rendered
            await renderMarkdownInto(content, m.content || '');
          } else {
            // User messages are plain text
            content.textContent = m.content || '';
          }
        }
        
        debugLog(`Loaded ${msgs.length} messages for ${accountSlug}/${agentInstanceSlug}`);
        historyLoaded = true;
        
      } catch (e) {
        console.error('[SalientWidget] History load error:', e);
      } finally {
        // Remove loading indicator
        if (indicator && indicator.parentNode) {
          indicator.remove();
        }
      }
    }
    
    async function getBackendConfig(){
      if (configCache) return configCache;
      try{
        const configUrl = new URL('/api/config', backend);
        const r = await fetch(configUrl.toString(), { mode: allowCross ? 'cors' : 'same-origin' });
        configCache = r.ok ? await r.json() : { ui: { sse_enabled: true, allow_basic_html: true } };
      }catch{
        configCache = { ui: { sse_enabled: true, allow_basic_html: true } };
      }
      return configCache;
    }
    
    function setBusy(v){ busy=v; send.disabled=v; send.style.opacity=v?'.6':'1'; hint.style.display=v?'inline':'none'; }

    async function sendMessage(){
      if (busy) return; const value=(input.value||'').trim(); if(!value) return;
      createMessage('user', value); input.value='';
      setBusy(true);
      // Create bot container for streaming
      activeBotDiv = createMessage('bot', '');
      accumulated = '';
      
      // Clear any existing typing timeout
      if (typingTimeout) clearTimeout(typingTimeout);
      
      // Show typing indicator after 500ms if no response yet
      typingTimeout = setTimeout(() => {
        showTypingIndicator(activeBotDiv);
      }, 500);
      
      // Get backend configuration to respect sse_enabled setting
      const config = await getBackendConfig();
      const backendSseEnabled = config.ui.sse_enabled;
      
      try{
        // Multi-tenant endpoints
        const sseUrl = new URL(`/accounts/${accountSlug}/agents/${agentInstanceSlug}/stream`, backend);
        sseUrl.searchParams.set('message', value);
        const postUrl = new URL(`/accounts/${accountSlug}/agents/${agentInstanceSlug}/chat`, backend);
        const same = postUrl.origin === window.location.origin;
        if (!allowCross && !same){ setMessage(activeBotDiv, 'Configuration requires same-origin for widget.'); setBusy(false); return; }
        
        // Use SSE only if both ssePreferred (client) and backendSseEnabled (server) are true
        if (ssePreferred && backendSseEnabled){
          // Start SSE with credentials to send session cookie
          debugLog('SSE', sseUrl.toString());
          const es = new EventSource(sseUrl.toString(), { withCredentials: true });
          activeSSE = es;
          // Accumulate chunks without rendering during streaming (render once when done)
          es.onmessage = (ev)=>{ 
            accumulated += ev.data;
            
            if(activeBotDiv && accumulated.length > 0){ 
              // Clear timeout and hide indicator when we start showing text
              if (typingTimeout) clearTimeout(typingTimeout);
              hideTypingIndicator(activeBotDiv);
              
              activeBotDiv.dataset.raw = accumulated;
              // Show accumulated text with basic line breaks (no markdown yet)
              const content = activeBotDiv.querySelector('.content') || activeBotDiv;
              content.textContent = accumulated;  // Plain text during streaming
              chat.scrollTop = chat.scrollHeight; 
            } 
          };
    es.addEventListener('done', async()=>{
      debugLog('SSE done event received, rendering markdown');
      if (typingTimeout) clearTimeout(typingTimeout);
      hideTypingIndicator(activeBotDiv);
      try{ es.close(); }catch{}
      activeSSE=null;
      const content = activeBotDiv && (activeBotDiv.querySelector('.content') || activeBotDiv);
      if (content){ 
        debugLog('Calling renderMarkdownInto with', accumulated.substring(0, 50) + '...');
        await renderMarkdownInto(content, accumulated); 
        debugLog('Markdown rendering complete');
      }
      setBusy(false);
    });
          es.onerror = ()=>{ 
            if (typingTimeout) clearTimeout(typingTimeout);
            hideTypingIndicator(activeBotDiv);
            try{ es.close(); }catch{}; activeSSE=null; // fallback to POST
            debugLog('SSE error, falling back to POST');
            doPost(postUrl.toString(), value);
          };
          return;
        }
        // POST fallback
        await doPost(postUrl.toString(), value);
      }catch(e){ 
        if (typingTimeout) clearTimeout(typingTimeout);
        hideTypingIndicator(activeBotDiv);
        setMessage(activeBotDiv, '[network error]'); 
        setBusy(false); 
      }
    }

    async function doPost(url, value){
      try{
        debugLog('POST', url, { value });
        const r = await fetch(url, { 
          method:'POST', 
          headers:{ 'Content-Type':'application/json' }, 
          body: JSON.stringify({ message: value }),
          credentials: 'include'  // Send session cookie
        });
        
        // Clear typing indicator on response
        if (typingTimeout) clearTimeout(typingTimeout);
        hideTypingIndicator(activeBotDiv);
        
        if (!r.ok){ 
          setMessage(activeBotDiv, `[http ${r.status} ${r.statusText}]`); 
        } else { 
          // Parse JSON and extract the 'response' field
          const json = await r.json();
          const txt = json.response || json.error || '[No response]';
          const content = activeBotDiv && (activeBotDiv.querySelector('.content') || activeBotDiv);
          if (activeBotDiv) activeBotDiv.dataset.raw = txt;
          if (content) {
            debugLog('POST response received, rendering markdown');
            await renderMarkdownInto(content, txt);
          }
        }
      }catch(e){ 
        debugLog('POST error:', e);
        if (typingTimeout) clearTimeout(typingTimeout);
        hideTypingIndicator(activeBotDiv);
        setMessage(activeBotDiv, '[network error]'); 
      }
      finally { setBusy(false); }
    }

    send.addEventListener('click', sendMessage);
    clear.addEventListener('click', ()=>{ chat.innerHTML=''; historyLoaded = false; });
    input.addEventListener('keydown', (e)=>{ const isEnter=e.key==='Enter'; const isCtrl=e.ctrlKey||e.metaKey; if(isEnter&&isCtrl){ e.preventDefault(); sendMessage(); }});

    root.appendChild(style);
    root.appendChild(overlay);
    root.appendChild(pane);
    root.appendChild(fab);
    root.appendChild(toast);

    let loaded=false;
    async function maybeFetch(){ if (loaded) return; try{ await fetch(new URL('/health', backend).toString(), { mode: allowCross? 'cors':'same-origin' }); }catch{} loaded=true; }

    function open(){ host.setAttribute('data-open', '1'); fab.setAttribute('aria-expanded','true'); pane.setAttribute('aria-hidden','false'); maybeFetch(); loadHistory(); }
    function close(){ host.removeAttribute('data-open'); fab.setAttribute('aria-expanded','false'); pane.setAttribute('aria-hidden','true'); if(activeSSE){ try{ activeSSE.close(); }catch{} activeSSE=null; setBusy(false);} }
    function toggle(){ host.hasAttribute('data-open') ? close() : open(); }
    
    // Toggle maximize/minimize state
    function toggleMaximize() {
      // Prevent maximize on mobile
      if (isMobile() && !isMaximized) {
        debugLog('Maximize disabled on mobile');
        return;
      }
      
      isMaximized = !isMaximized;
      
      // Apply/remove maximized CSS class
      if (isMaximized) {
        pane.classList.add('maximized');
      } else {
        pane.classList.remove('maximized');
      }
      
      // Save preference to localStorage
      try {
        localStorage.setItem(STORAGE_KEY, isMaximized ? '1' : '0');
      } catch (e) {
        debugLog('localStorage save failed:', e);
      }
      
      updateMaximizeButton();
      debugLog('Maximize toggled:', isMaximized);
    }
    
    // Load maximize preference from localStorage
    function loadMaximizePreference() {
      if (isMobile()) {
        // Force minimized on mobile
        isMaximized = false;
        return;
      }
      
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved === '1') {
          isMaximized = true;
          pane.classList.add('maximized');
          updateMaximizeButton();
          debugLog('Loaded maximize preference: true');
        }
      } catch (e) {
        debugLog('localStorage load failed:', e);
      }
    }
    
    // Handle window resize - force minimized on mobile
    function handleResize() {
      if (isMobile() && isMaximized) {
        isMaximized = false;
        pane.classList.remove('maximized');
        updateMaximizeButton();
        debugLog('Auto-minimized on mobile resize');
      }
    }
    
    // Update maximize button icon and ARIA attributes
    function updateMaximizeButton() {
      const img = maximizeBtn.querySelector('img');
      if (isMaximized) {
        img.src = minimizeIconSrc;
        maximizeBtn.setAttribute('aria-label', 'Minimize chat');
        maximizeBtn.setAttribute('aria-expanded', 'true');
        maximizeBtn.title = 'Minimize chat';
      } else {
        img.src = maximizeIconSrc;
        maximizeBtn.setAttribute('aria-label', 'Maximize chat');
        maximizeBtn.setAttribute('aria-expanded', 'false');
        maximizeBtn.title = 'Maximize chat';
      }
    }

    fab.addEventListener('click', toggle);
    overlay.addEventListener('click', close);
    maximizeBtn.addEventListener('click', toggleMaximize);
    
    // ESC key two-step behavior: maximize → minimize → close
    window.addEventListener('keydown', (e)=>{ 
      if(e.key === 'Escape') {
        if (!host.hasAttribute('data-open')) return; // Widget closed, do nothing
        
        if (isMaximized) {
          // First press: minimize
          toggleMaximize();
        } else {
          // Second press: close
          close();
        }
      }
    });
    
    // Handle window resize for mobile behavior
    window.addEventListener('resize', handleResize);
    
    // Load maximize preference on initialization
    loadMaximizePreference();

    window.SalientChatWidget = Object.assign(window.SalientChatWidget || {}, { 
      open, 
      close, 
      toggle, 
      host, 
      root, 
      config: { 
        backend: backend.toString(), 
        accountSlug, 
        agentInstanceSlug, 
        chatPath, // Deprecated
        allowCross, 
        ssePreferred, 
        copyIconSrc 
      } 
    });
  }

  if (!allowCross && !isSameOrigin(backend.toString())){
    console.warn('[SalientWidget] Backend origin differs from page origin and allow-cross is not enabled. SSE/POST will be blocked.');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createWidget);
  } else {
    createWidget();
  }
})();
