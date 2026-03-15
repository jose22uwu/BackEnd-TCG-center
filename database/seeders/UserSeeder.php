<?php

namespace Database\Seeders;

use App\Models\User;
use App\Models\UserType;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class UserSeeder extends Seeder
{
    /**
     * Create fixed users for development/testing. All use password: password
     */
    public function run(): void
    {
        $userType = UserType::where('slug', 'user')->first();
        $adminType = UserType::where('slug', 'administrator')->first();

        if (! $userType || ! $adminType) {
            throw new \RuntimeException('UserTypeSeeder must run first. Run: php artisan db:seed --class=UserTypeSeeder');
        }

        $users = [
            [
                'username' => 'seller',
                'name' => 'Vendedor Demo',
                'email' => 'seller@demo.local',
                'password' => 'password',
                'user_type_id' => $userType->id,
            ],
            [
                'username' => 'buyer',
                'name' => 'Comprador Demo',
                'email' => 'buyer@demo.local',
                'password' => 'password',
                'user_type_id' => $userType->id,
            ],
            [
                'username' => 'admin',
                'name' => 'Administrador',
                'email' => 'admin@demo.local',
                'password' => 'password',
                'user_type_id' => $adminType->id,
            ],
            [
                'username' => 'seller2',
                'name' => 'Segundo Vendedor',
                'email' => 'seller2@demo.local',
                'password' => 'password',
                'user_type_id' => $userType->id,
            ],
            [
                'username' => 'buyer2',
                'name' => 'Segundo Comprador',
                'email' => 'buyer2@demo.local',
                'password' => 'password',
                'user_type_id' => $userType->id,
            ],
        ];

        foreach ($users as $data) {
            $data['password'] = Hash::make($data['password']);
            User::updateOrCreate(
                ['username' => $data['username']],
                $data
            );
        }
    }
}
