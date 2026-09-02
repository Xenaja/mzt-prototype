/* ═══════════════════════════════════════════════════════════
   МЗТ — карточка товара в списке. Одна на каталог и на блок
   «Смотрите также» в карточке: раньше во втором месте была
   урезанная копия без свойств, метки и старой цены.
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  function money(n) {
    return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + ' ₽';
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c];
    });
  }

  /* Цвет в выгрузке бывает составным: «Бежевый;Коричневый» */
  function colorsOf(product) {
    return (product.color || '').split(';')
      .map(function (c) { return c.trim(); })
      .filter(Boolean);
  }

  /* Цена при выбранных условиях подбора: если толщина или плотность заданы,
     считаем только по подходящим вариантам, иначе — по всем. */
  function priceOf(product, picked) {
    picked = picked || {};
    var names = ['Толщина панели', 'Плотность ППС'];
    var list = product.variants.filter(function (v) {
      return names.every(function (name) {
        var want = picked[name];
        return !want || !want.length || want.indexOf(v.options[name]) !== -1;
      });
    });
    if (!list.length) list = product.variants;

    var prices = list.map(function (v) { return v.price; }).filter(Boolean);
    var olds   = list.map(function (v) { return v.price_old; }).filter(Boolean);
    return {
      min: Math.min.apply(null, prices),
      old: olds.length ? Math.min.apply(null, olds) : null
    };
  }

  /* Разметка карточки. Заголовок задаётся уровнем: в каталоге это h2,
     в блоке «Смотрите также» — h3, иначе уровни пойдут вразнобой. */
  function markup(product, opts) {
    opts = opts || {};
    var p = priceOf(product, opts.picked);
    var tag = opts.headingTag || 'h2';
    var props = [product.design, colorsOf(product).join(', ')].filter(Boolean).join(' · ');

    return '<div class="pcard__media">' +
        (product.mark ? '<span class="pcard__mark">' + esc(product.mark) + '</span>' : '') +
        '<img src="' + product.thumb + '" alt="' + esc(product.title) + '"' +
        ' width="520" height="390" loading="lazy" decoding="async">' +
      '</div>' +
      '<div class="pcard__body">' +
        '<p class="pcard__brand">' + esc(product.brand) + '</p>' +
        '<' + tag + ' class="pcard__title">' + esc(product.title) + '</' + tag + '>' +
        (props ? '<p class="pcard__props">' + esc(props) + '</p>' : '') +
        '<p class="pcard__price-row">' +
          '<span class="pcard__price">от ' + money(p.min) +
          ' <span>за ' + esc(product.unit || 'шт.') + '</span></span>' +
          (p.old && p.old > p.min ? '<span class="pcard__old">' + money(p.old) + '</span>' : '') +
        '</p>' +
      '</div>';
  }

  function build(product, opts) {
    var a = document.createElement('a');
    a.className = 'pcard';
    a.href = 'product.html?id=' + encodeURIComponent(product.id);
    a.innerHTML = markup(product, opts);
    return a;
  }

  window.MZTCard = { build: build, markup: markup, priceOf: priceOf, colorsOf: colorsOf, money: money };
})();
