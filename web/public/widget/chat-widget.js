(function(){
  if (typeof window === 'undefined') return;
  if (window.__salientWidgetLoaded) return; // guard
  window.__salientWidgetLoaded = true;

  const script = document.currentScript || (function(){
    const all = document.querySelectorAll('script');
    for (let i=all.length-1;i>=0;i--){ if (String(all[i].src||'').includes('chat-widget.js')) return all[i]; }
    return null;
  })();
  const dataSource = (script && script.getAttribute('data-source')) || '/';
  const dataBackend = (script && script.getAttribute('data-backend')) || window.location.origin;
  const chatPath = (script && script.getAttribute('data-chat-path')) || '/chat';
  const allowCross = (script && script.getAttribute('data-allow-cross')) === '1';
  let backend;
  try { backend = new URL(dataSource, dataBackend); } catch { backend = new URL('/', window.location.origin); }

  function isSameOrigin(u){ try { return new URL(u).origin === window.location.origin; } catch { return false; } }

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
      #pane{ position: fixed; right: 16px; bottom: 72px; width: min(92vw, 380px); max-height: 72vh; background: #fff; color: #111; border-radius: 12px; box-shadow: 0 12px 28px rgba(0,0,0,.25); transform: translateX(120%); transition: transform .25s ease; overflow: hidden; z-index: 2147483645; display: flex; flex-direction: column; }
      :host([data-open="1"]) #pane{ transform: translateX(0); }
      header{ padding: .6rem .85rem; background: #169CB5; color: #fff; font: 600 14px/1.2 system-ui, -apple-system, Segoe UI, Roboto, sans-serif; display:flex; justify-content:space-between; align-items:center; }
      .body{ padding: .75rem; overflow: auto; display:flex; flex-direction:column; gap:.5rem; }
      .chat{ border:1px solid #eee; border-radius:8px; padding:.5rem; height: 240px; overflow:auto; display:flex; flex-direction:column; gap:.4rem; background:#fff; }
      .msg{ padding:.4rem .6rem; border-radius:6px; max-width:85%; word-wrap:break-word; }
      .msg.user{ background:#eef6ff; align-self:flex-end; margin-left:auto; }
      .msg.bot{ background:#fffbe6; align-self:flex-start; margin-right:auto; }
      textarea{ width:100%; min-height:64px; padding:.5rem; border:1px solid #ddd; border-radius:6px; resize:vertical; }
      .row{ display:flex; align-items:center; gap:.5rem; }
      .btn{ padding:.45rem .7rem; border:1px solid #ccc; border-radius:6px; background:#f6f6f6; cursor:pointer; }
      .btn.primary{ background:#108D43; color:#fff; border-color:#108D43; }
      .hint{ font-size:.85rem; color:#666; }
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

    const header = document.createElement('header');
    header.textContent = 'Salient Chat';
    const closeX = document.createElement('button'); closeX.textContent = '×'; closeX.className='btn'; closeX.style.background='transparent'; closeX.style.color='#fff'; closeX.style.borderColor='transparent'; closeX.addEventListener('click', close);
    header.appendChild(closeX);

    const body = document.createElement('div');
    body.className = 'body';

    // Minimal chat UI (non-stream POST fallback)
    const chat = document.createElement('div'); chat.className='chat';
    const input = document.createElement('textarea'); input.placeholder = 'Type your message… (Ctrl/Cmd+Enter to send)';
    const row = document.createElement('div'); row.className='row';
    const send = document.createElement('button'); send.className='btn primary'; send.textContent='Send';
    const clear = document.createElement('button'); clear.className='btn'; clear.textContent='Clear';
    const hint = document.createElement('div'); hint.className='hint'; hint.textContent='Receiving…'; hint.style.display='none';

    body.appendChild(chat); body.appendChild(input); row.appendChild(send); row.appendChild(clear); row.appendChild(hint); body.appendChild(row);

    pane.appendChild(header); pane.appendChild(body);

    function append(role, text){ const div=document.createElement('div'); div.className='msg '+role; div.textContent=text; chat.appendChild(div); chat.scrollTop=chat.scrollHeight; }

    let busy=false;
    function setBusy(v){ busy=v; send.disabled=v; send.style.opacity=v?'.6':'1'; hint.style.display=v?'inline':'none'; }

    async function sendMessage(){
      if (busy) return; const value=(input.value||'').trim(); if(!value) return;
      append('user', value); input.value='';
      setBusy(true);
      try{
        const target = new URL(chatPath, backend);
        if (!allowCross && target.origin !== window.location.origin){
          append('bot', 'Configuration requires same-origin for widget.');
        } else {
          const url = target.toString();
          console.debug('[SalientWidget] POST', url, { value });
          const r = await fetch(url, { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ message: value }) });
          if (!r.ok){
            append('bot', `[http ${r.status} ${r.statusText}]`);
          } else {
            const txt = await r.text();
            append('bot', txt);
          }
        }
      }catch(e){ append('bot','[network error]'); }
      finally{ setBusy(false); }
    }

    send.addEventListener('click', sendMessage);
    clear.addEventListener('click', ()=>{ chat.innerHTML=''; });
    input.addEventListener('keydown', (e)=>{ const isEnter=e.key==='Enter'; const isCtrl=e.ctrlKey||e.metaKey; if(isEnter&&isCtrl){ e.preventDefault(); sendMessage(); }});

    root.appendChild(style);
    root.appendChild(overlay);
    root.appendChild(pane);
    root.appendChild(fab);

    let loaded=false;
    async function maybeFetch(){
      if (loaded) return;
      try{ await fetch(new URL('/health', backend).toString(), { mode: allowCross? 'cors':'same-origin' }); }catch{}
      loaded=true;
    }

    function open(){ host.setAttribute('data-open', '1'); fab.setAttribute('aria-expanded','true'); pane.setAttribute('aria-hidden','false'); maybeFetch(); }
    function close(){ host.removeAttribute('data-open'); fab.setAttribute('aria-expanded','false'); pane.setAttribute('aria-hidden','true'); }
    function toggle(){ host.hasAttribute('data-open') ? close() : open(); }

    fab.addEventListener('click', toggle);
    overlay.addEventListener('click', close);
    window.addEventListener('keydown', (e)=>{ if(e.key === 'Escape') close(); });

    window.SalientChatWidget = Object.assign(window.SalientChatWidget || {}, { open, close, toggle, host, root, config:{ backend: backend.toString(), chatPath, allowCross } });
  }

  if (!allowCross && !isSameOrigin(backend.toString())){
    console.warn('[SalientWidget] Backend origin differs from page origin and allow-cross is not enabled. The Send action will be blocked.');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createWidget);
  } else {
    createWidget();
  }
})();
