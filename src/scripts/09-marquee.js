try { (() => {
  // Стрічки відгуків на десктопі з мишею: біжать самі, але їх можна гортати вручну: перетягнути мишею,
  // колесо/тачпад убік або стрілки (кнопки біля паузи). Наведення курсора ставить біг на паузу.
  // Копії карток приховані від AT. На телефоні, сенсорному екрані, з reduced-motion або без JS відгуки
  // лишаються звичайною сіткою карток, яку зручно читати.
  const fine = matchMedia('(min-width: 760px) and (hover: hover) and (pointer: fine)').matches;
  if (!fine || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const rows = [...document.querySelectorAll('[data-marquee]')];
  const SPEED = 40; // px/с
  const root = document.documentElement;
  const st = [];
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
    const s = { m, track, dir: m.classList.contains('marquee-rev') ? -1 : 1, pos: 0, half: 0, hover: false, drag: false };
    const measure = () => { s.half = track.scrollWidth / 2; };
    measure();
    s.pos = s.dir < 0 ? s.half : 0;
    window.addEventListener('resize', measure);
    st.push(s);

    // перетягування мишею
    let sx = 0, sp = 0;
    m.addEventListener('pointerdown', (e) => {
      if (e.pointerType !== 'mouse' || e.button) return;
      s.drag = true; sx = e.clientX; sp = s.pos;
      m.classList.add('is-grabbing');
      m.setPointerCapture(e.pointerId);
    });
    m.addEventListener('pointermove', (e) => { if (s.drag) s.pos = sp - (e.clientX - sx); });
    const end = () => { s.drag = false; m.classList.remove('is-grabbing'); };
    m.addEventListener('pointerup', end);
    m.addEventListener('pointercancel', end);
    m.addEventListener('mouseenter', () => { s.hover = true; });
    m.addEventListener('mouseleave', () => { s.hover = false; });
    // колесо або тачпад убік (вертикальна прокрутка сторінки не чіпається)
    m.addEventListener('wheel', (e) => {
      const dx = e.deltaX || (e.shiftKey ? e.deltaY : 0);
      if (!dx || (!e.shiftKey && Math.abs(e.deltaX) < Math.abs(e.deltaY))) return;
      e.preventDefault();
      s.pos += dx;
    }, { passive: false });
  });
  if (!st.length) return;
  document.querySelector('.reviews')?.classList.add('has-marquee');

  // кнопки: плавний крок на ширину картки, обидва ряди їдуть в один бік
  let kick = 0;
  const step = (sign) => { kick += sign * 380; };
  document.querySelector('[data-marquee-prev]')?.addEventListener('click', () => step(-1));
  document.querySelector('[data-marquee-next]')?.addEventListener('click', () => step(1));

  let last = performance.now();
  const frame = (now) => {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    const k = kick * Math.min(1, dt * 9);
    kick -= k;
    if (Math.abs(kick) < 0.5) kick = 0;
    const paused = root.classList.contains('motion-paused');
    st.forEach((s) => {
      if (!paused && !s.hover && !s.drag) s.pos += s.dir * SPEED * dt;
      s.pos += k;
      if (s.half) s.pos = ((s.pos % s.half) + s.half) % s.half;
      s.m.scrollLeft = s.pos;
    });
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
})(); } catch (e) { console.error(e); }
