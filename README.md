# esi_to_cpp

Generate SDO as C++ nested ``struct`` from EtherCAT ESI file.

1. ``python3 esi_xml_to_json.py esi.xml  # produces esi.xml.json``
2. ``python3 esi_json_codegen.py esi.xml.json esi.h``


```bash
bash example/generate.bash
```
