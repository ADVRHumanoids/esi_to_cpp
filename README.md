# esi_to_cpp

Generate SDO as C++ nested ``struct`` from EtherCAT ESI file.

```bash
python3 esi_xml_to_json.py esi.xml  # produces esi.xml.json``
python3 esi_json_codegen.py esi.xml.json esi.h  # generate header with sdo struct definition``
python3 esi_json_codegen_objd.py esi.xml.json esi.h  # add the "objd" struct to the header file``
```

## Example (Synapticon CIRCULO, Novanta EVEREST XCR)

```bash
bash example/generate.bash
```
