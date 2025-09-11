// Initialise map centred in Manila for now
let currentAmbLat = 14.5995;
let currentAmbLon = 120.9842;

const map = L.map('map').setView([currentAmbLat, currentAmbLon], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19
}).addTo(map);

// Marker for ambulance
const ambulanceMarker = L.marker([currentAmbLat, currentAmbLon])
  .addTo(map)
  .bindPopup('Ambulance location')
  .openPopup();

let routingControl = null;      // to hold the route control
let currentRouteTarget = null;  // store the current client lat/lon

// Watch ambulance device GPS
if ('geolocation' in navigator) {
  navigator.geolocation.watchPosition(pos => {
    currentAmbLat = pos.coords.latitude;
    currentAmbLon = pos.coords.longitude;

    // update marker position
    ambulanceMarker.setLatLng([currentAmbLat, currentAmbLon]);

    // if a route is currently displayed, re-draw with new ambulance position
    if (currentRouteTarget) {
      showRoute(currentRouteTarget.lat, currentRouteTarget.lon);
    }

    // (optional) send location to server if logged in as ambulance
    fetch('/location_update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat: currentAmbLat, lon: currentAmbLon })
    }).catch(err => console.error('Location update failed', err));
  },
  err => console.error('GPS error', err),
  { enableHighAccuracy: true });
}

// Fetch client requests list
function fetchRequests() {
  fetch('/api/requests')
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById('requests-list');
      list.innerHTML = '';
      data.forEach(req => {
        const li = document.createElement('li');
        li.textContent = `Address: ${req.address} | Condition: ${req.condition} `;
        const btn = document.createElement('button');
        btn.textContent = 'Show Route';
        btn.addEventListener('click', () => {
          showRoute(req.lat, req.lon);
        });
        li.appendChild(btn);
        list.appendChild(li);
      });
    });
}

// Draw route from current ambulance location to client location
function showRoute(lat, lon) {
  currentRouteTarget = { lat, lon }; // remember the target

  if (routingControl) {
    map.removeControl(routingControl);
  }
  routingControl = L.Routing.control({
    waypoints: [
      L.latLng(currentAmbLat, currentAmbLon),
      L.latLng(lat, lon)
    ],
    routeWhileDragging: false
  }).addTo(map);
}

// Poll for requests
setInterval(fetchRequests, 5000);
fetchRequests();
