self.addEventListener('install', event => {
  event.waitUntil(
    caches.open('client-cache-v1').then(cache => {
      return cache.addAll([
        '/client/request',
        '/static/client/style.css',
        '/static/client/script.js'
      ]);
    })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
