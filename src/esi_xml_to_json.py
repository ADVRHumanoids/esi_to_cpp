import xml.etree.ElementTree as ET
import logging
import json

# debug
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_esi_to_sdo_list_with_formatted_name(xml_file_name):
    sdo_list = []
    sdo_idx_subidx = set()
    try:
        with open(xml_file_name) as xml_file:
            tree = ET.parse(xml_file)
            
        root = tree.getroot()

        # Locate the <DataTypes> tags
        datatypes_tag = root.find(".//DataTypes")

        if datatypes_tag is None:
            raise KeyError("Warning: <DataTypes> tag not found in the ESI file.")

        # Build a map of DataTypes for quick lookup
        datatype_map = {}
        for datatype in root.findall(".//DataType"):
            datatype_name = datatype.findtext("Name")
            if datatype_name:
                datatype_map[datatype_name] = datatype

        # Process each <Object>
        for obj in root.findall(".//Object"):
            
            # Extract the index
            object_code = obj.findtext("Index")
            if object_code is None or not object_code.startswith("#x"):
                logging.warning(f"Skipping object with missing or invalid <Index>: {ET.tostring(obj, encoding='unicode')}")
                continue

            index = object_code[2:]
            
            # Validate the index
            try:
                int(index, 16)
            except ValueError:
                raise ValueError(f"Warning: Invalid object code '{object_code}'")

            # Extract the base name
            base_name = obj.findtext("Name", default="Unnamed")

            logging.info(f"Processing object: {base_name} (0x{index})")

            # Extract the access flags
            access = obj.findtext("Flags/Access", default="UNKNOWN")

            # Extract the data type and bit size
            data_type_elem = obj.find("Type")
            data_type_text = data_type_elem.text if data_type_elem is not None else "UNKNOWN"
            
            bit_length_elem = obj.find("BitSize")
            bit_length = int(bit_length_elem.text) if bit_length_elem is not None else None
            
            # Get subitems
            subitems = obj.findall("Info/SubItem")
            
            # Get datatype
            datatype = datatype_map[data_type_text]
            
            # Datatype/Subitem
            d_subitems = datatype.findall("SubItem")
            
            # print(datatype)
            # print(subitems)
            # print(d_subitems)
            
            subitem_types = [] if subitems else [data_type_text]
            subitem_names = [] if subitems else ['']
            subitem_bitsize = [] if subitems else [bit_length]
            subitem_access = [] if subitems else [access]
            
            # Subindex name is either stored in Name or Info/DisplayName
            for s in subitems:
                sname = s.findtext("Info/DisplayName") or s.findtext("Name")
                subitem_names.append(sname)
            
            # Resolve subitem datatypes
            for d in d_subitems:
                
                dtype_name = d.findtext("Type")
                dtype = datatype_map[dtype_name]
                
                daccess = d.findtext("Flags/Access", default='UNKNOWN')
                
                # if type is array, get number of elements from ArrayInfo
                nelem = int(dtype.findtext("ArrayInfo/Elements", default="1"))
                
                # if type is array, get base type; otherwise type is the type name itself
                base_type = dtype.findtext("BaseType", default=dtype_name)
                
                # get bit size
                bit_size = int(datatype_map[base_type].findtext("BitSize", default="0"))
                
                # save
                subitem_types.extend([base_type] * nelem)
                subitem_bitsize.extend([bit_size] * nelem)
                subitem_access.extend([daccess] * nelem)
                    
            # print(subitem_types)
            # print(subitem_names)
            # print(subitem_bitsize)
            si = 0
            for st, sn, sb, sa in zip(subitem_types, subitem_names, subitem_bitsize, subitem_access):
                
                if (index, si) in sdo_idx_subidx:
                    logging.warning(f"Duplicate SDO entry found: Index 0x{index}, Subindex {si}. Skipping.")
                    si += 1
                    continue
                
                sdo_idx_subidx.add((index, si))
       
                sdo_list.append({
                    'name': base_name,
                    'sub_name': sn,
                    'index': index,
                    'subindex': si,
                    'type': st,
                    'bit_length': sb,
                    'access': sa
                })
                
                si += 1

    except ET.ParseError as e:
        print(f"Error: Failed to parse XML file: {e}")
    
    # disanbiguate names by appendind index in case of duplicates
    names_cache = set()
    for sdo in sdo_list:    
        if sdo['name'] in names_cache:
            # duplicate found, fix all occurrences
            for sdo2 in sdo_list:
                if sdo2['name'] == sdo['name']:
                    sdo2['name'] += f"_{sdo2['index']}"
        else:
            # first occurrence, store it
            names_cache.add(sdo['name'])
    
    return sdo_list

if __name__ == "__main__":
    # xml_file_name = "SOMANET_CiA_402.xml"
    import sys
    xml_file_name = sys.argv[1]
    sdo_objects = parse_esi_to_sdo_list_with_formatted_name(xml_file_name)
    
    # dump json
    with open(f"{xml_file_name}.json", "w") as json_file:
        json.dump(sdo_objects, json_file, indent=4)