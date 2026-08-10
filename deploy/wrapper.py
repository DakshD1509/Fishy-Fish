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

def main():
    # 1. Read 'uci' from python-chess
    line = sys.stdin.readline()
    if line.strip() != 'uci':
        sys.exit(1)
    
    # 2. Spawn Fairy-Stockfish briefly to get the options
    # We use Fairy-Stockfish because it advertises the UCI_Variant option
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
    
    # 3. Buffer options until 'isready'
    options = []
    variant = "standard"
    while True:
        line = sys.stdin.readline()
        if not line:
            return
        line_str = line.strip()
        if line_str == "isready":
            break
        elif line_str.startswith("setoption name UCI_Variant value "):
            variant = line_str.split("value ", 1)[1].strip().lower()
        elif line_str.startswith("setoption name UCI_Chess960 value true"):
            variant = "chess960"
        
        options.append(line)
        
    is_standard = variant in ["standard", "chess", "normal"]
    binary = "./stockfish" if is_standard else "./fairy-stockfish"
    
    # 4. Start the correct engine
    engine = subprocess.Popen([binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    engine.stdin.write(b"uci\n")
    engine.stdin.flush()
    
    # Ignore its uci output since we already sent one
    read_until_uciok(engine)
    
    # 5. Replay the options
    for opt in options:
        engine.stdin.write(opt.encode())
    engine.stdin.flush()
    
    # Send isready
    engine.stdin.write(b"isready\n")
    engine.stdin.flush()
    
    # 6. Pipe threads to proxy the rest of the communication
    def pump_out():
        while True:
            data = engine.stdout.read(1)
            if not data:
                break
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
            
    def pump_in():
        while True:
            data = sys.stdin.buffer.read(1)
            if not data:
                break
            engine.stdin.write(data)
            engine.stdin.flush()
            
    t1 = threading.Thread(target=pump_out)
    t2 = threading.Thread(target=pump_in)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

if __name__ == "__main__":
    main()
