// utils.js
function logRoomsAndUsers(io) {
  const rooms = io.sockets.adapter.rooms;
  const sids = io.sockets.adapter.sids; // Sockets und ihre Räume
  console.log(`🔍 Current rooms and users:`);

  rooms.forEach((value, room) => {
    // Räume ohne zugehörige Sockets (eigene Räume der Sockets) überspringen
    if (sids.has(room)) return;

    // Benutzer im Raum ermitteln
    const users = Array.from(value).map((socketId) => {
      const socket = io.sockets.sockets.get(socketId);
      return socket ? socket.id : 'unknown';
    });

    console.log(`Room "${room}" has ${users.length} user(s): ${users.join(', ')}`);
  });
}

const Y = require('yjs');
function printYDoc(ydoc, indent = 0) {
  const spaces = ' '.repeat(indent);

  // Gehe durch alle Maps im YDoc
  ydoc.share.forEach((value, key) => {
    console.log(`${spaces}📄 Map: ${key}`);

    if (value instanceof Y.Map) {
      value.forEach((mapValue, mapKey) => {
        if (mapValue instanceof Y.Text) {
          console.log(`${spaces}  📝 ${mapKey}: "${mapValue.toString()}"`);
        } else if (mapValue instanceof Y.Map) {
          console.log(`${spaces}  📦 ${mapKey}:`);
          printYDocMap(mapValue, indent + 4);
        } else {
          console.log(`${spaces}  ✨ ${mapKey}: ${JSON.stringify(mapValue)}`);
        }
      });
    }
  });
}

function printYDocMap(ymap, indent = 0) {
  const spaces = ' '.repeat(indent);

  ymap.forEach((value, key) => {
    if (value instanceof Y.Text) {
      console.log(`${spaces}📝 ${key}: "${value.toString()}"`);
    } else if (value instanceof Y.Map) {
      console.log(`${spaces}📦 ${key}:`);
      printYDocMap(value, indent + 2);
    } else {
      console.log(`${spaces}✨ ${key}: ${JSON.stringify(value)}`);
    }
  });
}

// Exportiere beide Funktionen
module.exports = {
  logRoomsAndUsers,
  printYDoc
};