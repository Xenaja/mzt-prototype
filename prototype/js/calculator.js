/* ═══════════════════════════════════════════════════════════
   МЗТ — калькулятор предварительного расчёта фасада.

   Источник: блок заказчика `mzt-assets/block-start-260831_1901.md`.
   Расчётная часть (цены, формулы, заполнение таблицы, пересчёт итога)
   перенесена без изменений.

   Что изменено против оригинала:
   1. Убрана карточка-форма на странице — по ТЗ калькулятор это общий
      поп-ап, открываемый кнопками [data-open-calculator]. Поле «Тип объекта»
      перенесено из карточки в параметры поп-апа, чтобы не потерять его в расчёте.
   2. Полностью удалена отправка через скрытую форму Tilda вместе со слоем
      капчи и наблюдателями за её ответом (~400 строк). По ТЗ показывается
      подтверждение успешной заявки без передачи данных.
   3. Добавлены удержание фокуса внутри поп-апа, закрытие по Esc и возврат
      фокуса на кнопку, из которой его открыли.
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ─── Цены и коэффициенты расчёта (из блока заказчика, без изменений) ─── */
  var CONFIG = {
    reserveDefault: 10,
    materials: {
      eps:   { label: "Термопанели ЭППС",   priceM2: 2850, panelAreaM2: 0.54 },
      pps25: { label: "Термопанели ППС 25",  priceM2: 2400, panelAreaM2: 0.54 }
    },
    glue:      { label: "Клей-пена", price: 850,  coverageM2: 7.7 },
    grout:     { label: "Затирка",   price: 2500, coverageM2: 10  },
    fasteners: { label: "Крепёж",    price: 18,   qtyPerM2: 11.5  },
    delivery:  { moscow: 8000, russia: 20000, pickup: 0 },
    install:   { priceM2: 2500 }
  };

  var TEXTS = {
    sending:   'Отправляем заявку…',
    success:   'Заявка отправлена. Мы свяжемся с вами в ближайшее время.',
    noPolicy:  'Подтвердите согласие с обработкой персональных данных.',
    badPhone:  'Укажите корректный номер телефона.',
    demo:      'Демо-режим: данные никуда не отправляются.'
  };

  var CLOSE_DELAY_MS = 1800;
  var FAKE_SEND_MS   = 700;

  var els = {
    modal:           document.getElementById("efCalcModal"),
    objectType:      document.getElementById("efObjectType"),
    modalArea:       document.getElementById("efModalArea"),
    reserveInput:    document.getElementById("efReserveInput"),
    modalMaterial:   document.getElementById("efModalMaterial"),
    deliveryInput:   document.getElementById("efDeliveryInput"),
    installInput:    document.getElementById("efInstallInput"),
    areaWithReserve: document.getElementById("efAreaWithReserve"),
    panelQtyInfo:    document.getElementById("efPanelQtyInfo"),
    total:           document.getElementById("efCalcTotal"),
    sendBtn:         document.getElementById("efSendCalcRequest"),
    phone:           document.getElementById("efClientPhone"),
    policy:          document.getElementById("efPolicyInput"),
    note:            document.getElementById("efCalcNote")
  };

  if (!els.modal) return;

  /* ═══════════ Расчёт — перенесено из блока заказчика без изменений ═══════════ */

  function formatRub(value, options) {
    var amount = new Intl.NumberFormat("ru-RU").format(Math.round(value || 0)) + " ₽";
    return options && options.from && value > 0 ? "от " + amount : amount;
  }

  function formatPrice(value, options) {
    var amount = new Intl.NumberFormat("ru-RU").format(Math.round(value || 0));
    return options && options.from && value > 0 ? "от " + amount : amount;
  }

  function numberValue(input) {
    return Number(String(input.value || "0").replace(",", ".")) || 0;
  }

  function fixedPriceForRow(name) {
    var materialKey = els.modalMaterial && els.modalMaterial.value ? els.modalMaterial.value : "eps";
    var material = CONFIG.materials[materialKey] || CONFIG.materials.eps;
    if (name === "panels")    return material.priceM2;
    if (name === "glue")      return CONFIG.glue.price;
    if (name === "grout")     return CONFIG.grout.price;
    if (name === "fasteners") return CONFIG.fasteners.price;
    if (name === "delivery")  return CONFIG.delivery[els.deliveryInput.value] || 0;
    if (name === "install")   return CONFIG.install.priceM2;
    return 0;
  }

  function rowHasFromPrefix(name) {
    return name === "panels" || name === "delivery" || name === "install";
  }

  function getRow(name) {
    return document.querySelector('[data-row="' + name + '"]');
  }

  function setRow(name, qty, price) {
    var row = getRow(name);
    if (!row) return;
    var qtyInput = row.querySelector(".ef-row-qty");
    var priceInput = row.querySelector(".ef-row-price");
    if (qtyInput) qtyInput.value = qty;
    if (priceInput) {
      priceInput.dataset.price = price;
      priceInput.textContent = formatPrice(price, { from: rowHasFromPrefix(name) });
    }
  }

  function getRowTotal(row) {
    var rowName = row.getAttribute("data-row");
    var qty = numberValue(row.querySelector(".ef-row-qty"));
    var price = fixedPriceForRow(rowName);
    var priceInput = row.querySelector(".ef-row-price");
    if (priceInput) {
      priceInput.dataset.price = price;
      priceInput.textContent = formatPrice(price, { from: rowHasFromPrefix(rowName) });
    }
    return qty * price;
  }

  function recalcTableOnly() {
    var rows = document.querySelectorAll(".ef-calc-table-row[data-row]");
    var total = 0;
    rows.forEach(function (row) {
      var rowTotal = getRowTotal(row);
      total += rowTotal;
      var totalEl = row.querySelector(".ef-row-total");
      var rowName = row.getAttribute("data-row");
      if (totalEl) totalEl.textContent = formatRub(rowTotal, { from: rowHasFromPrefix(rowName) });
    });
    if (els.total) els.total.textContent = formatRub(total, { from: true });
  }

  function fillAutoRows() {
    var area = Math.max(0, numberValue(els.modalArea));
    var reserve = Math.max(0, numberValue(els.reserveInput));
    var materialKey = els.modalMaterial.value || "eps";
    var material = CONFIG.materials[materialKey] || CONFIG.materials.eps;

    var areaWithReserve = area * (1 + reserve / 100);
    var panelQty    = Math.ceil(areaWithReserve / material.panelAreaM2);
    var glueQty     = Math.ceil(area / CONFIG.glue.coverageM2);
    var groutQty    = Math.ceil(area / CONFIG.grout.coverageM2);
    var fastenerQty = Math.ceil(area * CONFIG.fasteners.qtyPerM2);
    var deliveryPrice = CONFIG.delivery[els.deliveryInput.value] || 0;

    setRow("panels", areaWithReserve.toFixed(1), material.priceM2);
    setRow("glue", glueQty, CONFIG.glue.price);
    setRow("grout", groutQty, CONFIG.grout.price);
    setRow("fasteners", fastenerQty, CONFIG.fasteners.price);
    setRow("delivery", deliveryPrice > 0 ? 1 : 0, deliveryPrice);

    if (els.installInput.value === "install") {
      setRow("install", area.toFixed(1), CONFIG.install.priceM2);
    } else {
      setRow("install", 0, CONFIG.install.priceM2);
    }

    els.areaWithReserve.textContent = areaWithReserve.toFixed(1) + " м²";
    els.panelQtyInfo.textContent = panelQty + " шт.";

    var panelsRow = getRow("panels");
    if (panelsRow) panelsRow.querySelector("strong").textContent = material.label;

    recalcTableOnly();
  }

  function collectCalculationText() {
    var rows = Array.prototype.slice.call(document.querySelectorAll(".ef-calc-table-row[data-row]"));
    var lines = rows.map(function (row) {
      var title = row.querySelector("strong").textContent.trim();
      var qty   = row.querySelector(".ef-row-qty").value;
      var price = row.querySelector(".ef-row-price").textContent.trim();
      var total = row.querySelector(".ef-row-total").textContent.trim();
      return title + ": " + qty + " × " + price + " = " + total;
    });
    return [
      "Предварительный расчёт фасада",
      "Тип объекта: " + els.objectType.options[els.objectType.selectedIndex].text,
      "Материал: " + els.modalMaterial.options[els.modalMaterial.selectedIndex].text,
      "Площадь: " + els.modalArea.value + " м²",
      "Запас: " + els.reserveInput.value + "%",
      "Площадь с запасом: " + els.areaWithReserve.textContent,
      "Ориентировочно панелей: " + els.panelQtyInfo.textContent,
      "",
      lines.join("\n"),
      "",
      "Итого: " + els.total.textContent,
      "Доставка: " + els.deliveryInput.options[els.deliveryInput.selectedIndex].text,
      "Монтаж: " + els.installInput.options[els.installInput.selectedIndex].text
    ].join("\n");
  }

  /* ═══════════ Открытие и закрытие поп-апа ═══════════ */

  var lastFocused = null;

  function focusable() {
    return Array.prototype.slice.call(els.modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )).filter(function (el) { return !el.disabled && el.offsetParent !== null; });
  }

  function openModal() {
    lastFocused = document.activeElement;

    if (!els.modalArea.value) els.modalArea.value = 150;
    els.reserveInput.value = CONFIG.reserveDefault;
    if (els.policy) els.policy.checked = false;

    hideNote();
    lockBtn(false);
    fillAutoRows();

    els.modal.hidden = false;
    els.modal.classList.add("is-open");
    els.modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("ef-modal-lock");

    var first = focusable()[0];
    if (first) first.focus();
  }

  function closeModal() {
    els.modal.classList.remove("is-open");
    els.modal.setAttribute("aria-hidden", "true");
    els.modal.hidden = true;
    document.body.classList.remove("ef-modal-lock");
    if (lastFocused && lastFocused.focus) lastFocused.focus();
  }

  function isOpen() { return els.modal.classList.contains("is-open"); }

  document.querySelectorAll("[data-ef-close]").forEach(function (el) {
    el.addEventListener("click", closeModal);
  });

  document.addEventListener("keydown", function (e) {
    if (!isOpen()) return;

    if (e.key === "Escape") { closeModal(); return; }

    /* удержание фокуса внутри поп-апа */
    if (e.key === "Tab") {
      var list = focusable();
      if (!list.length) return;
      var first = list[0], last = list[list.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  [els.modalArea, els.reserveInput, els.modalMaterial,
   els.deliveryInput, els.installInput, els.objectType].forEach(function (el) {
    if (!el) return;
    el.addEventListener("input", fillAutoRows);
    el.addEventListener("change", fillAutoRows);
  });

  document.addEventListener("input", function (event) {
    if (event.target.classList.contains("ef-row-qty") ||
        event.target.classList.contains("ef-row-price")) {
      recalcTableOnly();
    }
  });

  /* ═══════════ Заявка — демо-режим ═══════════
     Оригинал отправлял данные скрытой формой Tilda и ждал её подтверждения.
     По ТЗ этап прототипа: подтверждение показывается без передачи данных. */

  var busy = false;

  function note(kind, text) {
    if (!els.note) return;
    els.note.textContent = text;
    els.note.className = "ef-calc-note is-visible is-" + kind;
  }

  function hideNote() {
    if (!els.note) return;
    els.note.className = "ef-calc-note";
    els.note.textContent = "";
  }

  function lockBtn(on) {
    if (!els.sendBtn) return;
    els.sendBtn.disabled = !!on;
    els.sendBtn.textContent = on ? "Отправляем…" : "Получить точный расчёт";
  }

  function normalizePhone(raw) {
    var d = String(raw || "").replace(/\D/g, "");
    if (d.length === 11 && d.charAt(0) === "8") d = "7" + d.slice(1);
    if (d.length === 10) d = "7" + d;
    return d.length >= 11 ? "+" + d : "";
  }

  if (els.sendBtn) {
    els.sendBtn.addEventListener("click", function () {
      if (busy) return;

      if (!els.policy || !els.policy.checked) {
        note("err", TEXTS.noPolicy);
        if (els.policy) els.policy.focus();
        return;
      }

      var phone = normalizePhone(els.phone.value);
      if (!phone) {
        note("err", TEXTS.badPhone);
        els.phone.focus();
        return;
      }

      busy = true;
      lockBtn(true);
      note("info", TEXTS.sending);

      /* Расчёт собирается так же, как в оригинале, — он понадобится,
         когда на проде появится реальный приём заявок. */
      var payload = {
        phone: phone,
        total: els.total.textContent.trim(),
        calculation: collectCalculationText()
      };
      console.info("[МЗТ] Демо-режим, заявка НЕ отправлена:\n" + payload.calculation);

      window.setTimeout(function () {
        busy = false;
        lockBtn(false);
        note("ok", TEXTS.success + " " + TEXTS.demo);
        els.phone.value = "";
        if (els.policy) els.policy.checked = false;
        window.setTimeout(function () { closeModal(); hideNote(); }, CLOSE_DELAY_MS);
      }, FAKE_SEND_MS);
    });
  }

  /* Точка подключения для main.js */
  window.MZTCalculator = { open: openModal, close: closeModal };

})();
