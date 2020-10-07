#!/bin/bash

wget https://ftp.ncbi.nlm.nih.gov/pub/lu/LitCovid/litcovid2pubtator.json.gz -P data/
wget ftp://nlmpubs.nlm.nih.gov/online/mesh/MESH_FILES/asciimesh/c2020.bin -P data/
wget ftp://nlmpubs.nlm.nih.gov/online/mesh/MESH_FILES/asciimesh/d2020.bin -P data/
wget ftp://nlmpubs.nlm.nih.gov/online/mesh/MESH_FILES/asciimesh/q2020.bin -P data/
gunzip data/*.gz
