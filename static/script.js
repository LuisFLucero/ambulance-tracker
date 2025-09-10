let routeLayer = null;

function updateAssignments() {
    fetch('/dispatch_message')
    .then(res => res.json())
    .then(assignments => {
        let ul = document.getElementById("messages");
        ul.innerHTML = '';

        //clear old routes
        if (routeLayer) {
            Map.removeLayer(routeLayer);
            
        }

        assignments.forEach(a => {
            let li = document.createElement("lis");
            li.textContent = a.message;
            ul.appendChile(li);

            let coords = [
                []
                []
                []
            ]
        })
    })
}