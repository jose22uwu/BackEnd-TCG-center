<?php

namespace App\Http\Controllers\Api;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Symfony\Component\Process\Exception\ProcessFailedException;
use Symfony\Component\Process\Process;

class AiChatController extends Controller
{
    /**
     * Chatbot analitico basado en cartas del usuario logueado.
     * Devuelve bloques estructurados: rules, strategy, collectionSummary, relevantCards.
     */
    public function __invoke(Request $request): JsonResponse
    {
        $user = $request->user();
        $validated = $request->validate([
            'question' => ['required', 'string', 'max:2000'],
        ]);

        $question = trim($validated['question']);
        if ($question === '') {
            return $this->error('Question cannot be empty.', 422);
        }

        $basePath = base_path();

        // On Windows use only Python (WSL from PHP triggers RPC 0x8007072c).
        if (PHP_OS_FAMILY === 'Windows') {
            $result = self::runChatViaWindowsPython($basePath, $user->id, $question);
            if ($result['out'] !== null && $result['out'] !== '') {
                return $this->buildResponseFromOutput($result['out'], $question);
            }
            return $this->error(
                'El asistente no pudo ejecutarse con Python en Windows.',
                500,
                ['error' => $result['error'] ?? 'Comprueba AI_PYTHON_PATH en .env y que el chatbot funcione en esa terminal.']
            );
        }

        // Linux (e.g. Docker): try AI_PYTHON_PATH or venv/python3 first.
        $result = self::runChatViaLinuxPython($basePath, $user->id, $question);
        if ($result['out'] !== null && $result['out'] !== '') {
            return $this->buildResponseFromOutput($result['out'], $question);
        }

        $windowsScriptPath = $basePath.\DIRECTORY_SEPARATOR.'ai model'.\DIRECTORY_SEPARATOR.'run_wsl_ai.sh';
        if (! is_file($windowsScriptPath)) {
            return $this->error('AI backend script not found.', 500);
        }

        $wslScriptPath = self::windowsPathToWsl($windowsScriptPath);
        $pathEscaped = str_replace("'", "'\\''", $wslScriptPath);
        $questionEscaped = str_replace("'", "'\\''", $question);
        $bashCommand = sprintf(
            "'%s' chat --user-id %d --question '%s' --format json",
            $pathEscaped,
            $user->id,
            $questionEscaped,
        );

        $process = new Process(
            ['wsl', '-d', 'Ubuntu', '--', 'bash', '-c', $bashCommand],
            $basePath,
            null,
            null,
            60
        );

        try {
            $process->mustRun();
            return $this->buildResponseFromOutput(trim($process->getOutput()), $question);
        } catch (ProcessFailedException $e) {
            $exitCode = $e->getProcess()->getExitCode();
            $output = $e->getProcess()->getOutput();
            if ($exitCode === -1 && str_contains($output, '0x8007072c')) {
                $result = self::runChatViaWindowsPython($basePath, $user->id, $question);
                if ($result['out'] !== null && $result['out'] !== '') {
                    return $this->buildResponseFromOutput($result['out'], $question);
                }
                return $this->error(
                    'WSL failed with RPC error (0x8007072c). Fallback a Python en Windows falló.',
                    500,
                    ['error' => $result['error'] ?? self::ensureUtf8($e->getMessage())]
                );
            }

            return $this->error('AI process failed.', 500, [
                'error' => self::ensureUtf8($e->getMessage()),
            ]);
        }
    }

    /**
     * Run chatbot via Linux Python (e.g. Docker). Returns ['out' => string|null, 'error' => string|null].
     */
    private static function runChatViaLinuxPython(string $basePath, int $userId, string $question): array
    {
        $scriptPath = $basePath.\DIRECTORY_SEPARATOR.'ai model'.\DIRECTORY_SEPARATOR.'chatbot.py';
        if (! is_file($scriptPath)) {
            return ['out' => null, 'error' => 'No se encuentra chatbot.py en ai model/'];
        }

        $env = self::envForPythonProcess();
        $aiModelDir = $basePath.\DIRECTORY_SEPARATOR.'ai model';

        $candidates = [
            $aiModelDir.\DIRECTORY_SEPARATOR.'.venv-wsl'.\DIRECTORY_SEPARATOR.'bin'.\DIRECTORY_SEPARATOR.'python3',
            $aiModelDir.\DIRECTORY_SEPARATOR.'.venv'.\DIRECTORY_SEPARATOR.'bin'.\DIRECTORY_SEPARATOR.'python3',
        ];
        $pythonPath = trim((string) (config('ai.python_path') ?? env('AI_PYTHON_PATH') ?? ''));
        if ($pythonPath !== '') {
            $candidates = array_merge([$pythonPath], $candidates);
        }
        $candidates[] = 'python3';

        foreach ($candidates as $python) {
            if ($python === 'python3' || (is_file($python) && is_executable($python))) {
                $process = new Process(
                    $python === 'python3'
                        ? ['python3', $scriptPath, '--user-id', (string) $userId, '--question', $question, '--format', 'json']
                        : [$python, $scriptPath, '--user-id', (string) $userId, '--question', $question, '--format', 'json'],
                    $basePath,
                    $env,
                    null,
                    60
                );
                try {
                    $process->mustRun();
                    return ['out' => trim($process->getOutput()), 'error' => null];
                } catch (\Throwable $e) {
                    $stderr = $process->getErrorOutput();
                    $err = $e->getMessage();
                    if ($stderr !== '') {
                        $err .= "\nStderr: ".self::ensureUtf8($stderr);
                    }
                    if ($python !== 'python3') {
                        continue;
                    }
                    return ['out' => null, 'error' => $err];
                }
            }
        }

        return ['out' => null, 'error' => 'AI_PYTHON_PATH no definida y no se encontró venv/python3 en ai model/.'];
    }

    /**
     * Run chatbot via Windows Python. Returns ['out' => string|null, 'error' => string|null].
     */
    private static function runChatViaWindowsPython(string $basePath, int $userId, string $question): array
    {
        $scriptPath = $basePath.\DIRECTORY_SEPARATOR.'ai model'.\DIRECTORY_SEPARATOR.'chatbot.py';
        if (! is_file($scriptPath)) {
            return ['out' => null, 'error' => 'No se encuentra chatbot.py en ai model/'];
        }

        $env = self::envForPythonProcess();
        $aiModelDir = $basePath.\DIRECTORY_SEPARATOR.'ai model';
        $venvPython = $aiModelDir.\DIRECTORY_SEPARATOR.'.venv-windows'.\DIRECTORY_SEPARATOR.'Scripts'.\DIRECTORY_SEPARATOR.'python.exe';
        if (file_exists($venvPython)) {
            $process = new Process(
                [$venvPython, $scriptPath, '--user-id', (string) $userId, '--question', $question, '--format', 'json'],
                $basePath,
                $env,
                null,
                60
            );
            try {
                $process->mustRun();
                return ['out' => trim($process->getOutput()), 'error' => null];
            } catch (\Throwable $e) {
                $stderr = $process->getErrorOutput();
                $msg = $e->getMessage();
                if ($stderr !== '') {
                    $msg .= "\nStderr: ".self::ensureUtf8($stderr);
                }
                return ['out' => null, 'error' => $msg];
            }
        }

        $pythonPath = trim((string) (config('ai.python_path') ?? env('AI_PYTHON_PATH') ?? ''));
        if ($pythonPath !== '') {
            $process = new Process(
                [$pythonPath, $scriptPath, '--user-id', (string) $userId, '--question', $question, '--format', 'json'],
                $basePath,
                $env,
                null,
                60
            );
            try {
                $process->mustRun();
                return ['out' => trim($process->getOutput()), 'error' => null];
            } catch (\Throwable $e) {
                $stderr = $process->getErrorOutput();
                $msg = $e->getMessage();
                if ($stderr !== '') {
                    $msg .= "\nStderr: ".self::ensureUtf8($stderr);
                }
                return ['out' => null, 'error' => $msg];
            }
        }

        $discovered = self::discoverWindowsPythonPath();
        if ($discovered !== null) {
            $process = new Process(
                [$discovered, $scriptPath, '--user-id', (string) $userId, '--question', $question, '--format', 'json'],
                $basePath,
                $env,
                null,
                60
            );
            try {
                $process->mustRun();
                return ['out' => trim($process->getOutput()), 'error' => null];
            } catch (\Throwable $e) {
                return ['out' => null, 'error' => $e->getMessage()];
            }
        }

        $scriptPathQuoted = '"'.str_replace('"', '""', $scriptPath).'"';
        $questionEscaped = '"'.str_replace(['\\', '"'], ['\\\\', '""'], $question).'"';

        foreach (['python', 'py -3'] as $pythonExe) {
            $command = $pythonExe.' '.$scriptPathQuoted.' --user-id '.(string) $userId.' --question '.$questionEscaped.' --format json';
            $process = Process::fromShellCommandline($command, $basePath, $env, null, 60);
            try {
                $process->mustRun();
                return ['out' => trim($process->getOutput()), 'error' => null];
            } catch (\Throwable $e) {
                continue;
            }
        }

        return ['out' => null, 'error' => 'AI_PYTHON_PATH no definida en .env y no se encontró python en PATH.'];
    }

    /**
     * Environment for the Python chatbot process: parent env plus DB_* from Laravel config.
     * Ensures the child process can connect to MySQL (avoids socket 10106 when env is not inherited).
     */
    private static function envForPythonProcess(): array
    {
        $env = getenv() ?: [];
        if (! is_array($env)) {
            $env = [];
        }
        $cfg = config('database.connections.mysql', []);
        $env['DB_HOST'] = (string) ($cfg['host'] ?? '127.0.0.1');
        $env['DB_PORT'] = (string) ($cfg['port'] ?? '3306');
        $env['DB_DATABASE'] = (string) ($cfg['database'] ?? '');
        $env['DB_USERNAME'] = (string) ($cfg['username'] ?? '');
        $env['DB_PASSWORD'] = (string) ($cfg['password'] ?? '');

        return $env;
    }

    /**
     * On Windows, run "where python" and return first path that exists and is not the WindowsApps stub.
     */
    private static function discoverWindowsPythonPath(): ?string
    {
        if (PHP_OS_FAMILY !== 'Windows') {
            return null;
        }
        try {
            $p = new Process(['cmd', '/c', 'where', 'python'], null, null, null, 5);
            $p->run();
            $out = trim($p->getOutput());
            if ($out === '') {
                return null;
            }
            foreach (explode("\n", $out) as $line) {
                $line = trim($line);
                if ($line === '' || str_contains(strtolower($line), 'windowsapps')) {
                    continue;
                }
                if (file_exists($line)) {
                    return $line;
                }
            }
        } catch (\Throwable) {
            return null;
        }
        return null;
    }

    /**
     * Decode script output and return JSON response (shared by WSL and Windows paths).
     */
    private function buildResponseFromOutput(string $output, string $question): JsonResponse
    {
        $output = self::ensureUtf8($output);
        $decoded = json_decode($output, true);

        if (! is_array($decoded)) {
            $fallbackPayload = self::sanitizePayload([
                'raw' => $output,
                'error' => null,
                'user' => null,
                'question' => $question,
                'intent' => null,
                'rules' => [],
                'scenarioConclusions' => [],
                'collectionSummary' => null,
                'recommendations' => [],
                'relevantCards' => [],
                'similarCards' => [],
                'recommendedCatalogCards' => [],
                'unrecognizedHint' => null,
                'helpMessage' => null,
                'embeddingsAvailable' => false,
            ]);

            return $this->success($fallbackPayload, 'OK', 200, \JSON_INVALID_UTF8_SUBSTITUTE);
        }

        $payload = self::sanitizePayload([
            'error' => $decoded['error'] ?? null,
            'user' => $decoded['user'] ?? null,
            'question' => $decoded['question'] ?? $question,
            'intent' => $decoded['intent'] ?? null,
            'rules' => $decoded['rules'] ?? [],
            'scenarioConclusions' => $decoded['scenarioConclusions'] ?? [],
            'collectionSummary' => $decoded['collectionSummary'] ?? null,
            'recommendations' => $decoded['recommendations'] ?? [],
            'relevantCards' => $decoded['relevantCards'] ?? [],
            'similarCards' => $decoded['similarCards'] ?? [],
            'recommendedCatalogCards' => $decoded['recommendedCatalogCards'] ?? [],
            'unrecognizedHint' => $decoded['unrecognizedHint'] ?? null,
            'helpMessage' => $decoded['helpMessage'] ?? null,
            'conclusion' => $decoded['conclusion'] ?? null,
            'embeddingsAvailable' => $decoded['embeddingsAvailable'] ?? false,
        ]);

        if (! empty($decoded['error'])) {
            return $this->success($payload, self::ensureUtf8((string) $decoded['error']), 200, \JSON_INVALID_UTF8_SUBSTITUTE);
        }

        return $this->success($payload, 'OK', 200, \JSON_INVALID_UTF8_SUBSTITUTE);
    }

    /**
     * Convert a Windows path to WSL (e.g. E:\foo\bar -> /mnt/e/foo/bar).
     * Avoids calling wslpath inside the bash command, which can trigger WSL RPC errors.
     */
    private static function windowsPathToWsl(string $windowsPath): string
    {
        $normalized = str_replace('\\', '/', $windowsPath);
        if (preg_match('/^([A-Za-z]):\/?(.*)$/', $normalized, $m)) {
            return '/mnt/'.strtolower($m[1]).'/'.ltrim($m[2], '/');
        }

        return $normalized;
    }

    /**
     * Ensure a string is valid UTF-8 so json_encode does not throw.
     * Converts from Windows/console encodings when capturing WSL subprocess output on Windows.
     */
    private static function ensureUtf8(string $value): string
    {
        if ($value === '') {
            return $value;
        }
        if (mb_check_encoding($value, 'UTF-8')) {
            return $value;
        }
        $encodings = ['Windows-1252', 'ISO-8859-1', 'CP850'];
        foreach ($encodings as $from) {
            $converted = @mb_convert_encoding($value, 'UTF-8', $from);
            if ($converted !== false && mb_check_encoding($converted, 'UTF-8')) {
                return $converted;
            }
        }
        $cleaned = @iconv('UTF-8', 'UTF-8//IGNORE', $value);
        return $cleaned !== false ? $cleaned : $value;
    }

    /**
     * Recursively sanitize payload: all string values and string keys to valid UTF-8.
     */
    private static function sanitizePayload(mixed $payload): mixed
    {
        if (is_string($payload)) {
            return self::ensureUtf8($payload);
        }
        if (is_array($payload)) {
            $out = [];
            foreach ($payload as $k => $v) {
                $safeKey = is_string($k) ? self::ensureUtf8($k) : $k;
                $out[$safeKey] = self::sanitizePayload($v);
            }
            return $out;
        }
        if (is_object($payload)) {
            $out = new \stdClass;
            foreach ((array) $payload as $k => $v) {
                $safeKey = is_string($k) ? self::ensureUtf8($k) : $k;
                $out->{$safeKey} = self::sanitizePayload($v);
            }
            return $out;
        }
        return $payload;
    }
}

