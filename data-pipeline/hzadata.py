import pandas as pd
import geopandas as gpd
import os
  
# Function to convert sq m to acres
m2acres = lambda x: x * 0.00024711

# Function to generate zone ID from state,
# jurisdiction name & abbreviated district name
def create_id(s, j, ad):
    s = str(s).upper()
    j = str(j).split('-')[0].strip().upper().split('/')[0]
    ad = str(ad).replace('-', '').replace(' ', '').upper()
    return f'{s}--{j}--{ad}'

def read_zoning_file(filepath):
    print("Filepath:", filepath)
    try:
        # Read GIS file into dataframe
        gdf = (gpd
               .read_file(filepath)
               .filter(['State', 'Jurisdiction', 'AbbreviatedDistrict', 'geometry'])
               .dropna(subset=['geometry']) # remove null geometries
               .to_crs('EPSG:4326') # set projection to WGS 84 (lat/lon)
              )
        # Rename districts with no names to "Not Zoned"

        gdf.AbbreviatedDistrict = gdf.AbbreviatedDistrict.fillna('Not Zoned')
        # Create an ID column that combines jurisdiction and zoning name
        gdf['id'] = gdf.apply(
            lambda r: create_id(r.State, r.Jurisdiction, r.AbbreviatedDistrict), axis=1
        )

        # Calculate area (in acres) for each geometry
        gdf['ZoneAcres'] = (gdf
                            .to_crs('EPSG:6933') # reproject to equal area
                            .geometry.area
                            .apply(m2acres)
                           )

        # Calculate total area by zone
        total_area_by_zone = (gdf
                              .groupby('id')
                              ['ZoneAcres']
                              .sum()
                             )
        # Combine (dissolve) geometries by zone
        gdf = gdf.dissolve(by='id')
        gdf.ZoneAcres = total_area_by_zone # assign new total areas

        # Move `id` from index to column
        gdf = gdf.reset_index()

        return gdf
               
    except:
        print(f"Error when reading {filepath}.")

# Folder with all GIS files
zoning_folder = './gis'

# Read the folder to get all filenames (ignore hidden files)
zoning_files = [x for x in os.listdir(zoning_folder) if x[-5:] == '.gpkg' ]

# Read all zones into a single pandas dataframe
gdfs = [ read_zoning_file(f"{zoning_folder}/{filename}")
         for filename in zoning_files ]

combined_df = pd.concat( gdfs ).reset_index(drop=True)

# Read federal-state-land GeoJSON
fed_state_land = gpd.read_file(
    './federal-state-singleparts.geojson'
).to_crs(epsg=4326)



# Intersect with all zones
# TODO: keep_geom_type=False should be true
# Different geometry types in Maui and Fed/state need to reconcile 
fed_state_land_ = gpd.overlay(
    combined_df,
    fed_state_land,
    keep_geom_type=False,
    how='intersection'
)

# Calculate acres
fed_state_land_['FedStateAcres'] = (fed_state_land_
    .to_crs(epsg=6933)
    .geometry.area
    .apply(m2acres)
)

# Account for repeating zone IDs
fed_state_land_ = (fed_state_land_
    .dissolve(by='id', aggfunc={'FedStateAcres': 'sum'})
    .reset_index()
    .filter(['id', 'FedStateAcres'])
)

# Add federal/state area per zoning district
combined_df = combined_df.merge(
    fed_state_land_,
    on='id',
    how='left'
)

# Calculate municipal (=zoneable) acres
combined_df.FedStateAcres = combined_df.FedStateAcres.fillna(0)
combined_df['MunicipalAcres'] = combined_df.ZoneAcres -\
    combined_df.FedStateAcres

spreadsheet_path = './hawaii-zoning-data.csv'

zoning = pd.read_csv(spreadsheet_path, skiprows=1)\
    .loc[ :, 'State': 'Tooltip Notes' ]

zoning['Tooltip Notes'] = zoning['Tooltip Notes'].fillna('')

# Remove spaces from column names
zoning.columns = [x.strip() for x in zoning.columns.tolist()]

# Trim all strings in the dataframe
str_columns = zoning.select_dtypes(['object'])
zoning[ str_columns.columns ] = str_columns.apply(lambda x: x.str.strip())

# Create id column (to perform linking later)
zoning['id'] = zoning.apply(
    lambda r: create_id(r.State, r.Jurisdiction, r['Abbreviated District Name']),
    axis=1
)

# Converts min lot size into a predefined range
#
# No size requirement, or 0 acres -> A
# 0.01-0.46 acres -> B
# 0.47-0.91 acres -> C
# 0.92-1.83 acres -> D
# 0.92-1.83 acres -> E
def min_lot_size(x):
    if x != x or x == '': # null
        return 'A'
    
    # x = float( x.split(' ')[0].split('-')[0].replace(',', '') )
    
    if x == 0:
        return 'A'
    if x <= 0.46:
        return 'B'
    if x <= 0.91:
        return 'C'
    if x <= 1.83:
        return 'D'
    
    return 'E'

zoning['AduMaxSizeLimit'] = ~zoning['ADU Max. Size (% of Main Unit)'].isna() | ~zoning['ADU Max. Size (SF)'].isna()

# Min Unit Size requirement: transform columns K, O, T, AC into true/false
zoning['1MUS'] = ~zoning['1-Family Min. Unit Size (SF)'].isna()
zoning['2MUS'] = ~zoning['2-Family Min. Unit Size (SF)'].isna()
zoning['3MUS'] = ~zoning['3-Family Min. Unit Size (SF)'].isna()
zoning['4MUS'] = ~zoning['4+-Family Min. Unit Size (SF)'].isna()

# Any minimum unit size is set? (for tooltip)
zoning['MUS'] = zoning['1MUS'] | zoning['2MUS'] | zoning['3MUS'] | zoning['4MUS']

# Min Lot Size
zoning['1MLS'] = zoning['1-Family Min. Lot (ACRES)'].apply(min_lot_size)
# TODO: Clean data
zoning['2MLS'] = zoning['2-Family Min. Lot (ACRES)'].apply(min_lot_size)
zoning['3MLS'] = zoning['3-Family Min. Lot (ACRES)'].apply(min_lot_size)
zoning['4MLS'] = zoning['4+-Family Min. Lot (ACRES)'].apply(min_lot_size)

# Elderly housing
# 1F Elderly Only —> value from BM column
# 2F Elderly Only —> value from BM column
# 3F Elderly Only —> Yes if BM = Yes, otherwise value from Y column
# 4F Elderly Only —> Yes if BM = Yes, otherwise value from AI column
def is_elderly_only(row, col):
    if row['Elderly Housing District'] == 'Yes':
        return 'Yes'
    return row[col]
    
zoning['1E'] = zoning['Elderly Housing District']
zoning['2E'] = zoning['Elderly Housing District']
zoning['3E'] = zoning.apply(lambda row: is_elderly_only(row, '3-Family Elderly Housing Only'), axis=1).fillna('No')
zoning['4E'] = zoning.apply(lambda row: is_elderly_only(row, '4+-Family Elderly Housing Only'), axis=1).fillna('No')

# Create ADU Elderly only
zoning['AEld'] = zoning['ADU Elderly Housing Only'].fillna('No')

def parking_text(row):
    one = row['1-Family Min. # Parking Spaces']
    two = row['2-Family Min. # Parking Spaces Per 2+ BR']
    two_ = row['2-Family Min. # Parking Spaces Per Studio or 1BR']
    three = row['3-Family Min. # Parking Spaces Per 2+ BR']
    three_ = row['3-Family Min. # Parking Spaces Per Studio or 1BR']
    four = row['4+-Family Min. # Parking Spaces Per Studio or 1BR']
    four_ = row['4+-Family Min. # Parking Spaces Per 2+ BR']
    
    text = []
    if one == one:
        text.append(str(one) + ' for 1-family')
    if two == two:
        text.append(str(two) + ' for 2-family (total)')
    if two_ == two_:
        text.append(str(two_) + ' for 2-family (per studio/1br)')
    if three == three:
        text.append(str(three) + ' for 3-family (total)')
    if three_ == three_:
        text.append(str(three_) + ' for 3-family (per studio/1br)')
    if four == four:
        text.append(str(four) + ' for 4+ family (total)')
    if four_ == four_:
        text.append(str(four_) + ' for 2+ family (per studio/1br)')

    return '; '.join(text)

#TODO: Clean Data
zoning['PK'] = zoning.apply(parking_text, axis=1)

final = combined_df.merge(
    zoning,
    on='id',
    how='left',
    suffixes=('', '_from_zoning')
)

zoning.drop(columns=['id'], inplace=True)

def overlay(j, ad, base=None, overlay=None, sep='/'):
    
    if not base:
        base = ad.split(sep)[0].strip()
        
    if not overlay:
        overlay = ad.split(sep)[1].strip()
    
    col_from = 'Type of Zoning District'
    col_to = 'PK' # Parking text column created above
    
    # Get proper zoning values from the spreadsheet
    base_values = zoning.loc[ zoning.Jurisdiction.eq(j) & zoning.AbbreviatedDistrict.eq(base), col_from : col_to ].values
    overlay_values = zoning.loc[ zoning.Jurisdiction.eq(j) & zoning.AbbreviatedDistrict.eq(overlay), col_from : col_to ].values
    
    if len(base_values) != 1:
        print(f'Base layer {base} in {j} does not exist, or is not unique!')
        return
     
    if len(overlay_values) != 1:
        print(f'Overlay layer {overlay} in {j} does not exist, or is not unique!')
        return
    
    
    base_values = base_values[0]
    overlay_values = overlay_values[0]
    
    combined_values = [ o if (o == o and o !='' and o != 'Overlay')
                            else b for b, o in zip(base_values, overlay_values) ]

    final.loc[ final.Jurisdiction.eq(j) & final.AbbreviatedDistrict.eq(ad), col_from : col_to ] = combined_values
    final.loc[ final.Jurisdiction.eq(j) & final.AbbreviatedDistrict.eq(ad), 'Jurisdiction' ] = j
    final.loc[ final.Jurisdiction.eq(j) & final.AbbreviatedDistrict.eq(ad), 'AbbreviatedDistrict' ] = base + '/' + overlay
    
    # Update full district name
    final.loc[ final['Jurisdiction'].eq(j) & final['AbbreviatedDistrict'].eq(ad), 'Full District Name' ] = zoning.loc[
        zoning.Jurisdiction.eq(j) & zoning.AbbreviatedDistrict.eq(base), 'Full District Name'].iloc[0] + '/' + zoning.loc[
        zoning.Jurisdiction.eq(j) & zoning.AbbreviatedDistrict.eq(overlay), 'Full District Name'].iloc[0]

final.loc[ final.AbbreviatedDistrict.isin(['NULL', 'Not Zoned']), 'AbbreviatedDistrict' ] = 'Not Zoned'
final.loc[ final.AbbreviatedDistrict.isin(['NULL', 'Not Zoned']), 'Full District Name' ] = 'Not Zoned'
final.loc[ final.AbbreviatedDistrict.isin(['NULL', 'Not Zoned']), 'Type of Zoning District' ] = 'Nonresidential'

final.loc[ final.AbbreviatedDistrict.eq('Not Zoned'), 'MunicipalAcres' ] = 0

cols_xwalk = {
    
    # Basic district info
    'Jurisdiction': 'T',
    'Full District Name': 'Z',
    'Type of Zoning District': 'Ty',
    'MunicipalAcres': 'MA',
    
    # Type of homes allowed
    '1-Family Treatment': '1F',
    '2-Family Treatment': '2F',
    '3-Family Treatment': '3F',
    '4+-Family Treatment': '4F',
    'Accessory Dwelling Unit (ADU) Treatment': 'AD',
    
    # Elderly housing
    '1E': '1E',
    '2E': '2E',
    '3E': '3E',
    '4E': '4E',
    
    # Minimum unit size requirement
    '1MUS': '1MUS',
    '2MUS': '2MUS',
    '3MUS': '3MUS',
    '4MUS': '4MUS',
    'MUS': 'MUS', # any MUS for tooltip
    
    # Mininum lot size requirement
    '1MLS': '1MLS',
    '2MLS': '2MLS',
    '3MLS': '3MLS',
    '4MLS': '4MLS',
    
    # Affordable/Elderly only
    'Affordable Housing District': 'AHD',
    'Elderly Housing District': 'EHD',
    
    # Accessory Dwelling Units restrictions
    'ADU Restricted to ONLY Primary Structure (i.e., No Outbuildings like Garages)': 'APrim',
    'AduMaxSizeLimit': 'ASize',
    'ADU Prohibition on Rental': 'ARent',
    'ADU Employees or Family Only': 'AFam',
    'ADU Owner Occupancy Required': 'AOwn',
    'AEld': 'AEld', # created above
    
    # Tooltip notes
    'Tooltip Notes': 'TN',
}

# Values to shorten
vals_xwalk = {
    'Allowed/Conditional': 'A',
    'Special Permit': 'AH',
    'Prohibited': 'N',
    
    'Primarily Residential': 'R',
    'Mixed with Residential': 'M',
    'No Residential': 'N',
    'Nonresidential': 'N'
}

(final
    .filter( list(cols_xwalk.keys()) + ['geometry'] )
    .rename(columns=cols_xwalk)
    .replace( vals_xwalk )
    .assign(geometry=lambda df_: df_.geometry.simplify(0.00004))
    .to_file('./final.geojson', driver='GeoJSON')
)

(final
 .filter([x for x in final.columns if x != 'geometry'])
 .to_csv('./final.csv')
)