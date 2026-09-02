/* ═══════════════════════════════════════════════════════════
   МЗТ — галерея проектов и просмотр фото на весь экран.

   Требование из комментария к макету (блок «Готовые проекты»):
   «При нажатии фотография увеличивается на весь экран»,
   пример — brick-art.ru.

   Клик по любому снимку — главному или миниатюре — открывает просмотр.
   Внутри одного проекта фотографии листаются стрелками и клавишами.
   Миниатюры главное фото не подменяют: в карточке у каждого снимка свой
   кадр по макету. На весь экран открывается оригинал из data-full —
   тот файл, который дизайнер загрузил в Figma, в полном разрешении.
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  var box     = document.getElementById('lightbox');
  var img     = document.getElementById('lightboxImg');
  var counter = document.getElementById('lightboxCounter');
  if (!box || !img) return;

  var shots = [];      // текущий набор: [{src, alt}]
  var index = 0;
  var opener = null;   // куда вернуть фокус

  /* Собираем набор фотографий. Два случая: блок «Готовые проекты»
     на главной (главное фото плюс миниатюры) и галерея карточки товара,
     где миниатюры и есть полный набор. */
  function collect(project) {
    var out = [];
    /* Для просмотра берём оригинал из data-full: в карточке стоит рендер,
       выверенный по макету, а на весь экран показываем полноразмерный снимок. */
    var pick = function (el) {
      return { src: el.getAttribute('data-full') || el.getAttribute('src'),
               alt: el.getAttribute('alt') || '' };
    };
    if (project.classList.contains('pgal')) {
      project.querySelectorAll('.pgal__thumb img').forEach(function (t) { out.push(pick(t)); });
      return out;
    }
    var main = project.querySelector('.project__main img');
    if (main) out.push(pick(main));
    project.querySelectorAll('.project__thumb img').forEach(function (t) {
      out.push(pick(t));
    });
    return out;
  }

  function render() {
    var shot = shots[index];
    if (!shot) return;
    img.src = shot.src;
    img.alt = shot.alt;
    counter.textContent = (index + 1) + ' / ' + shots.length;
    var many = shots.length > 1;
    box.querySelector('[data-lb-prev]').hidden = !many;
    box.querySelector('[data-lb-next]').hidden = !many;
    counter.hidden = !many;
  }

  function open(project, startIndex) {
    shots = collect(project);
    if (!shots.length) return;
    index = Math.max(0, Math.min(startIndex, shots.length - 1));
    opener = document.activeElement;

    render();
    box.hidden = false;
    box.classList.add('is-open');
    document.body.classList.add('lightbox-lock');
    box.querySelector('[data-lb-close]').focus();
  }

  function close() {
    box.classList.remove('is-open');
    box.hidden = true;
    document.body.classList.remove('lightbox-lock');
    if (opener && opener.focus) opener.focus();
  }

  function step(delta) {
    if (shots.length < 2) return;
    index = (index + delta + shots.length) % shots.length;
    render();
  }

  /* ─── Открытие ─── */
  document.addEventListener('click', function (e) {
    var main = e.target.closest('.project__main');
    if (main) {
      open(main.closest('.project'), 0);
      return;
    }
    /* карточка товара: и большой снимок, и миниатюры под ним */
    var pgalMain = e.target.closest('.pgal__main');
    if (pgalMain) {
      var gal = pgalMain.closest('.pgal');
      var cur = gal.querySelector('.pgal__thumb[aria-current="true"]');
      var thumbs = Array.prototype.slice.call(gal.querySelectorAll('.pgal__thumb'));
      open(gal, Math.max(0, thumbs.indexOf(cur)));
      return;
    }
    var pgalThumb = e.target.closest('.pgal__thumb');
    if (pgalThumb && e.detail === 0) {
      /* с клавиатуры миниатюра открывает просмотр, мышью — просто меняет снимок */
      var g = pgalThumb.closest('.pgal');
      open(g, Array.prototype.slice.call(g.querySelectorAll('.pgal__thumb')).indexOf(pgalThumb));
      return;
    }

    var thumb = e.target.closest('.project__thumb');
    if (thumb) {
      var project = thumb.closest('.project');
      var all = Array.prototype.slice.call(project.querySelectorAll('.project__thumb'));
      /* +1 — первым в наборе идёт главное фото */
      open(project, all.indexOf(thumb) + 1);
    }
  });

  /* ─── Управление просмотром ─── */
  box.addEventListener('click', function (e) {
    if (e.target.closest('[data-lb-close]')) { close(); return; }
    if (e.target.closest('[data-lb-prev]'))  { step(-1); return; }
    if (e.target.closest('[data-lb-next]'))  { step(1);  return; }
    if (e.target === box) close();            // клик по фону
  });

  document.addEventListener('keydown', function (e) {
    if (!box.classList.contains('is-open')) return;
    if (e.key === 'Escape')     { close(); }
    else if (e.key === 'ArrowLeft')  { step(-1); }
    else if (e.key === 'ArrowRight') { step(1); }
    else if (e.key === 'Tab') {
      /* удерживаем фокус внутри просмотра */
      var focusable = Array.prototype.slice.call(
        box.querySelectorAll('button:not([hidden])')
      ).filter(function (el) { return el.offsetParent !== null; });
      if (!focusable.length) return;
      var first = focusable[0], last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

})();
