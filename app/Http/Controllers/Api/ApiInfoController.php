<?php

namespace App\Http\Controllers\Api;

use Illuminate\Http\JsonResponse;

class ApiInfoController extends Controller
{
    /**
     * API info and version (public).
     */
    public function __invoke(): JsonResponse
    {
        return $this->success([
            'name' => config('app.name'),
            'version' => config('api.version'),
            'documentation' => url('/api'),
        ], 'OK');
    }
}
