// Тема до першого малювання, щоб не було спалаху. Без збереженого вибору береться системна.
try {
  const root = document.documentElement;
  root.classList.add('js');
  let theme = null;
  // ?theme=light|dark (вбудування в чужу сторінку) важливіше за збережений вибір і нічого не запам'ятовує
  try { theme = new URLSearchParams(location.search).get('theme'); } catch (e) { /* без адреси */ }
  if (theme !== 'light' && theme !== 'dark') {
    try { theme = localStorage.getItem('theme'); } catch (e) { /* приватний режим */ }
  }
  if (theme !== 'light' && theme !== 'dark') {
    theme = matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  root.dataset.theme = theme;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.content = theme === 'light' ? '#f6f3ee' : '#0e1218';
} catch (e) { console.error(e); }
