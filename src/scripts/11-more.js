try { (() => {
  // «Показати ще» для довгих списків (результати, відгуки). Згортаємо лише з JS, без нього все видно;
  // що саме сховати, вирішує CSS (тільки на телефоні, до 640px). data-more на кнопці це селектор елементів
  // списку: після розгортання фокус переходить на перший щойно показаний, бо кнопка зникає.
  document.querySelectorAll('[data-more]').forEach((btn) => {
    const list = document.getElementById(btn.getAttribute('aria-controls'));
    if (!list) return;
    list.classList.add('is-collapsed');
    btn.addEventListener('click', () => {
      const first = [...list.querySelectorAll(btn.dataset.more)].find((el) => !el.getClientRects().length);
      list.classList.remove('is-collapsed');
      btn.setAttribute('aria-expanded', 'true');
      if (!first) return;
      if (!first.matches('a, button')) first.setAttribute('tabindex', '-1');
      first.focus({ preventScroll: true });
    });
  });
})(); } catch (e) { console.error(e); }
