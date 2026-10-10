try { (() => {
  // Клік по логотипу (шапка й футер) плавно підіймає на початок сторінки. Шапка закріплена,
  // тому перехід за #top нічого не прокручує: робимо це явно. Без JS працює звичайний якір.
  document.querySelectorAll('a.logo[href="#top"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
      e.preventDefault();
      const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
      document.body.classList.remove('menu-open');
    });
  });
})(); } catch (e) { console.error(e); }
