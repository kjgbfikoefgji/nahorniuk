try { (() => {
  const items = document.querySelectorAll('.reveal');
  if (!items.length) return;
  const show = (el) => el.classList.add('in');
  if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) {
    items.forEach(show);
    return;
  }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (!en.isIntersecting) return;
      // невелика каскадна затримка для сусідів в одному рядку
      const idx = [...en.target.parentElement.children].indexOf(en.target);
      en.target.style.transitionDelay = Math.min(idx, 5) * 60 + 'ms';
      show(en.target);
      io.unobserve(en.target);
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  items.forEach((el) => io.observe(el));
})(); } catch (e) { console.error(e); }
