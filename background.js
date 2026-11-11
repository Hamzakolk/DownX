// Works in Chrome, Edge, Brave, Opera (service worker) and Firefox (background script).
const api = typeof browser !== "undefined" ? browser : chrome;

async function getSettings() {
  return new Promise((resolve) =>
    api.storage.local.get({ token: "", port: 47823 }, resolve)
  );
}

async function sendToDownX(url) {
  if (!url || !url.startsWith("http")) {
    return { ok: false, error: "No valid link" };
  }
  const { token, port } = await getSettings();
  try {
    const r = await fetch(`http://127.0.0.1:${port}/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-DownX-Token": token },
      body: JSON.stringify({ url })
    });
    if (r.ok) return { ok: true };
    if (r.status === 403) return { ok: false, error: "Wrong token. Check extension options." };
    return { ok: false, error: "DownX returned an error." };
  } catch (e) {
    return { ok: false, error: "DownX is not running." };
  }
}

function flashBadge(ok) {
  const action = api.action || api.browserAction;
  action.setBadgeBackgroundColor({ color: ok ? "#4CAF50" : "#E07A5F" });
  action.setBadgeText({ text: ok ? "OK" : "!" });
  setTimeout(() => action.setBadgeText({ text: "" }), 3000);
}

api.runtime.onInstalled.addListener(() => {
  api.contextMenus.create({
    id: "downx-link",
    title: "Download link with DownX",
    contexts: ["link"]
  });
  api.contextMenus.create({
    id: "downx-page",
    title: "Download this page with DownX",
    contexts: ["page", "video", "audio"]
  });
});

api.contextMenus.onClicked.addListener(async (info, tab) => {
  const url = info.linkUrl || info.pageUrl || (tab && tab.url);
  const res = await sendToDownX(url);
  flashBadge(res.ok);
});

// Messages from the popup and options page.
api.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "send") {
    sendToDownX(msg.url).then((res) => {
      flashBadge(res.ok);
      sendResponse(res);
    });
    return true; // keep the channel open for the async reply
  }
  if (msg && msg.type === "ping") {
    getSettings().then(({ port }) =>
      fetch(`http://127.0.0.1:${port}/ping`)
        .then((r) => r.json())
        .then((j) => sendResponse({ ok: j.app === "DownX" }))
        .catch(() => sendResponse({ ok: false }))
    );
    return true;
  }
});
