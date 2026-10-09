try { (() => {
  const dlg = document.getElementById('lightbox');
  if (!dlg || typeof dlg.showModal !== 'function') return;
  const triggers = [...document.querySelectorAll('[data-lb]')];
  const img = document.getElementById('lb-img');
  const cap = document.getElementById('lb-cap');
  const count = document.getElementById('lb-count');
  let cur = 0;
  let opener = null;

  const show = (i) => {
    cur = (i + triggers.length) % triggers.length;
    const t = triggers[cur];
    img.src = t.dataset.full;
    img.alt = t.querySelector('img').alt;
    cap.textContent = t.dataset.cap;
    if (count) count.textContent = (cur + 1) + ' / ' + triggers.length;
  };
  const open = (i) => {
    opener = triggers[i];
    show(i);
    dlg.showModal();
    document.body.classList.add('lb-open');
  };
  triggers.forEach((t, i) => t.addEventListener('click', () => open(i)));
  dlg.querySelector('[data-lb-prev]').addEventListener('click', () => show(cur - 1));
  dlg.querySelector('[data-lb-next]').addEventListener('click', () => show(cur + 1));
  dlg.querySelector('[data-lb-close]').addEventListener('click', () => dlg.close());
  // клік по затемненню (поза фігурою) закриває
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
  dlg.addEventListener('close', () => {
    document.body.classList.remove('lb-open');
    img.removeAttribute('src');
    if (opener) opener.focus();
  });
  // свайп убік на телефоні гортає фото (вертикальний рух ігноруємо)
  let sx = 0, sy = 0;
  dlg.addEventListener('touchstart', (e) => { sx = e.touches[0].clientX; sy = e.touches[0].clientY; }, { passive: true });
  dlg.addEventListener('touchend', (e) => {
    const dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
    if (Math.abs(dx) > 48 && Math.abs(dx) > Math.abs(dy) * 1.5) show(cur + (dx < 0 ? 1 : -1));
  }, { passive: true });
  dlg.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') show(cur - 1);
    if (e.key === 'ArrowRight') show(cur + 1);
  });
})(); } catch (e) { console.error(e); }
