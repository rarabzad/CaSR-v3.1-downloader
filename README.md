# 🌎 CaSR v3.1 Data Downloader

A user-friendly Streamlit app for downloading, filtering, and extracting CaSR v3.1 NetCDF climate data over a custom shapefile region and date range.

---

## 🚀 Overview

This app allows users to:
- Upload a zipped shapefile defining the spatial region of interest
- Select a range of dates between 1980 and 2023
- Choose from 40+ CaSR v3.1 climate variables
- Optionally apply rain/snow partitioning
- Download the processed NetCDF files (one or more)
- Or export all outputs as a zipped archive

---

## 🧰 Technologies

- **Python 3.9+**
- **Streamlit**
- `xarray`, `geopandas`, `rasterio`, `shapely`, `netCDF4`, `pyproj`, `zipfile`, `datetime`
- Custom function: [`get_CaSR_data`](./casr_utils.py)

---

## 📦 Installation

Clone this repository and install required packages:

```bash
git clone https://github.com/rarabzad/CaSR-v3.1-downloader.git
cd CaSR-v3.1-downloader
pip install -r requirements.txt
````

**Minimal `requirements.txt`:**

```txt
streamlit
pandas
numpy
geopandas
xarray
shapely
requests
tqdm
dill
netCDF4
pyproj
rasterio
dask
fiona
scipy
```

---

## 📁 File Structure

```
.
├── app.py                # Main Streamlit app
├── casr_utils.py         # Contains the `get_CaSR_data()` core function
└── README.md             # This documentation
```

---

## 🖥️ Running the App

```bash
streamlit run app.py
```

Then, open the app in your browser at:

```
http://localhost:8501
```

---

## 📋 Inputs

| Input                    | Description                               |
| ------------------------ | ----------------------------------------- |
| `Start date`             | Beginning of time range (1980–2023)       |
| `End date`               | End of time range (1980–2023)             |
| `Shapefile ZIP`          | Must contain `.shp`, `.shx`, `.dbf`, etc. |
| `Variables`              | One or more of the 40+ CaSR v3.1 fields   |
| `Rain/snow partitioning` | Optional toggle                           |

---

## 📤 Outputs

* NetCDF files clipped to the shapefile and date range
* Each variable is processed independently
* Files can be downloaded individually or as a ZIP archive

---

## 🧠 How It Works (Simplified Flow)

1. **UI Inputs**: Select time, variables, and shapefile
2. **Backend Processing**: Calls `get_CaSR_data()` with all user parameters
3. **Console Logs**: Output printed live in a scrollable terminal box
4. **Downloads**: Shows `.nc` file links and ZIP archive

---

## 🧪 Sample Variables

```text
CaSR_v3.1_A_TT_1.5m   → Air temperature
CaSR_v3.1_P_PR0_SFC   → Precipitation
CaSR_v3.1_P_SN0_SFC   → Snow depth
CaSR_v3.1_P_SD_LAND   → Snow depth over land
```

---

## 🔧 Developer Notes

### Function: `get_CaSR_data`

```python
def get_CaSR_data(start_date, end_date, shapefile_path, variables, partition_rain_snow, output_dir):
    ...
```

* **Handles**: time filtering, spatial subsetting, NetCDF I/O
* **Returns**: list of file paths or status object
* **Dependencies**: `xarray`, `geopandas`, `shapely`, `numpy`, `rasterio`

---

## 🛠 Troubleshooting

| Issue                   | Solution                                                   |
| ----------------------- | ---------------------------------------------------------- |
| No `.shp` file detected | Ensure ZIP includes `.shp`, `.shx`, `.dbf`, `.prj`         |
| No NetCDF found         | Verify output directory structure inside `get_CaSR_data()` |
| Date out of range       | Select only between 1980–2023                              |

---

## 📜 License

MIT License

## Live Demo
app on [steamlit](https://casr-v3-1-downloader.streamlit.app/) server
