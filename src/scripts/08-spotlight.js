try { (() => {
  // Підсвітка під курсором на картках: CSS-змінні --mx/--my читає radial-gradient у .card::before
  if (!matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  let raf = 0;
  document.addEventListener('pointermove', (e) => {
    const card = e.target.closest && e.target.closest('.card, .result');
    if (!card) return;
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => {
      const r = card.getBoundingClientRect();
      card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      card.style.setProperty('--my', (e.clientY - r.top) + 'px');
    });
  }, { passive: true });
})(); } catch (e) { console.error(e); }
