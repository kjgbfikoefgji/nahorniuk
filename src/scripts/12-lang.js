try { (() => {
  // Перемикач UA / EN: замість стрибка на початок нової сторінки запам'ятовуємо, яку секцію
  // (її номер у <main>) і з якого зсуву видно зараз, плавно згасаємо, а на новій сторінці
  // відновлюємо те саме місце й плавно проявляємось. Без JS лінки просто ведуть на / і /en/.
  const KEY = 'lang-scroll';
  const root = document.documentElement;
  const sections = [...document.querySelectorAll('main > section')];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // відновлення (нова сторінка)
  let saved = null;
  try { saved = JSON.parse(sessionStorage.getItem(KEY) || 'null'); sessionStorage.removeItem(KEY); } catch (e) { /* не критично */ }
  if (saved && sections[saved.i] && Date.now() - saved.t < 10000) {
    const s = sections[saved.i];
    const y = s.getBoundingClientRect().top + window.scrollY + Math.min(saved.off, Math.max(0, s.offsetHeight - 200));
    window.scrollTo({ top: Math.max(0, y), behavior: 'instant' });
  }
  root.classList.remove('lang-restore');
  if (saved && !reduce) {
    root.classList.add('lang-in');
    setTimeout(() => root.classList.remove('lang-in'), 450);
  }

  // перехід (поточна сторінка)
  document.querySelectorAll('.lang-switch a').forEach((a) => {
    a.addEventListener('click', (e) => {
      if (a.getAttribute('aria-current') === 'true') { e.preventDefault(); return; }
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
      e.preventDefault();
      const probe = 96; // висота шапки з запасом: секція, що зараз під шапкою
      let i = 0;
      sections.forEach((s, n) => { if (s.getBoundingClientRect().top <= probe) i = n; });
      const off = Math.max(0, probe - sections[i].getBoundingClientRect().top);
      try { sessionStorage.setItem(KEY, JSON.stringify({ i, off: Math.round(off), t: Date.now() })); } catch (err) { /* не критично */ }
      const go = () => { location.href = a.href; };
      if (reduce) { go(); return; }
      root.classList.add('lang-out');
      setTimeout(go, 220);
    });
  });
  // «Назад» з кешу браузера не повинно лишати сторінку згаслою
  window.addEventListener('pageshow', (e) => { if (e.persisted) root.classList.remove('lang-out', 'lang-restore'); });
})(); } catch (e) { console.error(e); document.documentElement.classList.remove('lang-restore'); }
