<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     * Prepares cards table for TCGdex API data (https://tcgdex.dev): image, category, set, etc.
     */
    public function up(): void
    {
        Schema::table('cards', function (Blueprint $table) {
            $table->string('image_url')->nullable()->after('name')->comment('TCGdex image base URL');
            $table->string('category')->nullable()->after('image_url')->comment('Pokemon, Trainer, Energy');
            $table->string('illustrator')->nullable()->after('category');
            $table->string('rarity')->nullable()->after('illustrator');
            $table->string('set_identifier')->nullable()->after('rarity')->comment('TCGdex set id');
            $table->string('set_name')->nullable()->after('set_identifier');
            $table->string('local_id')->nullable()->after('set_name')->comment('Card number within set');
            $table->json('variants')->nullable()->after('local_id')->comment('normal, reverse, holo, firstEdition');
            $table->timestamp('updated_at_api')->nullable()->after('variants')->comment('Last update from TCGdex');
            $table->json('api_data')->nullable()->after('updated_at_api')->comment('Attacks, hp, types, weaknesses, effect, etc.');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('cards', function (Blueprint $table) {
            $table->dropColumn([
                'image_url',
                'category',
                'illustrator',
                'rarity',
                'set_identifier',
                'set_name',
                'local_id',
                'variants',
                'updated_at_api',
                'api_data',
            ]);
        });
    }
};
