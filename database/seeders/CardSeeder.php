<?php

namespace Database\Seeders;

use App\Models\Card;
use Illuminate\Database\Seeder;

class CardSeeder extends Seeder
{
    /**
     * Ensure demo cards exist (by api_identifier). Safe to run with existing cards (e.g. from TCGdex).
     */
    public function run(): void
    {
        $cards = [
            [
                'api_identifier' => 'swsh1-1',
                'name' => 'Venusaur',
                'image_url' => 'https://tcgdex.dev/assets/cards/swsh1-1',
                'category' => 'Pokemon',
                'illustrator' => 'Mitsuhiro Arita',
                'rarity' => 'Rare Holo',
                'set_identifier' => 'swsh1',
                'set_name' => 'Sword & Shield',
                'local_id' => '1',
            ],
            [
                'api_identifier' => 'swsh1-2',
                'name' => 'Charizard',
                'image_url' => 'https://tcgdex.dev/assets/cards/swsh1-2',
                'category' => 'Pokemon',
                'illustrator' => 'Mitsuhiro Arita',
                'rarity' => 'Rare Holo',
                'set_identifier' => 'swsh1',
                'set_name' => 'Sword & Shield',
                'local_id' => '2',
            ],
            [
                'api_identifier' => 'swsh1-3',
                'name' => 'Blastoise',
                'image_url' => 'https://tcgdex.dev/assets/cards/swsh1-3',
                'category' => 'Pokemon',
                'illustrator' => 'Mitsuhiro Arita',
                'rarity' => 'Rare Holo',
                'set_identifier' => 'swsh1',
                'set_name' => 'Sword & Shield',
                'local_id' => '3',
            ],
            [
                'api_identifier' => 'swsh1-4',
                'name' => 'Pikachu',
                'image_url' => 'https://tcgdex.dev/assets/cards/swsh1-4',
                'category' => 'Pokemon',
                'illustrator' => 'Akira Komayama',
                'rarity' => 'Common',
                'set_identifier' => 'swsh1',
                'set_name' => 'Sword & Shield',
                'local_id' => '4',
            ],
            [
                'api_identifier' => 'swsh1-5',
                'name' => 'Eevee',
                'image_url' => 'https://tcgdex.dev/assets/cards/swsh1-5',
                'category' => 'Pokemon',
                'illustrator' => 'Saya Tsuruta',
                'rarity' => 'Common',
                'set_identifier' => 'swsh1',
                'set_name' => 'Sword & Shield',
                'local_id' => '5',
            ],
            [
                'api_identifier' => 'swsh1-6',
                'name' => 'Professor\'s Research',
                'image_url' => 'https://tcgdex.dev/assets/cards/swsh1-6',
                'category' => 'Trainer',
                'illustrator' => 'Yusuke Ohmura',
                'rarity' => 'Uncommon',
                'set_identifier' => 'swsh1',
                'set_name' => 'Sword & Shield',
                'local_id' => '6',
            ],
            [
                'api_identifier' => 'swsh1-7',
                'name' => 'Boss\'s Orders',
                'image_url' => 'https://tcgdex.dev/assets/cards/swsh1-7',
                'category' => 'Trainer',
                'illustrator' => 'Hitoshi Ariga',
                'rarity' => 'Uncommon',
                'set_identifier' => 'swsh1',
                'set_name' => 'Sword & Shield',
                'local_id' => '7',
            ],
            [
                'api_identifier' => 'swsh1-8',
                'name' => 'Marnie',
                'image_url' => 'https://tcgdex.dev/assets/cards/swsh1-8',
                'category' => 'Trainer',
                'illustrator' => 'Ken Sugimori',
                'rarity' => 'Uncommon',
                'set_identifier' => 'swsh1',
                'set_name' => 'Sword & Shield',
                'local_id' => '8',
            ],
        ];

        foreach ($cards as $data) {
            Card::firstOrCreate(
                ['api_identifier' => $data['api_identifier']],
                $data
            );
        }
    }
}
