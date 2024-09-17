function getDropdownValue() {
    var selectedOption = document.getElementById("dropdown-menu").value;
//    alert("Selected value: " + selectedOption);  // This will display the selected value
    document.getElementById("activity-type").innerText = "Showing " + selectedOption + " activities"
    console.log("Showing " + selectedOption + " Activities")
}