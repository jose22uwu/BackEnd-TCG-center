<?php

namespace App\Console\Commands;

use App\Services\TCGdexService;
use Illuminate\Console\Command;

class SyncTcgdexCards extends Command
{
    protected $signature = 'tcgdex:sync-cards
                            {--set= : Set id (e.g. swsh3) to sync all cards from the set}
                            {--card= : Single card id (e.g. swsh3-136) to sync}
                            {--limit= : Max cards when using --set (default: no limit)}';

    protected $description = 'Fetch cards from TCGdex API and sync to local cards table';

    public function handle(TCGdexService $tcgdex): int
    {
        $setId = $this->option('set');
        $cardId = $this->option('card');
        $limit = $this->option('limit') ? (int) $this->option('limit') : null;

        if ($cardId) {
            return $this->syncOneCard($tcgdex, $cardId);
        }

        if ($setId) {
            return $this->syncSet($tcgdex, $setId, $limit);
        }

        $this->components->warn('Provide --set=SET_ID (e.g. swsh3) or --card=CARD_ID (e.g. swsh3-136).');
        $this->line('Example: php artisan tcgdex:sync-cards --set=swsh3');
        $this->line('Example: php artisan tcgdex:sync-cards --card=swsh3-136');

        return self::FAILURE;
    }

    private function syncOneCard(TCGdexService $tcgdex, string $cardId): int
    {
        $this->info("Syncing card: {$cardId}");
        $card = $tcgdex->fetchAndSyncCard($cardId);
        if ($card === null) {
            $this->components->error("Card not found: {$cardId}");
            return self::FAILURE;
        }
        $this->components->info("Synced: {$card->name} ({$card->api_identifier})");
        return self::SUCCESS;
    }

    private function syncSet(TCGdexService $tcgdex, string $setId, ?int $limit): int
    {
        $this->info("Loading set: {$setId}");
        $sdk = $tcgdex->getSdk();
        $set = $sdk->set->get($setId);
        if ($set === null) {
            $this->components->error("Set not found: {$setId}");
            return self::FAILURE;
        }

        $cards = $set->cards;
        if (empty($cards)) {
            $this->components->warn("Set has no cards: {$setId}");
            return self::SUCCESS;
        }

        if ($limit !== null) {
            $cards = array_slice($cards, 0, $limit);
        }

        $total = count($cards);
        $this->info("Syncing {$total} cards from set: {$set->name} ({$setId})");
        $bar = $this->output->createProgressBar($total);
        $bar->start();

        $synced = 0;
        $failed = 0;
        foreach ($cards as $cardResume) {
            $cardId = $cardResume->id ?? null;
            if (empty($cardId)) {
                $failed++;
                $bar->advance();
                continue;
            }
            try {
                $fullCard = $cardResume->toCard();
                if ($fullCard !== null) {
                    $tcgdex->mapApiCardToModel($fullCard);
                    $synced++;
                } else {
                    $failed++;
                }
            } catch (\Throwable) {
                $failed++;
            }
            $bar->advance();
        }
        $bar->finish();
        $this->newLine(2);
        $this->components->info("Done. Synced: {$synced}, Failed: {$failed}");

        return self::SUCCESS;
    }
}
