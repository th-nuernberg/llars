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
