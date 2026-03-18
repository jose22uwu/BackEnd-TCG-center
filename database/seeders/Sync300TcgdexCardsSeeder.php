<?php

namespace Database\Seeders;

use App\Services\TCGdexService;
use Illuminate\Database\Seeder;

class Sync300TcgdexCardsSeeder extends Seeder
{
    /**
     * Sync up to 300 cards from TCGdex (swsh1 + swsh2) with full data:
     * HP, attacks, types, weaknesses, resistances, abilities (sinergias).
     * Requires network and TCGdex API (set TCGDEX_SSL_VERIFY=false if SSL fails).
     */
    public function run(): void
    {
        $limit = (int) (env('TCGDEX_SYNC_LIMIT', 300));
        $tcgdex = app(TCGdexService::class);

        $this->command?->info("Syncing up to {$limit} cards from TCGdex (HP, attacks, sinergias)...");

        try {
            $result = $tcgdex->syncCardsLimit($limit);
        } catch (\Throwable $e) {
            $this->command?->warn('TCGdex sync failed: ' . $e->getMessage());
            $this->command?->warn('Set TCGDEX_SSL_VERIFY=false in .env if SSL verification fails.');

            return;
        }

        $this->command?->info("Synced: {$result['synced']}, Failed: {$result['failed']}");
        if (! empty($result['errors'])) {
            foreach (array_slice($result['errors'], 0, 10) as $err) {
                $this->command?->warn($err);
            }
            if (count($result['errors']) > 10) {
                $this->command?->warn('... and ' . (count($result['errors']) - 10) . ' more errors.');
            }
        }
    }
}
