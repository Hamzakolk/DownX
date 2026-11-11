const api = typeof browser !== "undefined" ? browser : chrome;
const msg = document.getElementById("msg");

function show(text, ok) {
  msg.className = ok ? "ok" : "err";
  msg.textContent = text;
}

api.storage.local.get({ token: "", port: 47823 }, (s) => {
  document.getElementById("token").value = s.token;
  document.getElementById("port").value = s.port;
});

document.getElementById("save").addEventListener("click", () => {
  const token = document.getElementById("token").value.trim();
  const port = parseInt(document.getElementById("port").value, 10) || 47823;
  api.storage.local.set({ token, port }, () => show("Saved.", true));
});

document.getElementById("test").addEventListener("click", () => {
  api.runtime.sendMessage({ type: "ping" }, (res) => {
    if (res && res.ok) show("Connected to DownX.", true);
    else show("Could not reach DownX. Is it running?", false);
  });
});
