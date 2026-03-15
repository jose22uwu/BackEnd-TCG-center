<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('user_types', function (Blueprint $table) {
            $table->id();
            $table->string('name')->comment('Display name: Usuario, Administrador');
            $table->string('slug')->unique()->comment('Internal identifier: user, administrator');
            $table->timestamps();
        });

        DB::table('user_types')->insert([
            ['name' => 'Usuario', 'slug' => 'user', 'created_at' => now(), 'updated_at' => now()],
            ['name' => 'Administrador', 'slug' => 'administrator', 'created_at' => now(), 'updated_at' => now()],
        ]);
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('user_types');
    }
};
