"""
Parses the WHO essential medicines list and returns a list of drug names and drugbank ids.
"""

import os
import pandas as pd
from fuzzy_search import fuzzy_search_drug, load_drug_name_map
from generate_map import get_src_dir
from typing import List, Dict, Tuple
from tqdm import tqdm
from loguru import logger

def parse_who_essential_medicines(filepath: str = None) -> List[str]:
    if filepath is None:
        src_dir = get_src_dir()
        filepath = os.path.join(src_dir, "data", "who_essentials", "who_essential_medicines.txt")
    with open(filepath, "r") as f:
        lines = f.readlines()
    return lines

def get_closest_match(drug_name: str, drug_map: Dict[str, str]) -> Tuple[str, str, float]:
    return fuzzy_search_drug(drug_name, drug_map, method="fuzzywuzzy")[0]

def main():
    drug_map = load_drug_name_map()
    who_essential_medicines = parse_who_essential_medicines()

    # Collect all data
    logger.info("Getting closest matches")
    data = []
    for drug_name in tqdm(who_essential_medicines):
        closest_name, drugbank_id, score = get_closest_match(drug_name, drug_map)
        data.append({
            "drug_name": drug_name,
            "closest_name": closest_name,
            "drugbank_id": drugbank_id,
            "score": score
        })
    
    # Create DataFrame once with all data
    logger.info("Creating DataFrame")
    df = pd.DataFrame(data)

    # save as a csv
    logger.info("Saving to csv")
    df.to_csv(os.path.join(get_src_dir(), "saved_outputs", "who_essentials", "who_matches.csv"), index=False)

if __name__ == "__main__":
    main()

    