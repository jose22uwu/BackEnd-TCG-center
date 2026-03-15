<?php

return [

    /*
    |--------------------------------------------------------------------------
    | TCGdex API (https://tcgdex.dev)
    |--------------------------------------------------------------------------
    | Language for card data. Supported: en, fr, de, es, it, pt, etc.
    */

    'language' => env('TCGDEX_LANGUAGE', 'en'),

    /*
    | Set to false only in local dev if SSL certificate verification fails
    | (e.g. "unable to get local issuer certificate"). Prefer fixing PHP/cURL CA bundle.
    */
    'ssl_verify' => env('TCGDEX_SSL_VERIFY', true),

];
