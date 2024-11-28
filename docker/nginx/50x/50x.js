// Configuration for retry attempts
const PHASE_1_DURATION = 2 * 60 * 1000;  // 2 minutes in milliseconds
const PHASE_2_DURATION = 5 * 60 * 1000;  // 5 minutes in milliseconds
const PHASE_3_DURATION = 10 * 60 * 1000; // 10 minutes in milliseconds

const PHASE_1_INTERVAL = 5000;   // 5 seconds
const PHASE_2_INTERVAL = 10000;  // 10 seconds
const PHASE_3_INTERVAL = 30000;  // 30 seconds

let startTime = 0;
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

// Function to determine current retry interval based on elapsed time
function getCurrentInterval() {
    const elapsedTime = Date.now() - startTime;

    if (elapsedTime <= PHASE_1_DURATION) {
        return PHASE_1_INTERVAL;
    } else if (elapsedTime <= PHASE_2_DURATION) {
        return PHASE_2_INTERVAL;
    } else if (elapsedTime <= PHASE_3_DURATION) {
        return PHASE_3_INTERVAL;
    }
    return null; // Signal to stop retrying
}

// Function to remove loading animation
function removeLoadingAnimation() {
    const spinner = document.querySelector('.spinner');
    if (spinner) {
        spinner.style.display = 'none';
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
    const interval = getCurrentInterval();

    if (interval === null) {
        console.log('Maximum retry time reached');
        removeLoadingAnimation();
        return;
    }

    retryTimeout = setTimeout(checkConnection, interval);
}

// Start the first connection attempt
document.addEventListener('DOMContentLoaded', () => {
    startTime = Date.now();
    checkConnection();
});

// Cleanup function to prevent memory leaks
window.addEventListener('beforeunload', () => {
    if (retryTimeout) {
        clearTimeout(retryTimeout);
    }
});