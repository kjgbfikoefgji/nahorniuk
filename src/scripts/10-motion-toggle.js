try { (() => {
  // Пауза для рухомого контенту (WCAG 2.2.2): одна кнопка-перемикач на всіх стрічках, вибір пам'ятається
  const root = document.documentElement;
  const btns = [...document.querySelectorAll('[data-motion-toggle]')];
  if (!btns.length) return;
  const KEY = 'motion-paused';
  const set = (paused) => {
    root.classList.toggle('motion-paused', paused);
    btns.forEach((b) => {
      b.setAttribute('aria-pressed', String(paused));
      b.setAttribute('aria-label', paused ? 'Відновити анімацію стрічок' : 'Призупинити анімацію стрічок');
      const t = b.querySelector('.motion-label');
      if (t) t.textContent = paused ? 'Відновити' : 'Пауза';
    });
  };
  let saved = false;
  try { saved = localStorage.getItem(KEY) === '1'; } catch (e) { /* сховище недоступне */ }
  if (saved) set(true);
  btns.forEach((b) => b.addEventListener('click', () => {
    const next = !root.classList.contains('motion-paused');
    set(next);
    try { localStorage.setItem(KEY, next ? '1' : '0'); } catch (e) { /* сховище недоступне */ }
  }));
})(); } catch (e) { console.error(e); }
