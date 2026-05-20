import urllib.request
import os
import tarfile
from pathlib import Path

def progress(count, block_size, total_size):
    if total_size > 0:
        percent = min(int(count * block_size * 100 / total_size), 100)
        mb_done = count * block_size / 1024 / 1024
        mb_total = total_size / 1024 / 1024
        print(f"\r  {percent}% — {mb_done:.1f}MB / {mb_total:.1f}MB",
              end="", flush=True)

def download_mpiigaze():
    dest_dir = Path("datasets/MPIIGaze")
    dest_dir.mkdir(parents=True, exist_ok=True)
    tar_path = Path("datasets/MPIIGaze.tar.gz")

    # Tentar URLs em ordem
    urls = [
        "http://datasets.d2.mpi-inf.mpg.de/MPIIGaze/MPIIGaze.tar.gz",
        "https://datasets.d2.mpi-inf.mpg.de/MPIIGaze/MPIIGaze.tar.gz",
    ]

    downloaded = False
    for url in urls:
        try:
            print(f"Tentando: {url}")
            urllib.request.urlretrieve(url, str(tar_path), progress)
            print("\nDownload concluído!")
            downloaded = True
            break
        except Exception as e:
            print(f"\nFalhou: {e}")
            continue

    if not downloaded:
        print("\nNenhuma URL funcionou.")
        print("Baixe manualmente em:")
        print("https://darus.uni-stuttgart.de/dataset.xhtml?persistentId=doi:10.18419/darus-3230")
        print(f"E salve como: {tar_path.absolute()}")
        return

    # Extrair
    print("Extraindo...")
    with tarfile.open(str(tar_path)) as tar:
        tar.extractall("datasets/")
    print("Extração concluída!")
    print(f"Dataset em: {dest_dir.absolute()}")

    # Remover tar.gz para economizar espaço
    tar_path.unlink()
    print("Arquivo .tar.gz removido.")

if __name__ == "__main__":
    download_mpiigaze()
