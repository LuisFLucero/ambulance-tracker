// ================== Ambulance Side ==================

// Dummy PGH coords
let currentAmbLat = 14.578056;
let currentAmbLon = 120.985556;

const map = L.map('map').setView([currentAmbLat, currentAmbLon], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19
}).addTo(map);

// Marker for ambulance (always PGH)
const ambulanceMarker = L.marker([currentAmbLat, currentAmbLon])
  .addTo(map)
  .bindPopup('🚑 Ambulance (PGH)')
  .openPopup();

let routingControl = null;      
let currentRouteTarget = null;  
let activeRequestId = null;     

// ❌ REMOVE geolocation.watchPosition
// ✅ Instead, keep ambulance fixed at PGH
// (If later you want real GPS, re-enable the code)

// Fetch client requests list
function fetchRequests() {
  fetch('/api/requests')
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById('requests-list');
      list.innerHTML = '';
      data.forEach(req => {
        if (req.finished) return; // skip finished requests

        const li = document.createElement('li');
        li.textContent = `Address: ${req.address} | Condition: ${req.condition} `;

        const acceptBtn = document.createElement('button');
        acceptBtn.textContent = 'Accept';
        acceptBtn.addEventListener('click', () => {
          activeRequestId = req.id;
          showRoute(req.lat, req.lon);
          fetch(`/accept_request/${req.id}`, { method: 'POST' })
            .then(() => console.log("✅ Request accepted"))
            .catch(err => console.error("Accept failed", err));
        });

        const finishBtn = document.createElement('button');
        finishBtn.textContent = 'Finish';
        finishBtn.addEventListener('click', () => {
          if (!activeRequestId) return;
          fetch(`/finish_request/${activeRequestId}`, { method: 'POST' })
            .then(() => {
              li.remove();
              activeRequestId = null;
              if (routingControl) {
                map.removeControl(routingControl);
                routingControl = null;
              }
              alert('Request finished ✅');
            })
            .catch(err => console.error('Failed to finish request', err));
        });

        li.appendChild(acceptBtn);
        li.appendChild(finishBtn);
        list.appendChild(li);
      });
    });
}

// Draw route PGH → client
function showRoute(lat, lon) {
  currentRouteTarget = { lat, lon };

  if (routingControl) {
    map.removeControl(routingControl);
  }
  routingControl = L.Routing.control({
    waypoints: [
      L.latLng(currentAmbLat, currentAmbLon), // Always PGH
      L.latLng(lat, lon)
    ],
    routeWhileDragging: false
  }).addTo(map);
}

// Poll for requests
setInterval(fetchRequests, 5000);
fetchRequests();
