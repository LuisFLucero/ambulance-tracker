self.addEventListener('install', event => {
  event.waitUntil(
    caches.open('ambulance-cache-v1').then(cache => {
      return cache.addAll([
        '/ambulance',
        '/static/ambulance/style.css',
        '/static/ambulance/script.js'
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
