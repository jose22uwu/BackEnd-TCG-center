<?php

namespace Database\Seeders;

use App\Models\Card;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class JcrAlbumSeeder extends Seeder
{
    /**
     * Ensure user JCR exists and has 10 cards in their album.
     */
    public function run(): void
    {
        $user = User::firstOrCreate(
            ['username' => 'JCR'],
            [
                'name' => 'JCR',
                'email' => 'jcr@example.com',
                'password' => Hash::make('password'),
                'user_type_id' => 1,
            ]
        );

        $cardIds = Card::query()->limit(10)->pluck('id')->toArray();

        if (empty($cardIds)) {
            $this->command->warn('No cards in database. Run card sync or seed cards first.');

            return;
        }

        foreach ($cardIds as $cardId) {
            $user->cards()->syncWithoutDetaching([
                $cardId => ['quantity' => 1],
            ]);
        }

        $this->command->info('User JCR now has ' . count($cardIds) . ' cards in their album.');
    }
}
