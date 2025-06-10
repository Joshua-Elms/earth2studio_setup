""" Import libraries. """
import os
from pathlib import Path

output_dir = Path("outputs").resolve()
if not output_dir.exists():
    output_dir.mkdir(exist_ok=False)
    print(f"Making output directory: {output_dir}")
else:
    print(f"Using extant output directory: {output_dir}")
from dotenv import load_dotenv

load_dotenv();  # TODO: make common example prep function

from earth2studio.data import GFS
from earth2studio.io import XarrayBackend
from earth2studio.models.px import SFNO
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

import earth2studio.run as run
cache_loc = os.environ["EARTH2STUDIO_CACHE"]
print(f"Earth2Studio cache: {cache_loc}")

from datetime import datetime
from earth2studio.utils.type import TimeArray, VariableArray
import xarray as xr

class DataSetFile:
    """A local xarray dataset file data source. This file should be compatible with
    xarray. For example, a netCDF file.

    Parameters
    ----------
    file_path : str
        Path to xarray dataset compatible file.
    array_name : str
        Data array name in xarray dataset
    """

    def __init__(self, file_path: str, **xr_args ):
        self.file_path = file_path
        self.ds = xr.open_dataset(self.file_path, **xr_args)

    def __call__(
        self,
        time: datetime | list[datetime] | TimeArray,
        variable: str | list[str] | VariableArray,
    ) -> xr.DataArray:
        """Function to get data.

        Parameters
        ----------
        time : datetime | list[datetime] | TimeArray
            Timestamps to return data for.
        variable : str | list[str] | VariableArray
            Strings or list of strings that refer to variables to return.

        Returns
        -------
        xr.DataArray
            Loaded data array
        """
        # loop over variables and concatenate the data arrays
        da_list = [self.ds[v].sel(time=np.atleast_1d(time)) for v in variable]
        da = xr.concat(da_list, dim="variable")
        da = da.assign_coords(variable=variable)
        # reorder to time variable lat lon
        da = da.transpose("time", "variable", "lat", "lon")
        return da
    
    
""" Set up the model """
# Load the default model package which downloads the check point from NGC
package = SFNO.load_default_package()
model = SFNO.load_model(package)

print("Done loading stuff")


""" Set up the data sources. """
unperturbed_data = DataSetFile('ic_unperturbed.nc')
perturbed_data = DataSetFile('ic_perturbed.nc')


""" Set up tendency reversion. """
# set up IO
dummy_io = XarrayBackend()

# set up a hook function that appends the model state to a list
states = []
def append_state(x, coords):
    """ Appends the states to a list"""
    states.append(x)
    return x, coords

model.rear_hook = append_state
model.front_hook = append_state

# run the model for one step; this will populate the states[] list above
nsteps = 1
io = run.deterministic(["2024-01-01"], nsteps, model, unperturbed_data, dummy_io)

# get the recurrent perturbation
rpert = states[0] - states[1]


""" Verify that tendency reversion works. """

# set up a post-model hook function that reverts the tendency
def tendency_reversion(x, coords):
    """ Reverts the tendency to the first state """
    return x + rpert, coords

# set up a hook function that returns the input as is
def identity(x, coords):
    """ Returns the input as is """
    return x, coords

# reset the model hooks
model.front_hook = identity
model.rear_hook = tendency_reversion

nsteps = 1
io = XarrayBackend()
io = run.deterministic(["2024-01-01"], nsteps, model, unperturbed_data, io)
ds = io.root

# plot the difference between the timesteps
ds_diff = ds.diff(dim = "lead_time")
ds_diff['msl'].plot()
plt.title(f"Max difference: {ds_diff['msl'].max().values:.2f} hPa")
print(ds_diff.max())


""" Run the model with the perturbed data and tendency reversion. """

# reset the model hooks for tendency reversion
model.front_hook = identity
model.rear_hook = tendency_reversion

nsteps = 10 * 4 # steps, 10 days at 4 steps per day
io = XarrayBackend()
io = run.deterministic(["2024-01-01"], nsteps, model, perturbed_data, io)

""" Output data. """

ds = io.root
ds.to_netcdf(output_dir / "perturbed.nc")