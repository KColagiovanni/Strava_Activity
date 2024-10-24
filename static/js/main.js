//// Used for displaying "Activity Type" output to the page.
//function getDropdownTypeValue() {
//    var selectedOption = document.getElementById("dropdown-menu-type").value;
//    document.getElementById("activity-type").innerText = "Showing " + selectedOption + " Activities"
//    console.log("Showing " + selectedOption + " Activities")
//}
//
//// Used for displaying "Activity Gear" output to the page.
//function getDropdownTypeValue() {
//    var selectedOption = document.getElementById("dropdown-menu-gear").value;
//}
//
//const collapseElementList = document.querySelectorAll('.collapse')
//const collapseList = [...collapseElementList].map(collapseEl => new bootstrap.Collapse(collapseEl))
//console.log(collapseElementList)
//
//var movingTimeRadio = document.getElementById("movingTime").value;
//var distanceRadio = document.getElementById("distance").value;
//var avgSpeedRadio = document.getElementById("avgSpeed").value;
//var maxSpeedRadio = document.getElementById("maxSpeed").value;
//var elevationGainRadio = document.getElementById("elevationGain").value;
//
//function submitGraph() {
//    console.log("Moving Time: " + movingTimeRadio)
//    console.log("Distance: " + distanceRadio)
//    console.log("Average Speed: " + avgSpeedRadio)
//    console.log("Max Speed: " + maxSpeedRadio)
//    console.log("Elevation Gain: " + ElevationGainRadio)
//}

function showGraph(value) {
    const element = document.getElementById("graph")

    console.log("value is: " + value)

    if (value === "movingTime") {
        element.style.display = "block";
//        fetch("/activities")
//            .then(plot_moving_time_data=>{
//                Plotly.newPlot("graph", )
//            })
        element.innerHTML = { plot_moving_time_data }
    } else {
        element.style.display = "none";
    }
}

function movingTime() {
    console.log("movingTime has been selected")
}

function distance() {
    console.log("distance has been selected")
}

function avgSpeed() {
    console.log("avgSpeed has been selected")
}

function maxSpeed() {
    console.log("maxSpeed has been selected")
}

function elevationGain() {
    console.log("elevationGain has been selected")
}