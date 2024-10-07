# Comparing metadata model

Comparing the metadata from the spreadsheets of Demokritos with the implemented fields

DMKR refers to the spreadsheet of demokritos, IMPL refers to the implementation on 
https://api.aiod.eu/docs.

## Usage

I got a json from Demokritos with the fields that they have defined. It's located in the `data/` 
dir. `scripts/download_implemented_fields.sh` downloads `implemented.json` from our production 
server.

`scripts/create_comparison.py` creates a couple of files in the output directory. These files 
contain all fields of DMKR and the IMPL. 

Next step is to do perform a manual inspection of the differences, while writing comments. The 
manual inspections can be found in the `with_comments` dir.


## General issues:
- Demokritos uses camelCase for property names, implementation uses snake_case. camelCase would 
  be consistent with schema.org, so it would probably be better to change it. Still, it will 
  result in a lot of changes for all services that rely on the API. To be discussed.
- Some parent references of Demokritos are not consistent: referencing "KnowledgeAsset" or 
  "Knowledgeasset"
- In general, the description of the implementation tends to be more informative. I'd suggest 
  updating the descriptions of Demokritos towards the implementation's descriptions, and letting 
  the development team know if you'd suggest any changes (I've ignored most descriptions now).
- In general, examples and constraints are not part of Demokritos descriptions. The examples and 
  constraints of IMPL can be found in the "extra" column.
