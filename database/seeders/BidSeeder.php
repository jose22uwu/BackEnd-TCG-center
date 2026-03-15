<?php

namespace Database\Seeders;

use App\Models\Bid;
use App\Models\Listing;
use App\Models\User;
use Illuminate\Database\Seeder;

class BidSeeder extends Seeder
{
    /**
     * Create bids on active listings: pending, accepted, declined.
     */
    public function run(): void
    {
        $buyer = User::where('username', 'buyer')->first();
        $buyer2 = User::where('username', 'buyer2')->first();

        if (! $buyer) {
            throw new \RuntimeException('UserSeeder must run first.');
        }

        $activeListings = Listing::where('status', 'active')->orderBy('id')->get();
        if ($activeListings->isEmpty()) {
            throw new \RuntimeException('ListingSeeder must run first to create active listings.');
        }

        $listing = $activeListings->first();

        // Pending bid (counter-offer waiting for seller response)
        Bid::firstOrCreate(
            [
                'listing_id' => $listing->id,
                'user_id' => $buyer->id,
                'amount' => 12.00,
            ],
            ['status' => 'pending']
        );

        // Second pending bid from buyer2 if exists
        if ($buyer2) {
            Bid::firstOrCreate(
                [
                    'listing_id' => $listing->id,
                    'user_id' => $buyer2->id,
                    'amount' => 14.00,
                ],
                ['status' => 'pending']
            );
        }

        // Accepted and declined: create with status so UI can show history
        Bid::firstOrCreate(
            [
                'listing_id' => $listing->id,
                'user_id' => $buyer->id,
                'amount' => 11.00,
            ],
            ['status' => 'declined']
        );

        if ($buyer2) {
            Bid::firstOrCreate(
                [
                    'listing_id' => $listing->id,
                    'user_id' => $buyer2->id,
                    'amount' => 13.50,
                ],
                ['status' => 'accepted']
            );
        }
    }
}
