# Interview-Leitfaden: LLARS-Nutzungserfahrungen

**Zielgruppe:** Beratungsforscher:innen und Entwickler:innen, die LLARS aktiv nutzen
**Format:** Semi-strukturiertes Interview, ca. 30–45 Minuten
**Aufzeichnung:** Audio (mit Einverständnis), anonymisierte Auswertung

---

## 0. Einleitung (2 Min.)

- Begrüßung, Vorstellung des Interviewziels
- Einverständnis zur Aufzeichnung einholen
- Hinweis: Es gibt keine richtigen oder falschen Antworten — wir möchten Ihre ehrliche Erfahrung verstehen

> *"Wir möchten verstehen, wie LLARS in Ihrer täglichen Arbeit eingesetzt wird und was gut oder weniger gut funktioniert. Das Interview dauert ca. 30–45 Minuten."*

---

## 1. Hintergrund und Rolle (3 Min.)

1. **Was ist Ihre Rolle im Projekt?**
   - (Beratungsforschung / Entwicklung / beides)

2. **Wie lange nutzen Sie LLARS bereits?**

3. **Welche Module nutzen Sie hauptsächlich?**
   - (Prompt Editor / Batch Generation / Evaluation)

---

## 2. Arbeitsweise vor LLARS (5 Min.)

4. **Wie haben Sie vor LLARS Prompts für LLM-Systeme entwickelt?**
   - Nachfragen: Welche Tools? Wie wurde zusammengearbeitet? Wie wurden Versionen verwaltet?

5. **Wie haben Sie LLM-Outputs vorher verglichen oder bewertet?**
   - Nachfragen: Manuell? Tabellen? Eigene Skripte?

6. **Was waren die größten Schwierigkeiten bei diesem Vorgehen?**

---

## 3. Kollaboratives Prompt Engineering (7 Min.)

7. **Beschreiben Sie, wie Sie den Prompt-Editor typischerweise nutzen.**
   - Nachfragen: Allein oder mit anderen? Wie oft?

8. **Haben Sie gleichzeitig mit anderen an Prompts gearbeitet? Wie hat das funktioniert?**
   - Nachfragen: War klar, wer was geändert hat? Gab es Konflikte?

9. **Nutzen Sie die Test-Funktion im Editor? Wie hilft sie Ihnen?**
   - Nachfragen: Testen Sie gegen verschiedene Modelle?

10. **Nutzen Sie die Versionierung? Haben Sie schon mal auf eine ältere Version zurückgegriffen?**

11. **Was hat sich im Vergleich zu Ihrer vorherigen Arbeitsweise verbessert? Was fehlt Ihnen?**

---

## 4. Batch Generation (7 Min.)

12. **Haben Sie die Batch-Generierung genutzt? Für welchen Zweck?**
    - Nachfragen: Wie viele Modelle/Prompts/Datenpunkte?

13. **Wie hilfreich war die Kostenübersicht vor der Generierung?**
    - Nachfragen: Hat das Ihr Vorgehen beeinflusst?

14. **Konnten Sie die Ergebnisse gut nachvollziehen? (Provenienz: welches Modell, welcher Prompt, welche Kosten)**

15. **Hätten Sie diese Art von systematischem Vergleich ohne LLARS durchführen können?**
    - Nachfragen: Wenn ja, wie? Wenn nein, warum nicht?

---

## 5. Evaluation (7 Min.)

16. **Welche Evaluationstypen haben Sie genutzt?**
    - (Rating / Ranking / Labeling / Vergleich / domänenspezifisch)

17. **Wie war der Einstieg in die Evaluation? War der Scenario Wizard hilfreich?**

18. **Konnten Sie Evaluationen eigenständig einrichten und durchführen, oder brauchten Sie technische Unterstützung?**
    - Nachfragen: Was war einfach, was war schwierig?

19. **Haben Sie die Übereinstimmungsmetriken (z.B. Krippendorff's Alpha) genutzt? Waren sie für Sie verständlich und nützlich?**

20. **Haben Sie LLM-Evaluatoren eingesetzt? Wenn ja, wie war das Ergebnis im Vergleich zu menschlichen Bewertern?**

---

## 6. Zusammenarbeit Domain-Experten & Entwickler (5 Min.)

21. **Wie würden Sie die Zusammenarbeit zwischen Beratungsforscher:innen und Entwickler:innen in LLARS beschreiben?**

22. **Gibt es Funktionen, die besonders zur Zusammenarbeit beitragen?**

23. **Gab es Situationen, in denen die Zusammenarbeit in LLARS schwierig war?**
    - Nachfragen: Verständigungsprobleme? Fehlende Features?

---

## 7. Gesamtbewertung und Verbesserungswünsche (5 Min.)

24. **Was sind für Sie die drei größten Stärken von LLARS?**

25. **Was sind die drei größten Schwächen oder Einschränkungen?**

26. **Welche Features fehlen Ihnen am meisten?**

27. **Würden Sie LLARS anderen Forschungsgruppen empfehlen? Warum / warum nicht?**

---

## 8. Abschluss (2 Min.)

28. **Gibt es etwas, das wir nicht angesprochen haben und das Ihnen wichtig ist?**

29. **Wären Sie bereit, an einer kurzen Nachbefragung teilzunehmen, falls wir Rückfragen haben?**

- Dank und Verabschiedung

---

## Auswertungshinweise

Die Interviews werden thematisch codiert entlang folgender Dimensionen:

| Code | Thema | Paper-Bezug |
|------|-------|-------------|
| **COLLAB** | Kollaboratives Editing, Versionierung | Sec. 2.1, Interview-Theme 1 |
| **BATCH** | Systematischer Modellvergleich, Kosten | Sec. 2.2, Interview-Theme 2 |
| **EVAL** | Eigenständige Evaluation, Metriken | Sec. 2.3, Interview-Theme 3 |
| **BRIDGE** | Zusammenarbeit Domain-Experten & Entwickler | Zentrale These |
| **LIMIT** | Einschränkungen, fehlende Features | Sec. 4 Limitations |
| **BEFORE** | Arbeitsweise vor LLARS (Baseline) | Kontrast |
