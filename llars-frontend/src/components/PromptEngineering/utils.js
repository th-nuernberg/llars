// printYDoc.js

/**
 * Gibt die Struktur eines Y.Doc übersichtlich in der Konsole aus
 * @param {Y.Doc} ydoc - Das Yjs-Dokument, das ausgegeben werden soll
 * @param {Object} options - Optionale Konfiguration für die Ausgabe
 * @param {boolean} options.showContent - Ob der Inhalt der YText-Objekte angezeigt werden soll (Standard: true)
 * @param {boolean} options.showDetails - Ob zusätzliche Details angezeigt werden sollen (Standard: false)
 */
function printYDoc(ydoc, options = {}) {
    const {
        showContent = true,
        showDetails = false
    } = options;

    console.group('YDoc Structure');
    try {
        // Grundlegende Dokumentinformationen
        console.log('Document ID:', ydoc.clientID);
        if (showDetails) {
            console.log('GC enabled:', ydoc.gc);
            console.log('Auto Load:', ydoc.autoLoad);
        }

        // Blocks Map ausgeben
        const blocksMap = ydoc.getMap('blocks');
        console.group('blocks (YMap)');

        // Alle Blöcke durchgehen
        blocksMap.forEach((value, key) => {
            console.group(`"${key}" (YMap)`);

            // Titel und Position ausgeben
            console.log('title:', value.get('title'));
            console.log('position:', value.get('position'));

            // Content (YText) ausgeben
            const content = value.get('content');
            if (content && content.toString) {
                console.group('content (YText)');
                if (showContent) {
                    console.log('value:', `"${content.toString()}"`);
                }
                if (showDetails) {
                    console.log('length:', content.length);
                    console.log('deleted:', content.deleted);
                }
                console.groupEnd();
            }

            console.groupEnd();
        });

        console.groupEnd(); // blocks

        // Zusätzliche Maps oder Arrays ausgeben, falls vorhanden
        if (showDetails) {
            // Block-Positionen Map
            const blockPositions = ydoc.getMap('blockPositions');
            if (blockPositions.size > 0) {
                console.group('blockPositions (YMap)');
                blockPositions.forEach((value, key) => {
                    console.log(`${key}:`, value);
                });
                console.groupEnd();
            }
        }

    } catch (error) {
        console.error('Error while printing YDoc:', error);
    } finally {
        console.groupEnd(); // YDoc Structure
    }
}

/**
 * Einfachere Version für schnelles Debugging
 * @param {Y.Doc} ydoc - Das Yjs-Dokument
 */
function quickPrintYDoc(ydoc) {
    const blocks = {};
    const blocksMap = ydoc.getMap('blocks');

    blocksMap.forEach((value, key) => {
        blocks[key] = {
            title: value.get('title'),
            position: value.get('position'),
            content: value.get('content')?.toString() || ''
        };
    });

    console.log(JSON.stringify(blocks, null, 2));
}

// Export both functions
export { printYDoc, quickPrintYDoc };
export default printYDoc;
