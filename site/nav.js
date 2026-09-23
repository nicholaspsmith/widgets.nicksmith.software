// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.
//
// Copyright (c) 2026 Nicholas Smith

// The phone nav: a hamburger that discloses the links panel. Closes when a
// link is tapped, on Escape, and when the window grows into the desktop layout.
(() => {
  const nav = document.querySelector(".nav");
  const button = nav && nav.querySelector(".nav-toggle");
  const links = nav && nav.querySelector(".nav-links");
  if (!button || !links) return;
  const setOpen = (open) => {
    button.setAttribute("aria-expanded", String(open));
    links.classList.toggle("is-open", open);
  };
  button.addEventListener("click", () => setOpen(button.getAttribute("aria-expanded") !== "true"));
  links.addEventListener("click", (e) => { if (e.target.closest("a")) setOpen(false); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && button.getAttribute("aria-expanded") === "true") { setOpen(false); button.focus(); }
  });
  const desktop = matchMedia("(min-width: 720px)");
  desktop.addEventListener("change", (e) => { if (e.matches) setOpen(false); });
})();
