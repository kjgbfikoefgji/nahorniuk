try { (() => {
  // Нескінченна стрічка відгуків: копіюємо картки (копія прихована від AT). Без JS або з
  // reduced-motion лишається звичайний ряд із горизонтальним прокручуванням.
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  document.querySelectorAll('[data-marquee]').forEach((m) => {
    const track = m.querySelector('.track');
    if (!track) return;
    [...track.children].forEach((li) => {
      const c = li.cloneNode(true);
      c.setAttribute('aria-hidden', 'true');
      c.setAttribute('inert', '');
      track.appendChild(c);
    });
    m.classList.add('is-running');
  });
})(); } catch (e) { console.error(e); }
