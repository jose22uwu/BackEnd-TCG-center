<?php

namespace Database\Seeders;

use App\Models\Card;
use App\Models\User;
use Illuminate\Database\Seeder;

class JcrAlbumAddRareCardsSeeder extends Seeder
{
    /**
     * Add 5 more cards to user JCR, preferring higher rarity for modal testing.
     */
    public function run(): void
    {
        $user = User::where('username', 'JCR')->first();

        if (! $user) {
            $this->command->warn('User JCR not found. Run JcrAlbumSeeder first.');

            return;
        }

        $existingIds = $user->cards()->pluck('cards.id')->toArray();

        $query = Card::query()
            ->whereNotIn('id', $existingIds);

        $rareCards = (clone $query)
            ->whereNotNull('rarity')
            ->where(function ($q) {
                $q->where('rarity', 'like', '%Secret%')
                    ->orWhere('rarity', 'like', '%Hyper%')
                    ->orWhere('rarity', 'like', '%Ultra%')
                    ->orWhere('rarity', 'like', '%Double Rare%')
                    ->orWhere('rarity', 'like', '%Illustration Rare%')
                    ->orWhere('rarity', 'like', '%Special%')
                    ->orWhere('rarity', 'like', '%Rare%');
            })
            ->limit(5)
            ->pluck('id')
            ->toArray();

        $needed = 5 - count($rareCards);
        $extraIds = [];
        if ($needed > 0) {
            $extraIds = (clone $query)
                ->whereNotIn('id', $rareCards)
                ->limit($needed)
                ->pluck('id')
                ->toArray();
        }

        $cardIds = array_merge($rareCards, $extraIds);

        if (empty($cardIds)) {
            $this->command->warn('No extra cards available to add (JCR may already have all cards).');

            return;
        }

        foreach ($cardIds as $cardId) {
            $user->cards()->syncWithoutDetaching([
                $cardId => ['quantity' => 1],
            ]);
        }

        $this->command->info('Added ' . count($cardIds) . ' more cards to JCR (total in album: ' . $user->cards()->count() . ').');
    }
}
