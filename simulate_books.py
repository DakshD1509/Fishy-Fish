import chess
import chess.engine
import chess.variant
import chess.polyglot
import multiprocessing
import random
import struct
import sys
import time
import os

ENGINE_PATH = "temp-fs/src/stockfish"
MAX_UNIQUE_MOVES = 2500000
CONCURRENCY = 5
DEPTH = 5
MAX_PLIES = 20

def make_polyglot_move(move):
    from_file = chess.square_file(move.from_square) if move.from_square else 0
    from_rank = chess.square_rank(move.from_square) if move.from_square else 0
    to_file = chess.square_file(move.to_square)
    to_rank = chess.square_rank(move.to_square)
    
    if move.drop:
        from_file = move.drop
        from_rank = 7
        promo = 4
    else:
        promo = 0
        if move.promotion:
            if move.promotion == chess.KNIGHT: promo = 1
            elif move.promotion == chess.BISHOP: promo = 2
            elif move.promotion == chess.ROOK: promo = 3
            elif move.promotion == chess.QUEEN: promo = 4
    
    return (promo << 12) | (from_rank << 9) | (from_file << 6) | (to_rank << 3) | to_file

def worker(variant_name, queue):
    engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    engine.configure({"Threads": 1, "Hash": 16})
    
    board_classes = {
        "atomic": chess.variant.AtomicBoard,
        "horde": chess.variant.HordeBoard,
        "racingkings": chess.variant.RacingKingsBoard,
        "crazyhouse": chess.variant.CrazyhouseBoard,
        "kingofthehill": chess.variant.KingOfTheHillBoard
    }
    BoardClass = board_classes.get(variant_name.lower(), chess.Board)
    
    while True:
        board = BoardClass()
        for ply in range(MAX_PLIES):
            if board.is_game_over():
                break
            try:
                info = engine.analyse(board, chess.engine.Limit(depth=DEPTH), multipv=3)
                if not info:
                    break
                
                weights = [3, 2, 1][:len(info)]
                choice = random.choices(info, weights=weights)[0]
                best_move = choice.get("pv", [None])[0]
                
                if not best_move:
                    break
                    
                key = chess.polyglot.zobrist_hash(board)
                move_int = make_polyglot_move(best_move)
                
                queue.put((key, move_int))
                board.push(best_move)
                
            except Exception as e:
                break
    engine.quit()

def simulate_variant(variant_name):
    print(f"[{variant_name}] Starting simulation with {CONCURRENCY} workers...")
    manager = multiprocessing.Manager()
    queue = manager.Queue()
    
    workers = []
    for _ in range(CONCURRENCY):
        p = multiprocessing.Process(target=worker, args=(variant_name, queue))
        p.daemon = True
        p.start()
        workers.append(p)
        
    entries = {}
    unique_moves = 0
    last_print = 0
    
    try:
        while unique_moves < MAX_UNIQUE_MOVES:
            key, move_int = queue.get()
            tup = (key, move_int)
            if tup not in entries:
                unique_moves += 1
            entries[tup] = entries.get(tup, 0) + 1
            
            if unique_moves - last_print >= 1000:
                print(f"[{variant_name}] {unique_moves}/{MAX_UNIQUE_MOVES} unique moves generated...")
                last_print = unique_moves
                
    except KeyboardInterrupt:
        print("Interrupted! Saving current progress...")
        
    for p in workers:
        p.terminate()
        
    print(f"[{variant_name}] Finished! Writing {len(entries)} entries to bridge/books/{variant_name}.bin")
    os.makedirs("bridge/books", exist_ok=True)
    with open(f"bridge/books/{variant_name}.bin", "wb") as f:
        for (key, move_int), weight in sorted(entries.items()):
            weight = min(weight, 65535)
            f.write(struct.pack('>QHHH', key, move_int, weight, 0))

if __name__ == "__main__":
    variants = ["horde", "racingkings", "crazyhouse", "kingofthehill"]
    for v in variants:
        simulate_variant(v)
