try { (() => {
  // Нескінченна стрічка відгуків: копіюємо картки (копія прихована від AT).
  // Біжить лише на десктопі з мишею (наведення ставить на паузу). На телефоні, сенсорному екрані,
  // з reduced-motion або без JS відгуки лишаються звичайною сіткою карток, яку зручно читати.
  const fine = matchMedia('(min-width: 760px) and (hover: hover) and (pointer: fine)').matches;
  if (!fine || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const rows = document.querySelectorAll('[data-marquee]');
  rows.forEach((m) => {
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
  if (rows.length) document.querySelector('.reviews')?.classList.add('has-marquee');
})(); } catch (e) { console.error(e); }
