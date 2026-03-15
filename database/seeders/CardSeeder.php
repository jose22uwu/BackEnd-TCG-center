<?php

namespace Database\Seeders;

use App\Models\Card;
use App\Services\TCGdexService;
use Illuminate\Database\Seeder;

class CardSeeder extends Seeder
{
    /**
     * api_identifiers for the 8 demo cards (Sword & Shield base). Used for carousel.
     */
    private const DEMO_API_IDS = [
        'swsh1-1', 'swsh1-2', 'swsh1-3', 'swsh1-4',
        'swsh1-5', 'swsh1-6', 'swsh1-7', 'swsh1-8',
    ];

    /**
     * Extra cards for test users: Holo Rare V and Holo Rare VMAX.
     */
    private const RARE_FOR_USERS = ['swsh1-49', 'swsh1-50'];

    /**
     * Ensure demo cards exist (by api_identifier). Prefer TCGdex API so name and image match; fallback to static data.
     */
    public function run(): void
    {
        $tcgdex = app(TCGdexService::class);

        foreach (self::DEMO_API_IDS as $apiId) {
            try {
                $synced = $tcgdex->fetchAndSyncCard($apiId);
                if ($synced !== null) {
                    continue;
                }
            } catch (\Throwable $e) {
                // SSL, network or API errors: use static fallback so seed still runs
                $this->command?->warn("TCGdex failed for {$apiId}: " . $e->getMessage());
            }

            $this->createFallbackCard($apiId);
        }

        foreach (self::RARE_FOR_USERS as $apiId) {
            try {
                $synced = $tcgdex->fetchAndSyncCard($apiId);
                if ($synced !== null) {
                    continue;
                }
            } catch (\Throwable $e) {
                $this->command?->warn("TCGdex failed for {$apiId}: " . $e->getMessage());
            }

            $this->createFallbackCard($apiId);
        }
    }

    /**
     * Fallback when TCGdex is unavailable (SSL, network). Uses a snapshot of real TCGdex data
     * so name, image_url and rarity always match the same card.
     */
    private function createFallbackCard(string $apiId): void
    {
        $base = 'https://assets.tcgdex.net/en/swsh/swsh1';
        $fallbacks = [
            'swsh1-1' => ['name' => 'Celebi V', 'category' => 'Pokemon', 'rarity' => 'Holo Rare V', 'illustrator' => 'PLANETA Igarashi', 'local_id' => '1'],
            'swsh1-2' => ['name' => 'Roselia', 'category' => 'Pokemon', 'rarity' => 'Common', 'illustrator' => 'sowsow', 'local_id' => '2'],
            'swsh1-3' => ['name' => 'Roselia', 'category' => 'Pokemon', 'rarity' => 'Common', 'illustrator' => 'Naoyo Kimura', 'local_id' => '3'],
            'swsh1-4' => ['name' => 'Roserade', 'category' => 'Pokemon', 'rarity' => 'Rare', 'illustrator' => 'chibi', 'local_id' => '4'],
            'swsh1-5' => ['name' => 'Cottonee', 'category' => 'Pokemon', 'rarity' => 'Common', 'illustrator' => 'ryoma uratsuka', 'local_id' => '5'],
            'swsh1-6' => ['name' => 'Whimsicott', 'category' => 'Pokemon', 'rarity' => 'Rare', 'illustrator' => 'kodama', 'local_id' => '6'],
            'swsh1-7' => ['name' => 'Maractus', 'category' => 'Pokemon', 'rarity' => 'Common', 'illustrator' => 'Atsuko Nishida', 'local_id' => '7'],
            'swsh1-8' => ['name' => 'Durant', 'category' => 'Pokemon', 'rarity' => 'Rare', 'illustrator' => 'Miki Tanaka', 'local_id' => '8'],
            'swsh1-49' => ['name' => 'Lapras V', 'category' => 'Pokemon', 'rarity' => 'Holo Rare V', 'illustrator' => 'Hasuno', 'local_id' => '49'],
            'swsh1-50' => ['name' => 'Lapras VMAX', 'category' => 'Pokemon', 'rarity' => 'Holo Rare VMAX', 'illustrator' => '5ban Graphics', 'local_id' => '50'],
        ];
        $meta = $fallbacks[$apiId] ?? ['name' => $apiId, 'category' => 'Pokemon', 'rarity' => null, 'illustrator' => null, 'local_id' => substr($apiId, strrpos($apiId, '-') + 1)];

        Card::updateOrCreate(
            ['api_identifier' => $apiId],
            [
                'name' => $meta['name'],
                'image_url' => "{$base}/{$meta['local_id']}",
                'category' => $meta['category'],
                'illustrator' => $meta['illustrator'],
                'rarity' => $meta['rarity'],
                'set_identifier' => 'swsh1',
                'set_name' => 'Sword & Shield',
                'local_id' => $meta['local_id'],
            ]
        );
    }
}
