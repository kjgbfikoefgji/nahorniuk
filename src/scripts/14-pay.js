try { (() => {
  // Після натискання «Оплатити» банка monobank відкривається в новій вкладці, а тут з'являється вікно
  // «Оплатили?» з кнопкою в Telegram і заготовленим повідомленням (послуга й сума). Автоматично
  // перекинути з monobank у Telegram неможливо: банка не підтримує адресу повернення.
  const dlg = document.getElementById('paydone');
  if (!dlg || typeof dlg.showModal !== 'function') return;
  const go = dlg.querySelector('[data-pay-go]');
  const base = go.getAttribute('data-href');
  const tr = (s) => (window.__i18n ? window.__i18n.t(s) : s);
  document.querySelectorAll('a[href*="send.monobank.ua"]').forEach((a) => {
    a.addEventListener('click', () => {
      let amount = '', service = '';
      try {
        const u = new URL(a.href);
        amount = u.searchParams.get('a') || '';
        service = u.searchParams.get('t') || '';
      } catch (e) { /* без параметрів повідомлення лишається загальним */ }
      const msg = (dlg.getAttribute('data-msg') || '')
        .replace('{s}', () => tr(service))
        .replace('{a}', () => amount);
      go.href = base + '?text=' + encodeURIComponent(msg);
      setTimeout(() => { if (!dlg.open) { dlg.showModal(); go.focus(); } }, 400);
    });
  });
  dlg.querySelectorAll('[data-pay-close]').forEach((b) => b.addEventListener('click', () => dlg.close()));
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
  go.addEventListener('click', () => setTimeout(() => dlg.close(), 150));
})(); } catch (e) { console.error(e); }
