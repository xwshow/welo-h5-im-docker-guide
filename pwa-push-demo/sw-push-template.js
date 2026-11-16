/* Minimal Service Worker template for Web Push (PWA offline wake-up).
 *
 * This is intentionally small and framework-free so you can copy it into
 * any H5 IM front-end. It does NOT ship VAPID keys or a push gateway —
 * wire those on your own backend.
 *
 * Register example (page script):
 *   navigator.serviceWorker.register('/sw-push-template.js');
 */

self.addEventListener("install", (event) => {
  // Activate immediately on first install.
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  let payload = { title: "新消息", body: "你有一条新消息", url: "/" };
  try {
    if (event.data) {
      payload = Object.assign(payload, event.data.json());
    }
  } catch (err) {
    // Keep defaults when payload is plain text / empty.
  }

  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body,
      data: { url: payload.url || "/" },
      // Keep icons optional; missing icons should not break push.
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || "/";

  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ("focus" in client) {
          client.navigate(target);
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(target);
      }
      return undefined;
    })
  );
});
