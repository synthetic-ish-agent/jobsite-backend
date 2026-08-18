document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  const searchButton = document.getElementById('searchButton');
  const jobListingsContainer = document.querySelector('.job-list');

  function displayJobs(jobs) {
    jobListingsContainer.innerHTML = '';
    jobs.forEach(job => {
      const jobCard = document.createElement('div');
      jobCard.classList.add('job-card');
      jobCard.dataset.jobId = job.id; // Store the job ID as a data attribute
      jobCard.innerHTML = `
        <h3>${job.title}</h3>
        <p class="company">${job.company}</p>
        <p class="location">${job.location}</p>
        <p class="description">${job.description.substring(0, 100)}...</p>
        <button class="view-details-button">View Details</button>
      `;
      jobListingsContainer.appendChild(jobCard);
    });

    // Add event listeners to the "View Details" buttons
    const viewDetailsButtons = document.querySelectorAll('.view-details-button');
    viewDetailsButtons.forEach(button => {
      button.addEventListener('click', (event) => {
        const jobId = event.target.parentNode.dataset.jobId;
        window.location.href = `/job-details.html?id=${jobId}`;
      });
    });
  }

  function fetchJobs(query = '') {
    const backendBaseUrl = 'http://localhost:3000';
    const searchUrl = query ? `${backendBaseUrl}/api/jobs/search?q=${query}` : `${backendBaseUrl}/api/jobs`;
    fetch(searchUrl)
      .then(response => response.json())
      .then(data => displayJobs(data))
      .catch(error => console.error('Error fetching jobs:', error));
  }

  fetchJobs();

  searchButton.addEventListener('click', () => {
    const searchTerm = searchInput.value;
    fetchJobs(searchTerm);
  });

document.getElementById('searchInput')
searchInput.addEventListener('keydown', function(event) {
  console.log('Keydown event fired!');
});
});