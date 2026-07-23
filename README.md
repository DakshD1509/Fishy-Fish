# Chess Engine (C++)

A modern, high-performance UCI chess engine with a bitboard board representation,
a full modern search stack, hand-crafted **and** NNUE evaluation, opening-book and
tablebase support — built to reach a strong rating on Lichess.

> Status: **under active development.** Phase 1 (board + move generation) in progress.

---

## Goals

- **UCI compliant**, drop-in for any chess GUI or the `lichess-bot` bridge.
- **Bitboard** board representation with **magic bitboard** sliding-piece attacks.
- Fast, exact **legal move generation** (validated by perft).
- A complete modern **search**: alpha-beta / PVS, iterative deepening, aspiration
  windows, quiescence, TT (Zobrist), null-move pruning, LMR, LMP, futility
  pruning, check/singular extensions, and rich move ordering.
- **Evaluation** with both a tapered hand-crafted term set and **NNUE** inference.
- **Polyglot** opening book and **Syzygy** endgame tablebases.
- Bullet/blitz-tuned time management; configurable hash and threads.

## Build

Requires a 64-bit C++20 compiler (GCC 13+ / Clang 16+ / MSVC 2022). On this
machine the toolchain is **WinLibs GCC 16 (UCRT, 64-bit)**.

```powershell
# Windows (PowerShell) — wrapper puts the compiler on PATH and runs make:
.\build.ps1            # release build -> bin\engine.exe
.\build.ps1 perft      # build, then run the perft self-test
.\build.ps1 clean
```

```bash
# Any platform with make + a modern g++ on PATH:
mingw32-make           # or: make
```

Build flags default to `-O3 -flto -march=native`. For a portable deploy binary
(e.g. a VPS with a different CPU) override the arch:

```
mingw32-make ARCH="-mavx2 -mbmi2 -mpopcnt"
```

## Project layout

```
src/
  types.hpp        Core enums, Move encoding, value constants (the shared contract)
  bitboard.*       Bitboard type, bit-manipulation helpers, geometry tables
  attacks.*        Leaper tables + magic-bitboard slider attacks
  zobrist.*        Zobrist hashing keys
  position.*       Board representation, make/unmake, legality, SEE, draw detection
  movegen.*        Legal / pseudo-legal move generation
  ...              (search, eval, nnue, uci — added in later phases)
  main.cpp         Entry point (perft driver now; UCI loop later)
Makefile           Build rules
build.ps1          Windows build wrapper (sets up the WinLibs toolchain)
```

## Startup / init order

Global tables must be initialized once, in this order, before using a `Position`:

```cpp
Attacks::init();     // magic tables + leaper attacks
Bitboards::init();   // geometry tables (uses slider attacks — must follow Attacks)
Position::init();    // Zobrist keys
```

## Testing

- **Perft**: `bin\engine.exe perft` runs the standard 6-position suite and checks
  node counts against known-correct values.

## Deploy as a Lichess bot (GitHub Actions)

The engine can run as a Lichess bot straight from GitHub Actions — no server
needed. The workflow at
[`.github/workflows/lichess-bot.yml`](.github/workflows/lichess-bot.yml) builds
the engine, installs the
[`lichess-bot`](https://github.com/lichess-bot-devs/lichess-bot) bridge, and
plays continuously.

1. **Make the repository public.** Public repos get free standard-runner
   minutes, which the always-on workflow relies on.
2. **Create a Lichess BOT token** with the `bot:play` scope at
   [lichess.org/account/oauth/token](https://lichess.org/account/oauth/token/create)
   (register the account as a bot first).
3. **Add it as a secret:** in the repo, **Settings → Secrets and variables →
   Actions → New repository secret** → name it `LICHESS_BOT_TOKEN`.
4. **Start the bot:** open the **Actions** tab → **lichess-bot** → **Run
   workflow**. The first run compiles the engine and downloads the NNUE net
   (~2–4 min), then begins playing.

The workflow keeps the bot online continuously: each job runs up to ~5h50m (under
GitHub's 6h cap) and a scheduled run every 5h queues behind it, taking over as the
previous job ends. Brief gaps are harmless — an idle Lichess bot loses no rating.
Engine tuning (threads, hash, time management, book) lives in
[`deploy/config.yml`](deploy/config.yml).

## Roadmap

| Phase | Scope |
|------|-------|
| 1 | Board, bitboards, magic attacks, make/unmake, legal movegen — **perft passing** |
| 2 | UCI protocol + iterative-deepening alpha-beta + quiescence |
| 3 | Full search stack (TT, ordering, PVS, NMP, LMR, LMP, futility, extensions, threads) |
| 4 | Evaluation: tapered hand-crafted terms + NNUE |
| 5 | Polyglot book, Syzygy tablebases, blitz/bullet time management |
| 6 | Lichess deployment (`lichess-bot`) + rating climb |
| 7 | Benchmark suite vs Stockfish + performance report |
