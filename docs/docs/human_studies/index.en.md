# Human Studies in LLARS

This section bundles the **Human Studies** (studies with human raters) conducted
in LLARS. Here, LLARS is used not only as a tool but as a platform for repeatable
rating studies: create a scenario, recruit raters via tracked invitation links,
collect ratings, provide feedback.

The section is **designed to be extensible** — each study gets its own subfolder
and follows the same generic process, the [Playbook](playbook.md). Currently one
study is documented; more will be added and linked here.

## Structure of this section

| Page | Content |
|-------|--------|
| [Playbook](playbook.md) | **Reusable process** — how we set up and run a Human Study in LLARS from start to finish (study-independent). |
| [Can AI Do Counseling?](KannKIBeratung/index.md) | The **first** Human Study run in LLARS, documented along the Playbook. |
| [IJCAI 2026 Demo](ijcai-demo.md) | Conference **live demo**: one QR code, seven shared demo scenarios (one per evaluation type), seeding & joining. |

## Ongoing / completed studies

| Study | Type | Status | Docs |
|--------|-----|--------|------|
| **Can AI Do Counseling?** | Pairwise Comparison (AI/human comparison of counseling responses) | Live (production, scenario 492) | [Overview](KannKIBeratung/index.md) · [Setup](KannKIBeratung/setup.md) · [Recruiting](KannKIBeratung/recruiting.md) · [Annotation Audit](KannKIBeratung/annotations-audit.md) |

## Adding a new study

1. Create a new subfolder `human_studies/<StudyName>/`.
2. Work through the [Playbook](playbook.md) process (scenario, referral links,
   invitation, consent/anonymity, feedback, deploy, tracking).
3. Create an `index.md` as the study overview and — where it makes sense —
   add `setup.md` / `recruiting.md`.
4. Register the study in the table above as well as in the `mkdocs.yml`
   navigation.

> The "Can AI Do Counseling?" study serves as a fully worked-out reference
> example: it shows how the generic Playbook process was concretely implemented.
