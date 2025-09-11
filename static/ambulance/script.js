let map = L.map("map").setView([14.5995, 120.9842], 12);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19
}).addTo(map);

let markers = {};

function updateLocations() {
    fetch("/get_locations")
        .then(res => res.json())
        .then(data => {
            // Send ambulance’s current location
            if ("geolocation" in navigator) {
                navigator.geolocation.getCurrentPosition(pos => {
                    fetch("/location_update", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            lat: pos.coords.latitude,
                            lon: pos.coords.longitude
                        })
                    });
                });
            }

            // Update client markers on map
            Object.entries(data.clients).forEach(([id, loc]) => {
                if (markers[id]) {
                    markers[id].setLatLng([loc.lat, loc.lon]);
                } else {
                    markers[id] = L.marker([loc.lat, loc.lon], {
                        icon: L.divIcon({ className: "client-marker" })
                    }).addTo(map);
                }
            });
        })
        .catch(err => console.error("Error updating locations:", err));
}

// Refresh every 5 seconds
setInterval(updateLocations, 5000);
