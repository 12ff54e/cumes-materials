(() => {
  "use strict";

  const controls = document.querySelector(".font-controls");
  if (!controls) return;
  const summary = controls.querySelector("summary");
  const textSize = controls.querySelector("#font-text-size");
  const mathSize = controls.querySelector("#font-math-size");
  const textValue = controls.querySelector("#font-text-value");
  const mathValue = controls.querySelector("#font-math-value");
  const body = document.body;
  const baseScale = Number(getComputedStyle(body).getPropertyValue("--font-scale")) || 1;
  const storageKey = `cumes-materials:font-size:v1:${body.dataset.deck}`;

  function percentage(value) {
    return Number.isFinite(value) && value >= 80 && value <= 140
      ? Math.round(value / 5) * 5 : 100;
  }

  function applySizes() {
    const text = Number(textSize.value);
    const math = Number(mathSize.value);
    if (text === 100) body.style.removeProperty("--font-scale");
    else body.style.setProperty("--font-scale", String(baseScale * text / 100));
    body.style.setProperty("--view-math-scale", String(math / 100));
    body.classList.toggle("font-size-adjusted", text > 100 || math > 100);
    textValue.value = `${text}%`;
    mathValue.value = `${math}%`;
    textSize.setAttribute("aria-valuetext", `${text} percent`);
    mathSize.setAttribute("aria-valuetext", `${math} percent`);
  }

  function saveSizes() {
    try {
      localStorage.setItem(storageKey, JSON.stringify({
        text: Number(textSize.value), math: Number(mathSize.value),
      }));
    } catch {
      // Sizing still works when browser storage is unavailable.
    }
  }

  function closeControls({ restoreFocus = false } = {}) {
    controls.open = false;
    if (restoreFocus) summary.focus();
  }

  try {
    const saved = JSON.parse(localStorage.getItem(storageKey));
    textSize.value = percentage(saved?.text);
    mathSize.value = percentage(saved?.math);
  } catch {
    // Use the authored defaults if storage is blocked or contains invalid JSON.
  }
  applySizes();

  controls.addEventListener("input", (event) => {
    if (event.target !== textSize && event.target !== mathSize) return;
    applySizes();
    saveSizes();
  });
  controls.querySelector("[data-font-reset]").addEventListener("click", () => {
    textSize.value = 100;
    mathSize.value = 100;
    applySizes();
    try { localStorage.removeItem(storageKey); } catch { /* Optional persistence. */ }
  });
  controls.querySelector("[data-font-close]").addEventListener("click", () => {
    closeControls({ restoreFocus: true });
  });
  document.addEventListener("pointerdown", (event) => {
    if (!controls.contains(event.target)) closeControls();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && controls.open) closeControls({ restoreFocus: true });
  });
})();
