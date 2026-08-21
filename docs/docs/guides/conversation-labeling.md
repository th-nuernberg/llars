# Konversationslabeling

Konversationslabeling (`function_type_id = 9`) ist der Szenariotyp für Studien,
in denen **innerhalb** eines Gesprächs gelabelt wird: nicht die Nachricht als
Ganzes bekommt eine Kategorie, sondern jede Sinneinheit darin.

Entstanden ist er für die VRM-Studie (Verbal Response Modes nach Stiles), in der
rund 8.300 Spans über 86 Beratungsverläufe kodiert werden.

## Wann dieser Typ — und wann nicht

| Situation | Typ |
|-----------|-----|
| Ein Text bekommt **eine** Kategorie | Labeling (7) |
| Ein Gespräch bekommt **eine** Kategorie | Labeling (7), Item = Konversation |
| Jede Sinneinheit im Gespräch bekommt **eine eigene** Kategorie | **Konversationslabeling (9)** |

Der Unterschied ist nicht kosmetisch. Er bestimmt, worüber gerechnet wird:

- **Einheit der Analyse** ist der Span, nicht das Item. Krippendorffs Alpha
  betrachtet Span-Zellen; ein Gespräch trägt rund 92 Zeilen der Rater-Matrix bei,
  nicht eine.
- **Fortschritt** hat einen echten Zwischenstand. Ein Gespräch ist erst
  abgeschlossen, wenn *alle* seine Spans entschieden sind — „40 von 92" ist ein
  normaler Zustand, den klassisches Labeling gar nicht kennt.
- **Bearbeitungszeit** wird pro Span gemessen, nicht pro Gespräch.

## Segmentierung kommt aus dem Import

Die Spans werden **nicht** von den Bewertenden gezogen. Sie stehen beim Import
fest und sind für die Dauer der Studie eingefroren.

Das ist eine methodische Entscheidung, keine technische Einschränkung: Würde
jede Person selbst segmentieren, wären die Zeilen der Rater-Matrix nicht mehr
dieselben Einheiten, und ein Übereinstimmungsmaß über sie hinweg wäre nicht
interpretierbar. Man würde Uneinigkeit über die Kategorie nicht mehr von
Uneinigkeit über den Zuschnitt trennen können.

Ist eine Grenze erkennbar falsch, gibt es zwei Wege:

1. **Melden** über eine dafür vorgesehene Label-Karte (z. B. „Span-Grenze
   falsch"). Das ist der Normalweg — die Segmentierung bleibt für alle gleich,
   und das Problem ist dokumentiert.
2. **Trennen oder zusammenführen** über die beiden zurückhaltenden Werkzeuge
   am unteren Panelrand. Bewusst die Ausnahme.

## Die Oberfläche

Links das Gespräch als Sprechblasen, rechts die Entscheidung.

**Turn für Turn.** Sichtbar ist immer nur, was bis zur aktuellen Stelle gesagt
wurde. Ist eine Beratenden-Nachricht durchgelabelt, erscheint die Antwort der
ratsuchenden Person animiert, und es geht beim ersten Span der nächsten
Nachricht weiter. Spätere Nachrichten bleiben verborgen: Die Bewertenden sollen
nicht wissen, wie das Gespräch ausgeht.

**Auto-Weiter ist standardmäßig an.** Nach einer Entscheidung springt der Fokus
zum nächsten Span. Bei ~92 Entscheidungen je Gespräch ist das Zurückklicken in
den Text sonst der größte Einzelaufwand der ganzen Aufgabe. Der Schalter merkt
sich seinen Zustand. Ein *Abwählen* löst kein Weiterspringen aus — sonst käme
man nie zurück, um etwas zu korrigieren.

**Tastatur:** Ziffern `1`–`9` wählen eine Kategorie, `Enter` geht weiter,
`Backspace` zurück.

**Bereits entschiedene Spans** tragen ihr Label sichtbar im Text. So sieht man
die eigene Sequenz — und bemerkt zwei gleiche Labels hintereinander, den
Hinweis darauf, dass hier eigentlich ein Block zusammengehört.

**Gespeichert wird sofort bei jeder Auswahl.** Eingebettet in die
Evaluationssitzung blendet das Layout seine Aktionsleiste und damit jeden
Speichern-Knopf aus — eine Oberfläche, die auf einen solchen wartet, persistiert
nichts. Das ist in einer Produktivstudie schon einmal passiert.

Die Freitext-Notiz wird entprellt gespeichert (800 ms), nicht bei jedem
Tastenanschlag, und beim Verlassen eines Spans sofort weggeschrieben.

## Co-Pilot

Ist der Co-Pilot aktiv, steht über den Kategorien ein Modellvorschlag mit
Begründung und Textbeleg.

- **Nie vorausgewählt.** Übernehmen kostet einen bewussten Klick.
- **Pro Span**, nicht pro Gespräch — ein Vorschlag für den ganzen Verlauf wäre
  wertlos.
- **Gleiche Sicht wie der Mensch.** Der serverseitig gebaute `{context}` folgt
  denselben Sichtbarkeitsregeln (`context_window`, `no_future_messages`).
  Andernfalls entschieden beide über unterschiedliche Information und wären
  nicht vergleichbar.
- **Verdeckte Kontrollgruppe.** Ein Teil der Spans wird serverseitig ohne
  Vorschlag ausgespielt. Welche, entscheidet ein deterministischer Hash — die
  Zuordnung ist reproduzierbar und erreicht die Bewertenden nie.
- **Nützlichkeit** lässt sich per Daumen bewerten; die Stimme landet in der
  Log-Zeile *dieses* Spans.

## Span trennen

Am unteren Rand des Panels, über dem Notizfeld, sitzt ein leiser Textlink
„Span trennen". Er öffnet einen
zeichengenauen Schnittpunkt-Wähler: Klick in den Text, beide Hälften als
Vorschau, bestätigen.

Drei Regeln halten die Studiendaten dabei ehrlich:

- Der Schnitt muss **echt innerhalb** liegen — an der Kante entstünde eine
  Einheit der Länge null.
- Neue IDs werden **abgeleitet** (`x` → `x+a` / `x+b`), nicht neu
  durchnummeriert. Ein Export von vorher joint dadurch weiterhin, unberührte
  Spans behalten ihre ID.
- Das Vote auf den alten Span wird **für alle Bewertenden gelöscht**, zusammen
  mit dessen Co-Pilot-Log und Zeitmessung. Eine Entscheidung über den ganzen
  Span ist keine Entscheidung über eine Hälfte, und die Messungen beschreiben
  eine Einheit, die es nicht mehr gibt.

## Span zusammenführen

Der umgekehrte Weg. Die Spans werden mit **⌘- bzw. Strg-Klick** im Text
markiert — markierte Spans bekommen eine gestrichelte Umrandung, und der Knopf
zeigt die Anzahl. „Span zusammenführen" ist ausgegraut, bis die Markierung
tatsächlich zu einer Einheit werden kann.

Dass man die Spans selbst markiert, ist der Punkt: Eine frühere Fassung suchte
sich den Partner selbst (der folgende Span, sonst der vorherige). Das wirkte
willkürlich, weil nichts auf dem Bildschirm sagte, welcher Nachbar gemeint war.

Markierbar sind beliebig viele; zusammenführen lassen sie sich, wenn sie eine
**ununterbrochene Folge** in **derselben Nachricht** bilden. Zwischen ihnen darf
nur **Leerraum** stehen. Das ist keine Formalität: In einer echten Segmentierung
gehört das Trennzeichen zu keinem Span — Satz-Spans liegen typischerweise ein
Leerzeichen auseinander —, und strikte Lückenlosigkeit hätte den Knopf in jedem
realen Gespräch tot gelassen. Ein Leerzeichen zu schlucken ist harmlos, Wörter
zu schlucken nicht: über die hat niemand entschieden.

Ein normaler Klick navigiert wie gewohnt und **löscht die Markierung** — sonst
würde eine vergessene Auswahl den Knopf scharf halten, während man längst
woanders ist.

Die neue ID wird abgeleitet, und das Rückgängigmachen eines Splits ist der
Normalfall: `x+a` + `x+b` ergibt wieder `x`. Eine Studie, die geteilt und wieder
verbunden hat, trägt danach exakt die IDs von vorher.

Auch hier verschwinden **beide** Votes für alle Bewertenden. Zwei
Entscheidungen über zwei Einheiten sind keine Entscheidung über deren
Vereinigung, und eine davon zu übernehmen hieße, jemandem eine Meinung
unterzuschieben.

### „Ich labele einfach beide gleich"

Wenn zwei benachbarte Spans dieselbe Kategorie tragen, erscheint ein Hinweis,
der sie mit einem Klick zusammenführt — sowohl während man auf einem der beiden
steht als auch direkt danach, wenn Auto-Weiter schon zum nächsten gesprungen
ist.

Der Klick ist Absicht: **automatisch** darf das nicht passieren. Die
Segmentierung gehört allen Bewertenden gemeinsam. Würde sie sich anhand der
Labels *einer* Person ändern, verschöben sich die Einheiten unter allen anderen
— und deren Votes auf beiden Hälften würden gelöscht. Danach bewerteten zwei
Personen nicht mehr dieselben Dinge, was ein Übereinstimmungsmaß genau
bedeutungslos macht.

Für die Auswertung ist das Zusammenfassen gleicher Nachbarn ohnehin ein
Analyseschritt (Block-Merge), kein Eingriff in die Daten.

Weil beide Werkzeuge die Segmentierung für *alle* verändern, sitzen sie
zurückhaltend am unteren Rand über dem Notizfeld — sie sollen die Ausnahme
bleiben, nicht mit den Label-Buttons konkurrieren.

## Auswertung

Im Evaluations-Tab des Szenario-Managers wie bei jedem anderen Typ — mit dem
Unterschied, dass die Einheit der Span ist.

Der Export trägt zusätzlich `span_id`, `message_id` und `span_index`. Die
`span_id` ist ein **stabiler String aus dem Import**, keine laufende Datenbank-ID:
Nur so bleibt ein Re-Import idempotent und lassen sich Exporte aus zwei
Zeitpunkten joinen. Die drei Spalten stehen am Ende der Spaltenliste, damit
Auswertungen, die nach Position indizieren, unverändert weiterlaufen.

Ist ein LLM als Assessor beteiligt, ist sein „Vote" für die Übereinstimmung sein
**primärer Vorschlag** — genau der, den ein Mensch zu sehen bekommen hätte.

## Anlegen

Über die v1-Szenario-API mit `type: "conversation_labeling"`. Das genaue
Datenformat samt Validierungsregeln steht unter
[Evaluation-Datenformate](../entwickler/evaluation-datenformate.md#9-conversation-labeling-function_type_id--9).

Kurz gefasst: Ein Item ist ein Gespräch, seine Nachrichten tragen
`labelable: true|false`, und labelbare Nachrichten führen eine Liste von Spans
mit `span_id`, `start` und `end` — Zeichen-Offsets in den Nachrichtentext, der
nur **einmal** gespeichert wird.

## Bekannte Grenzen

- Der **LLM-Evaluator** (Assessors-Tab) läuft für diesen Typ noch über den
  Ganzes-Item-Klassifikator und erzeugte damit ein Label pro Gespräch statt pro
  Span. Für den Modellvergleich zählt der Co-Pilot-Pfad, der span-weise
  arbeitet.
- Die **Batch-Generierung** über Spans ist noch nicht auf das Mengengerüst der
  Vollstudie ausgelegt.
