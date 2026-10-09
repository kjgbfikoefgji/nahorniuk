try { (() => {
  const root = document.documentElement;
  const btn = document.querySelector('[data-theme-toggle]');
  if (!btn) return;
  const meta = document.querySelector('meta[name="theme-color"]');
  btn.addEventListener('click', () => {
    const next = root.dataset.theme === 'light' ? 'dark' : 'light';
    root.dataset.theme = next;
    if (meta) meta.content = next === 'light' ? '#f6f3ee' : '#0e1218';
    try { localStorage.setItem('theme', next); } catch (e) { /* не критично */ }
  });
})(); } catch (e) { console.error(e); }
