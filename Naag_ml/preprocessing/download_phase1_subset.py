import os
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

manifest_path = "datasets/metadata/snakeclef_phase1_manifest.csv"
target_dir = "datasets/raw/snakeclef"

df = pd.read_csv(manifest_path)
os.makedirs(target_dir, exist_ok=True)

# iNaturalist image resolution base format
def download_image(row):
    file_rel_path = os.path.normpath(row["file_path"])
    save_path = os.path.join(target_dir, file_rel_path)
    
    # Agar already downloaded hai toh skip karo
    if os.path.exists(save_path):
        return True
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # iNaturalist CDN fallback using observation/photo ID from filename
    photo_id = os.path.splitext(os.path.basename(file_rel_path))[0]
    img_url = f"https://inaturalist-open-data.s3.amazonaws.com/photos/{photo_id}/medium.jpg"
    
    try:
        r = requests.get(img_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False

print(f"Downloading Phase-1 images to {target_dir}...")
rows = [row for _, row in df.iterrows()]

# Multi-threaded fast download (16 threads)
with ThreadPoolExecutor(max_workers=16) as executor:
    results = list(tqdm(executor.map(download_image, rows), total=len(rows)))

print(f"Downloaded {sum(results)} / {len(rows)} images successfully.")