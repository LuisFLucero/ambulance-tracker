let map = L.map("map").setView([14.5995, 120.9842], 12); // Manila coords
L.tileLayer("https://{s}.tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png", {
  maxZoom: 19
}).addTo(map);

let markers = {};

// Fetch locations every 5 seconds
setInterval(() => {
  fetch("/get_locations")
    .then(res => res.json())
    .then(data => {
      data.forEach(loc => {
        if (markers[loc.user_id]) {
          markers[loc.user_id].setLatLng([loc.lat, loc.lng]);
        } else {
          markers[loc.user_id] = L.marker([loc.lat, loc.lng]).addTo(map);
        }
      });
    });
}, 5000);

// If driver → update location using browser geolocation
if (navigator.geolocation) {
  setInterval(() => {
    navigator.geolocation.getCurrentPosition(pos => {
      fetch("/update_location", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude
        })
      });
    });
  }, 7000);
}