<?php

namespace App\Providers;

use App\Http\TCGdex\InsecureCurlClient;
use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\ServiceProvider;
use Nyholm\Psr7\Factory\Psr17Factory;
use TCGdex\TCGdex;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        if (config('tcgdex.ssl_verify', true) === false) {
            $factory = new Psr17Factory();
            TCGdex::$requestFactory = $factory;
            TCGdex::$responseFactory = $factory;
            TCGdex::$client = new InsecureCurlClient($factory);
        }
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        $throttle = config('api.throttle', '60,1');
        [$maxAttempts, $decayMinutes] = array_map('intval', explode(',', $throttle)) + [1 => 1];

        RateLimiter::for('api', function ($request) use ($maxAttempts, $decayMinutes) {
            return Limit::perMinutes($decayMinutes, $maxAttempts)
                ->by($request->user()?->id ?: $request->ip());
        });
    }
}
