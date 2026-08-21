"""Generate the branded HTML recruitment invitation ("Kann KI Beratung?"),
one file per source-tracking org link, into data/human_study/v15/invitation_branded/.

Same branded shell as the LLARS welcome/reset mails (header gradient, logo,
CTA button, footer). Canonical wording = data/human_study/v15/RECRUITMENT.md.
One file per org so the "Jetzt mitmachen" button carries that org's referral
link (source tracking).

Send: NOT via the app — these are blasted via the Brevo transactional API from
the LLARS server's authorised IPv4 (see docs/MAIL_RUNBOOK.md). Subject:
"Kann KI Beratung?". From: team@llars.e-beratungsinstitut.de, Reply-To:
llars@e-beratungsinstitut.de.

    python3 scripts/human_study/build_invitation_mails.py
"""
import os

# Output dir is resolved relative to the repo root (this file lives at
# scripts/human_study/), so the generator is portable across checkouts.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
OUT = os.path.join(_REPO_ROOT, "data", "human_study", "v15", "invitation_branded")
BASE = "https://llars.e-beratungsinstitut.de/join"
LOGO = "https://llars.e-beratungsinstitut.de/android-chrome-192x192.png"

# One file per recruiting source — the slug = the referral link => source tracking.
ORGS = [
    ("DigiSucht", "kann-ki-beratung-digi-sucht"),
    ("bke", "kann-ki-beratung-bke"),
    ("BVkE", "kann-ki-beratung-bvke"),
    ("KI-Zentrum Bayern", "kann-ki-beratung-kiz"),
    ("Institut für E-Beratung", "kann-ki-beratung-ieb"),
    ("Friends & Family", "kann-ki-beratung-faf"),
    ("Test", "kann-ki-beratung-test"),
]

P = "margin:0 0 14px;font-size:15px;line-height:1.6;"
PS = "margin:0 0 14px;font-size:14px;line-height:1.6;color:#5a6650;"


def shell(inner: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f6f2;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#2c3320;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f2;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:14px 4px 14px 4px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        <tr>
          <td align="center" style="background:linear-gradient(135deg,#b0ca97,#88c4c8);padding:30px 24px;">
            <img src="{LOGO}" width="64" height="64" alt="Kann KI Beratung?" style="display:block;border:0;margin-bottom:10px;border-radius:12px;">
            <div style="font-size:22px;font-weight:600;color:#ffffff;">Kann KI Beratung?</div>
            <div style="font-size:13px;color:#ffffff;opacity:0.9;margin-top:2px;">KI-Zentrum Bayern · TH Nürnberg</div>
          </td>
        </tr>
        <tr><td style="padding:28px 30px 26px;">{inner}</td></tr>
      </table>
      <div style="max-width:600px;font-size:11px;color:#9aa48d;padding:14px 8px;">KI-Zentrum Bayern · TH Nürnberg · <a href="https://ki-zentrum.bayern" style="color:#9aa48d;">ki-zentrum.bayern</a></div>
    </td></tr>
  </table>
</body>
</html>
"""


def inner(join_url: str) -> str:
    return f"""
<p style="{P}">Liebe Fachkräfte,</p>
<p style="{P}">die Entwicklungen in den KI-Technologien schreiten rasant voran. Insbesondere KI-Chatbots erfreuen sich einer breiten Aufmerksamkeit und werden als persönliche Assistenten und Ratgeber in allen Lebenslagen genutzt. Wir am KI-Zentrum Bayern möchten verstehen, welche Rolle KI-Chatbots künftig in professionellen Beratungskontexten der Onlineberatung einnehmen können. Hierzu möchten wir in einem ersten Schritt prüfen:</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 16px;">
  <tr><td style="padding:0 0 8px;font-size:15px;line-height:1.55;">• <strong>Standard-KI vs. trainierte KI:</strong> wie sich die Qualität häufig genutzter KI-Modelle gegenüber speziell trainierten KI-Modellen unterscheidet, und</td></tr>
  <tr><td style="font-size:15px;line-height:1.55;">• <strong>KI vs. Mensch:</strong> wie die Qualität von KI-Modellen im Vergleich zu Antworten professioneller Fachkräfte der Onlineberatung bewertet wird.</td></tr>
</table>
<p style="margin:24px 0;text-align:center;font-size:20px;font-weight:700;line-height:1.4;color:#2c3320;">Wir bitten Sie um Unterstützung und Ihre Expertise.</p>
<p style="margin:0 0 10px;text-align:center;">
  <a href="{join_url}" style="display:inline-block;background:#b0ca97;color:#2c3320;text-decoration:none;font-weight:600;font-size:16px;padding:14px 34px;border-radius:10px 3px 10px 3px;">Jetzt mitmachen</a>
</p>
<p style="margin:0 0 20px;text-align:center;font-size:12px;color:#8a9580;word-break:break-all;"><a href="{join_url}" style="color:#3f7d6b;">{join_url}</a></p>
<p style="{P}">Über den Link gelangen Sie zu einer Testplattform. Darin finden Sie kleine Fallvignetten, in denen Beratungsinteraktionen dargestellt werden — überwiegend aus der Mailberatung, ergänzt um Chat- und Transkript-Formate. Ziel ist es, diese Beratungsinteraktionen durch die Auswahl einer Beratungsantwort fortzuführen. Hierzu werden stets zwei mögliche Antworten bereitgestellt. Diese stammen entweder von einer menschlichen Beratungsfachkraft, einer speziell trainierten KI oder einer untrainierten Standard-KI. Sie wählen, welche der Antworten Sie am ehesten verwenden würden.</p>
<div style="background:#f4f6f2;border-radius:10px 3px 10px 3px;padding:16px 18px;margin:0 0 16px;">
  <p style="margin:0 0 8px;font-size:14px;line-height:1.55;"><strong>1.</strong> Öffnen Sie den Link und legen Sie ein Konto an — <strong>anonym oder mit E-Mail</strong> (Benutzername + Passwort; E-Mail optional).</p>
  <p style="margin:0;font-size:14px;line-height:1.55;"><strong>2.</strong> Starten Sie den Test durch Auswahl der ersten Fallvignette.</p>
</div>
<p style="{P}"><strong>Sie möchten wissen, was Sie persönlich bevorzugen?</strong> Bewerten Sie 5 Fälle (ca. 5–10 Minuten), dann erscheint ein Pop-up-Fenster, das Ihnen zeigt, wie oft Sie bisher Antworten von menschlichen Beratungsfachkräften, einer trainierten KI oder einer Standard-KI bevorzugt haben. Anschließend werden weitere Fälle freigeschaltet. Nach jeder 5er-Etappe erhalten Sie eine neue Auswertung.</p>
<p style="{PS}">Jeder bewertete Fall ist für die Gesamttestung ein Gewinn! Fühlen Sie sich aber frei, so viele Fälle zu beantworten, wie Sie möchten. Sie können jederzeit pausieren und sich wieder einloggen.</p>
<p style="{PS}">Leiten Sie diese Mail gerne an andere Beratungsfachkräfte in Ihrem Umfeld weiter.</p>
<p style="{PS}">Bei Fragen erreichen Sie uns unter <a href="mailto:llars@e-beratungsinstitut.de" style="color:#3f7d6b;">llars@e-beratungsinstitut.de</a>.</p>
<p style="{P}">Vielen Dank!</p>
<p style="margin:0;font-size:15px;line-height:1.6;">Mit kollegialen Grüßen<br>Philipp Steigerwald<br>KI-Zentrum Bayern</p>
"""


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for _label, slug in ORGS:
        path = os.path.join(OUT, f"{slug}.html")
        with open(path, "w") as f:
            f.write(shell(inner(f"{BASE}/{slug}")))
        print("wrote", path)
    with open(os.path.join(OUT, "_SUBJECT.txt"), "w") as f:
        f.write("Kann KI Beratung?\n")


if __name__ == "__main__":
    main()
