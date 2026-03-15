<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\HasOne;
use Illuminate\Support\Facades\DB;

class Listing extends Model
{
    protected $fillable = [
        'seller_id',
        'starting_price',
        'status',
        'closed_at',
    ];

    protected function casts(): array
    {
        return [
            'starting_price' => 'decimal:2',
            'closed_at' => 'datetime',
        ];
    }

    public function seller(): BelongsTo
    {
        return $this->belongsTo(User::class, 'seller_id');
    }

    public function cards(): BelongsToMany
    {
        return $this->belongsToMany(Card::class, 'listing_cards')
            ->withPivot('quantity')
            ->withTimestamps();
    }

    public function bids(): HasMany
    {
        return $this->hasMany(Bid::class);
    }

    public function invoice(): HasOne
    {
        return $this->hasOne(Invoice::class);
    }

    /**
     * Complete the sale: create invoice, invoice items, transfer cards to buyer, close listing.
     */
    public function completeSale(int $buyerId, float $amount): Invoice
    {
        return DB::transaction(function () use ($buyerId, $amount) {
            $listing = $this->fresh(['cards', 'seller']);
            if ($listing->status !== 'active') {
                throw new \InvalidArgumentException('Listing is not active.');
            }
            if ($listing->seller_id === $buyerId) {
                throw new \InvalidArgumentException('Seller cannot buy own listing.');
            }

            $totalQuantity = $listing->cards->sum(fn ($c) => $c->pivot->quantity);
            $unitPrice = $totalQuantity > 0 ? round($amount / $totalQuantity, 2) : 0;

            $invoice = Invoice::create([
                'seller_id' => $listing->seller_id,
                'buyer_id' => $buyerId,
                'listing_id' => $listing->id,
                'total_amount' => $amount,
                'status' => 'paid',
            ]);

            foreach ($listing->cards as $card) {
                $qty = (int) $card->pivot->quantity;
                InvoiceItem::create([
                    'invoice_id' => $invoice->id,
                    'card_id' => $card->id,
                    'quantity' => $qty,
                    'unit_price' => $unitPrice,
                ]);

                $seller = User::find($listing->seller_id);
                $buyer = User::find($buyerId);
                $sellerPivot = $seller->cards()->where('card_id', $card->id)->first();
                $current = $sellerPivot ? (int) $sellerPivot->pivot->quantity : 0;
                if ($current < $qty) {
                    throw new \InvalidArgumentException("Seller does not have enough quantity for card {$card->id}.");
                }
                if ($current === $qty) {
                    $seller->cards()->detach($card->id);
                } else {
                    $seller->cards()->updateExistingPivot($card->id, ['quantity' => $current - $qty]);
                }

                $buyerPivot = $buyer->cards()->where('card_id', $card->id)->first();
                $buyerQty = $buyerPivot ? (int) $buyerPivot->pivot->quantity : 0;
                if ($buyerQty === 0) {
                    $buyer->cards()->attach($card->id, ['quantity' => $qty]);
                } else {
                    $buyer->cards()->updateExistingPivot($card->id, ['quantity' => $buyerQty + $qty]);
                }
            }

            $listing->update(['status' => 'closed', 'closed_at' => now()]);

            return $invoice->fresh();
        });
    }
}
