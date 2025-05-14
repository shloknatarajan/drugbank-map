import pickle
import os
from typing import Dict, List, Tuple, Union, Optional
import difflib
import re
from fuzzywuzzy import fuzz, process
from loguru import logger

# Get the path to the src directory
def get_src_dir():
    """Get the path to the src directory regardless of where the script is run from."""
    # If running from root, src is in the current directory
    if os.path.exists(os.path.join(os.getcwd(), 'src')):
        return os.path.join(os.getcwd(), 'src')
    # If running from within src directory
    elif os.path.basename(os.getcwd()) == 'src':
        return os.getcwd()
    # Default case
    else:
        return os.getcwd()

def load_drug_name_map(filepath: Optional[str] = None) -> Dict[str, str]:
    """
    Load the drug name to id map from a pickle file.
    
    Args:
        filepath (str, optional): Path to the pickle file. If None, will try to find the most recent
                                  drug_name_to_id file in saved_outputs directory.
    
    Returns:
        dict: A dictionary mapping drug names to drugbank ids
    """
    if filepath is None:
        logger.warning("No filepath provided. Trying to find the most recent drug_name_to_id pkl file")
        # Get the src directory
        src_dir = get_src_dir()
        saved_outputs_dir = os.path.join(src_dir, 'saved_outputs')
        
        # Try to find the most recent drug_name_to_id file
        if os.path.exists(saved_outputs_dir):
            files = [f for f in os.listdir(saved_outputs_dir) if f.startswith('drug_name_to_id') and f.endswith('.pkl')]
            if not files:
                raise FileNotFoundError(f"No drug_name_to_id pickle files found in {saved_outputs_dir}")
                
            # Sort by creation time (newest first)
            files.sort(key=lambda x: os.path.getctime(os.path.join(saved_outputs_dir, x)), reverse=True)
            filepath = os.path.join(saved_outputs_dir, files[0])
        else:
            raise FileNotFoundError(f"Saved maps directory not found at {saved_outputs_dir}")
    
    logger.info(f"Loading drug name to id map from {filepath}")
    with open(filepath, 'rb') as f:
        drug_map = pickle.load(f)
    
    return drug_map

def fuzzy_search_drug(query: str, 
                      drug_map: Dict[str, str],
                      method: str = "fuzzywuzzy",
                      threshold: float = 70.0,
                      max_results: int = 5) -> List[Tuple[str, str, float]]:
    """
    Search for a drug name using fuzzy matching.
    
    Args:
        query (str): The drug name to search for
        drug_map (dict): Dictionary mapping drug names to drugbank ids
        method (str): The matching method to use. Options: 
                      "fuzzywuzzy" - Uses fuzzywuzzy's process.extract
                      "difflib" - Uses difflib's get_close_matches
                      "regex" - Uses regex partial matching
        threshold (float): Minimum similarity score (0-100) for matches to be returned
        max_results (int): Maximum number of results to return
    
    Returns:
        list: List of tuples containing (drug_name, drugbank_id, similarity_score)
    """
    query = query.lower().strip()
    results = []
    
    if method == "fuzzywuzzy":
        # Use fuzzywuzzy to find matches
        matches = process.extract(query, drug_map.keys(), 
                                  scorer=fuzz.token_sort_ratio, 
                                  limit=max_results)
        for drug_name, score in matches:
            if score >= threshold:
                results.append((drug_name, drug_map[drug_name], score))
    
    elif method == "difflib":
        # Use difflib to find matches
        drug_names = list(drug_map.keys())
        matches = difflib.get_close_matches(query, drug_names, n=max_results, cutoff=threshold/100)
        
        # Calculate similarity scores
        for drug_name in matches:
            similarity = difflib.SequenceMatcher(None, query, drug_name).ratio() * 100
            results.append((drug_name, drug_map[drug_name], similarity))
            
        # Sort by similarity score
        results.sort(key=lambda x: x[2], reverse=True)
    
    elif method == "regex":
        # Build a simple regex pattern for partial matching
        pattern = f".*{re.escape(query)}.*"
        regex = re.compile(pattern)
        
        # Find matches
        matches = []
        for drug_name in drug_map.keys():
            if regex.match(drug_name):
                # Calculate similarity using difflib
                similarity = difflib.SequenceMatcher(None, query, drug_name).ratio() * 100
                if similarity >= threshold:
                    matches.append((drug_name, similarity))
        
        # Sort by similarity and take top matches
        matches.sort(key=lambda x: x[1], reverse=True)
        for drug_name, score in matches[:max_results]:
            results.append((drug_name, drug_map[drug_name], score))
    
    else:
        raise ValueError(f"Unknown method: {method}. Choose from 'fuzzywuzzy', 'difflib', or 'regex'")

    # Sort by similarity score
    results.sort(key=lambda x: x[2], reverse=True)
    # If no results, return empty list
    if not results:
        return [('', '', 0.0)]
    return results

def search_drug(query: str, 
                drug_map: Optional[Dict[str, str]] = None,
                method: str = "fuzzywuzzy",
                threshold: float = 70.0,
                max_results: int = 5) -> List[Tuple[str, str, float]]:
    """
    Convenience function that loads the drug map if not provided and performs a fuzzy search.
    
    Args:
        query (str): The drug name to search for
        drug_map (dict, optional): Dictionary mapping drug names to drugbank ids. If None, will load it.
        method (str): The matching method to use
        threshold (float): Minimum similarity score (0-100) for matches
        max_results (int): Maximum number of results to return
    
    Returns:
        list: List of tuples containing (drug_name, drugbank_id, similarity_score)
    """
    if drug_map is None:
        drug_map = load_drug_name_map()
    
    return fuzzy_search_drug(query, drug_map, method, threshold, max_results)

if __name__ == "__main__":
    # Example usage
    src_dir = get_src_dir()
    filepath = os.path.join(src_dir, "saved_outputs", "drug_name_to_id.pkl")
    query = "metformin"
    logger.info(f"Searching for: {query}")
    
    # Load the drug map once
    drug_map = load_drug_name_map(filepath)
    
    # Try different methods
    for method in ["fuzzywuzzy", "difflib", "regex"]:
        logger.info(f"\nMethod: {method}")
        results = fuzzy_search_drug(query, drug_map, method=method)
        for drug_name, drugbank_id, score in results:
            logger.info(f"  {drug_name} (ID: {drugbank_id}) - Score: {score:.1f}")

    print(f"Results: {results}")