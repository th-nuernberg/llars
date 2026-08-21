"""
Canonical consent text v3 (2026-05) for LLARS research-study referrals.

Both DE and EN texts are stored verbatim here and hashed at import
time. The SHA-256 lands in every audit-trail row so we can prove the
exact wording a user clicked through later.

Drafting basis:
- Art. 6(1)(a), Art. 9(2)(a) + (j), Art. 13, Art. 89(1) GDPR
- §27 Abs. 1 BDSG (Forschungsprivileg)
- §22 Abs. 2 BDSG (technical-organisational safeguards)
- Erwägungsgrund 33 GDPR (broad consent for "certain areas of
  scientific research" if recognised ethical standards apply)
- EDPB Guidelines 05/2020 paras 153–164 (research consent)
- BayLDA Orientierungshilfe Einwilligung v1.0 (01.09.2021)
- DFG-Kodex "Leitlinien zur Sicherung guter wissenschaftlicher Praxis"

If this text changes, increment the version string AND create a new
module — never edit an existing version. Audit-trail integrity
depends on past versions staying byte-identical.
"""

import hashlib

CONSENT_VERSION = "study-consent-v3-2026-05"


CONSENT_TEXT_DE = """\
Ich bin volljährig (mindestens 18 Jahre alt) und nehme freiwillig an der \
Forschungsstudie LLARS des Zentrums für Künstliche Intelligenz (KIZ) der \
Technischen Hochschule Nürnberg Georg Simon Ohm teil.

Ich willige ein, dass meine Bewertungen, technische Metadaten (Session-ID, \
Zeitstempel, gehashte IP-Adresse, Browser-Typ) und – sofern ich sie eingebe \
– optionale demografische Basisangaben pseudonymisiert auf Servern in \
Deutschland gespeichert und im Forschungsbereich „Counsellor-LLM-Evaluation \
am KIZ der TH Nürnberg" verarbeitet werden. Rechtsgrundlage: Art. 6 Abs. 1 \
lit. a DSGVO sowie – soweit besondere Kategorien personenbezogener Daten \
betroffen sind – Art. 9 Abs. 2 lit. a + lit. j DSGVO i.V.m. §27 Abs. 1 BDSG \
und Art. 89 Abs. 1 DSGVO unter den Garantien des §22 Abs. 2 BDSG \
(insbesondere Pseudonymisierung und Zugangskontrolle). Diese Forschung \
folgt dem DFG-Kodex „Leitlinien zur Sicherung guter wissenschaftlicher \
Praxis" sowie den Ethikleitlinien der TH Nürnberg.

Ergebnisse werden ausschließlich in aggregierter, nicht-personenbezogener \
Form in wissenschaftlichen Veröffentlichungen (u. a. EMNLP, ACL) \
publiziert. Eine zeilenweise Rohdaten-Veröffentlichung auf Zenodo, \
HuggingFace oder vergleichbaren Repositorien erfolgt NICHT. Eine \
Weiterverwendung der pseudonymisierten Daten für inhaltlich verwandte \
Folgestudien derselben Forschungslinie am KIZ ist eingeschlossen (Erwgr. 33 \
DSGVO). Empfänger sind ausschließlich die unmittelbar an der Studie \
beteiligten Forschenden der TH Nürnberg sowie – bezogen auf aggregierte, \
anonymisierte Ergebnisse – die jeweilige wissenschaftliche \
Veröffentlichungsplattform. Eine Übermittlung in Drittländer findet nicht \
statt. Eine automatisierte Entscheidungsfindung einschließlich Profiling \
i.S.v. Art. 22 DSGVO findet nicht statt.

Speicherdauer: Pseudonymisierte Bewertungsdaten werden gemäß den \
DFG-Leitlinien und §27 Abs. 1 BDSG für bis zu zehn Jahre nach Ende der \
Studie zu Reproduzierbarkeits- und Archivzwecken aufbewahrt. \
Account-Zugangsdaten werden bei Widerruf bzw. spätestens zwölf Monate nach \
Studien-Ende gelöscht.

Mir ist bekannt, dass die Teilnahme freiwillig ist, dass mir aus einer \
Nichtteilnahme oder einem späteren Widerruf keinerlei Nachteile entstehen, \
und dass ich meine Einwilligung jederzeit ohne Angabe von Gründen mit \
Wirkung für die Zukunft widerrufen kann (Art. 7 Abs. 3 DSGVO). Die \
Rechtmäßigkeit der bis zum Widerruf erfolgten Verarbeitung bleibt davon \
unberührt. Mir stehen die Betroffenenrechte nach Art. 15 (Auskunft), \
Art. 16 (Berichtigung), Art. 17 (Löschung — eingeschränkt durch Art. 17 \
Abs. 3 lit. d DSGVO für bereits in aggregierter Form veröffentlichte \
Ergebnisse), Art. 18 (Einschränkung), Art. 20 (Datenübertragbarkeit) und \
Art. 21 (Widerspruch) DSGVO zu. Beschwerden kann ich beim Bayerischen \
Landesamt für Datenschutzaufsicht (BayLDA, Promenade 18, 91522 Ansbach, \
poststelle@lda.bayern.de) einreichen.

Verantwortlich: Technische Hochschule Nürnberg Georg Simon Ohm, \
Keßlerplatz 12, 90489 Nürnberg, gesetzlich vertreten durch den Präsidenten \
Prof. Dr. Niels Oberbeck. Forschungsdurchführung: Zentrum für Künstliche \
Intelligenz (KIZ), Hohfederstraße 40, 90489 Nürnberg. Studienleitung: \
Philipp Steigerwald, philipp.steigerwald@th-nuernberg.de (Telefon auf \
Anfrage). Datenschutzbeauftragte:r: datenschutz@th-nuernberg.de.

Die vollständige Datenschutzinformation gemäß Art. 13 DSGVO habe ich \
gelesen und ich willige in die oben beschriebene Verarbeitung ein.\
"""


CONSENT_TEXT_EN = """\
I am of legal age (at least 18 years old) and voluntarily participate in \
the LLARS research study conducted by the Centre for Artificial \
Intelligence (KIZ) at Nuremberg Institute of Technology Georg Simon Ohm.

I consent that my ratings, technical metadata (session ID, timestamps, \
hashed IP address, browser type) and – if I provide them – optional basic \
demographic information are stored pseudonymously on servers located in \
Germany and processed within the research area "Counsellor-LLM evaluation \
at KIZ, TH Nürnberg". Legal basis: Art. 6(1)(a) GDPR and – insofar as \
special categories of personal data are affected – Art. 9(2)(a) + (j) GDPR \
in conjunction with §27(1) BDSG and Art. 89(1) GDPR, under the technical \
and organisational safeguards of §22(2) BDSG (in particular \
pseudonymisation and access control). This research follows the DFG Code \
"Guidelines for Safeguarding Good Research Practice" and the ethics \
guidelines of TH Nürnberg.

Results will be published only in aggregated, non-personal form in \
scientific venues (incl. EMNLP, ACL). NO row-level dataset release on \
Zenodo, HuggingFace or comparable repositories will take place. Reuse of \
the pseudonymised data for topically related follow-up studies within the \
same research line at KIZ is included (Recital 33 GDPR). Recipients are \
exclusively the researchers at TH Nürnberg directly involved in the study \
and — limited to aggregated, anonymised results — the respective scientific \
publication venue. No transfer to third countries takes place. No \
automated decision-making including profiling within the meaning of Art. 22 \
GDPR takes place.

Retention: pseudonymised evaluation data are stored, in line with the DFG \
guidelines and §27(1) BDSG, for up to ten years after the end of the \
study, for reproducibility and archival purposes. Account credentials are \
deleted on withdrawal of consent, or at the latest twelve months after the \
end of the study.

I am aware that participation is voluntary, that no disadvantage arises \
from non-participation or later withdrawal, and that I may withdraw my \
consent at any time without giving reasons, with effect for the future \
(Art. 7(3) GDPR). The lawfulness of processing carried out before \
withdrawal remains unaffected. I retain my rights under Art. 15 (access), \
Art. 16 (rectification), Art. 17 (erasure — limited by Art. 17(3)(d) GDPR \
for results already published in aggregated form), Art. 18 (restriction), \
Art. 20 (data portability) and Art. 21 (objection) GDPR. I may lodge a \
complaint with the Bavarian Data Protection Authority (BayLDA, Promenade \
18, 91522 Ansbach, poststelle@lda.bayern.de).

Controller: Technische Hochschule Nürnberg Georg Simon Ohm, Keßlerplatz \
12, 90489 Nürnberg, legally represented by its President, Prof. Dr. Niels \
Oberbeck. Research conducted at: Centre for Artificial Intelligence (KIZ), \
Hohfederstraße 40, 90489 Nürnberg. Study lead: Philipp Steigerwald, \
philipp.steigerwald@th-nuernberg.de (phone on request). Data protection \
officer: datenschutz@th-nuernberg.de.

I have read the full Art. 13 GDPR privacy information and I consent to \
the processing described above.\
"""


# SHA-256 digests of the canonical UTF-8 bytes. Recomputed at every
# Python import — if the constants above change accidentally, the
# digest changes too, so any consent record referencing this version
# can be cryptographically verified against the literal text bytes.
CONSENT_TEXT_SHA256_DE = hashlib.sha256(
    CONSENT_TEXT_DE.encode("utf-8")
).hexdigest()

CONSENT_TEXT_SHA256_EN = hashlib.sha256(
    CONSENT_TEXT_EN.encode("utf-8")
).hexdigest()
