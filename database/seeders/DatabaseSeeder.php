<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     * Order matters: UserType -> User -> Card -> UserCard -> Listing -> Bid.
     */
    public function run(): void
    {
        $this->call([
            UserTypeSeeder::class,
            UserSeeder::class,
            CardSeeder::class,
            UserCardSeeder::class,
            ListingSeeder::class,
            BidSeeder::class,
        ]);
    }
}
