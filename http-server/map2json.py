#!/usr/bin/env python3
'''Converts a geometry map file with EPSG:3857 projection into JSON format and writes the ouput in data/countries.json.
   The original comes from https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/ but was
   later re-projected into EPSG:3857 by David Mills: https://github.com/dmillz/misc/blob/master/shapefiles/ne_10m_admin_0_countries_lakes-EPSG_3857.zip
   That projection, also called WGS 84 and Pseudo-Mercator, are used by most online mapping systems.
   
   The file data/countries.json is used by the web server to chart different countries.'''

import geopandas as gpd

shapefile = 'data/ne_10m_admin_0_countries_lakes-EPSG_3857.shp'
gdf = gpd.read_file(shapefile)
gdf = gdf[(gdf['type']=='Country')|(gdf['type']=='Sovereign country')|(gdf['type']=='Indeterminate')]
gdf = gdf[['geounit', 'adm0_a3', 'geometry']]
gdf.columns = 'country country_code geometry'.split()
t = gdf.to_json()
open('data/countries.json', 'w').write(gdf.to_json())
