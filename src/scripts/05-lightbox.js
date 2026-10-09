try { (() => {
  const dlg = document.getElementById('lightbox');
  if (!dlg || typeof dlg.showModal !== 'function') return;
  const triggers = [...document.querySelectorAll('[data-lb]')];
  const img = document.getElementById('lb-img');
  const cap = document.getElementById('lb-cap');
  let cur = 0;
  let opener = null;

  const show = (i) => {
    cur = (i + triggers.length) % triggers.length;
    const t = triggers[cur];
    img.src = t.dataset.full;
    img.alt = t.querySelector('img').alt;
    cap.textContent = t.dataset.cap;
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
  dlg.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') show(cur - 1);
    if (e.key === 'ArrowRight') show(cur + 1);
  });
})(); } catch (e) { console.error(e); }
