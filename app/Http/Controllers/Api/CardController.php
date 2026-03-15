<?php

namespace App\Http\Controllers\Api;

use App\Models\Card;
use App\Models\Invoice;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class CardController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $perPage = min((int) $request->get('per_page', 15), 50);
        $cards = Card::query()
            ->when($request->filled('search'), fn ($q) => $q->where('name', 'like', '%' . $request->search . '%'))
            ->when($request->filled('category'), fn ($q) => $q->where('category', $request->category))
            ->when($request->filled('set'), fn ($q) => $q->where('set_identifier', $request->set))
            ->orderBy('name')
            ->paginate($perPage);

        return $this->success($cards);
    }

    public function show(Card $card): JsonResponse
    {
        return $this->success($card);
    }

    /**
     * Last 10 sale prices for this card (from completed listings that included it).
     */
    public function priceHistory(Card $card): JsonResponse
    {
        $history = Invoice::query()
            ->whereHas('listing', function ($q) use ($card) {
                $q->whereHas('cards', fn ($q2) => $q2->where('cards.id', $card->id));
            })
            ->orderByDesc('created_at')
            ->limit(10)
            ->get(['total_amount', 'created_at'])
            ->map(fn ($inv) => [
                'amount' => (float) $inv->total_amount,
                'sold_at' => $inv->created_at->toIso8601String(),
            ])
            ->values()
            ->all();

        return $this->success($history);
    }
}
