import os
import urllib.request
import zipfile
import shutil

def download_stockfish():
    url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_18/stockfish-windows-x86-64-avx2.zip"
    zip_path = "bridge/engines/stockfish.zip"
    extract_dir = "bridge/engines/"
    
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
        
    print("Downloading Stockfish 18 from GitHub Releases...")
    urllib.request.urlretrieve(url, zip_path)
    
    print("Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        
    extracted_exe = os.path.join(extract_dir, "stockfish", "stockfish-windows-x86-64-avx2.exe")
    target_exe = os.path.join(extract_dir, "stockfish.exe")
    
    if os.path.exists(extracted_exe):
        if os.path.exists(target_exe):
            os.remove(target_exe)
        os.rename(extracted_exe, target_exe)
        print("Stockfish 18 downloaded and installed to", target_exe)
        
        # Cleanup
        shutil.rmtree(os.path.join(extract_dir, "stockfish"))
    else:
        print("Could not find the extracted executable. Please check the ZIP contents manually.")
        
    os.remove(zip_path)

if __name__ == "__main__":
    download_stockfish()
