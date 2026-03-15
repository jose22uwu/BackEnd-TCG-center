<?php

namespace App\Services;

use App\Models\Card;
use TCGdex\TCGdex;

class TCGdexService
{
    protected TCGdex $tcgdex;

    public function __construct()
    {
        $this->tcgdex = new TCGdex(config('tcgdex.language', 'en'));
    }

    /**
     * Fetch a card from TCGdex API by id (e.g. 'swsh3-136') and sync to our cards table.
     */
    public function fetchAndSyncCard(string $cardId): ?Card
    {
        $apiCard = $this->tcgdex->card->get($cardId);
        if ($apiCard === null) {
            return null;
        }

        return $this->mapApiCardToModel($apiCard);
    }

    /**
     * Map TCGdex SDK Card object to our Card model (create or update).
     */
    public function mapApiCardToModel(object $apiCard): Card
    {
        $setId = isset($apiCard->set) ? ($apiCard->set->id ?? null) : null;
        $setName = isset($apiCard->set) ? ($apiCard->set->name ?? null) : null;

        $variants = null;
        if (isset($apiCard->variants)) {
            $v = $apiCard->variants;
            $variants = [
                'normal' => $v->normal ?? false,
                'reverse' => $v->reverse ?? false,
                'holo' => $v->holo ?? false,
                'firstEdition' => $v->firstEdition ?? false,
            ];
        }

        $apiData = $this->buildApiData($apiCard);

        $updatedAtApi = isset($apiCard->updated) ? \Carbon\Carbon::parse($apiCard->updated) : null;

        return Card::updateOrCreate(
            ['api_identifier' => $apiCard->id],
            [
                'name' => $apiCard->name,
                'image_url' => $apiCard->image ?? null,
                'category' => $apiCard->category ?? null,
                'illustrator' => $apiCard->illustrator ?? null,
                'rarity' => $apiCard->rarity ?? null,
                'set_identifier' => $setId,
                'set_name' => $setName,
                'local_id' => (string) ($apiCard->localId ?? ''),
                'variants' => $variants,
                'updated_at_api' => $updatedAtApi,
                'api_data' => $apiData,
            ]
        );
    }

    /**
     * Build api_data JSON from TCGdex card (attacks, hp, types, weaknesses, etc.).
     */
    protected function buildApiData(object $apiCard): array
    {
        $data = [];

        if (! empty($apiCard->hp)) {
            $data['hp'] = $apiCard->hp;
        }
        if (! empty($apiCard->types)) {
            $data['types'] = $apiCard->types;
        }
        if (! empty($apiCard->attacks)) {
            $data['attacks'] = array_map(fn ($a) => [
                'name' => $a->name ?? null,
                'cost' => $a->cost ?? [],
                'damage' => $a->damage ?? null,
                'effect' => $a->effect ?? null,
            ], $apiCard->attacks);
        }
        if (! empty($apiCard->abilities)) {
            $data['abilities'] = array_map(fn ($a) => [
                'name' => $a->name ?? null,
                'effect' => $a->effect ?? null,
                'type' => $a->type ?? null,
            ], $apiCard->abilities);
        }
        if (! empty($apiCard->weaknesses)) {
            $data['weaknesses'] = array_map(fn ($w) => ['type' => $w->type ?? null, 'value' => $w->value ?? null], $apiCard->weaknesses);
        }
        if (! empty($apiCard->resistances)) {
            $data['resistances'] = array_map(fn ($r) => ['type' => $r->type ?? null, 'value' => $r->value ?? null], $apiCard->resistances);
        }
        if (isset($apiCard->retreat)) {
            $data['retreat'] = $apiCard->retreat;
        }
        if (! empty($apiCard->description)) {
            $data['description'] = $apiCard->description;
        }
        if (! empty($apiCard->stage)) {
            $data['stage'] = $apiCard->stage;
        }
        if (! empty($apiCard->evolveFrom)) {
            $data['evolve_from'] = $apiCard->evolveFrom;
        }
        if (! empty($apiCard->effect)) {
            $data['effect'] = $apiCard->effect;
        }
        if (! empty($apiCard->trainerType)) {
            $data['trainer_type'] = $apiCard->trainerType;
        }
        if (! empty($apiCard->energyType)) {
            $data['energy_type'] = $apiCard->energyType;
        }
        if (! empty($apiCard->regulationMark)) {
            $data['regulation_mark'] = $apiCard->regulationMark;
        }

        return $data;
    }

    /**
     * Sync all cards from a TCGdex set (e.g. 'swsh3' = Darkness Ablaze).
     * Returns ['synced' => int, 'failed' => int, 'errors' => string[]].
     */
    public function syncSet(string $setId): array
    {
        $set = $this->tcgdex->set->get($setId);
        if ($set === null || empty($set->cards)) {
            return ['synced' => 0, 'failed' => 0, 'errors' => ['Set not found or has no cards.']];
        }

        $synced = 0;
        $failed = 0;
        $errors = [];

        foreach ($set->cards as $cardResume) {
            $cardId = $cardResume->id ?? null;
            if (empty($cardId)) {
                $failed++;
                continue;
            }
            try {
                $fullCard = $cardResume->toCard();
                if ($fullCard !== null) {
                    $this->mapApiCardToModel($fullCard);
                    $synced++;
                } else {
                    $failed++;
                }
            } catch (\Throwable $e) {
                $failed++;
                $errors[] = "{$cardId}: " . $e->getMessage();
            }
        }

        return ['synced' => $synced, 'failed' => $failed, 'errors' => $errors];
    }

    /**
     * Get SDK instance for direct use (list, query, etc.).
     */
    public function getSdk(): TCGdex
    {
        return $this->tcgdex;
    }
}
