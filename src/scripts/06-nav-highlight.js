try { (() => {
  if (!('IntersectionObserver' in window)) return;
  const links = [...document.querySelectorAll('.nav a[href^="#"]')];
  const map = new Map();
  links.forEach((a) => {
    const sec = document.getElementById(a.getAttribute('href').slice(1));
    if (sec) map.set(sec, a);
  });
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      const a = map.get(en.target);
      if (!a) return;
      if (en.isIntersecting) {
        links.forEach((l) => l.removeAttribute('aria-current'));
        a.setAttribute('aria-current', 'true');
      }
    });
  }, { rootMargin: '-40% 0px -55% 0px' });
  map.forEach((_, sec) => io.observe(sec));
})(); } catch (e) { console.error(e); }
