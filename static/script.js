// script.js
document.addEventListener('DOMContentLoaded', function() {
  const resultDiv = document.getElementById("result");
  const encodingForm = document.querySelector('form[action="/encode"]');
  const decodingForm = document.querySelector('form[action="/decode"]');

  function showAlert(message, isError = false) {
    console.log('Showing alert:', message, 'isError:', isError);
    const alertDiv = document.createElement('div');
    alertDiv.textContent = message;
    alertDiv.style.padding = '10px';
    alertDiv.style.margin = '10px 0';
    alertDiv.style.borderRadius = '5px';
    alertDiv.style.color = 'white';
    alertDiv.style.backgroundColor = isError ? '#f44336' : '#4CAF50';
    resultDiv.innerHTML = ''; // Clear previous results
    resultDiv.appendChild(alertDiv);
    resultDiv.style.display = 'block'; // Make sure the result div is visible
  }

  function displayDownloadLinks(links) {
    const linksDiv = document.createElement('div');
    linksDiv.innerHTML = '<h3>Download Encoded Images:</h3>';
    links.forEach((link, index) => {
      const linkElement = document.createElement('a');
      linkElement.href = link;
      linkElement.textContent = `Download Image ${index + 1}`;
      linkElement.style.display = 'block';
      linkElement.style.margin = '5px 0';
      linksDiv.appendChild(linkElement);
    });
    resultDiv.appendChild(linksDiv);
  }

  if (encodingForm) {
    console.log('Encoding form found');
    encodingForm.addEventListener('submit', function(e) {
      e.preventDefault();
      console.log('Encoding form submitted');
      const formData = new FormData(this);
      
      fetch('/encode', {
        method: 'POST',
        body: formData
      })
      .then(response => {
        console.log('Response received:', response);
        return response.json();
      })
      .then(data => {
        console.log('Data received:', data);
        if (data.error) {
          showAlert(data.error, true);
        } else {
          showAlert(data.result);
          if (data.download_links && data.download_links.length > 0) {
            displayDownloadLinks(data.download_links);
          }
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred: ' + error, true);
      });
    });
  } else {
    console.log('Encoding form not found');
  }

  if (decodingForm) {
    decodingForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const formData = new FormData(this);
      
      fetch('/decode', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          showAlert(data.error, true);
        } else {
          showAlert(data.result);
          displayDecodedFileDownload(data.download_link);
        }
      })
      .catch(error => {
        showAlert('An error occurred: ' + error, true);
      });
    });
  }
  
  function displayDecodedFileDownload(downloadLink) {
    const downloadDiv = document.createElement('div');
    downloadDiv.innerHTML = `
      <h3>Decoded Text File:</h3>
      <a href="${downloadLink}" download>Download Decoded Text</a>
    `;
    resultDiv.appendChild(downloadDiv);
  }

  // Keep the existing video playback rate code
  var video = document.querySelector(".background-video");
  if(video) {
    video.playbackRate = 0.1;
  }
});