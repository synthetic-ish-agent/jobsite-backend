document.addEventListener('DOMContentLoaded', function() {
    const searchButton = document.getElementById('searchButton');
    const searchInput = document.getElementById('searchInput');
    const searchResultsContainer = document.getElementById('searchResults'); // Make sure you have this div in your index.html

    function performSearch() {
        const query = searchInput.value.trim();

        if (query) {
            fetch(`http://localhost:5000/api/search-jobs?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    searchResultsContainer.innerHTML = ''; // Clear previous results
                    if (data.error) {
                        searchResultsContainer.innerHTML = `<p class="error-message">${data.error}</p>`;
                    } else if (data.length > 0) {
                        data.forEach(job => {
                            const jobDiv = document.createElement('div');
                            jobDiv.classList.add('job-listing'); // You might need to add CSS for this class
                            jobDiv.innerHTML = `
                                <h3>${job.title}</h3>
                                <p class="company">${job.company} - ${job.location}</p>
                                <p class="type">${job.type}</p>
                                ${job.salary ? `<p class="salary">Salary: ${job.salary}</p>` : ''}
                                <p class="description">${job.description.substring(0, 200)}...</p>
                                <p class="application-email">Apply at: <a href="mailto:${job.application_email}">${job.application_email}</a></p>
                                <p class="posted-date">Posted on: ${new Date(job.posted_date).toLocaleDateString()}</p>
                                <a href="#" class="view-details">View Details</a>
                            `;
                            searchResultsContainer.appendChild(jobDiv);
                            // Add event listener for "View Details" if needed
                        });
                    } else {
                        searchResultsContainer.innerHTML = '<p>No jobs found matching your search.</p>';
                    }
                })
                .catch(error => {
                    console.error('Error searching jobs:', error);
                    searchResultsContainer.innerHTML = '<p class="error-message">Failed to perform search.</p>';
                });
        } else {
            searchResultsContainer.innerHTML = '<p>Please enter a search term.</p>';
        }
    }
 searchButton.addEventListener('click', performSearch)
    searchInput.addEventListener('keydown', function(event)
{
    if (event.key === 'Enter')
{  
     event.preventDefault();
     performSearch(); // Prevent default form submission performance();
        }

    });
});