<?php

declare(strict_types=1);

use Piwik\Access;
use Piwik\DbHelper;
use Piwik\FrontController;
use Piwik\Option;
use Piwik\SettingsPiwik;

if (!defined('PIWIK_DOCUMENT_ROOT')) {
    define('PIWIK_DOCUMENT_ROOT', '/var/www/html');
}

if (!defined('PIWIK_INCLUDE_PATH')) {
    define('PIWIK_INCLUDE_PATH', PIWIK_DOCUMENT_ROOT);
}

require_once PIWIK_INCLUDE_PATH . '/core/bootstrap.php';

if (!Piwik\Common::isPhpCliMode()) {
    fwrite(STDERR, "This configurator must be run in CLI mode.\n");
    exit(1);
}

Piwik\ErrorHandler::registerErrorHandler();
Piwik\ExceptionHandler::setUp();
FrontController::setUpSafeMode();

try {
    $environment = new Piwik\Application\Environment(null);
    $environment->init();

    if (!SettingsPiwik::isMatomoInstalled() || !DbHelper::isInstalled()) {
        fwrite(STDERR, "Matomo is not installed. Run the installer first.\n");
        exit(1);
    }

    $oidcEnabled = filter_var(getenv('MATOMO_OIDC_ENABLED') ?: 'false', FILTER_VALIDATE_BOOLEAN);
    if (!$oidcEnabled) {
        echo "[matomo-oidc] MATOMO_OIDC_ENABLED is false; skipping.\n";
        exit(0);
    }

    if (!class_exists(\Piwik\Plugins\RebelOIDC\SystemSettings::class)) {
        fwrite(STDERR, "RebelOIDC plugin not found. Install/activate it first.\n");
        exit(1);
    }

    $projectState = trim((string) (getenv('PROJECT_STATE') ?: 'development'));
    $projectUrl = trim((string) (getenv('PROJECT_URL') ?: ''));
    $projectHost = trim((string) (getenv('PROJECT_HOST') ?: 'localhost'));
    $nginxExternalPort = trim((string) (getenv('NGINX_EXTERNAL_PORT') ?: '80'));

    $baseUrl = rtrim($projectUrl, '/');
    if ($baseUrl === '') {
        if ($projectState === 'production') {
            $baseUrl = 'https://' . $projectHost;
        } else {
            $baseUrl = 'http://' . $projectHost . ':' . $nginxExternalPort;
        }
    }

    $authentikPublicUrl = trim((string) (getenv('AUTHENTIK_PUBLIC_URL') ?: ''));
    $authentikExternalBase = '';
    if ($authentikPublicUrl !== '') {
        $authentikExternalBase = rtrim($authentikPublicUrl, '/');
    } else {
        $authentikExternalPort = trim((string) (getenv('AUTHENTIK_EXTERNAL_PORT') ?: ''));
        $baseScheme = str_starts_with($baseUrl, 'https://') ? 'https' : 'http';

        // In development, Authentik is exposed on its own port by default (AUTHENTIK_EXTERNAL_PORT=55095).
        // Authentik is NOT reliably usable behind a subpath proxy (/authentik/) without additional proxy_redirect
        // and prefix handling, because it issues redirects to absolute paths like "/flows/...".
        if ($projectState !== 'production' && $authentikExternalPort !== '') {
            $authentikExternalBase = $baseScheme . '://' . $projectHost . ':' . $authentikExternalPort;
        } else {
            $authentikExternalBase = rtrim($baseUrl, '/') . '/authentik';
        }
    }
    $authentikInternalBase = rtrim((string) (getenv('AUTHENTIK_INTERNAL_URL') ?: 'http://authentik-server:9000'), '/');

    $clientId = trim((string) (getenv('AUTHENTIK_MATOMO_CLIENT_ID') ?: ''));
    $clientSecret = (string) (getenv('AUTHENTIK_MATOMO_CLIENT_SECRET') ?: '');
    $appSlug = trim((string) (getenv('AUTHENTIK_MATOMO_APP_SLUG') ?: ''));

    if ($clientId === '' || $clientSecret === '' || $appSlug === '') {
        fwrite(STDERR, "Missing Authentik Matomo OIDC env vars (AUTHENTIK_MATOMO_CLIENT_ID/_SECRET/_APP_SLUG).\n");
        exit(1);
    }

    $authorizeUrl = $authentikExternalBase . '/application/o/authorize/';
    $tokenUrl = $authentikInternalBase . '/application/o/token/';
    $userInfoUrl = $authentikInternalBase . '/application/o/userinfo/';
    $endSessionUrl = $authentikExternalBase . '/application/o/' . $appSlug . '/end-session/';

    $force = filter_var(getenv('MATOMO_OIDC_FORCE_CONFIG') ?: 'false', FILTER_VALIDATE_BOOLEAN);

    $configuredFlag = 'llars_matomo_rebeloidc_configured';
    $settings = new \Piwik\Plugins\RebelOIDC\SystemSettings();
    $alreadyConfigured = Option::get($configuredFlag) === '1';
    $alreadyMatches =
        trim((string) $settings->authorizeUrl->getValue()) === $authorizeUrl &&
        trim((string) $settings->tokenUrl->getValue()) === $tokenUrl &&
        trim((string) $settings->userInfoUrl->getValue()) === $userInfoUrl &&
        trim((string) $settings->endSessionUrl->getValue()) === $endSessionUrl &&
        trim((string) $settings->clientId->getValue()) === $clientId &&
        $settings->disableDirectLoginUrl->getValue() === false;

    if (!$force && $alreadyConfigured && $alreadyMatches) {
        echo "[matomo-oidc] RebelOIDC already configured; skipping.\n";
        exit(0);
    }

    Access::getInstance();
    Access::doAsSuperUser(static function () use (
        $settings,
        $authorizeUrl,
        $tokenUrl,
        $userInfoUrl,
        $endSessionUrl,
        $clientId,
        $clientSecret,
        $configuredFlag
    ): void {
        $settings->authenticationName->setValue('LLARS (SSO)');
        $settings->authorizeUrl->setValue($authorizeUrl);
        $settings->tokenUrl->setValue($tokenUrl);
        $settings->userInfoUrl->setValue($userInfoUrl);
        $settings->endSessionUrl->setValue($endSessionUrl);

        // Match Authentik to Matomo user login for auto-linking
        $settings->userInfoId->setValue('preferred_username');
        $settings->usernameAttribute->setValue('preferred_username');
        $settings->fallbackToEmail->setValue(true);

        $settings->clientId->setValue($clientId);
        $settings->clientSecret->setValue($clientSecret);
        $settings->scope->setValue('openid email profile');

        // Security defaults: only pre-existing Matomo users can log in via OIDC.
        $settings->allowSignup->setValue(false);
        $settings->autoLinking->setValue(true);

        // UX defaults
        $settings->bypassTwoFa->setValue(true);
        $settings->disablePasswordConfirmation->setValue(true);
        // Allow starting SSO via direct URL (GET) for deep-links from LLARS UI.
        // (Otherwise RebelOIDC only allows POST from Matomo login form)
        $settings->disableDirectLoginUrl->setValue(false);
        $settings->disableSuperuser->setValue(false);

        $settings->save();
        Option::set($configuredFlag, '1');
    });

    echo "[matomo-oidc] RebelOIDC configuration complete.\n";
    exit(0);
} catch (Throwable $e) {
    fwrite(STDERR, "[matomo-oidc] Failed: {$e->getMessage()}\n");
    exit(1);
}
