# Backend API (Laravel). PHP 8.2+ (composer.json).
FROM php:8.4-cli

RUN apt-get update && apt-get install -y --no-install-recommends \
    git unzip libzip-dev libcurl4-openssl-dev libonig-dev libxml2-dev \
    python3 python3-pip python3-venv \
    && docker-php-ext-install pdo_mysql mbstring xml curl zip bcmath \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /app

COPY composer.json composer.lock ./
RUN composer install --no-dev --no-scripts --no-autoloader --prefer-dist

COPY . .
RUN composer dump-autoload --optimize

# AI chatbot: venv and minimal runtime deps (no tensorflow).
RUN python3 -m venv "/app/ai model/.venv" \
    && "/app/ai model/.venv/bin/pip" install --no-cache-dir -r "/app/ai model/requirements-docker.txt"

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]

EXPOSE 8000
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8000"]
