
import pandas as pd
from datasets import load_dataset
import os

def download_goemotions():
    print("Attempting to download 'monologg/goemotions-korean' from Hugging Face...")
    
    # Define output directory
    output_dir = os.path.dirname(os.path.abspath(__file__))

    try:
        # Try loading the dataset
        # Note: If this specific ID doesn't exist as a Dataset (only model), this might fail.
        # But monologg usually provides datasets.
        dataset = load_dataset("monologg/goemotions-korean")
        
        print("Download successful! Processing...")
        
        # Process and save splits
        for split in dataset.keys():
            df = dataset[split].to_pandas()
            output_file = os.path.join(output_dir, f"goemotions_korean_{split}.csv")
            df.to_csv(output_file, index=False)
            print(f"Saved {split} set to: {output_file} ({len(df)} rows)")
            
    except Exception as e:
        print(f"\nHugging Face load failed: {e}")
        print("\nFallback: Downloading raw files directly from monologg/GoEmotions-Korean GitHub...")
        
        # Fallback to direct download
        base_url = "https://raw.githubusercontent.com/monologg/GoEmotions-Korean/master/data"
        files = {
            "train": "train.tsv",
            "dev": "dev.tsv", 
            "test": "test.tsv"
        }
        
        for split_name, filename in files.items():
            try:
                url = f"{base_url}/{filename}"
                print(f"Downloading {url}...")
                # It's a TSV file with no header usually, or specific format.
                # Let's inspect first few lines if possible, or just download as text.
                # We can use pandas to read csv with tab separator.
                
                # We need to specify names if no header. 
                # According to GoEmotions original: text, labels, id
                # usage in monologg repo: text, label(indices)
                
                df = pd.read_csv(url, sep='\t', names=['text', 'labels', 'unk'], on_bad_lines='skip')
                # Check columns. If 'unk' is mostly empty/NaN, drop it.
                
                # Simplification: Just save as is to local CSV for the user to inspect
                output_file = os.path.join(output_dir, f"goemotions_korean_{split_name}.csv")
                df.to_csv(output_file, index=False)
                print(f"Saved {split_name} set to: {output_file} ({len(df)} rows)")
                
            except Exception as e2:
                print(f"Failed to download {split_name}: {e2}")

if __name__ == "__main__":
    download_goemotions()
