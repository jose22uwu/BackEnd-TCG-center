<?php

return [

    /*
    |--------------------------------------------------------------------------
    | API version / prefix
    |--------------------------------------------------------------------------
    |
    | Used for response headers or versioning. Routes are already prefixed
    | with "api" in bootstrap/app.php.
    |
    */

    'version' => env('API_VERSION', '1'),

    /*
    |--------------------------------------------------------------------------
    | Throttle
    |--------------------------------------------------------------------------
    |
    | Default: 60 requests per minute per user/IP for API routes.
    | Format: 'max_attempts,decay_minutes'
    |
    */

    'throttle' => env('API_THROTTLE', '60,1'),

];
