# current script directory
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR" 

# generate somanet
echo "Generating SOMANET CiA 402 files..."
python3 ../src/esi_xml_to_json.py SOMANET_CiA_402.xml
python3 ../src/esi_json_codegen.py SOMANET_CiA_402.xml.json SOMANET_CiA_402.h

# generate everest
echo "Generating Everest XCR files..."
python3 ../src/esi_xml_to_json.py eve-e-xcr-e_esi_2.7.5.xml
python3 ../src/esi_json_codegen.py eve-e-xcr-e_esi_2.7.5.xml.json eve-e-xcr-e_esi_2.7.5.h