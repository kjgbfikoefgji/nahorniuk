try { (() => {
  const nums = document.querySelectorAll('[data-count]');
  if (!nums.length) return;
  if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const run = (el) => {
    const to = Number(el.dataset.count);
    const plus = el.hasAttribute('data-plus') ? '+' : '';
    const t0 = performance.now();
    const dur = 1100;
    const tick = (now) => {
      const p = Math.min(1, (now - t0) / dur);
      el.textContent = Math.round(to * (1 - Math.pow(1 - p, 3))) + (p === 1 ? plus : '');
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (!en.isIntersecting) return;
      run(en.target);
      io.unobserve(en.target);
    });
  }, { threshold: 0.6 });
  nums.forEach((el) => io.observe(el));
})(); } catch (e) { console.error(e); }
