import pandas as pd
import os
import sqlite3
import sys

# Add project root to path to allow imports if needed, though this script is self-contained mostly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.core.config import get_settings

def clean_currency(value):
    """Removes currency symbols and converts to float."""
    if isinstance(value, str):
        return float(value.replace('$', '').replace(',', '').strip())
    return value

def load_data():
    settings = get_settings()
    data_dir = "data/raw"
    db_path = settings.DB_PATH
    
    files = {
        "activities-web.csv": "proyectos",
        "procesos_competitivos.csv": "licitaciones",
        "adjudicatarios_psd.csv": "adjudicaciones"
    }

    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)

    for filename, table_name in files.items():
        file_path = os.path.join(data_dir, filename)
        if not os.path.exists(file_path):
            print(f"Warning: File {filename} not found in {data_dir}. Skipping.")
            continue
        
        print(f"Processing {filename} -> {table_name}...")
        try:
            # Try common encodings
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin-1')

            # Naive currency cleanup - we apply it to object columns that look like currency
            # This is a general euristics for the scaffold. In prod, column names should be explicit.
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Check first non-null value
                    sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else ""
                    if isinstance(sample, str) and ('$' in sample):
                        print(f"  Cleaning currency column: {col}")
                        df[col] = df[col].apply(clean_currency)
            
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"  Loaded {len(df)} rows into '{table_name}'.")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    conn.close()
    print("ETL process completed.")

if __name__ == "__main__":
    load_data()
