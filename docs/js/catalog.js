/* ═══════════════════════════════════════════════════════════
   МЗТ — каталог: подбор, сортировка, вывод карточек.
   Данные лежат в data/catalog.js (window.MZT_CATALOG): прототип
   открывают с диска, а по file:// браузер запрещает fetch.
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  var DATA = window.MZT_CATALOG;
  var grid = document.getElementById('catGrid');
  if (!DATA || !grid) return;

  var form   = document.getElementById('catFilters');
  var countEl = document.getElementById('catCount');
  var emptyEl = document.getElementById('catEmpty');
  var resetEl = document.getElementById('catReset');
  var sortEl  = document.getElementById('catSort');

  /* Выбранное: имя условия -> набор значений */
  var picked = {};

  /* Цвет в выгрузке бывает составным: «Бежевый;Коричневый» */
  function colorsOf(product) {
    return (product.color || '').split(';').map(function (c) { return c.trim(); }).filter(Boolean);
  }

  function optionValues(name) {
    var o = (DATA.options || []).filter(function (x) { return x.name === name; })[0];
    return o ? o.values : [];
  }

  /* Цена товара при выбранных толщине и плотности: если условие задано,
     берём только подходящие варианты, иначе — самый дешёвый */
  function priceOf(product) {
    var vs = product.variants.filter(function (v) {
      return ['Толщина панели', 'Плотность ППС'].every(function (name) {
        var want = picked[name];
        return !want || !want.length || want.indexOf(v.options[name]) !== -1;
      });
    });
    if (!vs.length) vs = product.variants;
    var prices = vs.map(function (v) { return v.price; }).filter(Boolean);
    var olds   = vs.map(function (v) { return v.price_old; }).filter(Boolean);
    return { min: Math.min.apply(null, prices), old: olds.length ? Math.min.apply(null, olds) : null };
  }

  function matches(product) {
    if ((picked.brand || []).length && picked.brand.indexOf(product.brand) === -1) return false;
    if ((picked.color || []).length) {
      var mine = colorsOf(product);
      var hit = picked.color.some(function (c) { return mine.indexOf(c) !== -1; });
      if (!hit) return false;
    }
    return ['Толщина панели', 'Плотность ППС'].every(function (name) {
      var want = picked[name];
      if (!want || !want.length) return true;
      return product.variants.some(function (v) { return want.indexOf(v.options[name]) !== -1; });
    });
  }

  var money = function (n) {
    return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + ' ₽';
  };

  function card(product) {
    var p = priceOf(product);
    var props = [product.design, colorsOf(product).join(', ')].filter(Boolean).join(' · ');
    var a = document.createElement('a');
    a.className = 'pcard';
    a.href = 'product.html?id=' + encodeURIComponent(product.id);
    a.innerHTML =
      '<div class="pcard__media">' +
        (product.mark ? '<span class="pcard__mark">' + product.mark + '</span>' : '') +
        '<img src="' + product.thumb + '" alt="' + product.title.replace(/"/g, '&quot;') + '"' +
        ' width="520" height="520" loading="lazy" decoding="async">' +
      '</div>' +
      '<div class="pcard__body">' +
        '<p class="pcard__brand">' + product.brand + '</p>' +
        '<h2 class="pcard__title">' + product.title + '</h2>' +
        (props ? '<p class="pcard__props">' + props + '</p>' : '') +
        '<p class="pcard__price-row">' +
          '<span class="pcard__price">от ' + money(p.min) + ' <span>за ' + (product.unit || 'шт.') + '</span></span>' +
          (p.old && p.old > p.min ? '<span class="pcard__old">' + money(p.old) + '</span>' : '') +
        '</p>' +
      '</div>';
    return a;
  }

  function render() {
    var list = DATA.products.filter(matches);
    var mode = sortEl ? sortEl.value : 'default';
    if (mode === 'price-asc')  list.sort(function (a, b) { return priceOf(a).min - priceOf(b).min; });
    if (mode === 'price-desc') list.sort(function (a, b) { return priceOf(b).min - priceOf(a).min; });
    if (mode === 'title')      list.sort(function (a, b) { return a.title.localeCompare(b.title, 'ru'); });

    grid.textContent = '';
    list.forEach(function (p) { grid.appendChild(card(p)); });

    var word = list.length % 10 === 1 && list.length % 100 !== 11 ? 'товар'
             : ([2, 3, 4].indexOf(list.length % 10) !== -1 && (list.length % 100 < 10 || list.length % 100 >= 20)) ? 'товара'
             : 'товаров';
    countEl.innerHTML = '<strong>' + list.length + '</strong> ' + word +
      (list.length === DATA.products.length ? '' : ' из ' + DATA.products.length);
    emptyEl.hidden = list.length > 0;

    var anyPicked = Object.keys(picked).some(function (k) { return picked[k] && picked[k].length; });
    resetEl.hidden = !anyPicked;
  }

  /* Кнопки подбора собираются из самих данных */
  function buildChips() {
    form.querySelectorAll('[data-filter]').forEach(function (box) {
      var name = box.getAttribute('data-filter');
      var values = name === 'brand' ? DATA.brands
                 : name === 'color' ? DATA.colors.join(';').split(';').filter(function (v, i, a) {
                     return v && a.indexOf(v) === i;
                   }).sort(function (a, b) { return a.localeCompare(b, 'ru'); })
                 : optionValues(name);
      values.forEach(function (v) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'cat__chip';
        b.textContent = v;
        b.setAttribute('aria-pressed', 'false');
        b.addEventListener('click', function () {
          picked[name] = picked[name] || [];
          var i = picked[name].indexOf(v);
          if (i === -1) picked[name].push(v); else picked[name].splice(i, 1);
          b.setAttribute('aria-pressed', i === -1 ? 'true' : 'false');
          render();
        });
        box.appendChild(b);
      });
    });
  }

  resetEl.addEventListener('click', function () {
    picked = {};
    form.querySelectorAll('[aria-pressed="true"]').forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
    render();
  });
  if (sortEl) sortEl.addEventListener('change', render);
  form.addEventListener('submit', function (e) { e.preventDefault(); });

  buildChips();
  render();
})();
