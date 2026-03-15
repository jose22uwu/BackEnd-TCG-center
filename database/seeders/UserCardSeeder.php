<?php

namespace Database\Seeders;

use App\Models\Card;
use App\Models\User;
use Illuminate\Database\Seeder;

class UserCardSeeder extends Seeder
{
    /**
     * Give users cards so they can create listings and complete sales.
     */
    public function run(): void
    {
        $seller = User::where('username', 'seller')->first();
        $buyer = User::where('username', 'buyer')->first();
        $seller2 = User::where('username', 'seller2')->first();

        if (! $seller || ! $buyer) {
            throw new \RuntimeException('UserSeeder must run first.');
        }

        $demoIdentifiers = ['swsh1-1', 'swsh1-2', 'swsh1-3', 'swsh1-4', 'swsh1-5', 'swsh1-6', 'swsh1-7', 'swsh1-8', 'swsh1-49', 'swsh1-50'];
        $cardIds = Card::whereIn('api_identifier', $demoIdentifiers)->orderBy('api_identifier')->pluck('id')->toArray();
        if (count($cardIds) < 5) {
            throw new \RuntimeException('Need at least 5 demo cards. Run CardSeeder first.');
        }

        // Lapras V (Holo Rare V) = cardIds[8], Lapras VMAX (Holo Rare VMAX) = cardIds[9]
        $laprasV = $cardIds[8] ?? null;
        $laprasVmax = $cardIds[9] ?? null;

        // Seller: cards 1-5 (quantities 2,2,1,1,1) + Holo Rare V y Holo Rare VMAX para pruebas
        $sellerAttach = [
            $cardIds[0] => ['quantity' => 2],
            $cardIds[1] => ['quantity' => 2],
            $cardIds[2] => ['quantity' => 1],
            $cardIds[3] => ['quantity' => 1],
            $cardIds[4] => ['quantity' => 1],
        ];
        if ($laprasV) {
            $sellerAttach[$laprasV] = ['quantity' => 1];
        }
        if ($laprasVmax) {
            $sellerAttach[$laprasVmax] = ['quantity' => 1];
        }
        $seller->cards()->syncWithoutDetaching($sellerAttach);

        // Buyer: a few cards + Lapras VMAX para tener rareza VMAX de prueba
        $buyerAttach = [
            $cardIds[5] => ['quantity' => 1],
            $cardIds[6] => ['quantity' => 1],
        ];
        if (isset($cardIds[7])) {
            $buyerAttach[$cardIds[7]] = ['quantity' => 1];
        }
        if ($laprasVmax) {
            $buyerAttach[$laprasVmax] = ['quantity' => 1];
        }
        $buyer->cards()->syncWithoutDetaching($buyerAttach);

        // Seller2: some cards for extra listings
        if ($seller2) {
            $seller2->cards()->syncWithoutDetaching([
                $cardIds[2] => ['quantity' => 1],
                $cardIds[3] => ['quantity' => 2],
            ]);
        }
    }
}
