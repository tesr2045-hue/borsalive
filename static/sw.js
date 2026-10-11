/* BIST Analiz Service Worker — alarm notifications + Web Push (v1.27.1, VAPID; tür bazlı mod/ses) */
const SW_VERSION = "1.38.1";

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("message", (event) => {
  const data = event.data || {};
  if (data.type === "SHOW_NOTIFICATION") {
    const title = data.title || "BIST Alarm";
    const opts = {
      body: data.body || "",
      tag: data.tag || "bist-alarm",
      renotify: !!data.renotify,
      silent: !!data.silent,
      vibrate: Array.isArray(data.vibrate) ? data.vibrate : undefined,
      data: { url: data.url || "/", symbol: data.symbol || null, version: SW_VERSION },
      icon: data.icon || "/static/favicon.ico",
      badge: data.badge || "/static/favicon.ico",
      requireInteraction: !!data.requireInteraction,
    };
    event.waitUntil(
      self.registration.showNotification(title, opts).catch((err) => {
        console.warn("[sw] showNotification failed", err);
      })
    );
  } else if (data.type === "PING") {
    if (event.ports && event.ports[0]) {
      event.ports[0].postMessage({ type: "PONG", version: SW_VERSION });
    }
  }
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const symbol = (event.notification.data && event.notification.data.symbol) || null;
  const targetUrl = symbol
    ? `/?symbol=${encodeURIComponent(symbol)}`
    : (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ("focus" in client) {
          client.postMessage({ type: "ALARM_CLICK", symbol });
          return client.focus();
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(targetUrl);
    })
  );
});

// v1.20.0: Web Push (sunucu: pywebpush + VAPID) — tarayıcı arka planda/kapalıyken bildirim
self.addEventListener("push", (event) => {
  let d = {};
  try { d = event.data ? event.data.json() : {}; } catch (e) { d = { title: "BIST Canlı", body: event.data ? event.data.text() : "" }; }
  const title = d.title || "BIST Canlı";
  event.waitUntil(self.registration.showNotification(title, {
    body: d.body || "", tag: d.tag || "bist-push", renotify: true, silent: !!d.silent, vibrate: d.silent ? undefined : [150, 80, 150],
    data: { url: d.url || "/", symbol: d.symbol || null, version: SW_VERSION },
    icon: "/static/favicon.ico", badge: "/static/favicon.ico",
  }));
});
