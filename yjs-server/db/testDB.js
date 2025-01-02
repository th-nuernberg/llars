// db/testDB.js (Beispieldatei zum Testen)
const pool = require('./db');

async function testDBConnection() {
  try {
    const [rows] = await pool.query('SELECT NOW() AS now');
    console.log('DB-Zeit:', rows[0].now);
  } catch (err) {
    console.error('DB-Verbindungsfehler:', err);
  }
}

module.exports = { testDBConnection };


async function testDBConnection() {
  try {
    const [rows] = await pool.query('SELECT NOW() AS now');
    console.log('DB-Zeit:', rows[0].now);
  } catch (err) {
    console.error('DB-Verbindungsfehler:', err);
  }
}

module.exports = { testDBConnection };
