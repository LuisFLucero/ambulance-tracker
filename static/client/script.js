// Initialise map centred in Manila
const map = L.map("map").setView([14.5995, 120.9842], 13);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19
}).addTo(map);

// Marker cache for ambulances
let ambulanceMarkers = {};

// Add client marker when they geolocate
if ("geolocation" in navigator) {
  navigator.geolocation.getCurrentPosition(pos => {
    const clientLat = pos.coords.latitude;
    const clientLon = pos.coords.longitude;
    L.marker([clientLat, clientLon]).addTo(map).bindPopup("You are here").openPopup();
  });
}

// Poll ambulance locations from server
function updateAmbulances() {
  fetch("/get_locations")
    .then(res => res.json())
    .then(data => {
      // ambulances dictionary: {id: {lat, lon}}
      Object.entries(data.ambulances).forEach(([id, loc]) => {
        if (ambulanceMarkers[id]) {
          ambulanceMarkers[id].setLatLng([loc.lat, loc.lon]);
        } else {
          ambulanceMarkers[id] = L.marker([loc.lat, loc.lon], {
            icon: L.divIcon({
              className: "ambulance-marker",
              html: "<div style='color:red;font-weight:bold;'>🚑</div>",
              iconSize: [20, 20]
            })
          }).addTo(map).bindPopup("Ambulance");
        }
      });
    })
    .catch(err => console.error("Error fetching ambulances:", err));
}

// Request ambulance button handler
async function requestAmbulance() {
  const address = document.getElementById("address").value;
  const condition = document.getElementById("condition").value;
  if (!address || !condition) {
    alert("Please enter both address and condition");
    return;
  }

  try {
    // Geocode address to lat/lon
    const geoRes = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`
    );
    const geoData = await geoRes.json();
    if (geoData.length === 0) {
      alert("Address not found");
      return;
    }

    const lat = parseFloat(geoData[0].lat);
    const lon = parseFloat(geoData[0].lon);

    // send request to server
    const res = await fetch("/request_ambulance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address, condition, lat, lon })
        });


    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    const data = await res.json();
    document.getElementById("status-message").textContent = data.message;
  } catch (err) {
    console.error(err);
    alert("Error requesting ambulance");
  }
}

document.getElementById("emergency-btn")?.addEventListener("click", requestAmbulance);

// Poll ambulances every 5 seconds
setInterval(updateAmbulances, 5000);
updateAmbulances();
