<?php

return [
    /*
    |--------------------------------------------------------------------------
    | Python executable path (Windows)
    |--------------------------------------------------------------------------
    | When set, the AI chat uses this path to run the chatbot instead of
    | relying on PATH. Use when "php artisan serve" or the web server
    | does not inherit a PATH that includes python (e.g. new terminal).
    | Example: C:\Users\You\AppData\Local\Programs\Python\Python312\python.exe
    | Get it by running "where python" in a terminal where python works.
    */
    'python_path' => env('AI_PYTHON_PATH'),
];
