<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     * Order: UserType -> User -> Card (demo) -> Sync300Tcgdex (300 cartas) -> UserWith75Cards -> UserCard -> Listing -> Bid.
     */
    public function run(): void
    {
        $this->call([
            UserTypeSeeder::class,
            UserSeeder::class,
            CardSeeder::class,
            Sync300TcgdexCardsSeeder::class,
            UserWith75CardsSeeder::class,
            UserCardSeeder::class,
            ListingSeeder::class,
            BidSeeder::class,
        ]);
    }
}
