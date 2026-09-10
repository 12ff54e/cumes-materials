(() => {
  "use strict";

  const slides = [...document.querySelectorAll(".slide")];
  const progress = document.querySelector(".progress-bar");
  const count = document.querySelector(".slide-count");
  const chapter = document.querySelector(".chapter");
  const overview = document.querySelector(".overview");
  const notesOverlay = document.querySelector("#notes-overlay");
  const notesCopy = document.querySelector(".notes-copy");
  const helpOverlay = document.querySelector("#help-overlay");
  let current = 0;
  let touchStartX = null;
  let touchStartY = null;

  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

  function fragmentsFor(index = current) {
    return [...slides[index].querySelectorAll(".fragment")];
  }

  function parseHash() {
    const match = window.location.hash.match(/^#\/(\d+)$/);
    return match ? clamp(Number(match[1]) - 1, 0, slides.length - 1) : 0;
  }

  function titleFor(slide) {
    return slide.dataset.title || slide.querySelector("h1, h2, h3")?.textContent.trim() || "Untitled";
  }

  function updateHud() {
    const slide = slides[current];
    count.textContent = `${String(current + 1).padStart(2, "0")} / ${String(slides.length).padStart(2, "0")}`;
    chapter.textContent = slide.dataset.chapter || "cuMES run";
    progress.style.width = `${((current + 1) / slides.length) * 100}%`;
    document.title = `${titleFor(slide)} — cuMES run`;
  }

  function showSlide(index, { updateHash = true } = {}) {
    const next = clamp(index, 0, slides.length - 1);
    const direction = next < current ? "right" : "left";

    slides.forEach((slide, i) => {
      slide.classList.remove("active", "exiting-left");
      slide.setAttribute("aria-hidden", i === next ? "false" : "true");
      if (i === current && direction === "left" && i !== next) {
        slide.classList.add("exiting-left");
      }
    });

    current = next;
    slides[current].classList.add("active");
    fragmentsFor().forEach((fragment) => fragment.classList.remove("visible"));
    updateHud();

    if (updateHash) {
      history.replaceState(null, "", `#/${current + 1}`);
    }
  }

  function next() {
    const hidden = fragmentsFor().find((fragment) => !fragment.classList.contains("visible"));
    if (hidden) {
      hidden.classList.add("visible");
      return;
    }
    showSlide(current + 1);
  }

  function previous() {
    const visible = fragmentsFor().filter((fragment) => fragment.classList.contains("visible"));
    if (visible.length) {
      visible.at(-1).classList.remove("visible");
      return;
    }
    showSlide(current - 1);
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  }

  function buildOverview() {
    const fragment = document.createDocumentFragment();
    slides.forEach((slide, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "overview-card";
      button.innerHTML = `<span class="n">${String(index + 1).padStart(2, "0")} · ${slide.dataset.chapter || "cuMES"}</span><strong>${titleFor(slide)}</strong><span>${slide.dataset.summary || ""}</span>`;
      button.addEventListener("click", () => {
        toggleOverview(false);
        showSlide(index);
      });
      fragment.append(button);
    });
    overview.append(fragment);
  }

  function toggleOverview(force) {
    const open = force ?? !overview.classList.contains("open");
    overview.classList.toggle("open", open);
    overview.setAttribute("aria-hidden", String(!open));
    document.body.classList.toggle("overview-mode", open);
    if (open) {
      const cards = [...overview.querySelectorAll(".overview-card")];
      cards.forEach((card, index) => card.classList.toggle("current", index === current));
      cards[current]?.scrollIntoView({ block: "center" });
    }
  }

  function toggleOverlay(overlay, force) {
    const open = force ?? !overlay.classList.contains("open");
    overlay.classList.toggle("open", open);
    overlay.setAttribute("aria-hidden", String(!open));
  }

  function toggleNotes() {
    const notes = slides[current].querySelector(".speaker-notes");
    if (notes) {
      notesCopy.replaceChildren(...Array.from(notes.childNodes, node => node.cloneNode(true)));
    } else {
      notesCopy.textContent = "No additional notes for this slide.";
    }
    toggleOverlay(notesOverlay);
  }

  function closeOverlays() {
    toggleOverview(false);
    toggleOverlay(notesOverlay, false);
    toggleOverlay(helpOverlay, false);
  }

  function renderMath() {
    if (!window.katex) {
      const warning = document.createElement("p");
      warning.className = "math-load-warning";
      warning.setAttribute("role", "alert");
      warning.textContent = "Equations could not load. Connect to the internet and reload, or open a standalone export.";
      document.body.prepend(warning);
      document.querySelectorAll("[data-tex]").forEach((element) => {
        element.textContent = element.dataset.tex;
      });
      return;
    }
    document.querySelectorAll("[data-tex]").forEach((element) => {
      window.katex.render(element.dataset.tex, element, {
        displayMode: element.classList.contains("math-display"),
        output: "htmlAndMathml",
        throwOnError: false,
        strict: "warn",
        trust: false,
      });
    });
  }

  document.addEventListener("keydown", (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;

    if (event.key === "Escape") {
      closeOverlays();
      return;
    }

    if (event.target.closest?.("input, select, textarea, [contenteditable], .font-controls[open]")) return;
    if ((event.key === " " || event.key === "Enter") && event.target.closest?.("button, summary")) return;

    if (overview.classList.contains("open") || notesOverlay.classList.contains("open") || helpOverlay.classList.contains("open")) {
      return;
    }

    switch (event.key) {
      case "ArrowRight":
      case "ArrowDown":
      case " ":
      case "PageDown":
        event.preventDefault();
        next();
        break;
      case "ArrowLeft":
      case "ArrowUp":
      case "PageUp":
        event.preventDefault();
        previous();
        break;
      case "Home":
        showSlide(0);
        break;
      case "End":
        showSlide(slides.length - 1);
        break;
      case "f":
      case "F":
        toggleFullscreen();
        break;
      case "o":
      case "O":
        toggleOverview();
        break;
      case "n":
      case "N":
        toggleNotes();
        break;
      case "?":
        toggleOverlay(helpOverlay);
        break;
      default:
        break;
    }
  });

  document.addEventListener("click", (event) => {
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (!action) return;
    if (action === "next") next();
    if (action === "previous") previous();
    if (action === "overview") toggleOverview();
    if (action === "notes") toggleNotes();
    if (action === "fullscreen") toggleFullscreen();
    if (action === "help") toggleOverlay(helpOverlay);
    if (action === "close") closeOverlays();
  });

  document.addEventListener("touchstart", (event) => {
    if (event.target.closest?.("input, select, textarea, button, summary, .font-controls, .overlay, .overview")) {
      touchStartX = null;
      touchStartY = null;
      return;
    }
    for (let node = event.target; node instanceof Element; node = node.parentElement) {
      if (node.scrollWidth > node.clientWidth + 1 && /auto|scroll/.test(getComputedStyle(node).overflowX)) {
        touchStartX = null;
        touchStartY = null;
        return;
      }
    }
    touchStartX = event.changedTouches[0].clientX;
    touchStartY = event.changedTouches[0].clientY;
  }, { passive: true });

  document.addEventListener("touchend", (event) => {
    if (touchStartX === null || touchStartY === null) return;
    const dx = event.changedTouches[0].clientX - touchStartX;
    const dy = event.changedTouches[0].clientY - touchStartY;
    touchStartX = null;
    touchStartY = null;
    if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy)) return;
    dx < 0 ? next() : previous();
  }, { passive: true });

  window.addEventListener("hashchange", () => showSlide(parseHash(), { updateHash: false }));

  renderMath();
  buildOverview();
  showSlide(parseHash(), { updateHash: false });
})();
