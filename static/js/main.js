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