self.addEventListener("install", event => {
  event.waitUntil(
    caches.open("ambulance-cache-v1").then(cache => {
      return cache.addAll([
        "/ambulance",
        "/static/ambulance/style.css",
        "/static/ambulance/script.js"
      ]);
    })
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});

// 🔔 Push notifications
self.addEventListener("push", event => {
  const data = event.data.json();
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: "/static/icons/ambulance-192.png",
      badge: "/static/icons/ambulance-192.png"
    })
  );
});

self.addEventListener("notificationclick", event => {
  event.notification.close();
  event.waitUntil(clients.openWindow("/ambulance"));
});
