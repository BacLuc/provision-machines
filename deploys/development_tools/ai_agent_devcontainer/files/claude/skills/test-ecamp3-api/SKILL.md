---
name: test-ecamp3-api
description: Test the ecamp3 API - run PHPUnit tests, PHPStan static analysis, and PHP-CS-Fixer formatting checks against the ecamp3 backend.
---

# Testing the ecamp3 API

## Where the API lives

The ecamp3 API is in the `ecamp/ecamp3` repository under `api/`. It is a PHP/Symfony application built on API Platform, tested with PHPUnit.

- API Dockerfile: `api/Dockerfile`
- API config: `api/docker/`
- CI env vars: `.env.ci` at the repo root (USER_ID=1001, XDEBUG_MODE=off, APP_ENV=e2e); the GitHub Action copies it with `cp .env.ci .env`

## Run the tests

From the repo root:

```bash
docker compose run --rm api composer test
```

or directly:

```bash
docker compose run --rm api php vendor/bin/phpunit
```

NOTE: the PHPUnit binary is at `vendor/bin/phpunit` — NOT `php bin/phpunit`.

## PHPStan static analysis

```bash
docker compose run --rm api php vendor/bin/phpstan analyse
```

## PHP-CS-Fixer formatting check

```bash
docker compose run --rm api php vendor/bin/php-cs-fixer fix --dry-run --diff
```

NOTE: include the `vendor/bin/` prefix — the binary is not on the default PATH inside the container.

## Start the API and send requests

```bash
docker compose up -d
sh wait-for-container-startup.sh
curl http://localhost:3000/api
```

## Get an auth token

```bash
docker compose exec api bin/console lexik:jwt:generate-token test@example.com --no-debug
```

## Notes

- The default branch of `ecamp/ecamp3` is `devel`, not `main`

## When to use

This skill loads when developing or testing the ecamp3 API.