(function(){
  if (typeof window === 'undefined') return;
  if (window.__salientWidgetLoaded) return; // guard
  window.__salientWidgetLoaded = true;

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
      header{ padding: .6rem .85rem; background: #169CB5; color: #fff; font: 600 14px/1.2 system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
      .body{ padding: .75rem; overflow: auto; }
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
    const body = document.createElement('div');
    body.className = 'body';
    body.textContent = 'Widget ready. (Content will load in later chunks.)';
    pane.appendChild(header); pane.appendChild(body);

    root.appendChild(style);
    root.appendChild(overlay);
    root.appendChild(pane);
    root.appendChild(fab);

    function open(){
      host.setAttribute('data-open', '1');
      fab.setAttribute('aria-expanded', 'true');
      pane.setAttribute('aria-hidden', 'false');
    }
    function close(){
      host.removeAttribute('data-open');
      fab.setAttribute('aria-expanded', 'false');
      pane.setAttribute('aria-hidden', 'true');
    }
    function toggle(){ host.hasAttribute('data-open') ? close() : open(); }

    fab.addEventListener('click', toggle);
    overlay.addEventListener('click', close);
    window.addEventListener('keydown', (e)=>{ if(e.key === 'Escape') close(); });

    // expose a minimal API for future chunks
    window.SalientChatWidget = Object.assign(window.SalientChatWidget || {}, { open, close, toggle, host, root });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createWidget);
  } else {
    createWidget();
  }
})();
