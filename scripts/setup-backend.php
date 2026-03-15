#!/usr/bin/env php
<?php

/**
 * Backend setup from scratch: composer, .env, key, migrate, seed.
 * Run from project root: php scripts/setup-backend.php
 * Or: composer run setup-backend
 */

$projectRoot = dirname(__DIR__);
chdir($projectRoot);

$phpVersion = PHP_VERSION_ID;
if ($phpVersion < 80200) {
    fwrite(STDERR, "Error: PHP 8.2+ required (current: " . PHP_VERSION . ").\n");
    exit(1);
}

function run(string $command, string $step): bool
{
    echo "\n--- " . $step . " ---\n";
    passthru($command, $code);
    if ($code !== 0) {
        fwrite(STDERR, "\nSetup failed at: " . $step . " (exit code " . $code . ")\n");
        return false;
    }
    return true;
}

echo "Backend setup (project root: " . realpath($projectRoot) . ")\n";

if (!run('composer install --no-interaction', 'Composer install')) {
    exit(1);
}

$envPath = $projectRoot . DIRECTORY_SEPARATOR . '.env';
if (!file_exists($envPath)) {
    $example = $projectRoot . DIRECTORY_SEPARATOR . '.env.example';
    if (!file_exists($example)) {
        fwrite(STDERR, "Error: .env.example not found.\n");
        exit(1);
    }
    copy($example, $envPath);
    echo "\n--- Created .env from .env.example ---\n";
} else {
    echo "\n--- .env already exists (skipped copy) ---\n";
}

if (!run('php artisan key:generate --force', 'Application key')) {
    exit(1);
}

if (!run('php artisan migrate --seed --force', 'Migrations + seeders')) {
    fwrite(STDERR, "\nTip: If DB connection failed, set DB_* in .env and run again:\n  php artisan migrate --seed --force\n");
    exit(1);
}

run('php artisan config:clear', 'Config clear');
run('php artisan cache:clear', 'Cache clear');

if (file_exists($projectRoot . DIRECTORY_SEPARATOR . 'storage' . DIRECTORY_SEPARATOR . 'app' . DIRECTORY_SEPARATOR . 'public')) {
    @run('php artisan storage:link', 'Storage link (optional)');
}

echo "\n" . str_repeat('=', 60) . "\n";
echo "Setup finished. Backend is ready.\n\n";
echo "Next steps:\n";
echo "  1. Edit .env with your DB credentials (DB_DATABASE, DB_USERNAME, DB_PASSWORD) if needed.\n";
echo "  2. Start the API: php artisan serve\n";
echo "  3. (Optional) Start queue worker: php artisan queue:work\n\n";
echo "Test users (see docs/SEEDERS.md): seller, buyer, admin, seller2, buyer2 / password: password\n";
echo str_repeat('=', 60) . "\n";

exit(0);
