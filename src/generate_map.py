from lxml import etree
import pickle
import os
from loguru import logger
import tqdm

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

def build_drug_name_to_id_map(xml_path: str, save_output: bool = True):
    """
    Build a map from drug name to drugbank id. Iterate through the XML file and extract the drugbank id and name for each drug.
    Args:
        xml_path (str): Path to the drugbank xml file
        save_output (bool, optional): Whether to save the output to a pickle file. Defaults to True.
    Returns:
        dict: A dictionary mapping drug names to drugbank ids
    """
    logger.info(f"Building drug name to id map from {xml_path}")
    ns = {'db': 'http://www.drugbank.ca'}
    name_to_id = {}

    # Iterate through the tree
    context = etree.iterparse(xml_path, events=('end',))
    for event, elem in tqdm.tqdm(context):
        if elem.tag == '{http://www.drugbank.ca}drug':
            # Get the drugbank id
            drugbank_id = elem.find('db:drugbank-id', ns)
            if drugbank_id is not None:
                # Get the name
                name = elem.find('db:name', ns)
                if name is not None:
                    name_to_id[name.text.lower()] = drugbank_id.text
            elem.clear()
    logger.info(f"Built drug name to id map with {len(name_to_id)} entries")

    # Save the map to a pickle file
    if save_output:
        src_dir = get_src_dir()
        saved_outputs_dir = os.path.join(src_dir, 'saved_outputs')
        os.makedirs(saved_outputs_dir, exist_ok=True)
        
        # Check if the file exists. If it does, add a suffix to the filename
        if os.path.exists(os.path.join(saved_outputs_dir, 'drug_name_to_id.pkl')):
            suffix = 1
            while os.path.exists(os.path.join(saved_outputs_dir, f'drug_name_to_id_{suffix}.pkl')):
                suffix += 1
            output_path = os.path.join(saved_outputs_dir, f'drug_name_to_id_{suffix}.pkl')
            with open(output_path, 'wb') as f:
                pickle.dump(name_to_id, f)
            logger.info(f"Saved drug name to id map to {output_path}")
        else:
            output_path = os.path.join(saved_outputs_dir, 'drug_name_to_id.pkl')
            with open(output_path, 'wb') as f:
                pickle.dump(name_to_id, f)
            logger.info(f"Saved drug name to id map to {output_path}")
    else:
        logger.info(f"Not saving drug name to id map")
    return name_to_id

if __name__ == '__main__':
    # Get the src directory
    src_dir = get_src_dir()
    # Default xml_path to drugbank.xml
    xml_path = os.path.join(src_dir, 'data', 'full_database.xml')
    name_to_id = build_drug_name_to_id_map(xml_path, save_output=True)