/* ═══════════════════════════════════════════════════════════
   МЗТ — карточка товара. Собирается по номеру из адреса
   (product.html?id=…) на данных из data/catalog.js.
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  var DATA = window.MZT_CATALOG;
  var root = document.getElementById('productRoot');
  if (!DATA || !root) return;

  var id = new URLSearchParams(location.search).get('id');
  var product = DATA.products.filter(function (p) { return p.id === id; })[0] || DATA.products[0];

  var money = function (n) {
    return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + ' ₽';
  };

  var esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c];
    });
  };

  /* aria-labelledby принимает список id через пробел, а «Толщина панели»
     сам пробел содержит — браузер читал id="opt-Толщина панели" как два
     несуществующих id вместо одного, и группа оставалась без имени
     для скринридера. Дефис вместо пробела снимает разбор на токены. */
  var slug = function (s) { return String(s).replace(/\s+/g, '-'); };

  /* Выбранные толщина и плотность: по умолчанию самый дешёвый вариант */
  var cheapest = product.variants.slice().sort(function (a, b) { return a.price - b.price; })[0];
  var chosen = {};
  Object.keys(cheapest.options).forEach(function (k) { chosen[k] = cheapest.options[k]; });

  function variantFor(selection) {
    return product.variants.filter(function (v) {
      return Object.keys(selection).every(function (k) { return v.options[k] === selection[k]; });
    })[0];
  }

  function currentVariant() {
    return variantFor(chosen) || cheapest;
  }

  function optionNames() {
    return (DATA.options || []).map(function (o) { return o.name; })
      .filter(function (n) { return product.variants.some(function (v) { return v.options[n]; }); });
  }

  function valuesFor(name) {
    var seen = [];
    product.variants.forEach(function (v) {
      if (v.options[name] && seen.indexOf(v.options[name]) === -1) seen.push(v.options[name]);
    });
    return seen;
  }

  /* Похожие: тот же бренд или та же отделка */
  function sameProducts() {
    return DATA.products.filter(function (p) {
      return p.id !== product.id && (p.brand === product.brand || p.design === product.design);
    }).slice(0, 4);
  }

  /* Кнопка выбора недоступна, если сочетание с уже выбранными значениями
     других групп не находит варианта в выгрузке — иначе цену и артикул
     показывали от совсем другого сочетания молча, без предупреждения
     (так было с одной строкой у Керамин Куба 2, где в данных нет пары
     «100 мм / 16», а кнопки её всё равно позволяли выбрать). */
  function combinationExists(name, val) {
    var test = {};
    Object.keys(chosen).forEach(function (k) { test[k] = chosen[k]; });
    test[name] = val;
    return !!variantFor(test);
  }

  /* ─── Статичная часть: один раз при загрузке ───
     Фото, вкладки, похожие товары и структура выбора не зависят от того,
     какая толщина/плотность выбрана — их не трогаем при каждом клике. */
  function renderStatic() {
    var opts = optionNames().map(function (name) {
      var gid = 'opt-' + slug(name);
      return '<div class="popt">' +
        '<span class="popt__name" id="' + gid + '">' + esc(name) + '</span>' +
        '<div class="popt__row" role="group" aria-labelledby="' + gid + '">' +
          valuesFor(name).map(function (val) {
            return '<button class="popt__btn" type="button" data-opt="' + esc(name) + '" data-val="' + esc(val) + '"' +
              ' aria-pressed="false">' + esc(val) + '</button>';
          }).join('') +
        '</div></div>';
    }).join('');

    var specs = (product.specs || []).map(function (s) {
      return '<div class="pspecs__row"><span class="pspecs__key">' + esc(s[0]) +
             '</span><span class="pspecs__val">' + esc(s[1]) + '</span></div>';
    }).join('');

    var tabs = product.tabs || [];
    var tabList = tabs.map(function (t, i) {
      return '<button class="ptabs__btn" type="button" role="tab" id="tab-' + i + '"' +
             ' aria-controls="panel-' + i + '" aria-selected="' + (i === 0) + '">' + esc(t.label) + '</button>';
    }).join('');
    var tabPanels = tabs.map(function (t, i) {
      return '<div class="ptabs__panel" role="tabpanel" id="panel-' + i + '" aria-labelledby="tab-' + i + '"' +
             (i === 0 ? '' : ' hidden') + '><h2>' + esc(t.title) + '</h2><p>' + esc(t.text) + '</p></div>';
    }).join('');

    var also = sameProducts().map(function (p) {
      return '<a class="pcard" href="product.html?id=' + encodeURIComponent(p.id) + '">' +
        window.MZTCard.markup(p, { headingTag: 'h3' }) + '</a>';
    }).join('');

    var crumbs =
      '<section class="page-head"><div class="page-head__inner">' +
        '<p class="page-head__crumbs"><a href="index.html">Главная</a><span aria-hidden="true">→</span>' +
        '<a href="catalog.html">Каталог</a><span aria-hidden="true">→</span><span>' + esc(product.title) + '</span></p>' +
      '</div></section>';

    var gallery =
      '<div class="pgal">' +
        '<button class="pgal__main" type="button" id="pgalMain" aria-label="Открыть снимок на весь экран">' +
          '<img src="' + product.photos[0] + '" alt="' + esc(product.title) + '" width="900" height="675">' +
        '</button>' +
        '<div class="pgal__thumbs">' +
          product.photos.map(function (src, i) {
            return '<button class="pgal__thumb" type="button" data-photo="' + i + '"' +
              ' aria-current="' + (i === 0) + '" aria-label="Снимок ' + (i + 1) + '">' +
              '<img src="' + src + '" alt="" width="200" height="200" loading="lazy"></button>';
          }).join('') +
        '</div>' +
      '</div>';

    var info =
      '<div class="pinfo">' +
        '<div class="pinfo__brand-row">' +
          '<p class="pinfo__brand">' + esc(product.brand) + '</p>' +
          (product.mark ? '<span class="pinfo__mark">' + esc(product.mark) + '</span>' : '') +
        '</div>' +
        '<h1 class="pinfo__title">' + esc(product.title) + '</h1>' +
        opts +
        '<p class="pprice">' +
          '<span class="pprice__now" id="priceNow"></span>' +
          '<span class="pprice__old" id="priceOld" hidden></span>' +
          '<span class="pprice__sku" id="priceSku" hidden></span>' +
        '</p>' +
        '<div class="pinfo__actions">' +
          '<button class="btn btn--accent" type="button" data-open-calculator>Рассчитать стоимость</button>' +
          '<a class="btn btn--light" href="index.html#request">Заказать консультацию</a>' +
          '<a class="btn btn--dark" href="visualizer.html">Визуализатор</a>' +
        '</div>' +
        '<div class="pspecs">' + specs + '</div>' +
      '</div>';

    root.removeAttribute('data-loading');
    root.innerHTML = crumbs +
      '<section class="prod-page"><div class="section-inner">' +
        '<div class="prod-top">' + gallery + info + '</div>' +
        (tabs.length ? '<div class="ptabs"><div class="ptabs__list" role="tablist">' + tabList + '</div>' + tabPanels + '</div>' : '') +
        (also ? '<section class="palso"><h2 class="palso__title">Смотрите также</h2><div class="palso__grid">' + also + '</div></section>' : '') +
      '</div></section>';

    document.title = product.title + ' — Московский Завод Термопанелей';
  }

  /* ─── Цена, артикул и состояния кнопок: при каждом клике по параметру ───
     Раньше клик перерисовывал весь #productRoot — сброшенными оказывались
     открытая фотография, активная вкладка и фокус (уходил на <body> вместе
     с уничтоженной кнопкой). Теперь трогаем только то, что действительно
     меняется от выбора толщины и плотности. */
  function updateSelection() {
    var v = currentVariant();

    root.querySelectorAll('.popt__btn').forEach(function (btn) {
      var name = btn.getAttribute('data-opt');
      var val = btn.getAttribute('data-val');
      btn.setAttribute('aria-pressed', chosen[name] === val ? 'true' : 'false');
      var ok = combinationExists(name, val);
      btn.disabled = !ok;
      btn.setAttribute('aria-disabled', String(!ok));
    });

    document.getElementById('priceNow').innerHTML =
      money(v.price) + ' <span>за ' + esc(product.unit || 'шт.') + '</span>';

    var oldEl = document.getElementById('priceOld');
    if (v.price_old && v.price_old > v.price) {
      oldEl.hidden = false;
      oldEl.textContent = money(v.price_old);
    } else {
      oldEl.hidden = true;
    }

    /* У одной строки в выгрузке артикул относится к другому сочетанию
       (см. prepare_catalog.py, check_variants) — на этот случай sku
       приходит пустым, и строку с артикулом просто не показываем,
       вместо того чтобы показать заведомо неверный номер. */
    var skuEl = document.getElementById('priceSku');
    if (v.sku) {
      skuEl.hidden = false;
      skuEl.textContent = 'артикул ' + v.sku;
    } else {
      skuEl.hidden = true;
    }
  }

  /* ─── Нажатия: выбор параметра, снимок, вкладка ─── */
  root.addEventListener('click', function (e) {
    var opt = e.target.closest('[data-opt]');
    if (opt) {
      chosen[opt.getAttribute('data-opt')] = opt.getAttribute('data-val');
      updateSelection();
      return;
    }

    var thumb = e.target.closest('[data-photo]');
    if (thumb) {
      var i = +thumb.getAttribute('data-photo');
      document.getElementById('pgalMain').querySelector('img').src = product.photos[i];
      root.querySelectorAll('[data-photo]').forEach(function (t) {
        t.setAttribute('aria-current', t === thumb ? 'true' : 'false');
      });
      return;
    }

    var tab = e.target.closest('.ptabs__btn');
    if (tab) {
      root.querySelectorAll('.ptabs__btn').forEach(function (b) {
        var on = b === tab;
        b.setAttribute('aria-selected', on);
        document.getElementById(b.getAttribute('aria-controls')).hidden = !on;
      });
    }
  });

  renderStatic();
  updateSelection();
})();
