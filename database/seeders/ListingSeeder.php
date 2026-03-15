<?php

namespace Database\Seeders;

use App\Models\Card;
use App\Models\Listing;
use App\Models\User;
use Illuminate\Database\Seeder;

class ListingSeeder extends Seeder
{
    /**
     * Create listings: active, one closed (via completeSale), one cancelled.
     */
    public function run(): void
    {
        $seller = User::where('username', 'seller')->first();
        $buyer = User::where('username', 'buyer')->first();

        if (! $seller || ! $buyer) {
            throw new \RuntimeException('UserSeeder must run first.');
        }

        $demoIdentifiers = ['swsh1-1', 'swsh1-2', 'swsh1-3', 'swsh1-4', 'swsh1-5', 'swsh1-6', 'swsh1-7', 'swsh1-8'];
        $cardIds = Card::whereIn('api_identifier', $demoIdentifiers)->orderBy('api_identifier')->pluck('id')->toArray();
        if (count($cardIds) < 5) {
            throw new \RuntimeException('Run CardSeeder and UserCardSeeder first.');
        }

        // Idempotent: if demo data already exists (seller has a closed listing), skip
        if (Listing::where('seller_id', $seller->id)->where('status', 'closed')->exists()) {
            return;
        }

        // Listing 1: active, then we close it with completeSale (creates invoice, moves cards to buyer)
        $listing1 = Listing::create([
            'seller_id' => $seller->id,
            'starting_price' => 25.00,
            'status' => 'active',
        ]);
        $listing1->cards()->attach([
            $cardIds[0] => ['quantity' => 1],
            $cardIds[1] => ['quantity' => 1],
        ]);
        $listing1->completeSale($buyer->id, 25.00);

        // Listing 2: active (has room for bids)
        $listing2 = Listing::create([
            'seller_id' => $seller->id,
            'starting_price' => 15.00,
            'status' => 'active',
        ]);
        $listing2->cards()->attach([
            $cardIds[2] => ['quantity' => 1],
            $cardIds[3] => ['quantity' => 1],
        ]);

        // Listing 3: cancelled
        $listing3 = Listing::create([
            'seller_id' => $seller->id,
            'starting_price' => 10.00,
            'status' => 'cancelled',
        ]);
        $listing3->cards()->attach([$cardIds[4] => ['quantity' => 1]]);

        // Listing 4: another active (seller2 if exists; he has cards 2 and 3)
        $seller2 = User::where('username', 'seller2')->first();
        if ($seller2) {
            $listing4 = Listing::create([
                'seller_id' => $seller2->id,
                'starting_price' => 8.50,
                'status' => 'active',
            ]);
            $listing4->cards()->attach([$cardIds[3] => ['quantity' => 1]]);
        }
    }
}
