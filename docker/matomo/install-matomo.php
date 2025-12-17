<?php

declare(strict_types=1);

use Piwik\Access;
use Piwik\Config;
use Piwik\DbHelper;
use Piwik\FrontController;
use Piwik\SettingsPiwik;
use Piwik\Updater;
use Piwik\Version;
use Piwik\Plugins\SitesManager\API as APISitesManager;
use Piwik\Plugins\UsersManager\API as APIUsersManager;

if (!defined('PIWIK_DOCUMENT_ROOT')) {
    define('PIWIK_DOCUMENT_ROOT', '/var/www/html');
}

if (!defined('PIWIK_INCLUDE_PATH')) {
    define('PIWIK_INCLUDE_PATH', PIWIK_DOCUMENT_ROOT);
}

require_once PIWIK_INCLUDE_PATH . '/core/bootstrap.php';

if (!Piwik\Common::isPhpCliMode()) {
    fwrite(STDERR, "This installer must be run in CLI mode.\n");
    exit(1);
}

Piwik\ErrorHandler::registerErrorHandler();
Piwik\ExceptionHandler::setUp();
FrontController::setUpSafeMode();

$superUserLogin = getenv('MATOMO_SUPERUSER_LOGIN') ?: 'matomo-admin';
$superUserPassword = getenv('MATOMO_SUPERUSER_PASSWORD') ?: '';
$superUserEmail = getenv('MATOMO_SUPERUSER_EMAIL') ?: 'admin@example.com';

$siteName = getenv('MATOMO_SITE_NAME') ?: 'LLARS';
$siteUrl = getenv('MATOMO_SITE_URL') ?: '';

if ($superUserPassword === '') {
    fwrite(STDERR, "MATOMO_SUPERUSER_PASSWORD is required.\n");
    exit(1);
}

if ($siteUrl === '') {
    fwrite(STDERR, "MATOMO_SITE_URL is required.\n");
    exit(1);
}

try {
    echo "[matomo-install] Starting...\n";

    echo "[matomo-install] Initializing Matomo environment...\n";
    $environment = new Piwik\Application\Environment(null);
    $environment->init();

    $alreadyInstalled = SettingsPiwik::isMatomoInstalled() && DbHelper::isInstalled();
    if ($alreadyInstalled) {
        echo "[matomo-install] Matomo is already installed; ensuring config/users/sites...\n";
    }

    echo "[matomo-install] Checking existing tables...\n";
    $tablesInstalled = DbHelper::getTablesInstalled();
    if (count($tablesInstalled) === 0) {
        echo "Creating Matomo tables...\n";
        DbHelper::createTables();
        DbHelper::createAnonymousUser();
        DbHelper::recordInstallVersion();
    } else {
        echo "Matomo tables already exist (" . count($tablesInstalled) . ").\n";
    }

    echo "[matomo-install] Loading activated plugins...\n";
    \Piwik\Plugin\Manager::getInstance()->loadActivatedPlugins();

    // Ensure plugin install hooks run (creates plugin tables like custom_dimensions)
    Access::getInstance();
    \Piwik\Plugin\Manager::getInstance()->installLoadedPlugins();

    echo "[matomo-install] Running updater...\n";
    $updater = new Updater();
    $componentsWithUpdateFile = $updater->getComponentUpdates();
    if (!empty($componentsWithUpdateFile)) {
        Access::getInstance();
        Access::doAsSuperUser(static function () use ($updater, $componentsWithUpdateFile): void {
            $updater->updateComponents($componentsWithUpdateFile);
        });
    }

    Updater::recordComponentSuccessfullyUpdated('core', Version::VERSION);

    echo "[matomo-install] Ensuring superuser exists...\n";
    Access::doAsSuperUser(static function () use ($superUserLogin, $superUserPassword, $superUserEmail): void {
        $api = APIUsersManager::getInstance();

        $userExists = false;
        try {
            $userExists = (bool) $api->userExists($superUserLogin);
        } catch (Throwable) {
            $userExists = false;
        }

        if (!$userExists) {
            echo "Creating Matomo superuser '{$superUserLogin}'...\n";
            try {
                $api->addUser($superUserLogin, $superUserPassword, $superUserEmail);
            } catch (Throwable $e) {
                $message = $e->getMessage();
                $emailAlreadyExists =
                    str_contains($message, 'UsersManager_ExceptionEmailExists') ||
                    str_contains($message, 'ExceptionEmailExists');

                if (!$emailAlreadyExists) {
                    throw $e;
                }

                $fallbackEmail = $superUserLogin . '+matomo@example.com';
                if (str_contains($superUserEmail, '@')) {
                    [$local, $domain] = explode('@', $superUserEmail, 2);
                    if ($domain !== '') {
                        $fallbackEmail = $local . '+' . $superUserLogin . '@' . $domain;
                    }
                }

                fwrite(
                    STDERR,
                    "[matomo-install] Warning: email '{$superUserEmail}' already exists; retrying with '{$fallbackEmail}'.\n"
                );
                $api->addUser($superUserLogin, $superUserPassword, $fallbackEmail);
            }
        } else {
            echo "User '{$superUserLogin}' already exists. Ensuring password/email...\n";
            try {
                APIUsersManager::$UPDATE_USER_REQUIRE_PASSWORD_CONFIRMATION = false;
                $api->updateUser($superUserLogin, $superUserPassword, $superUserEmail, false, false);
            } catch (Throwable $e) {
                fwrite(
                    STDERR,
                    "[matomo-install] Warning: could not update user '{$superUserLogin}': {$e->getMessage()}\n"
                );
            }
        }

        $api->setSuperUserAccess($superUserLogin, true);
    });

    echo "[matomo-install] Ensuring site exists...\n";
    $siteIds = Access::doAsSuperUser(static function () {
        return APISitesManager::getInstance()->getAllSitesId();
    });

    if (empty($siteIds)) {
        echo "Creating Matomo site '{$siteName}' ({$siteUrl})...\n";
        $siteId = Access::doAsSuperUser(static function () use ($siteName, $siteUrl): int {
            return (int) APISitesManager::getInstance()->addSite($siteName, $siteUrl, 0);
        });
        echo "Created site idSite={$siteId}\n";
    } else {
        echo "Site already exists (first idSite=" . (int) $siteIds[0] . "). Skipping.\n";
    }

    $config = Config::getInstance();
    unset($config->General['installation_in_progress']);
    unset($config->General['installation_first_accessed']);
    $config->General['enable_installer'] = 0;
    $config->forceSave();

    echo "Matomo installation complete.\n";
    exit(0);
} catch (Throwable $e) {
    fwrite(STDERR, "Matomo installation failed: {$e->getMessage()}\n");
    exit(1);
}
