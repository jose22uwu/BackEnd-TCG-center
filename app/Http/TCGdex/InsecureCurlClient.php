<?php

namespace App\Http\TCGdex;

use Buzz\Client\Curl;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;

/**
 * Buzz Curl client that disables SSL verification when required (e.g. local dev without CA bundle).
 * Use only when TCGDEX_SSL_VERIFY=false in .env.
 */
class InsecureCurlClient extends Curl
{
    public function sendRequest(RequestInterface $request, array $options = []): ResponseInterface
    {
        $options['curl'] = ($options['curl'] ?? []) + [
            \CURLOPT_SSL_VERIFYPEER => 0,
        ];

        return parent::sendRequest($request, $options);
    }
}
