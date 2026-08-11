import sys
import subprocess
import threading

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

def wait_for_readyok(proc):
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        if line.strip() == b'readyok':
            break

def main():
    line = sys.stdin.buffer.readline().decode()
    if not line or line.strip() != 'uci':
        sys.exit(1)
        
    sf = subprocess.Popen(["./stockfish"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    fs = subprocess.Popen(["./fairy-stockfish"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    
    sf.stdin.write(b"uci\n")
    sf.stdin.flush()
    fs.stdin.write(b"uci\n")
    fs.stdin.flush()
    
    read_until_uciok(sf)
    fs_lines = read_until_uciok(fs)
    
    # We forward Fairy-Stockfish's uci output so lichess-bot sees all variant options
    for l in fs_lines:
        sys.stdout.buffer.write(l)
    sys.stdout.buffer.flush()
    
    active_engine = sf
    
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            break
            
        line_str = line.decode().strip()
        
        if line_str == "isready":
            sf.stdin.write(b"isready\n")
            sf.stdin.flush()
            fs.stdin.write(b"isready\n")
            fs.stdin.flush()
            
            wait_for_readyok(sf)
            wait_for_readyok(fs)
            
            sys.stdout.buffer.write(b"readyok\n")
            sys.stdout.buffer.flush()
            
        elif line_str.startswith("setoption name UCI_Variant value "):
            variant = line_str.split("value ", 1)[1].strip().lower()
            is_standard = variant in ["standard", "chess", "normal"]
            active_engine = sf if is_standard else fs
            
            sf.stdin.write(line)
            sf.stdin.flush()
            fs.stdin.write(line)
            fs.stdin.flush()
            
        elif line_str.startswith("setoption name UCI_Chess960 value true"):
            is_standard = False
            active_engine = fs
            
            sf.stdin.write(line)
            sf.stdin.flush()
            fs.stdin.write(line)
            fs.stdin.flush()
            
        elif line_str.startswith("setoption") or line_str == "ucinewgame":
            sf.stdin.write(line)
            sf.stdin.flush()
            fs.stdin.write(line)
            fs.stdin.flush()
            
        elif line_str == "quit":
            sf.stdin.write(b"quit\n")
            sf.stdin.flush()
            fs.stdin.write(b"quit\n")
            fs.stdin.flush()
            sys.exit(0)
            
        elif line_str.startswith("position") or line_str.startswith("go") or line_str.startswith("eval"):
            # Start forwarding commands to the active engine
            active_engine.stdin.write(line)
            active_engine.stdin.flush()
            break
            
    def pump_out():
        while True:
            data = active_engine.stdout.readline()
            if not data:
                break
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
            
    def pump_in():
        while True:
            data = sys.stdin.buffer.readline()
            if not data:
                break
            active_engine.stdin.write(data)
            active_engine.stdin.flush()
            
    t1 = threading.Thread(target=pump_out, daemon=True)
    t2 = threading.Thread(target=pump_in, daemon=True)
    t1.start()
    t2.start()
    
    active_engine.wait()
    sys.exit(active_engine.returncode)

if __name__ == "__main__":
    main()
