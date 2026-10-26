"""Quick check: is the raw dataset in the right place and readable?"""

import sys

from utils import RAW_FILE, load_raw_data


def main() -> int:
    try:
        df = load_raw_data()
    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        return 1
    except Exception as error:  # unreadable or corrupted file
        print(f"ERROR: could not read {RAW_FILE}: {error}")
        return 1

    print("File loaded successfully.")
    print(f"Rows (records): {df.shape[0]:,}")
    print(f"Columns       : {df.shape[1]}")
    print("\nColumn names:")
    for column in df.columns:
        print(f"  - {column}")
    print("\nFirst 3 rows:")
    print(df.head(3).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
