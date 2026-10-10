try { (() => {
  // Мова: повний переклад без перезавантаження. Словник (src/data/i18n-en.json) вшитий у сторінку:
  // ключ це точний український текст вузла чи атрибута. Перемикач ходить по текстових вузлах і
  // атрибутах, оригінали пам'ятає в WeakMap (повернення бере їх, а не здогад). Підхід як на Katsko.
  const DICT = {{ json "data/i18n-en.json" }};
  const KEY = 'lang';
  const ATTRS = ['alt', 'aria-label', 'placeholder', 'title', 'content', 'data-cap'];
  const btn = document.querySelector('.lang');
  if (!btn) return;
  const has = (k) => Object.prototype.hasOwnProperty.call(DICT, k);
  const origText = new WeakMap();
  const origAttr = new WeakMap();
  let lang = 'uk';
  try { if (localStorage.getItem(KEY) === 'en') lang = 'en'; } catch (e) { /* сховище недоступне */ }
  let own = false; // власні правки спостерігач ігнорує

  const text = (node, en) => {
    const p = node.parentElement;
    if (!p || p.tagName === 'SCRIPT' || p.tagName === 'STYLE') return;
    if (en) {
      const t = node.textContent.trim();
      if (!t || !has(t)) return;
      origText.set(node, node.textContent);
      node.textContent = node.textContent.replace(t, () => DICT[t]);
    } else {
      const was = origText.get(node);
      if (was === undefined) return;
      node.textContent = was;
      origText.delete(node);
    }
  };

  const attrs = (el, en) => {
    if (!el.getAttribute) return;
    for (const a of ATTRS) {
      if (en) {
        const v = el.getAttribute(a);
        if (!v || !has(v.trim())) continue;
        const saved = origAttr.get(el) || {};
        saved[a] = v;
        origAttr.set(el, saved);
        el.setAttribute(a, DICT[v.trim()]);
      } else {
        const saved = origAttr.get(el);
        if (!saved || saved[a] === undefined) continue;
        el.setAttribute(a, saved[a]);
        delete saved[a];
      }
    }
  };

  const translate = (root, en) => {
    if (root.nodeType === 3) { text(root, en); return; }
    if (root.nodeType !== 1 && root.nodeType !== 9 && root.nodeType !== 11) return;
    const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walk.nextNode())) text(n, en);
    if (root.nodeType === 1) attrs(root, en);
    if (root.querySelectorAll) root.querySelectorAll('*').forEach((e) => attrs(e, en));
  };

  // Те, що скрипти ставлять уже в браузері (підписи кнопок меню й паузи, підпис у перегляді фото),
  // у розмітці не лежить. Спостерігач живе лише в англійській версії.
  const observer = new MutationObserver((changes) => {
    if (own || lang !== 'en') return;
    own = true;
    for (const c of changes) {
      if (c.type === 'childList') c.addedNodes.forEach((n) => translate(n, true));
      else if (c.type === 'characterData') text(c.target, true);
      else if (c.type === 'attributes') attrs(c.target, true);
    }
    own = false;
  });
  const watch = () => {
    if (lang === 'en') {
      observer.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTRS });
    } else {
      observer.disconnect();
    }
  };

  const apply = () => {
    own = true;
    const en = lang === 'en';
    translate(document.head, en);
    translate(document.body, en);
    document.documentElement.lang = lang;
    // ім'я кнопки стале («English»), стан несе лише aria-checked
    btn.setAttribute('aria-checked', String(en));
    own = false;
    watch();
  };

  btn.addEventListener('click', () => {
    lang = lang === 'en' ? 'uk' : 'en';
    try { localStorage.setItem(KEY, lang); } catch (e) { /* сховище недоступне */ }
    // сотні вузлів міняються одним махом: startViewTransition розчиняє два знімки на композиторі,
    // тому швидко й без перерахунку розкладки щокадру
    const motion = !matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!motion || !document.startViewTransition) { apply(); return; }
    const root = document.documentElement;
    root.dataset.langAnim = '';
    const t = document.startViewTransition(apply);
    t.ready.catch(() => {});
    const done = () => root.removeAttribute('data-lang-anim');
    t.finished.then(done, done);
  });

  if (lang === 'en') apply();
})(); } catch (e) { console.error(e); }
