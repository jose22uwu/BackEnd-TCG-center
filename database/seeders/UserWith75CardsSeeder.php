<?php

namespace Database\Seeders;

use App\Models\Card;
use App\Models\User;
use App\Models\UserType;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;

class UserWith75CardsSeeder extends Seeder
{
    /**
     * Crea un usuario con unas 75 cartas en su inventario (user_cards).
     * Depende de: UserTypeSeeder, UserSeeder (o usuarios existentes), y cartas en la tabla cards.
     */
    public function run(): void
    {
        $userType = UserType::where('slug', 'user')->first();
        if (! $userType) {
            throw new \RuntimeException('UserTypeSeeder debe ejecutarse antes.');
        }

        $user = User::updateOrCreate(
            ['username' => 'coleccion75'],
            [
                'name' => 'Usuario 75 Cartas',
                'email' => 'coleccion75@demo.local',
                'password' => Hash::make('password'),
                'user_type_id' => $userType->id,
            ]
        );

        $targetDistinctCards = 75;
        $cardIds = Card::orderBy('id')->limit($targetDistinctCards)->pluck('id')->toArray();
        if (empty($cardIds)) {
            throw new \RuntimeException('No hay cartas en la base de datos. Ejecuta CardSeeder o Sync300TcgdexCardsSeeder antes.');
        }
        if (count($cardIds) < $targetDistinctCards) {
            $this->command->warn("Solo hay " . count($cardIds) . " cartas en la BD; se asignaran esas.");
        }

        $attach = [];
        foreach ($cardIds as $cardId) {
            $attach[$cardId] = ['quantity' => 1];
        }

        $user->cards()->syncWithoutDetaching($attach);

        $distinctCount = $user->cards()->count();
        $this->command->info("Usuario 'coleccion75' creado/actualizado con {$distinctCount} cartas distintas en inventario (user_cards).");
    }
}
