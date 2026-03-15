<?php

namespace App\Http\Controllers\Api;

use App\Models\Invoice;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class InvoiceController extends Controller
{
    /**
     * Invoices where the user is seller or buyer (purchases and sales).
     */
    public function index(Request $request): JsonResponse
    {
        $user = $request->user();
        $query = Invoice::query()
            ->with(['seller:id,username,name', 'buyer:id,username,name', 'listing', 'items.card'])
            ->where(fn ($q) => $q->where('seller_id', $user->id)->orWhere('buyer_id', $user->id))
            ->orderByDesc('created_at');

        if ($request->filled('role')) {
            if ($request->role === 'seller') {
                $query->where('seller_id', $user->id);
            }
            if ($request->role === 'buyer') {
                $query->where('buyer_id', $user->id);
            }
        }

        $invoices = $query->paginate(min((int) $request->get('per_page', 15), 50));

        return $this->success($invoices);
    }

    /**
     * Single invoice (for receipt / comprobante). Only own invoices.
     */
    public function show(Request $request, Invoice $invoice): JsonResponse
    {
        $user = $request->user();
        if ($invoice->seller_id !== $user->id && $invoice->buyer_id !== $user->id) {
            return $this->error('Forbidden', 403);
        }

        $invoice->load(['seller:id,username,name', 'buyer:id,username,name', 'listing', 'items.card']);

        return $this->success($invoice);
    }
}
