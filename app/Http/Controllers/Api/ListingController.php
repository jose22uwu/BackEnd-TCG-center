<?php

namespace App\Http\Controllers\Api;

use App\Models\Listing;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ListingController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $perPage = min((int) $request->get('per_page', 15), 50);
        $listings = Listing::query()
            ->with(['seller:id,username,name', 'cards'])
            ->when($request->filled('status'), fn ($q) => $q->where('status', $request->status))
            ->when($request->filled('seller_id'), fn ($q) => $q->where('seller_id', $request->seller_id))
            ->orderByDesc('created_at')
            ->paginate($perPage);

        return $this->success($listings);
    }

    public function show(Listing $listing): JsonResponse
    {
        $listing->load(['seller:id,username,name', 'cards', 'bids' => fn ($q) => $q->orderByDesc('amount')->limit(10)->with('user:id,username,name')]);

        return $this->success($listing);
    }

    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'starting_price' => ['required', 'numeric', 'min:0'],
            'cards' => ['required', 'array', 'min:1'],
            'cards.*.card_id' => ['required', 'integer', 'exists:cards,id'],
            'cards.*.quantity' => ['sometimes', 'integer', 'min:1', 'max:999'],
        ]);

        $user = $request->user();

        $listing = Listing::create([
            'seller_id' => $user->id,
            'starting_price' => $validated['starting_price'],
            'status' => 'active',
        ]);

        foreach ($validated['cards'] as $item) {
            $listing->cards()->attach($item['card_id'], [
                'quantity' => $item['quantity'] ?? 1,
            ]);
        }

        $listing->load('cards');

        return $this->success($listing, 'Listing created', 201);
    }

    public function update(Request $request, Listing $listing): JsonResponse
    {
        if ($listing->seller_id !== $request->user()->id) {
            return $this->error('Forbidden', 403);
        }
        if ($listing->status !== 'active') {
            return $this->error('Cannot update closed or cancelled listing.', 422);
        }

        $validated = $request->validate([
            'starting_price' => ['sometimes', 'numeric', 'min:0'],
            'status' => ['sometimes', 'in:active,cancelled'],
        ]);

        $listing->update($validated);

        return $this->success($listing->fresh(['seller:id,username,name', 'cards']));
    }

    public function destroy(Request $request, Listing $listing): JsonResponse
    {
        if ($listing->seller_id !== $request->user()->id) {
            return $this->error('Forbidden', 403);
        }
        if ($listing->status !== 'active') {
            return $this->error('Cannot delete closed or cancelled listing.', 422);
        }

        $listing->delete();

        return $this->success(null, 'Listing deleted');
    }

    /**
     * Listings created by the authenticated user (for "Anuncios de venta").
     * Query params: status (active|closed|cancelled), has_pending_bids (1 to show only listings with pending counter-offers).
     */
    public function myListings(Request $request): JsonResponse
    {
        $perPage = min((int) $request->get('per_page', 15), 50);
        $status = $request->get('status');
        $hasPendingBids = $request->boolean('has_pending_bids');

        $query = $request->user()
            ->listingsAsSeller()
            ->with(['cards', 'bids' => fn ($q) => $q->with('user:id,username,name')->orderByDesc('created_at')]);

        if ($status !== null && $status !== '') {
            $allowed = ['active', 'closed', 'cancelled'];
            $statuses = array_map('trim', explode(',', $status));
            $statuses = array_intersect($statuses, $allowed);
            if (count($statuses) > 0) {
                $query->whereIn('status', array_values($statuses));
            }
        }

        if ($hasPendingBids) {
            $query->whereHas('bids', fn ($q) => $q->where('status', 'pending'));
        }

        $listings = $query->orderByDesc('created_at')->paginate($perPage);

        return $this->success($listings);
    }

    /**
     * Buyer accepts the listing at asking price. Sale is completed immediately.
     */
    public function accept(Request $request, Listing $listing): JsonResponse
    {
        if ($listing->status !== 'active') {
            return $this->error('La oferta no está activa.', 422);
        }
        if ($listing->seller_id === $request->user()->id) {
            return $this->error('No puedes aceptar tu propia oferta.', 422);
        }

        try {
            $invoice = $listing->completeSale($request->user()->id, (float) $listing->starting_price);
            return $this->success($invoice->load('listing.cards'), 'Compra realizada. La carta se ha añadido a tu perfil.', 201);
        } catch (\InvalidArgumentException $e) {
            return $this->error($e->getMessage(), 422);
        }
    }
}
