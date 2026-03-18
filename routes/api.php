<?php

use App\Http\Controllers\Api\AiChatController;
use App\Http\Controllers\Api\ApiInfoController;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\BidController;
use App\Http\Controllers\Api\CardController;
use App\Http\Controllers\Api\InvoiceController;
use App\Http\Controllers\Api\ListingController;
use App\Http\Controllers\Api\UserCardController;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

Route::get('/', ApiInfoController::class)->name('api.info');

Route::post('/register', [AuthController::class, 'register'])->name('api.register');
Route::post('/login', [AuthController::class, 'login'])->name('api.login');

Route::get('/cards', [CardController::class, 'index'])->name('api.cards.index');
Route::get('/carousel', [CardController::class, 'carousel'])->name('api.carousel');
Route::get('/cards/{card}/price-history', [CardController::class, 'priceHistory'])->name('api.cards.price-history');
Route::get('/cards/{card}', [CardController::class, 'show'])->name('api.cards.show');

Route::get('/listings', [ListingController::class, 'index'])->name('api.listings.index');
Route::get('/listings/{listing}', [ListingController::class, 'show'])->name('api.listings.show');
Route::get('/listings/{listing}/bids', [BidController::class, 'index'])->name('api.listings.bids.index');

Route::middleware('auth:sanctum')->group(function () {
    Route::post('/logout', [AuthController::class, 'logout'])->name('api.logout');
    Route::get('/user', fn (Request $request) => $request->user()->load('userType'))->name('api.user');

    Route::get('/user/cards', [UserCardController::class, 'index'])->name('api.user.cards.index');
    Route::post('/user/cards', [UserCardController::class, 'store'])->name('api.user.cards.store');
    Route::match(['put', 'patch'], '/user/cards/{card}', [UserCardController::class, 'update'])->name('api.user.cards.update');
    Route::delete('/user/cards/{card}', [UserCardController::class, 'destroy'])->name('api.user.cards.destroy');

    Route::post('/listings', [ListingController::class, 'store'])->name('api.listings.store');
    Route::get('/user/listings', [ListingController::class, 'myListings'])->name('api.user.listings');
    Route::post('/listings/{listing}/accept', [ListingController::class, 'accept'])->name('api.listings.accept');
    Route::match(['put', 'patch'], '/listings/{listing}', [ListingController::class, 'update'])->name('api.listings.update');
    Route::delete('/listings/{listing}', [ListingController::class, 'destroy'])->name('api.listings.destroy');

    Route::post('/listings/{listing}/bids', [BidController::class, 'store'])->name('api.listings.bids.store');
    Route::match(['put', 'patch'], '/listings/{listing}/bids/{bid}', [BidController::class, 'update'])->name('api.listings.bids.update');

    Route::get('/user/invoices', [InvoiceController::class, 'index'])->name('api.user.invoices');
    Route::get('/invoices/{invoice}', [InvoiceController::class, 'show'])->name('api.invoices.show');

    Route::post('/ai/chat', AiChatController::class)->name('api.ai.chat');
});
