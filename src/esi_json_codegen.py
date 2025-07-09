import json

def parse_type_name(data_type: str):
    try:
        return {
            'BOOL': 'bool',
            'SINT': 'int8_t',
            'INT': 'int16_t',
            'DINT': 'int32_t',
            'USINT': 'uint8_t',
            'UINT': 'uint16_t',
            'UDINT': 'uint32_t',
            'REAL': 'float',
            'BYTE': 'uint8_t',
        }[data_type], 1
    except KeyError:
        if data_type.startswith('STRING('):
            # 'STRING(20)' -> 'char', 20
            length = int(data_type[7:-1])
            return 'char', length
        elif data_type.startswith('ARRAY'):
            # 'ARRAY [0..7] OF BYTE' -> 'uint8_t[8]'
            array_type = data_type.split('OF')[-1].strip()
            array_size = int(data_type.split('[')[1].split(']')[0].split('..')[1].strip()) + 1
            return parse_type_name(array_type)[0], array_size
        else:
            raise ValueError(f"Unknown data type: {data_type}")
    
def sanitize_name(name):
    return name.replace(" ", "_").replace("-", "_").replace("(", "_").replace(")", "_").replace('.', '').replace(':', '').replace('/', '_').replace('&', 'and')

def generate_c_struct(json_file, output_file):
    with open(json_file, "r") as f:
        sdo_objects = json.load(f)

    # Group objects by index
    grouped_objects = {}
    for obj in sdo_objects:
        index = obj["index"]
        if index not in grouped_objects:
            grouped_objects[index] = []
        grouped_objects[index].append(obj)
        
    # Generate C code
    c_code = ["#include <stdint.h>", "typedef struct SDO {"]
    for index, objects in grouped_objects.items():
        if len(objects) == 1 and objects[0]["subindex"] == 0:
            # Single subindex, no nested struct
            obj = objects[0]
            name = sanitize_name(obj['name'])
            c_type, arr_size = parse_type_name(obj["type"])
            arr_placeholder = f"[{arr_size}]" if arr_size > 1 else ""
            c_code.append(f"    {c_type} {name}{arr_placeholder}; // Index: 0x{index}, Subindex: {obj['subindex']}, {obj['bit_length']} bits")
        else:
            # Multiple subindices, use a nested struct
            struct_name = obj = objects[0]["name"].replace(" ", "_").replace("-", "_")
            c_code.append(f"    struct {{  // Index: 0x{index}")
            for obj in objects:
                sub_name = sanitize_name(obj["sub_name"])
                c_type, arr_size = parse_type_name(obj["type"])
                arr_placeholder = f"[{arr_size}]" if arr_size > 1 else ""
                c_code.append(f"        {c_type} {sub_name}{arr_placeholder}; // Subindex: {obj['subindex']}, {obj['bit_length']} bits")
            c_code.append(f"    }} {struct_name}; // Index: 0x{index}")

    c_code.append("} SDO;")

    # Write to output file
    with open(output_file, "w") as f:
        f.write("\n\n".join(c_code))

if __name__ == "__main__":
    
    import argparse
    parser = argparse.ArgumentParser(description="Generate C structs from JSON description.")
    parser.add_argument("json_file", help="Path to the input JSON file.")
    parser.add_argument("output_file", help="Path to the output C header file.")
    args = parser.parse_args()

    json_file = args.json_file
    output_file = args.output_file
    
    generate_c_struct(json_file, output_file)
    print(f"C structs generated in {output_file}")
    
    # try to include it and compile
    cmd = f'g++ -c {output_file} -o {output_file}.o'
    import os
    result = os.system(cmd)
    if result == 0:
        print("Compilation successful.")
    else:
        print("Compilation failed. Check the output for errors.")
        exit(1)