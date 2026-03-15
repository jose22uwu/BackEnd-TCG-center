<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Casts\Attribute;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;

class Card extends Model
{
    protected $fillable = [
        'api_identifier',
        'name',
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
    ];

    protected function casts(): array
    {
        return [
            'variants' => 'array',
            'api_data' => 'array',
            'updated_at_api' => 'datetime',
        ];
    }

    /**
     * TCGdex stores a base image path; the actual image needs /high.png or /low.png.
     */
    protected function imageUrl(): Attribute
    {
        return Attribute::get(function (?string $value): ?string {
            if (empty($value)) {
                return null;
            }
            if (preg_match('/\.(png|webp|jpg|jpeg|gif)(\?|$)/i', $value)) {
                return $value;
            }
            return rtrim($value, '/') . '/high.png';
        });
    }

    public function users(): BelongsToMany
    {
        return $this->belongsToMany(User::class, 'user_cards')
            ->withPivot('quantity')
            ->withTimestamps();
    }

    public function listings(): BelongsToMany
    {
        return $this->belongsToMany(Listing::class, 'listing_cards')
            ->withPivot('quantity')
            ->withTimestamps();
    }
}
