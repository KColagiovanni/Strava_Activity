// File upload - Have user choose a directory and find the activities.csv file in it.
document.getElementById('directory-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const targetFilename = "activities.csv";
    const input = document.getElementById('form-file');
    const formData = new FormData();
    let fileFound = false;

    // Check if the target file is in the selected files
    for (const file of input.files) {
        if (file.name == targetFilename) {
            console.log("activity file is: " + file)
            formData.append('files', file);
            fileFound = true;
            break;  // Only upload the target file, not the entire directory
        }
    }
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
