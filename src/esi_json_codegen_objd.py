import json
from esi_json_codegen import sanitize_name

def parse_type_name(data_type: str):
    try:
        return {
            'BOOL': 'ECT_BOOLEAN',
            'SINT': 'ECT_INTEGER8',
            'INT': 'ECT_INTEGER16',
            'DINT': 'ECT_INTEGER32',
            'USINT': 'ECT_UNSIGNED8',
            'UINT': 'ECT_UNSIGNED16',
            'UDINT': 'ECT_UNSIGNED32',
            'REAL': 'ECT_REAL32',
            'BYTE': 'ECT_UNSIGNED8',  # CHECK THIS!
        }[data_type]
    except KeyError:
        if data_type.startswith('STRING('):
            return 'ECT_VISIBLE_STRING'
        elif data_type.startswith('ARRAY'):
            # 'ARRAY [0..7] OF BYTE' -> 'uint8_t[8]'
            array_type = data_type.split('OF')[-1].strip()
            array_size = int(data_type.split('[')[1].split(']')[0].split('..')[1].strip()) + 1
            return parse_type_name(array_type)
        else:
            raise ValueError(f"Unknown data type: {data_type}")

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
    preample = """

#ifdef ESI_TO_CPP_TEST
#define SDO_VAR_NAME sdo
#define ECT_BOOLEAN 0x0
#define ECT_INTEGER8 0x1
#define ECT_INTEGER16 0x2
#define ECT_INTEGER32 0x3
#define ECT_UNSIGNED8 0x4
#define ECT_UNSIGNED16 0x5
#define ECT_UNSIGNED32 0x6
#define ECT_REAL32 0x7
#define ECT_VISIBLE_STRING 0x8
#define ATYPE_RO 0x01
#define ATYPE_WO 0x02
#define ATYPE_RW 0x03
#define ATYPE_UNKNOWN 0x00

typedef struct {
    int index;
    int subindex;
    int datatype;
    int bitlength;
    int access;
    const char * name;
    void * data;
} objd_t;

SDO sdo;
#endif  // ESI_TO_CPP_TEST

static const objd_t source_SDOs[] = {
"""
    c_code = [preample]
    
    for index, objects in grouped_objects.items():
        c_code.append(f"  // Index: 0x{index}")
        for obj in objects:
            subindex = obj["subindex"]
            datatype = parse_type_name(obj["type"])
            bitlength = obj["bit_length"]
            access = f'ATYPE_{obj["access"].upper()}'
            name = sanitize_name(obj["name"])
            subname = sanitize_name(obj["sub_name"]) if len(objects) > 1 else ""
            name = f"{name}.{subname}" if subname else name
            c_code.append(f'  {{ 0x{index}, {subindex}, {datatype}, {bitlength}, {access}, "{name}", (void*)&SDO_VAR_NAME.{name} }},')

    c_code.append("};")

    # Write to output file
    with open(output_file, "a") as f:
        f.write("\n".join(c_code))

if __name__ == "__main__":
    
    import argparse
    parser = argparse.ArgumentParser(description="Generate C structs from JSON description.")
    parser.add_argument("json_file", help="Path to the input JSON file.")
    parser.add_argument("sdo_header_file", help="Path to the SDO header file.")
    args = parser.parse_args()

    json_file = args.json_file
    sdo_header_file = args.sdo_header_file

    generate_c_struct(json_file, sdo_header_file)
    print(f"C structs generated in {sdo_header_file}")

    # try to include it and compile
    cmd = f'g++ -c {sdo_header_file} -o {sdo_header_file}.o -DESI_TO_CPP_TEST'
    import os
    result = os.system(cmd)
    if result == 0:
        print("Compilation successful.")
    else:
        print("Compilation failed. Check the output for errors.")
        exit(1)