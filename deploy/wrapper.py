import sys
import subprocess
import threading
import time

def read_until_uciok(proc):
    lines = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        lines.append(line)
        if line.strip() == b'uciok':
            break
    return lines

def read_until_readyok(proc):
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        if line.strip() == b'readyok':
            break

def main():
    # 1. Read 'uci' from python-chess
    line = sys.stdin.buffer.readline().decode()
    if not line:
        sys.exit(1)
    if line.strip() != 'uci':
        sys.exit(1)
    
    # 2. Spawn Fairy-Stockfish briefly to get the options
    dummy = subprocess.Popen(["./fairy-stockfish"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    dummy.stdin.write(b"uci\n")
    dummy.stdin.flush()
    
    # Forward its uci output to lichess-bot so lichess-bot sees all the options
    uci_lines = read_until_uciok(dummy)
    for l in uci_lines:
        sys.stdout.buffer.write(l)
    sys.stdout.buffer.flush()
    
    dummy.terminate()
    dummy.wait()
    
    # 3. Buffer options until we see a command that requires the engine
    options = []
    variant = "standard"
    saw_ucinewgame = False
    
    while True:
        line = sys.stdin.buffer.readline().decode()
        if not line:
            return
        line_str = line.strip()
        
        if line_str == "isready":
            # Mock readyok so python-chess continues initialization
            sys.stdout.buffer.write(b"readyok\n")
            sys.stdout.buffer.flush()
            continue
            
        elif line_str.startswith("setoption name UCI_Variant value "):
            variant = line_str.split("value ", 1)[1].strip().lower()
            options.append(line)
            
        elif line_str.startswith("setoption name UCI_Chess960 value true"):
            variant = "chess960"
            options.append(line)
            
        elif line_str.startswith("setoption"):
            options.append(line)
            
        elif line_str == "ucinewgame":
            saw_ucinewgame = True
            
        elif line_str == "quit":
            sys.exit(0)
            
        else:
            # We received 'position', 'go', or something else. Spawn the actual engine!
            is_standard = variant in ["standard", "chess", "normal"]
            binary = "./stockfish" if is_standard else "./fairy-stockfish"
            
            engine = subprocess.Popen([binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            engine.stdin.write(b"uci\n")
            engine.stdin.flush()
            
            # Discard uciok from the real engine
            read_until_uciok(engine)
            
            # Send all buffered options
            for opt in options:
                engine.stdin.write(opt.encode())
            
            if saw_ucinewgame:
                engine.stdin.write(b"ucinewgame\n")
                
            engine.stdin.write(b"isready\n")
            engine.stdin.flush()
            
            # Wait for real engine to be ready
            read_until_readyok(engine)
            
            # Forward the command that triggered the spawn
            engine.stdin.write(line.encode())
            engine.stdin.flush()
            break
            
    # 6. Pipe threads to proxy the rest of the communication
    def pump_out():
        while True:
            data = engine.stdout.readline()
            if not data:
                break
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
            
    def pump_in():
        while True:
            data = sys.stdin.buffer.readline()
            if not data:
                break
            engine.stdin.write(data)
            engine.stdin.flush()
            
    t1 = threading.Thread(target=pump_out, daemon=True)
    t2 = threading.Thread(target=pump_in, daemon=True)
    t1.start()
    t2.start()
    engine.wait()
    sys.exit(engine.returncode)

if __name__ == "__main__":
    main()
