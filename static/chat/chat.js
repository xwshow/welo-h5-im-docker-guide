(function () {
  var list = document.getElementById("msg-list");
  if (!list) return;

  var threadId = list.getAttribute("data-thread-id");
  var selfId = Number(list.getAttribute("data-self-id"));
  var input = document.getElementById("msg-input");
  var sendBtn = document.getElementById("msg-send");
  var proto = location.protocol === "https:" ? "wss://" : "ws://";
  var socket = null;
  var seen = {};

  Array.prototype.forEach.call(list.querySelectorAll("[data-id]"), function (el) {
    seen[el.getAttribute("data-id")] = true;
  });

  function appendMessage(msg) {
    if (!msg || seen[msg.id]) return;
    seen[msg.id] = true;
    var div = document.createElement("div");
    div.className = "bubble " + (Number(msg.sender_id) === selfId ? "mine" : "theirs");
    div.setAttribute("data-id", msg.id);
    var p = document.createElement("p");
    p.textContent = msg.body;
    div.appendChild(p);
    list.appendChild(div);
    list.scrollTop = list.scrollHeight;
  }

  function connect() {
    socket = new WebSocket(proto + location.host + "/ws/thread/" + threadId + "/");
    socket.onmessage = function (ev) {
      try {
        var data = JSON.parse(ev.data);
        if (data.type === "chat") appendMessage(data.message);
      } catch (e) {}
    };
    socket.onclose = function () {
      setTimeout(connect, 1500);
    };
  }

  function send() {
    var body = (input.value || "").trim();
    if (!body || !socket || socket.readyState !== 1) return;
    // Never trust client-side sender fields; server ignores them anyway.
    socket.send(JSON.stringify({ type: "chat", body: body }));
    input.value = "";
  }

  sendBtn.addEventListener("click", send);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") send();
  });
  connect();
  list.scrollTop = list.scrollHeight;
})();
