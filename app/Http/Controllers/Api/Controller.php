<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller as BaseController;
use Illuminate\Http\JsonResponse;

abstract class Controller extends BaseController
{
    /**
     * Success JSON response.
     *
     * @param  int  $encodingOptions  Optional flags for json_encode (e.g. JSON_INVALID_UTF8_SUBSTITUTE).
     */
    protected function success(mixed $data = null, string $message = 'OK', int $code = 200, int $encodingOptions = 0): JsonResponse
    {
        $body = [
            'success' => true,
            'message' => $message,
        ];

        if ($data !== null) {
            $body['data'] = $data;
        }

        return response()->json($body, $code, [], $encodingOptions);
    }

    /**
     * Error JSON response.
     */
    protected function error(string $message = 'Error', int $code = 400, mixed $errors = null): JsonResponse
    {
        $body = [
            'success' => false,
            'message' => $message,
        ];

        if ($errors !== null) {
            $body['errors'] = $errors;
        }

        return response()->json($body, $code);
    }
}
