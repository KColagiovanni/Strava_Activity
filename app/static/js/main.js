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
//    const element = document.getElementById("graph")
//
//    console.log(document.getElementById("start-time-date"))
//
//    var trace1 = {
//        x: [document.getElementById("start-time-date")],
//        y: [document.getElementById("movingTimeData")],
//        type: 'line'
//    };
//
//    var data = [trace1];
//
//    var layout = {
//        title: 'Test',
//        xaxis: {
//            title: 'X-Axis'
//        },
//        yaxis: {
//            title: 'Y-Axis'
//        }
//    };
//
//    Plotly.newPlot('graph', data, layout)
//    var startTime = document.getElementById("start-time-date")
//    var movingTime = document.getElementById("movingTimeData")
//    for (var st in startTime){
//        console.log(startTime)
//    }
    console.log("value is: " + value)
//    for (st in starttTime) {
//        console.log(st)
//    }
//
//    if (value === "movingTime") {
//        element.style.display = "block";
//        fetch("/activities")
//            .then(plot_moving_time_data=>{
//                Plotly.newPlot("graph", )
//            })
}

// Handle displaying the graph based on filters
//document.getElementById('graphBtn').addEventListener('click', function() {
//    var formData = new FormData(document.getElementById('filterActivitiesForm'));
//
//    console.log(formData)
//
//    fetch('/graph', {
//        method: 'POST',
//        body: new URLSearchParams(formData)
//    })
//    .then(response => response.json())
//    .then(data => {
//        Plotly.newPlot('graph', data.graph_data, data.layout);
//    })
////    .catch(error => console.error('Error loading graph:', error));
//});
//
//// File Upload
//document.getElementById('directoryForm').addEventListener('submit', function(event) {
//    event.preventDefault();
//
//    const input = document.getElementById('formFile');
//
//    console.log("input is: " + input)
//
//    const formData = new FormData();
//
//    // Append all selected files to the FormData
//    for (const file of input.files) {
//        formData.append('files', file);
//    }
//
//    // Send the files to the server
//    fetch('/upload-directory', {
//        method: 'POST',
//        body: formData
//    })
//    .then(response => response.json())
//    .then(data => {
//        const fileList = document.getElementById('fileList');
//        fileList.innerHTML = '';  // Clear any existing entries
//
//        // Display the relative paths of the files
//        data.forEach(file => {
//            const li = document.createElement('li');
//            li.textContent = file.filename;
//            fileList.appendChild(li);
//        });
//    })
//    .catch(error => console.error('Error uploading directory:', error));
//});


// File upload - Have user choose a directory and find the activities.csv file in it.
document.getElementById('directory-form').addEventListener('submit', function(event) {
    event.preventDefault();

    var activities = /\d{7,11}(.gpx|.fit.gz|.tcx.gz)/;
    const activityFilename = "activities/" + activities
//    const targetFilename = "activities/" + activities
    const targetFilename = "1297099.fit.gz"
//    const targetFilename = "activities.csv";  // Define the target filename here
    const input = document.getElementById('form-file');
    const formData = new FormData();
    let fileFound = false;

    // Check if the target file is in the selected files
    console.log("files are: " + input)
    for (const file of input.files) {
        if (file.name == targetFilename) {
            formData.append('files', file);
            fileFound = true;
            break;  // Only upload the target file, not the entire directory
        }
//        if (file.name == activityFilename) {
//            console.log("activity file is: " + file)
//            formData.append('files', file);
//            fileFound = true;
//            break;  // Only upload the target file, not the entire directory
//        }
    }

//    if (!fileFound) {
//        console.log('`File "${targetFilename}" not found in the selected directory.`')
////        document.getElementById('search-result').textContent = `File "${targetFilename}" not found in the selected directoryyyyy.`;
//        return;
//    }
//    else {
//        document.getElementById('searchResult').textContent = `File "${targetFilename}" was found in the selected directory.`;
//        return;
//    }

    // Send the target file to the server
    fetch('/upload-file', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message)
        document.getElementById('search-result').textContent = data.message;
    })
    .catch(error => console.error('Error searching for file:', error));
});