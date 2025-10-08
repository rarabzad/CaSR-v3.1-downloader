import streamlit as st
import tempfile
import os
import datetime
import io
import sys
from zipfile import ZipFile
from casr_utils import get_CaSR_data

st.set_page_config(page_title="CaSR v3.1 Downloader", layout="wide")

st.title("🌧️ CaSR v3.1 Data Downloader")

st.markdown(
    "<p style='font-size: 0.9rem; color: grey;'>"
    "This app allows users to download and process CaSR v3.1 NetCDF datasets (1980–2023) using uploaded shapefiles and selected variables. "
    "Rain/snow partitioning is optional, and results are available as NetCDF or zipped outputs. "
    "For more information, see <a href='https://github.com/rarabzad/CaSR-v3.1-downloader' target='_blank'>the GitHub repository</a>."
    "</p>",
    unsafe_allow_html=True
)

# Sidebar inputs
st.sidebar.header("Input Parameters")

# Dates
start_date = st.sidebar.date_input("Start Date", datetime.date(2000, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.date(2005, 12, 31))

# Shapefile upload
shp_zip = st.sidebar.file_uploader("Upload Shapefile (.zip)", type=["zip"])
shapefile_path = None
if shp_zip:
    tmpdir = tempfile.mkdtemp()
    zpath = os.path.join(tmpdir, "shape.zip")
    with open(zpath, "wb") as f:
        f.write(shp_zip.read())
    with ZipFile(zpath, "r") as z:
        z.extractall(tmpdir)
    for fn in os.listdir(tmpdir):
        if fn.lower().endswith(".shp"):
            shapefile_path = os.path.join(tmpdir, fn)
            break

# Variable options
VARIABLE_OPTIONS = [
    "CaSR_v3.1_A_PR0_SFC", "CaSR_v3.1_P_FB_SFC", "CaSR_v3.1_P_FI_SFC", "CaSR_v3.1_P_FR0_SFC",
    "CaSR_v3.1_P_GZ_09975", "CaSR_v3.1_P_GZ_10000", "CaSR_v3.1_P_HR_09975", "CaSR_v3.1_P_HR_1.5m",
    "CaSR_v3.1_P_HU_09975", "CaSR_v3.1_P_HU_1.5m", "CaSR_v3.1_P_P0_SFC", "CaSR_v3.1_P_PE0_SFC",
    "CaSR_v3.1_P_PN_SFC", "CaSR_v3.1_P_PR0_SFC", "CaSR_v3.1_P_RN0_SFC", "CaSR_v3.1_P_SN0_SFC",
    "CaSR_v3.1_P_TD_09975", "CaSR_v3.1_P_TD_1.5m", "CaSR_v3.1_P_TT_09975", "CaSR_v3.1_P_TT_1.5m",
    "CaSR_v3.1_P_UU_09975", "CaSR_v3.1_P_UU_10m", "CaSR_v3.1_P_VV_09975", "CaSR_v3.1_P_VV_10m",
    "CaSR_v3.1_P_WDC_09975", "CaSR_v3.1_P_WDC_10m", "CaSR_v3.1_A_TT_1.5m", "CaSR_v3.1_A_CFIA_SFC",
    "CaSR_v3.1_A_PR24_SFC", "CaSR_v3.1_P_SD_LAND", "CaSR_v3.1_P_SWE_LAND"
]
variables = st.sidebar.multiselect("Select Variables", VARIABLE_OPTIONS)

partition_rain_snow = st.sidebar.checkbox("Partition Rain/Snow", value=False)

output_dir = tempfile.mkdtemp()

def run_with_capture(func, *args, **kwargs):
    """Capture stdout/stderr while running a function."""
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        result = func(*args, **kwargs)
        out = sys.stdout.getvalue()
        err = sys.stderr.getvalue()
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return result, out, err

if st.sidebar.button("🚀 Run"):
    if not shapefile_path:
        st.error("Please upload a valid shapefile ZIP.")
    elif not variables:
        st.error("Please select at least one variable.")
    elif start_date > end_date:
        st.error("Invalid date range.")
    else:
        with st.spinner("Processing CaSR data... please wait ⏳"):
            try:
                results, out_text, err_text = run_with_capture(
                    get_CaSR_data,
                    str(start_date), str(end_date),
                    shapefile_path,
                    variables,
                    partition_rain_snow,
                    output_dir
                )
                st.success("✅ Processing Complete!")

                st.subheader("Log Output")
                st.text_area("Console Output", out_text + "\n" + err_text, height=300)

                st.subheader("Download Results")
                for f in results:
                    with open(f, "rb") as data:
                        st.download_button(
                            label=f"⬇️ {os.path.basename(f)}",
                            data=data,
                            file_name=os.path.basename(f),
                            mime="application/x-netcdf"
                        )
            except Exception as e:
                st.error(f"❌ Error: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("Developed by Rezgar Arabzadeh — University of Waterloo")
