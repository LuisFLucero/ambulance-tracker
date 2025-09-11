// Initialize map
let map = L.map("map").setView([14.5995, 120.9842], 12);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19
}).addTo(map);

let routeControl = null;

// send ambulance’s location to server every 5 s
function updateLocations() {
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
}

setInterval(updateLocations, 5000);

// handle route button clicks
document.addEventListener("click", e => {
  if (e.target.classList.contains("route-btn")) {
    const clientLat = parseFloat(e.target.dataset.lat);
    const clientLon = parseFloat(e.target.dataset.lon);

    // get ambulance current position
    navigator.geolocation.getCurrentPosition(pos => {
      const ambLat = pos.coords.latitude;
      const ambLon = pos.coords.longitude;

      // clear previous route if any
      if (routeControl) {
        map.removeControl(routeControl);
      }

      // draw route
      routeControl = L.Routing.control({
        waypoints: [
          L.latLng(ambLat, ambLon),
          L.latLng(clientLat, clientLon)
        ],
        routeWhileDragging: false
      }).addTo(map);

      // zoom map to fit route
      routeControl.on('routesfound', function (e) {
        let bounds = L.latLngBounds([L.latLng(ambLat, ambLon), L.latLng(clientLat, clientLon)]);
        map.fitBounds(bounds);
      });
    });
  }
});
