<?php

namespace App\Http\Controllers\Api;

use App\Models\Card;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class UserCardController extends Controller
{
    /**
     * Current user's virtual album (cards they own).
     */
    public function index(Request $request): JsonResponse
    {
        $user = $request->user();
        $query = $user->cards()
            ->withPivot('quantity')
            ->wherePivot('quantity', '>', 0)
            ->when($request->filled('search'), fn ($q) => $q->where('cards.name', 'like', '%' . $request->search . '%'))
            ->orderBy('cards.name');

        $perPage = $request->get('per_page', 15);
        if ($perPage === 'all' || (is_numeric($perPage) && (int) $perPage === 0)) {
            $cards = $query->get();
            return $this->success($cards);
        }

        $cards = $query->paginate(min((int) $perPage, 500));
        return $this->success($cards);
    }

    /**
     * Add a card to the user's album or increase quantity.
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'card_id' => ['required', 'integer', 'exists:cards,id'],
            'quantity' => ['sometimes', 'integer', 'min:1', 'max:999'],
        ]);

        $user = $request->user();
        $quantity = $validated['quantity'] ?? 1;

        $existing = $user->cards()->where('cards.id', $validated['card_id'])->first();
        if ($existing) {
            $user->cards()->updateExistingPivot($validated['card_id'], [
                'quantity' => $existing->pivot->quantity + $quantity,
            ]);
        } else {
            $user->cards()->attach($validated['card_id'], ['quantity' => $quantity]);
        }

        $card = $user->cards()->where('cards.id', $validated['card_id'])->first();

        return $this->success($card, 'Card added to album', 201);
    }

    /**
     * Update quantity of a card in the album.
     */
    public function update(Request $request, Card $card): JsonResponse
    {
        $validated = $request->validate([
            'quantity' => ['required', 'integer', 'min:0', 'max:999'],
        ]);

        $user = $request->user();
        if (! $user->cards()->where('cards.id', $card->id)->exists()) {
            return $this->error('Card not in your album.', 404);
        }

        if ($validated['quantity'] === 0) {
            $user->cards()->detach($card->id);
            return $this->success(['removed' => true], 'Card removed from album');
        }

        $user->cards()->updateExistingPivot($card->id, ['quantity' => $validated['quantity']]);

        $updated = $user->cards()->where('cards.id', $card->id)->first();

        return $this->success($updated);
    }

    /**
     * Remove a card from the album.
     */
    public function destroy(Request $request, Card $card): JsonResponse
    {
        $request->user()->cards()->detach($card->id);

        return $this->success(null, 'Card removed from album');
    }
}
