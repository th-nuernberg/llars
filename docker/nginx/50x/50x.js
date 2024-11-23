// Configuration for retry attempts
const RETRY_INTERVAL = 5000; // 5 seconds between attempts
const MAX_RETRIES = 10;      // Maximum number of attempts
let retryCount = 0;
let retryTimeout;

// Main navigation functions
function goHome() {
    window.location.href = '/';
}

function navigateTo(link) {
    switch (link) {
        case 'Impressum':
            window.location.href = '/impressum';
            break;
        case 'Datenschutz':
            window.location.href = '/datenschutz';
            break;
        case 'Kontakt':
            window.location.href = '/kontakt';
            break;
    }
}

// Function to check connection
function checkConnection() {
    fetch('/', {
        method: 'HEAD',
        cache: 'no-cache'
    })
    .then(response => {
        if (response.ok) {
            console.log('Connection restored');
            window.location.reload();
        } else {
            retryConnection();
        }
    })
    .catch(() => {
        retryConnection();
    });
}

// Function for retry attempts
function retryConnection() {
    retryCount++;

    if (retryCount < MAX_RETRIES) {
        retryTimeout = setTimeout(checkConnection, RETRY_INTERVAL);
    } else {
        window.location.reload(); // Simply reload the page after max retries
    }
}

// Start the first connection attempt
document.addEventListener('DOMContentLoaded', () => {
    checkConnection();
});