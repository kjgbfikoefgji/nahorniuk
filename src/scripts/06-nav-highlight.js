try { (() => {
  if (!('IntersectionObserver' in window)) return;
  const links = [...document.querySelectorAll('.nav a[href^="#"]')];
  const map = new Map();
  links.forEach((a) => {
    const sec = document.getElementById(a.getAttribute('href').slice(1));
    if (sec) map.set(sec, a);
  });
  // герой, «Як це працює», умови, заклик і футер не мають пункту меню: на них підсвітка знімається
  const none = ['.hero', '#how', '#terms', '.cta', '.site-footer'].map((q) => document.querySelector(q)).filter(Boolean);
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (!en.isIntersecting) return;
      if (none.includes(en.target)) { links.forEach((l) => l.removeAttribute('aria-current')); return; }
      const a = map.get(en.target);
      if (!a) return;
      links.forEach((l) => l.removeAttribute('aria-current'));
      a.setAttribute('aria-current', 'true');
    });
  }, { rootMargin: '-40% 0px -55% 0px' });
  map.forEach((_, sec) => io.observe(sec));
  none.forEach((sec) => io.observe(sec));
})(); } catch (e) { console.error(e); }
