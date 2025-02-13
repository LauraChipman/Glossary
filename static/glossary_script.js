function toggleVisibility(id, editId, deleteId) {
    var contentElement = document.getElementById(id);
    var editElement = document.getElementById(editId);
    var deleteButton = document.getElementById(deleteId);

    if (contentElement.style.display === "none") {
        contentElement.style.display = "block";
        if (editElement) {
            editElement.style.display = "inline";  // Show edit link when content is visible
        }
        if (deleteButton) {
            deleteButton.style.display = "inline";  // Show delete link when content is visible
        }
    } else {
        contentElement.style.display = "none";
        if (editElement) {
            editElement.style.display = "none";  // Hide edit link when content is hidden
        }
        if (deleteButton) {
            deleteButton.style.display = "none";  // Hide delete link when content is hidden
        }
    }
}

// Function to toggle display of all titles under an alphabet letter
function toggleAlphabetVisibility(letterId) {
    var titleGroup = document.getElementById("titles-" + letterId);

    // Toggle display for the title group
    if (titleGroup.style.display === "none") {
        titleGroup.style.display = "block";
    } else {
        titleGroup.style.display = "none";
    }
}

function filterTerms() {
    let input = document.getElementById('search-bar').value.toLowerCase();
    let terms = document.getElementsByClassName('definition-title');
    let definitions = document.getElementsByClassName('definition-content');
    let alphabetHeaders = document.getElementsByClassName('alphabet-title');
    let titleGroups = document.getElementsByClassName('title-group');
    let matchesFound = false;

    // Hide all alphabet headers and title groups by default
    Array.from(alphabetHeaders).forEach(header => header.style.display = "none");
    Array.from(titleGroups).forEach(group => group.style.display = "none");

    // Clear previous highlights
    function clearHighlight(element) {
        element.innerHTML = element.textContent;
    }
    Array.from(terms).forEach(clearHighlight);
    Array.from(definitions).forEach(clearHighlight);

    // Reset the search heading and results display
    document.getElementById("search-heading").style.display = "none";
    document.getElementById("no-results").style.display = "none";

    // Filter entries based on the search input
    Array.from(terms).forEach((term, index) => {
        // Check if the current definition is related to action buttons and skip it if so
        if (definitions[index] && definitions[index].classList.contains('action-buttons')) {
            definitions[index].style.display = "none";
            return; // Skip the action-buttons divs entirely
        }

        let termText = term.textContent || term.innerText;
        let definitionText = definitions[index] ? definitions[index].textContent || definitions[index].innerText : "";

        // Check if the search query matches either the term or the definition
        if (termText.toLowerCase().includes(input) || definitionText.toLowerCase().includes(input)) {
            term.style.display = ""; // Show matching term title
            definitions[index].style.display = ""; // Show the matching definition

            // Ensure the relevant alphabet header and title group are visible
            let letterGroup = term.closest('.title-group'); // Find the title group for this term
            if (letterGroup) {
                letterGroup.style.display = ""; // Show relevant title group
                let alphabetHeader = letterGroup.previousElementSibling; // Get the alphabet header for the group
                if (alphabetHeader) alphabetHeader.style.display = ""; // Show relevant alphabet header
            }

            matchesFound = true;

            // Highlight the matching search query in both title and definition
            const regex = new RegExp(`(${input})`, "gi");
            term.innerHTML = term.innerHTML.replace(regex, `<span class="highlight">$1</span>`);
            if (definitions[index]) {
                definitions[index].innerHTML = definitions[index].innerHTML.replace(regex, `<span class="highlight">$1</span>`);
            }
        } else {
            term.style.display = "none"; // Hide non-matching term titles
            if (definitions[index]) definitions[index].style.display = "none"; // Hide non-matching definitions
        }
    });

    // Show results heading if any matches were found
    document.getElementById("search-heading").style.display = matchesFound ? "block" : "none";
    document.getElementById("no-results").style.display = matchesFound ? "none" : "block";
}

function toggleFilter() {
    const filterArea = document.getElementById("tag-filter");

    filterArea.classList.toggle("show");
}

        function toggleStats() {
            const statsArea = document.getElementById("glossary-stats");
            statsArea.classList.toggle("show");
        }
        function openAndScrollToEntry(entryId, letter) {
            const entry = document.getElementById(entryId);
            if (entry) {
                // If entry is already present, scroll to it
                entry.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                // Fetch the entry if not present
                fetch(`/get_entry/${entryId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.html) {
                            // Insert entry HTML into the correct alphabet section
                            const titleGroup = document.getElementById(`titles-${letter}`);
                            titleGroup.insertAdjacentHTML("beforeend", data.html);
                            titleGroup.style.display = 'block'; // Ensure the section is expanded
        
                            // Scroll to the newly added entry
                            document.getElementById(entryId).scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    })
                    .catch(error => console.error("Error loading entry:", error));
            }
        }
          

function filterByTag(tag) {
    // Get all glossary entry titles, definitions, alphabet headers, and title groups
    let terms = document.getElementsByClassName('definition-title');
    let definitions = document.getElementsByClassName('definition-content');
    let alphabetHeaders = document.getElementsByClassName('alphabet-title');
    let titleGroups = document.getElementsByClassName('title-group'); // Groups for each letter
    
    // Hide all alphabet headers and title groups by default
    Array.from(alphabetHeaders).forEach(header => header.style.display = "none");
    Array.from(titleGroups).forEach(group => group.style.display = "none");

    let matchesFound = false;

    // Loop through each term and definition to find matches based on the selected tag
    Array.from(terms).forEach((term, index) => {
        let definition = definitions[index];
        let tags = definition.getAttribute('data-tags') || '';

        // Check if the entry includes the selected tag
        if (tags.includes(tag)) {
            term.style.display = ""; // Show matching term title
            definition.style.display = ""; // Show matching definition content

            // Show the title group containing this term and its alphabet header
            let letterGroup = term.closest('.title-group'); // Find the title group for this term
            if (letterGroup) {
                letterGroup.style.display = ""; // Show relevant title group
                let alphabetHeader = letterGroup.previousElementSibling; // Get the alphabet header for the group
                if (alphabetHeader) alphabetHeader.style.display = ""; // Show relevant alphabet header
            }
            matchesFound = true;
        } else {
            // Hide terms and definitions that do not match
            term.style.display = "none";
            definition.style.display = "none";
        }
    });

    // Show results heading if matches were found
    document.getElementById("search-heading").style.display = matchesFound ? "block" : "none";
    document.getElementById("no-results").style.display = matchesFound ? "none" : "block";
}

function viewImages(imageIds) {
    // Fetch images using their IDs
    fetch('/images', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_ids: imageIds })
    })
    .then(response => response.json())
    .then(images => {
        console.log("Fetched Images:", images); // Debugging: Log images array

        // Create a modal overlay
        let modalOverlay = document.createElement("div");
        modalOverlay.classList.add("modal-overlay");

        // Create modal content container for images
        let modalContent = document.createElement("div");
        modalContent.classList.add("modal-content");

        // Append each image to modal content
        images.forEach(image => {
            if (!image.error) {
                let fullSizeImage = document.createElement("img");
                fullSizeImage.src = image.data; // Set image data as src
                fullSizeImage.alt = "Full Size Image";
                fullSizeImage.classList.add("full-size-image");
                modalContent.appendChild(fullSizeImage);
                console.log("Appending image:", image.image_id); // Debugging: Confirm appending
            } else {
                console.error(`Error loading image ${image.image_id}: ${image.error}`);
            }
        });

        // Append modal content to the overlay
        modalOverlay.appendChild(modalContent);

        // Append overlay to the body
        document.body.appendChild(modalOverlay);

        // Close the modal on overlay click
        modalOverlay.addEventListener("click", function () {
            document.body.removeChild(modalOverlay);
        });
    })
    .catch(error => {
        console.error("Error fetching images:", error);
    });
}

function closeAllTopics() {
    // Select all elements with the class that indicates an expanded definition
    const definitions = document.querySelectorAll('.definition-content');
    definitions.forEach(def => {
        def.style.display = 'none'; // Hide each definition
    });

    // Select all letter headings or title groups and collapse them if needed
    const titleGroups = document.querySelectorAll('.title-group');
    titleGroups.forEach(group => {
        group.style.display = 'none'; // Collapse each letter heading
    });
}

function deleteEntry(entryId) {
    if (confirm("Are you sure you want to delete this entry?")) {
        fetch(`/delete_entry/${entryId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (response.ok) {
                alert("Entry deleted successfully!");
                // Optionally, redirect or update the page without a refresh
                window.location.href = '/'; // Redirect to index page after deletion
            } else {
                alert("Failed to delete entry.");
            }
        })
        .catch(error => console.error('Error:', error));
    }
}
// Show button after scrolling down 100px
window.onscroll = function() { toggleBackToTopButton() };

function toggleBackToTopButton() {
    const backToTopButton = document.getElementById("backToTop");
    if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
        backToTopButton.style.display = "block";
    } else {
        backToTopButton.style.display = "none";
    }
}

// Smooth scroll to top when button is clicked
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: "smooth" });
}


// Handle Enter key for search
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("search-bar").addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            filterTerms();  
        }
    });
});


console.log("JavaScript file loaded");
