// Тема до першого малювання, щоб не було спалаху. Без збереженого вибору береться системна.
try {
  const root = document.documentElement;
  root.classList.add('js');
  // після перемикання мови сторінка лишається прихованою, доки 12-lang.js не відновить прокрутку
  try {
    if (sessionStorage.getItem('lang-scroll')) {
      root.classList.add('lang-restore');
      setTimeout(() => root.classList.remove('lang-restore'), 1500);
    }
  } catch (e) { /* сховище недоступне */ }
  let theme = null;
  try { theme = localStorage.getItem('theme'); } catch (e) { /* приватний режим */ }
  if (theme !== 'light' && theme !== 'dark') {
    theme = matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  root.dataset.theme = theme;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.content = theme === 'light' ? '#f6f3ee' : '#0e1218';
} catch (e) { console.error(e); }
