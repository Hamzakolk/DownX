const api = typeof browser !== "undefined" ? browser : chrome;
let currentUrl = "";

api.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  currentUrl = tabs[0] && tabs[0].url ? tabs[0].url : "";
  document.getElementById("url").textContent = currentUrl;
});

document.getElementById("send").addEventListener("click", () => {
  const status = document.getElementById("status");
  status.className = "";
  status.textContent = "Sending...";
  api.runtime.sendMessage({ type: "send", url: currentUrl }, (res) => {
    if (res && res.ok) {
      status.className = "ok";
      status.textContent = "Added to DownX.";
    } else {
      status.className = "err";
      status.textContent = (res && res.error) || "Could not send.";
    }
  });
});
