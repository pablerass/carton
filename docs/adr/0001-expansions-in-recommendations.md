# 1. Expansions in recommendations

Date: 2026-11-09

## Status

Proposed

## Context

User collections include both base games and expansions, and both are downloaded
as `BGGGame` objects. `BoardGame.is_expansion` marks the expansions, but nothing
else separates them yet. An expansion on its own can't be played, so recommending
it as an independent game would be wrong.

For a recommendation tool, most expansions don't matter: new cards, scenarios,
art or small rule changes don't change *when* a game is a good fit. An expansion
only matters when it changes one of the parameters recommendations are based on:

- **Number of players**, e.g. an expansion that adds a 5-6 player range.
- **Play time**.
- **Complexity**, the BGG weight.

## Decision

### Relevance filter

Compare each expansion with its base game and keep it only if it:

- widens the player range (`players` or `community_players`),
- changes the play time noticeably (threshold to be defined, e.g. >= 15 minutes
  or >= 25% of the base game play time), or
- changes the weight noticeably, and only when the expansion has enough weight
  votes to be trusted (`numweights` in the BGG statistics, threshold to be
  defined).

Players and play time are the most reliable signals. Expansion weight on BGG is
noisy: it usually has few votes, and some users rate the expansion alone while
others rate base game plus expansion.

Expansions that don't pass the filter are dropped from recommendations, or just
shown next to their base game.

### Recommendation

- A relevant expansion is recommended as a **"base game + expansion"**
  combination, using the expansion's parameters where they differ from the base
  game (e.g. the wider player range).
- A combination is only recommended if the base game is also in the collection.
- Expansions are never recommended on their own.

### Prerequisites

- Relate expansions to their base games in the model (the existing
  `# TODO: Add expansions relation` in `BoardGame`). BGG's XML API v1 lists the
  base games of an expansion as `<boardgameexpansion inbound="true">` elements,
  the same data used to set `is_expansion`.
- An expansion can belong to several base games (e.g. big box editions), so the
  relation must be one-to-many.
- Download the number of weight votes (`numweights`).

## Consequences

- Recommendations will cover combinations such as "Base game + 5-6 player
  expansion" for larger groups, without polluting results with irrelevant
  expansions.
- Expansions whose base game isn't in the collection are never recommended.
- The thresholds will need tuning against real collections.
- Combining parameters from base game and expansion adds complexity to the
  recommendation logic, e.g. whether to use the base game's or the expansion's
  community polls for the combination.
