// Shows a slim DownX bar on top of every video in the page.
// Runs in the top frame only. Clicking sends the page URL to the DownX app.
(() => {
  if (window.top !== window) return;

  const api = typeof browser !== "undefined" ? browser : chrome;
  const MIN_WIDTH = 200;
  const MIN_HEIGHT = 120;
  const BAR_HEIGHT = 28;
  const entries = new Map(); // video -> { host, label, button }
  let scheduled = false;

  function makeBar() {
    const host = document.createElement("div");
    host.style.cssText = "position:fixed;z-index:2147483647;display:none;margin:0;padding:0;";
    const root = host.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        .bar {
          box-sizing: border-box;
          height: ${BAR_HEIGHT}px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 6px 0 10px;
          background: rgba(14, 20, 37, 0.85);
          border-bottom: 2px solid #1E88FF;
          font: 600 12px/1 system-ui, sans-serif;
          color: #E8ECF8;
          border-radius: 6px 6px 0 0;
          backdrop-filter: blur(4px);
          pointer-events: auto;
          user-select: none;
        }
        .brand { color: #1E88FF; font-weight: 700; letter-spacing: .2px; }
        button {
          all: unset;
          cursor: pointer;
          padding: 5px 10px;
          border-radius: 6px;
          background: #1E88FF;
          color: #fff;
          font: 600 11px/1 system-ui, sans-serif;
          white-space: nowrap;
        }
        button:hover { background: #1570D6; }
      </style>
      <div class="bar">
        <span class="brand">DownX</span>
        <button type="button">Download</button>
      </div>
    `;
    const button = root.querySelector("button");
    const label = button;

    button.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      label.textContent = "Sending...";
      api.runtime.sendMessage({ type: "send", url: location.href }, (res) => {
        label.textContent = res && res.ok ? "Added" : ((res && res.error) ? "Error" : "Error");
        if (res && !res.ok && res.error) button.title = res.error;
        setTimeout(() => (label.textContent = "Download"), 2000);
      });
    });

    document.documentElement.appendChild(host);
    return { host, label, button };
  }

  function attach(video) {
    if (entries.has(video)) return;
    entries.set(video, makeBar());
    schedule();
  }

  function reposition() {
    scheduled = false;
    for (const [video, entry] of entries) {
      if (!video.isConnected) {
        entry.host.remove();
        entries.delete(video);
        continue;
      }
      const r = video.getBoundingClientRect();
      const visible =
        r.width >= MIN_WIDTH &&
        r.height >= MIN_HEIGHT &&
        r.bottom > BAR_HEIGHT &&
        r.top < window.innerHeight;
      if (!visible) {
        entry.host.style.display = "none";
        continue;
      }
      entry.host.style.display = "block";
      entry.host.style.left = `${r.left}px`;
      entry.host.style.top = `${Math.max(0, r.top)}px`;
      entry.host.style.width = `${r.width}px`;
    }
  }

  function schedule() {
    if (!scheduled) {
      scheduled = true;
      requestAnimationFrame(reposition);
    }
  }

  function scan(node) {
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    if (node.tagName === "VIDEO") attach(node);
    node.querySelectorAll?.("video").forEach(attach);
  }

  scan(document.documentElement);

  new MutationObserver((mutations) => {
    for (const m of mutations) m.addedNodes.forEach(scan);
    schedule();
  }).observe(document.documentElement, { childList: true, subtree: true });

  window.addEventListener("scroll", schedule, { capture: true, passive: true });
  window.addEventListener("resize", schedule, { passive: true });
  setInterval(schedule, 500);
})();
