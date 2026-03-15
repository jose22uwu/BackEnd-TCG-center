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

        $demoIdentifiers = ['swsh1-1', 'swsh1-2', 'swsh1-3', 'swsh1-4', 'swsh1-5', 'swsh1-6', 'swsh1-7', 'swsh1-8'];
        $cardIds = Card::whereIn('api_identifier', $demoIdentifiers)->orderBy('api_identifier')->pluck('id')->toArray();
        if (count($cardIds) < 5) {
            throw new \RuntimeException('Need at least 5 demo cards. Run CardSeeder first.');
        }

        // Seller: cards 1-5 (quantities 2,2,1,1,1) so we can create listings
        $seller->cards()->syncWithoutDetaching([
            $cardIds[0] => ['quantity' => 2],
            $cardIds[1] => ['quantity' => 2],
            $cardIds[2] => ['quantity' => 1],
            $cardIds[3] => ['quantity' => 1],
            $cardIds[4] => ['quantity' => 1],
        ]);

        // Buyer: a few cards so profile is not empty
        $buyer->cards()->syncWithoutDetaching([
            $cardIds[5] => ['quantity' => 1],
            $cardIds[6] => ['quantity' => 1],
        ]);
        if (isset($cardIds[7])) {
            $buyer->cards()->syncWithoutDetaching([$cardIds[7] => ['quantity' => 1]]);
        }

        // Seller2: some cards for extra listings
        if ($seller2) {
            $seller2->cards()->syncWithoutDetaching([
                $cardIds[2] => ['quantity' => 1],
                $cardIds[3] => ['quantity' => 2],
            ]);
        }
    }
}
