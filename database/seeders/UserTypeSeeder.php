<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

class UserTypeSeeder extends Seeder
{
    /**
     * Ensure user types exist (same as migration).
     */
    public function run(): void
    {
        if (! Schema::hasTable('user_types')) {
            throw new \RuntimeException('Migrations not run. Execute first: php artisan migrate');
        }

        $rows = [
            ['name' => 'Usuario', 'slug' => 'user'],
            ['name' => 'Administrador', 'slug' => 'administrator'],
        ];

        foreach ($rows as $row) {
            DB::table('user_types')->updateOrInsert(
                ['slug' => $row['slug']],
                array_merge($row, ['created_at' => now(), 'updated_at' => now()])
            );
        }
    }
}
