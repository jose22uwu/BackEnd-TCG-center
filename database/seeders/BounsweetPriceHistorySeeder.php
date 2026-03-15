<?php

namespace Database\Seeders;

use App\Models\Card;
use App\Models\Invoice;
use App\Models\InvoiceItem;
use App\Models\Listing;
use App\Models\User;
use Carbon\Carbon;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class BounsweetPriceHistorySeeder extends Seeder
{
    /**
     * Crea la carta Bounsweet si no existe y 10 ventas históricas de prueba
     * para que el gráfico de historial de precios muestre datos.
     */
    public function run(): void
    {
        $bounsweet = Card::firstOrCreate(
            ['name' => 'Bounsweet'],
            [
                'api_identifier' => 'bounsweet-seed-' . uniqid(),
                'image_url' => 'https://api.tcgdex.net/v2/en/cards/swsh1-130',
                'category' => 'Pokemon',
                'rarity' => 'Common',
                'set_identifier' => 'swsh1',
                'set_name' => 'Sword & Shield',
            ]
        );

        $seller = User::orderBy('id')->first();
        if (! $seller) {
            $this->command->warn('No hay usuarios. Ejecuta DatabaseSeeder o crea un usuario.');

            return;
        }

        $buyer = User::orderBy('id')->skip(1)->first();
        if (! $buyer || $buyer->id === $seller->id) {
            $buyer = User::factory()->create([
                'username' => 'CompradorTest',
                'name' => 'Comprador Test',
                'user_type_id' => $seller->user_type_id ?? 1,
            ]);
        }

        $prices = [1.25, 1.50, 1.35, 1.80, 1.60, 2.00, 1.90, 1.45, 1.70, 1.55];
        $now = Carbon::now();

        for ($i = 0; $i < 10; $i++) {
            $soldAt = $now->copy()->subDays(9 - $i);

            DB::transaction(function () use ($bounsweet, $seller, $buyer, $prices, $i, $soldAt) {
                $listing = Listing::create([
                    'seller_id' => $seller->id,
                    'starting_price' => $prices[$i],
                    'status' => 'closed',
                    'closed_at' => $soldAt,
                ]);
                $listing->cards()->attach($bounsweet->id, ['quantity' => 1]);

                $invoice = Invoice::create([
                    'seller_id' => $seller->id,
                    'buyer_id' => $buyer->id,
                    'listing_id' => $listing->id,
                    'total_amount' => $prices[$i],
                    'status' => 'paid',
                ]);
                $invoice->created_at = $soldAt;
                $invoice->save();

                InvoiceItem::create([
                    'invoice_id' => $invoice->id,
                    'card_id' => $bounsweet->id,
                    'quantity' => 1,
                    'unit_price' => $prices[$i],
                ]);
            });
        }

        $seller->cards()->syncWithoutDetaching([$bounsweet->id => ['quantity' => 1]]);

        $this->command->info("Bounsweet (id {$bounsweet->id}): 10 ventas de prueba creadas y carta añadida al álbum de {$seller->username}. Inicia sesión con ese usuario, ve a Vender cartas, haz clic en Bounsweet y revisa el historial de precios.");
    }
}
