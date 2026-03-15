<?php

namespace App\Http\Controllers\Api;

use App\Models\Bid;
use App\Models\Listing;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class BidController extends Controller
{
    /**
     * Bids for a listing (e.g. for display on listing detail).
     */
    public function index(Listing $listing): JsonResponse
    {
        $bids = $listing->bids()
            ->with('user:id,username,name')
            ->orderByDesc('amount')
            ->orderByDesc('created_at')
            ->paginate(20);

        return $this->success($bids);
    }

    /**
     * Place a bid (counter-offer) on a listing. Seller must accept or decline.
     */
    public function store(Request $request, Listing $listing): JsonResponse
    {
        if ($listing->status !== 'active') {
            return $this->error('La oferta no está activa.', 422);
        }
        if ($listing->seller_id === $request->user()->id) {
            return $this->error('No puedes ofertar en tu propia oferta.', 422);
        }

        $validated = $request->validate([
            'amount' => ['required', 'numeric', 'min:0.01'],
        ]);

        $bid = Bid::create([
            'listing_id' => $listing->id,
            'user_id' => $request->user()->id,
            'amount' => $validated['amount'],
            'status' => 'pending',
        ]);

        $bid->load('user:id,username,name');

        return $this->success($bid, 'Contraoferta enviada. El vendedor puede aceptarla o declinarla.', 201);
    }

    /**
     * Seller accepts or declines a pending bid (counter-offer).
     */
    public function update(Request $request, Listing $listing, Bid $bid): JsonResponse
    {
        if ($listing->seller_id !== $request->user()->id) {
            return $this->error('Forbidden', 403);
        }
        if ($bid->listing_id !== $listing->id) {
            return $this->error('Bid does not belong to this listing.', 404);
        }
        if ($bid->status !== 'pending') {
            return $this->error('Esta contraoferta ya fue procesada.', 422);
        }
        if ($listing->status !== 'active') {
            return $this->error('La oferta no está activa.', 422);
        }

        $validated = $request->validate([
            'action' => ['required', 'in:accept,decline'],
        ]);

        if ($validated['action'] === 'decline') {
            $bid->update(['status' => 'declined']);
            return $this->success($bid->fresh('user:id,username,name'), 'Contraoferta declinada.');
        }

        try {
            $listing->completeSale($bid->user_id, (float) $bid->amount);
            $listing->bids()->where('id', '!=', $bid->id)->where('status', 'pending')->update(['status' => 'declined']);
            $bid->update(['status' => 'accepted']);
            $invoice = $listing->fresh()->invoice;
            return $this->success([
                'bid' => $bid->fresh('user:id,username,name'),
                'invoice' => $invoice,
            ], 'Venta realizada. Las cartas se han transferido al comprador.', 200);
        } catch (\InvalidArgumentException $e) {
            return $this->error($e->getMessage(), 422);
        }
    }
}
