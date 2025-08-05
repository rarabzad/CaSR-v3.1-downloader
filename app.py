import streamlit as st
import tempfile
import zipfile
import os
import glob
import io
import contextlib
from io import BytesIO
import datetime
from casr_utils import get_CaSR_data
import xarray as xr
import matplotlib.pyplot as plt


st.set_page_config(page_title="CaSR v3.1 Data Downloader", layout="wide")
st.title("CaSR v3.1 Data Downloader")
st.markdown(
    "<p style='font-size: 0.9rem; color: grey;'>"
    "This app allows users to download and process CaSR v3.1 NetCDF datasets (1980–2023) using uploaded shapefiles and selected variables. "
    "Rain/snow partitioning is optional, and results are available as NetCDF or zipped outputs. "
    "For more information, see <a href='https://github.com/rarabzad/CaSR-v3.1-downloader' target='_blank'>the GitHub repository</a>."
    "</p>",
    unsafe_allow_html=True
)
# Sidebar inputs
st.sidebar.header("Parameters")
start_date = st.sidebar.date_input(
    "Start date",
    value=datetime.date(1980, 1, 1),
    min_value=datetime.date(1980, 1, 1),
    max_value=datetime.date(2023, 12, 31)
)
end_date = st.sidebar.date_input(
    "End date",
    value=datetime.date(2023, 12, 31),
    min_value=datetime.date(1980, 1, 1),
    max_value=datetime.date(2023, 12, 31)
)
uploaded_zip = st.sidebar.file_uploader(
    "Upload shapefile zip",
    type=["zip"],
    help="Zip containing .shp, .shx, .dbf, etc."
)

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
variables = st.sidebar.multiselect(
    "Select variables to download/process",
    options=VARIABLE_OPTIONS
)

partition_rain_snow = st.sidebar.checkbox(
    "Partition rain and snow?",
    value=False
)

run_button = st.sidebar.button("Run Download & Process")

if run_button:
    # Validate inputs
    if not variables:
        st.error("Select at least one variable.")
        st.stop()
    if not uploaded_zip:
        st.error("Upload a shapefile zip first.")
        st.stop()
    if start_date is None or end_date is None:
        st.error("Select both start and end dates.")
        st.stop()

    # Ensure working directory is script directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    # Unzip shapefile
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "shape.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.read())
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(tmpdir)

        shp_files = [f for f in os.listdir(tmpdir) if f.lower().endswith('.shp')]
        if not shp_files:
            st.error("No .shp file found in zip.")
            st.stop()
        shapefile_path = os.path.join(tmpdir, shp_files[0])
        st.info(f"Using shapefile: {shp_files[0]}")

        # Prepare output directory
        output_dir = os.path.join(base_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        # Capture console output
        log_buffer = io.StringIO()
        with st.spinner("Downloading & processing CaSR data..."), \
             contextlib.redirect_stdout(log_buffer), \
             contextlib.redirect_stderr(log_buffer):
            try:
                _ = get_CaSR_data(
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d'),
                    shapefile_path,
                    variables,
                    partition_rain_snow,
                    output_dir
                )
            except Exception as err:
                st.error(f"Error during processing: {err}")
                st.stop()

        # Display logs in styled box
        logs = log_buffer.getvalue()
        st.markdown(
            "<div style='background-color:black;color:white;padding:10px;"
            "border-radius:5px;overflow:auto;max-height:300px;'>"
            "<pre style='white-space: pre-wrap; word-wrap: break-word;'>"
            f"{logs}"
            "</pre></div>",
            unsafe_allow_html=True
        )

        # Gather and display .nc files
        nc_files = glob.glob(os.path.join(output_dir, '**', '*.nc'), recursive=True)
        if nc_files:
            st.success("Processing complete! 🎉")
            st.subheader("Result NetCDF Files")
            for fpath in sorted(nc_files):
                fname = os.path.basename(fpath)
                with open(fpath, 'rb') as file_obj:
                    st.download_button(
                        label=f"Download {fname}",
                        data=file_obj,
                        file_name=fname,
                        mime='application/x-netcdf'
                    )
            # Zip all and offer single download
            buffer = BytesIO()
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for fpath in nc_files:
                    arcname = os.path.relpath(fpath, output_dir)
                    zipf.write(fpath, arcname)
            buffer.seek(0)
            st.download_button(
                label="Download All as ZIP",
                data=buffer,
                file_name="CaSR_output.zip",
                mime='application/zip'
            )
        else:
            st.warning("Processing finished but no NetCDF files were found under 'output/'.")
        st.subheader("Variable Preview Panels")
        
        for fpath in sorted(nc_files):
            var_name = os.path.splitext(os.path.basename(fpath))[0]
        
            try:
                ds = xr.open_dataset(fpath)
                if var_name not in ds:
                    st.warning(f"Variable '{var_name}' not found in file.")
                    continue
        
                # Compute time-mean
                da_mean = ds[var_name].mean(dim="time", skipna=True)
        
                # Prepare figure
                fig, ax = plt.subplots(figsize=(6, 4))
                img = ax.imshow(da_mean, cmap='viridis', aspect='auto')
                ax.set_title(f"{var_name} (Mean over time)")
                plt.colorbar(img, ax=ax, shrink=0.8, label=ds[var_name].attrs.get("units", ""))
        
                with st.expander(f"🔍 {var_name} preview", expanded=False):
                    st.pyplot(fig)
                plt.close(fig)
                ds.close()
        
            except Exception as e:
                st.error(f"Failed to process {var_name}: {e}")
            st.info(f"Searched path: {os.path.abspath(output_dir)}")



