// db/db.js
const mysql = require('mysql2/promise');

// Hole die Werte aus den Umgebungsvariablen
const {
  MYSQL_HOST = 'localhost',
  MYSQL_PORT = '3306',
  MYSQL_USER = 'root',
  MYSQL_PASSWORD = '',
  MYSQL_DATABASE = 'test'
} = process.env;

// Einen Pool erzeugen (empfohlen für Node-Server)
const pool = mysql.createPool({
  host: MYSQL_HOST,
  port: Number(MYSQL_PORT),
  user: MYSQL_USER,
  password: MYSQL_PASSWORD,
  database: MYSQL_DATABASE,
  // Optional: Pool-Optionen
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

module.exports = pool;
