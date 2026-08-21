<?php

declare(strict_types=1);

/**
 * Aktiviert das LLARS-Branding (Custom-Logo) in Matomo.
 *
 * Matomo zeigt ein eigenes Logo nur, wenn die Option `branding_use_custom_logo`
 * gesetzt ist UND die Logo-Dateien unter misc/user/ liegen (das Kopieren
 * erledigt init-matomo.sh). Dieses Skript setzt die Option idempotent.
 *
 * Bewusst NICHT-fatal: Branding ist kosmetisch und darf den Matomo-Init nie
 * abbrechen — bei jedem Fehler wird mit Exit-Code 0 beendet.
 */

use Piwik\Option;

if (!defined('PIWIK_DOCUMENT_ROOT')) {
    define('PIWIK_DOCUMENT_ROOT', '/var/www/html');
}
if (!defined('PIWIK_INCLUDE_PATH')) {
    define('PIWIK_INCLUDE_PATH', PIWIK_DOCUMENT_ROOT);
}

require_once PIWIK_INCLUDE_PATH . '/core/bootstrap.php';

if (!Piwik\Common::isPhpCliMode()) {
    fwrite(STDERR, "[matomo-branding] Must run in CLI mode.\n");
    exit(0);
}

Piwik\ErrorHandler::registerErrorHandler();
Piwik\ExceptionHandler::setUp();

try {
    $environment = new Piwik\Application\Environment(null);
    $environment->init();

    if (!Piwik\SettingsPiwik::isMatomoInstalled() || !Piwik\DbHelper::isInstalled()) {
        fwrite(STDERR, "[matomo-branding] Matomo not installed yet; skipping.\n");
        exit(0);
    }

    // '1' aktiviert das Custom-Logo (Matomo liest misc/user/logo*.png|svg).
    Option::set('branding_use_custom_logo', '1');

    echo "[matomo-branding] LLARS custom logo enabled (branding_use_custom_logo=1).\n";
    exit(0);
} catch (\Throwable $e) {
    fwrite(STDERR, "[matomo-branding] Non-fatal: " . $e->getMessage() . "\n");
    exit(0);
}
