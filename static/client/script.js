let map = L.map("map").setView([14.5995, 120.9842], 12);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19
}).addTo(map);

let markers = {};

// Update client + fetch ambulances
function updateLocations() {
    // Send client's current position
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

    // Display nearby ambulances
    fetch("/get_locations")
        .then(res => res.json())
        .then(data => {
            Object.entries(data.ambulances).forEach(([id, loc]) => {
                if (markers[id]) {
                    markers[id].setLatLng([loc.lat, loc.lon]);
                } else {
                    markers[id] = L.marker([loc.lat, loc.lon], {
                        icon: L.divIcon({ className: "ambulance-marker" })
                    }).addTo(map);
                }
            });
        })
        .catch(err => console.error("Error fetching ambulances:", err));
}

// Emergency request button
document.getElementById("emergency-btn")?.addEventListener("click", () => {
    fetch("/request_ambulance", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
        .then(res => res.json())
        .then(data => {
            document.getElementById("status-message").textContent = data.message;
        });
});

// Auto-refresh every 5s
setInterval(updateLocations, 5000);
