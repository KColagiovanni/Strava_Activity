// Used for displaying "Activity Type" output to the page.
function getDropdownTypeValue() {
    var selectedOption = document.getElementById("dropdown-menu-type").value;
    document.getElementById("activity-type").innerText = "Showing " + selectedOption + " Activities"
    console.log("Showing " + selectedOption + " Activities")
}

// Used for displaying "Activity Gear" output to the page.
function getDropdownTypeValue() {
    var selectedOption = document.getElementById("dropdown-menu-gear").value;
}

const collapseElementList = document.querySelectorAll('.collapse')
const collapseList = [...collapseElementList].map(collapseEl => new bootstrap.Collapse(collapseEl))
console.log(collapseElementList)

function movingTime() {
    console.log("movingTime has been selected")
}

function distance() {
    console.log("distance has been selected")
}

function avgSpeed() {
    console.log("Avgrage Speed has been selected")
}

function maxSpeed() {
    console.log("maxSpeed has been selected")
}

function elevationGain() {
    console.log("elevationGain has been selected")
}