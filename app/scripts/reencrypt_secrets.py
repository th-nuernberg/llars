"""
Re-Encrypt gespeicherter Secrets nach einer Encryption-Key-Rotation (C1/C2).

Hintergrund (Pentest 2026-06-10): LLM_PROVIDER_ENCRYPTION_KEY war in Prod der
öffentlich bekannte Dev-Default → alle gespeicherten Provider-API-Keys faktisch
im Klartext. Dieses Skript verschlüsselt sie mit dem neuen Key neu.

Sicheres, zero-downtime Vorgehen (Dual-Key):

  1. Dual-Key-Code deployen (secret_encryption mit Fallback).
  2. In /var/llars/.env setzen:
       LLM_PROVIDER_ENCRYPTION_KEY=<NEU>
       LLM_PROVIDER_ENCRYPTION_KEY_FALLBACK=dev-secret-key-change-in-production
     und die App recreaten (lädt neue Env). Ab jetzt: neu schreiben = NEU,
     lesen = NEU oder ALT (Fallback) → nichts bricht.
  3. Dieses Skript laufen lassen (liest ALT via Fallback, schreibt NEU):
       docker exec llars_flask_<color> python /app/scripts/reencrypt_secrets.py --dry-run
       docker exec llars_flask_<color> python /app/scripts/reencrypt_secrets.py
  4. Nach sauberem Lauf die *_FALLBACK-Env-Variablen entfernen und App recreaten.
     Danach ist der alte (öffentliche) Key endgültig wertlos.

Idempotent: bereits auf den neuen Key migrierte Zeilen werden via primärem Key
gelesen und identisch zurückgeschrieben. Pro-Zeilen-Fehler werden geloggt und
übersprungen (ein korruptes Chiffrat bricht nicht die ganze Migration ab).
"""

import sys


def _reencrypt_column(rows, attr, decrypt_fn, encrypt_fn, label, dry_run):
    """Decrypt+re-encrypt one Fernet column over a set of ORM rows."""
    migrated = skipped = empty = 0
    for row in rows:
        stored = getattr(row, attr, None)
        if not stored:
            empty += 1
            continue
        try:
            plaintext = decrypt_fn(stored)
        except Exception as exc:  # noqa: BLE001 - log + skip, never abort the batch
            skipped += 1
            print(f"  [SKIP] {label} id={getattr(row, 'id', '?')}: decrypt failed: {exc}")
            continue
        new_cipher = encrypt_fn(plaintext)
        if not dry_run:
            setattr(row, attr, new_cipher)
        migrated += 1
    print(f"  {label}: {migrated} re-encrypted, {empty} empty, {skipped} skipped")
    return migrated


def main(dry_run: bool) -> int:
    from main import app
    with app.app_context():
        from db.database import db
        from db.models.llm_provider import LLMProvider
        from db.models.user_llm_provider import UserLLMProvider
        from services.llm.secret_encryption import (
            encrypt_api_key as llm_encrypt, decrypt_api_key as llm_decrypt,
        )

        print(f"=== Re-Encrypt secrets {'(DRY-RUN)' if dry_run else '(LIVE)'} ===")
        total = 0
        total += _reencrypt_column(
            LLMProvider.query.all(), "api_key_encrypted",
            llm_decrypt, llm_encrypt, "llm_providers", dry_run)
        total += _reencrypt_column(
            UserLLMProvider.query.all(), "api_key_encrypted",
            llm_decrypt, llm_encrypt, "user_llm_providers", dry_run)

        if dry_run:
            db.session.rollback()
            print(f"DRY-RUN complete — {total} rows would be re-encrypted. No changes written.")
        else:
            db.session.commit()
            print(f"DONE — {total} rows re-encrypted and committed.")
        print("Hinweis: Tavily-Keys in chatbot-config (enc:v1:) re-encrypten sich "
              "beim nächsten Speichern selbst (Lesen via Fallback bleibt gültig).")
    return 0


if __name__ == "__main__":
    sys.exit(main(dry_run="--dry-run" in sys.argv))
