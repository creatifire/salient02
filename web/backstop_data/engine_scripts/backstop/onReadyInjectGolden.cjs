module.exports = async (page, scenario) => {
  const GOLDEN = [
    '# Golden Sample',
    '',
    'This paragraph checks line breaks and spacing.',
    '',
    '- Item 1',
    '- Item 2',
    '',
    '| Col A | Col B |',
    '| --- | --- |',
    '| A1 | B1 |',
    '| A2 | B2 |',
    '',
    'Inline `code` and:',
    '',
    '```',
    'def add(a, b):',
    '    return a + b',
    '```',
    '',
    'A final sentence.'
  ].join('\n');

  const url = await page.url();

  if (url.includes(':8000/')) {
    await page.waitForSelector('#chatPane');
    await page.evaluate((md) => {
      const chat = document.querySelector('#chatPane');
      const wrap = document.createElement('div'); wrap.className = 'msg bot';
      const content = document.createElement('div'); content.className = 'msg-content';
      if (window.DOMPurify && window.marked) {
        content.innerHTML = window.DOMPurify.sanitize(window.marked.parse(md, { breaks: true }));
      } else {
        content.textContent = md;
      }
      wrap.appendChild(content); chat && chat.appendChild(wrap);
    }, GOLDEN);
  } else if (url.includes('/htmx-chat.html') || url.includes('/demo/htmx-chat')) {
    await page.waitForSelector('.chat');
    await page.evaluate((md) => {
      const chat = document.querySelector('.chat');
      const wrap = document.createElement('div'); wrap.className = 'msg bot';
      const content = document.createElement('div'); content.className = 'content';
      if (window.DOMPurify && window.marked) {
        content.innerHTML = window.DOMPurify.sanitize(window.marked.parse(md, { breaks: true }));
      } else {
        content.textContent = md;
      }
      wrap.appendChild(content); chat && chat.appendChild(wrap);
    }, GOLDEN);
  } else if (url.includes('/demo/widget')) {
    // Ensure widget is open and inject into shadow DOM
    await page.evaluate(() => window.SalientChatWidget && window.SalientChatWidget.open());
    await page.waitForFunction(() => {
      const host = document.getElementById('salient-chat-widget-host');
      return !!host && host.shadowRoot && host.shadowRoot.querySelector('.chat');
    });
    await page.evaluate((md) => {
      const host = document.getElementById('salient-chat-widget-host');
      const chat = host && host.shadowRoot && host.shadowRoot.querySelector('.chat');
      if (!chat) return;
      const wrap = document.createElement('div'); wrap.className = 'msg bot';
      const content = document.createElement('div'); content.className = 'content';
      content.textContent = md;
      wrap.appendChild(content); chat.appendChild(wrap);
      // Clone chat into a top-level capture container for Backstop
      let cap = document.getElementById('widget-capture');
      if (!cap) { cap = document.createElement('div'); cap.id = 'widget-capture'; document.body.appendChild(cap); }
      cap.innerHTML = '';
      const clone = chat.cloneNode(true);
      cap.appendChild(clone);
    }, GOLDEN);
  }
};


