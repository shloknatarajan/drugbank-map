from lxml import etree
import pickle
import sys
from loguru import logger

def build_drug_name_to_id_map(xml_path):
    logger.info(f"Building drug name to id map from {xml_path}")
    ns = {'db': 'http://www.drugbank.ca'}
    name_to_id = {}

    context = etree.iterparse(xml_path, events=('end',))
    for event, elem in context:
        if elem.tag == '{http://www.drugbank.ca}drug':
            drugbank_id = elem.find('db:drugbank-id', ns)
            if drugbank_id is not None:
                name = elem.find('db:name', ns)
                if name is not None:
                    name_to_id[name.text.lower()] = drugbank_id.text
            elem.clear()
    logger.info(f"Built drug name to id map with {len(name_to_id)} entries")
    return name_to_id

if __name__ == '__main__':
    xml_path = sys.argv[1]
    name_to_id = build_drug_name_to_id_map(xml_path)
    with open('drug_name_to_id.pkl', 'wb') as f:
        pickle.dump(name_to_id, f)
    logger.info(f"Saved drug name to id map to drug_name_to_id.pkl")