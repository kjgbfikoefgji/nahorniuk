try { (() => {
  // Липка кнопка на мобільному: з'являється після героя й ховається біля фінального CTA та футера.
  const bar = document.querySelector('[data-sticky-cta]');
  const hero = document.querySelector('.hero');
  const end = document.querySelector('.cta');
  if (!bar || !hero || !('IntersectionObserver' in window)) return;
  let pastHero = false;
  let atEnd = false;
  const update = () => bar.classList.toggle('on', pastHero && !atEnd);
  new IntersectionObserver(([en]) => { pastHero = !en.isIntersecting && en.boundingClientRect.top < 0; update(); }).observe(hero);
  if (end) new IntersectionObserver(([en]) => { atEnd = en.isIntersecting; update(); }).observe(end);
})(); } catch (e) { console.error(e); }
