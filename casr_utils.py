def get_CaSR_data(start_date, end_date, shapefile_path, variables,partition_rain_snow,output_dir):
    """
    Download, filter, and merge CaSR NetCDF data for specific variables over time and space.
    Args:
        start_date (str): Start date in 'YYYY-MM-DD'. min 1980-01-01
        end_date (str): End date in 'YYYY-MM-DD'. max is 2023-12-31
        shapefile_path (str): Path to shapefile (EPSG:4326).
        variables (list): List of variable names. see variable options below:
        partition_rain_snow (logical): whether to partition rain and snow (additional variables may downloaded).
        output_dir (str): directory to deposit results'.
    VARIABLE_OPTIONS = [
        "CaSR_v3.1_A_PR0_SFC", "CaSR_v3.1_P_FB_SFC", "CaSR_v3.1_P_FI_SFC", "CaSR_v3.1_P_FR0_SFC", "CaSR_v3.1_P_GZ_09975",
        "CaSR_v3.1_P_GZ_10000", "CaSR_v3.1_P_HR_09975", "CaSR_v3.1_P_HR_1.5m", "CaSR_v3.1_P_HU_09975", "CaSR_v3.1_P_HU_1.5m",
        "CaSR_v3.1_P_P0_SFC", "CaSR_v3.1_P_PE0_SFC", "CaSR_v3.1_P_PN_SFC", "CaSR_v3.1_P_PR0_SFC", "CaSR_v3.1_P_RN0_SFC",
        "CaSR_v3.1_P_SN0_SFC", "CaSR_v3.1_P_TD_09975", "CaSR_v3.1_P_TD_1.5m", "CaSR_v3.1_P_TT_09975", "CaSR_v3.1_P_TT_1.5m",
        "CaSR_v3.1_P_UU_09975", "CaSR_v3.1_P_UU_10m", "CaSR_v3.1_P_UUC_09975", "CaSR_v3.1_P_UUC_10m", "CaSR_v3.1_P_UVC_09975",
        "CaSR_v3.1_P_UVC_10m", "CaSR_v3.1_P_VV_09975", "CaSR_v3.1_P_VV_10m", "CaSR_v3.1_P_VVC_09975", "CaSR_v3.1_P_VVC_10m",
        "CaSR_v3.1_P_WDC_09975", "CaSR_v3.1_P_WDC_10m", "CaSR_v3.1_A_TD_1.5m", "CaSR_v3.1_A_TT_1.5m", "CaSR_v3.1_A_CFIA_SFC",
        "CaSR_v3.1_A_PR24_SFC", "CaSR_v3.1_P_SD_LAND", "CaSR_v3.1_P_SWE_LAND"
    ]
    """
    import subprocess
    import sys
    def install_and_import(packages):
        import importlib
        for package in packages:
            try:
                importlib.import_module(package)
            except ImportError:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            finally:
                globals()[package] = importlib.import_module(package)
    packages = ['requests','dill','numpy','pandas','geopandas','xarray','shapely','tqdm','scipy']
    install_and_import(packages)
    import os
    import requests, zipfile
    from io import BytesIO
    import dill
    import numpy as np
    import pandas as pd
    import geopandas as gpd
    import xarray as xr
    from shapely.geometry import Point
    from shapely.ops import unary_union
    from tqdm import tqdm
    import gc
    import shutil
    import zipfile
    if not isinstance(start_date, str):
        raise TypeError("start_date must be a string in 'YYYY-MM-DD' format.")
    if not isinstance(end_date, str):
        raise TypeError("end_date must be a string in 'YYYY-MM-DD' format.")
    try:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
    except Exception as e:
        raise ValueError(f"Invalid date format: {e}")
    if start_date > end_date:
        raise ValueError("start_date must be earlier than or equal to end_date.")
    if not isinstance(shapefile_path, str) or not os.path.exists(shapefile_path):
        raise FileNotFoundError(f"Shapefile path not found: {shapefile_path}")
    if not isinstance(variables, list) or not all(isinstance(v, str) for v in variables):
        raise TypeError("variables must be a list of strings.")
    if not isinstance(partition_rain_snow, bool):
        raise TypeError("partition_rain_snow must be a boolean.")
    if output_dir is None:
        output_dir = "output"
    elif not isinstance(output_dir, str):
        raise TypeError("output_dir must be a string.")
    elif not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if partition_rain_snow:
        needed_vars = ['CaSR_v3.1_P_RN0_SFC','CaSR_v3.1_P_FR0_SFC','CaSR_v3.1_P_PE0_SFC','CaSR_v3.1_P_SN0_SFC']
        variables = list(set(variables + needed_vars))
    with zipfile.ZipFile(BytesIO(requests.get("https://github.com/rarabzad/CaSR-v3.1-downloader/raw/refs/heads/main/CaSR_metadata.zip").content)) as z:
        CaSR_metadata = dill.load(z.open("CaSR_metadata.pkl"))
    def url_maker(tile, variable, period):
        return f"https://hpfx.collab.science.gc.ca/~scar700/rcas-casr/data/CaSRv3.1/netcdf_tile/{tile}/{variable}_{tile}_{period}.nc"
    CaSR_metadata['url_maker'] = url_maker
    os.makedirs("download", exist_ok=True)
    start_date = pd.to_datetime(start_date)
    end_date   = pd.to_datetime(end_date)
    polygon = gpd.read_file(shapefile_path)
    if polygon.crs is None or polygon.crs.to_epsg() != 4326:
        polygon = polygon.to_crs(epsg=4326)
    polygon = polygon.geometry.union_all()
    polygon = polygon.buffer(0.1)
    valid_vars = CaSR_metadata['variables']['variable'].values
    missing = [v for v in variables if v not in valid_vars]
    if missing:
        raise ValueError(f"Missing variables in metadata: {missing}")
    tile_sf = CaSR_metadata['lonlat']
    tile_sf["lon"] = tile_sf.geometry.x
    tile_sf["lat"] = tile_sf.geometry.y
    tile_sf.loc[tile_sf.lon > 180, "lon"] -= 360
    in_bbox = tile_sf.cx[polygon.bounds[0]:polygon.bounds[2], polygon.bounds[1]:polygon.bounds[3]]
    tiles = in_bbox[in_bbox.intersects(polygon)].tile.unique().tolist()
    if not tiles:
        raise ValueError("No intersecting tiles found.")
    valid_periods = []
    for period in CaSR_metadata['periods']:
        y1, y2 = map(int, period.split("-"))
        if y2 >= start_date.year and y1 <= end_date.year:
            valid_periods.append(period)
    if not valid_periods:
        raise ValueError("No valid periods matched.")
    downloaded = []
    for vname in variables:
        print(f"\n📦 Processing: {vname}")
        url_maker = CaSR_metadata['url_maker']
        urls = [url_maker(tile, vname, p) for tile in tiles for p in valid_periods]
        for url in tqdm(urls, desc="⬇️ Downloading"):
            fname = os.path.join("download", os.path.basename(url))
            if not os.path.exists(fname):
                for _ in range(5):
                    try:
                        r = requests.get(url, timeout=60)
                        if r.status_code == 200:
                            with open(fname, 'wb') as f:
                                f.write(r.content)
                            break
                    except:
                        pass
            if os.path.exists(fname):
                downloaded.append(fname)
        if not downloaded:
            print(f"⚠️ No files downloaded for {vname}")
            continue
    for vname in variables:
        print(f"\n📦 Merging: {vname}")
        var_files = [f for f in downloaded if os.path.basename(f).startswith(vname)]
        try:
            total_size_gb = sum(os.path.getsize(f) for f in var_files) / (1024 ** 3)  # in GB
            if total_size_gb < 0.5:
                chunk_setting = None
            else:
                divisor = int(total_size_gb / 0.5) + 1  # e.g. 0.6 GB → 2, 1.2 GB → 3
                chunk_size = int(400_000 / divisor)
                chunk_setting = {'time': chunk_size}
            ds = xr.open_mfdataset(var_files, combine='by_coords', chunks=chunk_setting, parallel=False)
            ds = ds.sel(time=slice(start_date, end_date))
            lat = ds['lat'].values
            lon = ds['lon'].values
            lon = np.where(lon > 180, lon - 360, lon)
            minx, miny, maxx, maxy = polygon.bounds
            inside_bbox = (lon >= minx) & (lon <= maxx) & (lat >= miny) & (lat <= maxy)
            rows_within_bbox = np.arange(np.where(inside_bbox.any(axis=1))[0].min(), np.where(inside_bbox.any(axis=1))[0].max() + 1)
            cols_within_bbox = np.arange(np.where(inside_bbox.any(axis=0))[0].min(), np.where(inside_bbox.any(axis=0))[0].max() + 1)
            ds = ds.isel(
                rlon=slice(rows_within_bbox.min(), rows_within_bbox.max() + 1),
                rlat=slice(cols_within_bbox.min(), cols_within_bbox.max() + 1)
            )
            lon_cropped = ds['lon'].values
            lat_cropped = ds['lat'].values
            lon_cropped = np.where(lon_cropped > 180, lon_cropped - 360, lon_cropped)
            points = [Point(x, y) for x, y in zip(lon_cropped.flatten(), lat_cropped.flatten())]
            mask_flat = np.array([polygon.contains(pt) for pt in points])
            mask = mask_flat.reshape(lon_cropped.shape)
            ds[vname] = ds[vname].where(mask)
            outfile = os.path.join(output_dir, f"{vname}.nc")
            print(f"💾 Saving {outfile}")
            ds.to_netcdf(outfile)
            ds.close()
            del ds, mask, lat, lon, lon_cropped, lat_cropped
            gc.collect()
        except Exception as e:
            print(f"⚠️ Failed to process {vname}: {e}")
            continue
    if partition_rain_snow:
        print("🔄 Partitioning Rain and Snow...")
        var_files = {
            "P_RN0_SFC": os.path.join(output_dir, "CaSR_v3.1_P_RN0_SFC.nc"),
            "P_FR0_SFC": os.path.join(output_dir, "CaSR_v3.1_P_FR0_SFC.nc"),
            "P_PE0_SFC": os.path.join(output_dir, "CaSR_v3.1_P_PE0_SFC.nc"),
            "P_SN0_SFC": os.path.join(output_dir, "CaSR_v3.1_P_SN0_SFC.nc")
        }
        ds_dict = {k: xr.open_dataset(v) for k, v in var_files.items()}
        for k, ds in ds_dict.items():
            assert f"CaSR_v3.1_{k}" in ds, f"Variable CaSR_v3.1_{k} not found in {var_files[k]}"
        RN = ds_dict["P_RN0_SFC"][f"CaSR_v3.1_P_RN0_SFC"]
        FR = ds_dict["P_FR0_SFC"][f"CaSR_v3.1_P_FR0_SFC"]
        PE = ds_dict["P_PE0_SFC"][f"CaSR_v3.1_P_PE0_SFC"]
        SN = ds_dict["P_SN0_SFC"][f"CaSR_v3.1_P_SN0_SFC"]
        PRECIPITATION = RN + FR + PE + SN
        PRECIPITATION.name = "P_PR0_SFC"
        PRECIPITATION.attrs["long_name"] = "Total Predicted Precipitation"
        PRECIPITATION.attrs["units"] = RN.attrs.get("units", "mm")
        RAIN_RATIO = xr.where(
            PRECIPITATION != 0,
            RN / PRECIPITATION,
            np.nan
        )
        RAIN_RATIO.name = "RAIN_RATIO"
        RAIN_RATIO.attrs["long_name"] = "Rain Ratio (Rain / Total Precipitation)"
        RAIN_RATIO.attrs["description"] = "Set to nan where total precipitation is zero and the interpolated"
        RAIN_RATIO = RAIN_RATIO.interpolate_na(dim="time", method="nearest", fill_value="extrapolate")
        RAIN = PRECIPITATION * RAIN_RATIO
        RAIN.name = "RAIN"
        RAIN.attrs["long_name"] = "Rain partitioned from total PRECIPITATION"
        RAIN.attrs["units"] = PRECIPITATION.attrs["units"]
        SNOW = PRECIPITATION * (1 - RAIN_RATIO)
        SNOW.name = "SNOW"
        SNOW.attrs["long_name"] = "Snow partitioned from total PRECIPITATION"
        SNOW.attrs["units"] = PRECIPITATION.attrs["units"]
        template_ds = ds_dict["P_RN0_SFC"]
        for var in [PRECIPITATION, RAIN, SNOW, RAIN_RATIO]:
            out_ds = template_ds.copy()
            for name in list(out_ds.data_vars):
                if name != "rotated_pole":
                    out_ds = out_ds.drop_vars(name)
            out_ds[var.name] = var
            out_ds.to_netcdf(os.path.join(output_dir, f"{var.name}.nc"))
            print(f"💾 Saved {var.name}.nc")
        for ds in ds_dict.values():
            ds.close()
        print("✅ Rain/Snow partitioning complete.")
    shutil.rmtree("download", ignore_errors=True)
    result_files = []
    for fname in os.listdir(output_dir):
        if fname.endswith(".nc"):
            result_files.append(os.path.join(output_dir, fname))
    print("\n✅ All variables processed.")
    return result_files
