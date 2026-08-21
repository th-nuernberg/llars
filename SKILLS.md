# LLARS Skills Index

Diese Datei listet alle projektspezifischen Codex/Claude Skills im Repository.

## Zweck

1. Neue Entwickler sehen sofort, welche Skill-Workflows verfügbar sind.
2. Skill-Änderungen werden versioniert und reviewbar.
3. CI/CD- und Test-bezogene Skills sind zentral auffindbar.

## Verfügbare Skills

| Skill | Datei | Zweck |
|---|---|---|
| chatbot-debugging | `.claude/skills/chatbot-debugging/SKILL.md` | Chatbot-Fehleranalyse und Debugging |
| ci-cd-debugging | `.claude/skills/ci-cd-debugging/SKILL.md` | Pipeline-Status, Job-Logs, Retry/Monitoring |
| code-review | `.claude/skills/code-review/SKILL.md` | Strukturiertes Review mit Findings |
| feature-development | `.claude/skills/feature-development/SKILL.md` | Standardablauf für neue Features |
| llars-api-guide | `.claude/skills/llars-api-guide/skill.md` | API-Routen, Patterns, Integrationshinweise |
| local-setup | `.claude/skills/local-setup/SKILL.md` | Lokales Setup und Troublehooting |
| manual-deployment | `.claude/skills/manual-deployment/SKILL.md` | Manueller Deploy-Ablauf |
| paper-writing | `.claude/skills/paper-writing/SKILL.md` | Wissenschaftliches Schreib-Setup |
| security-review | `.claude/skills/security-review/SKILL.md` | Security-Fokus für Code-Änderungen |
| tdd | `.claude/skills/tdd/SKILL.md` | Test-First/TDD-Workflow |
| update-docs | `.claude/skills/update-docs/SKILL.md` | Dokumentation konsistent aktualisieren |
| wizard-testing | `.claude/skills/wizard-testing/SKILL.md` | Wizard-spezifische Teststrategie |

## Pflege

Bei neuen Skills:

1. Skill-Datei unter `.claude/skills/<name>/SKILL.md` anlegen.
2. Diese `SKILLS.md` um den Eintrag ergänzen.
3. Wenn der Skill Tests/CI betrifft, auch `docs/testing/nightly/NIGHTLY_TILE_MATRIX.md` und `CLAUDE.md` prüfen.
