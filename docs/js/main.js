/* ═══════════════════════════════════════════════════════════
   МЗТ — прототип. Поведение страницы.
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ─── Плавный переход по внутренним якорям ───
     Уважает prefers-reduced-motion и переводит фокус на цель,
     иначе навигация с клавиатуры теряет место. */
  document.addEventListener('click', function (e) {
    var link = e.target.closest('a[href^="#"]');
    if (!link) return;

    var id = link.getAttribute('href');
    /* Ссылки, для которых ещё нет страниц (PENDING, строки P-05, P-06, P-14),
       стоят с href="#". Без этого браузер уводил страницу наверх. */
    if (id === '#' || id.length < 2) { e.preventDefault(); return; }

    var target = document.querySelector(id);
    if (!target) return;

    e.preventDefault();
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    target.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });

    if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
  });

  /* ─── Параллакс первого экрана ───
     Требование из комментария к макету: «добавить эффект параллакса снизу
     вверх как здесь на первом экране» (brick-art.ru). Фотография смещается
     медленнее страницы, поэтому кажется, что она уходит вверх с отставанием.
     Коэффициент 0.18 подобран под запас высоты фона в CSS (120%), чтобы
     нижний край кадра не открывался. */
  var heroBg = document.querySelector('.hero__bg');
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (heroBg && !reduceMotion) {
    var ticking = false;
    var shift = function () {
      var y = window.scrollY || window.pageYOffset || 0;
      if (y < 1200) {
        heroBg.style.transform = 'translate3d(0,' + (y * 0.18).toFixed(1) + 'px,0)';
      }
      ticking = false;
    };
    window.addEventListener('scroll', function () {
      if (!ticking) { window.requestAnimationFrame(shift); ticking = true; }
    }, { passive: true });
    shift();
  }

  /* ─── Нижняя панель: в потоке первого экрана, дальше — плавающая ───
     В макете панель нарисована внутри первого экрана и не мешает карточкам
     показателей. Если сделать её плавающей сразу, на окнах ниже 875px она
     их перекрывает. Поэтому: пока первый экран не прокручен, панель стоит
     в макетной позиции; как только его низ попадает в кадр — открепляется.
     На внутренних страницах панели-в-hero нет, там она плавающая всегда. */
  var sentinel = document.getElementById('dockSentinel');
  var heroDock = document.querySelector('.hero .dock');

  if (heroDock) {
    /* Макетная позиция панели — 822px от верха первого экрана. Если окно ниже
       875px, она оказывается за нижним краем и кнопки не видны, а комментарий
       к макету требует «статичные кнопки, идущие через всю страницу».
       Поэтому на низких окнах панель плавает сразу, на высоких — стоит по макету
       и открепляется только при прокрутке. */
    var scrolledPast = false;

    /* Первый экран теперь высотой с окно, поэтому панель в его нижнем углу
       всегда в кадре — отдельная проверка высоты больше не нужна. */
    var applyDock = function () {
      heroDock.classList.toggle('is-floating', scrolledPast);
    };

    if (sentinel && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          scrolledPast = e.isIntersecting || e.boundingClientRect.top < 0;
          applyDock();
        });
      }, { threshold: 0 }).observe(sentinel);
    } else {
      scrolledPast = true;                   // запасной вариант для старых браузеров
    }

    window.addEventListener('resize', applyDock, { passive: true });
    applyDock();
  }


  /* ─── Аккордеон в блоке «Производство» ───
     В макете первый пункт раскрыт, остальные свёрнуты: у раскрытого знак
     «минус», у свёрнутых «плюс». Открытым может быть только один пункт. */
  document.addEventListener('click', function (e) {
    var head = e.target.closest('.acc__head');
    if (!head) return;

    var acc = head.closest('.acc');
    var open = head.getAttribute('aria-expanded') === 'true';

    acc.querySelectorAll('.acc__head').forEach(function (h) {
      var body = document.getElementById(h.getAttribute('aria-controls'));
      h.setAttribute('aria-expanded', 'false');
      if (body) body.hidden = true;
    });

    if (!open) {
      head.setAttribute('aria-expanded', 'true');
      var body = document.getElementById(head.getAttribute('aria-controls'));
      if (body) body.hidden = false;
    }
  });


  /* ─── Карта дилеров ───
     Комментарий к макету требует интерактивную карту Яндекса. Точек дилеров
     и ключа API пока нет (PENDING, строка P-11), поэтому по умолчанию стоит
     вид из макета, а по нажатию подключается живой виджет: он работает без
     ключа, метки дилеров добавятся вместе с их адресами. */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-map-live]');
    if (!btn) return;

    var box = btn.closest('.dealers__map');
    if (!box || box.classList.contains('is-live')) return;

    var frame = document.createElement('iframe');
    frame.src = 'https://yandex.ru/map-widget/v1/?ll=44.0%2C56.5&z=5';
    frame.title = 'Карта дилеров МЗТ';
    frame.loading = 'lazy';
    frame.allowFullscreen = true;

    var shot = box.querySelector('.dealers__map-shot');
    if (shot) shot.replaceWith(frame);
    box.classList.add('is-live');
  });

  /* ─── Заявка на расчёт фасада ───
     По ТЗ этого этапа заявка никуда не уходит: показываем подтверждение,
     как и в калькуляторе. Проверяем поля сами — у формы стоит novalidate,
     чтобы подсказки браузера не спорили с оформлением макета. */
  var request = document.getElementById('request');

  if (request) {
    request.addEventListener('submit', function (e) {
      e.preventDefault();

      var note   = document.getElementById('reqNote');
      var name   = document.getElementById('reqName');
      var phone  = document.getElementById('reqPhone');
      var policy = document.getElementById('reqPolicy');
      var digits = (phone.value.match(/\d/g) || []).length;

      var problem = !name.value.trim() ? ['Напишите, как к вам обращаться.', name]
                  : digits < 10        ? ['Проверьте номер телефона.', phone]
                  : !policy.checked    ? ['Нужно согласие на обработку данных.', policy]
                  : null;

      if (problem) {
        note.textContent = problem[0];
        note.classList.remove('is-done');
        problem[1].focus();
        return;
      }

      note.textContent = 'Заявка принята — специалист свяжется с вами. '
                       + 'Это прототип: заявка никуда не отправлена.';
      note.classList.add('is-done');
      request.reset();
    });
  }

  /* ─── Калькулятор ───
     Готовая логика расчёта лежит в mzt-assets/block-start-260831_1901.md
     и подключается следующим шагом (реестр PENDING, строка P-07).
     Здесь — единственная точка интеграции: заменить тело openCalculator
     на вызов реального модуля, снять data-pending с кнопок. */
  function openCalculator() {
    if (typeof window.MZTCalculator === 'object' && window.MZTCalculator.open) {
      window.MZTCalculator.open();
      return;
    }
    console.info('[МЗТ] Калькулятор ещё не подключён — см. PENDING.md, строка P-07.');
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-open-calculator]');
    if (!btn) return;
    e.preventDefault();
    openCalculator();
  });

})();
