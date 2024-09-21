// Liste der Admin-Benutzer
const admins = ['admin', 'Admin2']; // Diese Benutzernamen sind Admins

// Funktion zur Überprüfung, ob ein Benutzer ein Admin ist
export function isAdmin(username) {
  return admins.includes(username);
}
