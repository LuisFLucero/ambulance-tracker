// ================== Client Side ==================
let map = L.map('map').setView([14.5995, 120.9842], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19
}).addTo(map);

let clientMarker = null;
let ambulanceMarker = null;
let routingControl = null;
let currentRequestId = null;

// Request ambulance button
document.getElementById('emergency-btn').addEventListener('click', async function () {
  const address = document.getElementById('address').value;
  const condition = document.getElementById('condition').value;

  if (!address || !condition) {
    alert("⚠️ Please enter both address and condition");
    return;
  }

  if (!navigator.geolocation) {
    alert("Geolocation not supported");
    return;
  }

  navigator.geolocation.getCurrentPosition(async pos => {
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;

    if (clientMarker) map.removeLayer(clientMarker);
    clientMarker = L.marker([lat, lon]).addTo(map).bindPopup("📍 You").openPopup();

    try {
      let res = await fetch('/request_ambulance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address, condition, lat, lon })
      });
      let data = await res.json();

      if (data.request_id) {
        currentRequestId = data.request_id;
        document.getElementById("status-message").innerText = "🚑 Ambulance request submitted!";
      } else {
        document.getElementById("status-message").innerText = "❌ Failed to submit request";
      }
    } catch (err) {
      console.error(err);
      alert("❌ Request failed");
    }
  });
});

// Poll ambulance location + ETA
async function pollAmbulance() {
  if (!currentRequestId) return;

  try {
    let res = await fetch(`/get_locations?request_id=${currentRequestId}`);
    let data = await res.json();

    if (data.accepted && data.ambulance) {
      const ambLat = data.ambulance.lat;
      const ambLon = data.ambulance.lon;

      // 🚑 Place or update ambulance marker
      if (!ambulanceMarker) {
  ambulanceMarker = L.marker([ambLat, ambLon], {
    icon: L.icon({
      iconUrl: '/static/ambulance/ambulance.ico',  // ✅ local ambulance icon
      iconSize: [40, 40],  // adjust size if needed
      iconAnchor: [20, 40], // base of the icon sits on location
      popupAnchor: [0, -40]
    })
  }).addTo(map).bindPopup("🚑 Ambulance");
} else {
  ambulanceMarker.setLatLng([ambLat, ambLon]);
}


      // 🗺️ Draw route + calculate ETA
      if (clientMarker) {
        if (routingControl) map.removeControl(routingControl);

        routingControl = L.Routing.control({
          waypoints: [
            L.latLng(ambLat, ambLon),
            clientMarker.getLatLng()
          ],
          routeWhileDragging: false,
          addWaypoints: false,
          draggableWaypoints: false,
          fitSelectedRoutes: true
        });

        // Attach before adding
        routingControl.on('routesfound', function (e) {
          if (e.routes && e.routes.length > 0) {
            let route = e.routes[0];
            let etaMins = Math.round(route.summary.totalTime / 60);
            document.getElementById('eta').innerText = `⏱ ETA: ${etaMins} minutes`;
          }
        });

        routingControl.addTo(map);
      }

    } else {
      // Before ambulance accepts
      document.getElementById('eta').innerText = "⏱ Waiting for ambulance...";
    }
  } catch (err) {
    console.error("Poll error:", err);
  }
}

setInterval(pollAmbulance, 5000);
