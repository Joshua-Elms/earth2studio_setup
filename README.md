Preparing an installation of NVIDIA's earth2studio to run on BigRed200.

Temporary repo; E2MIP -> E2Studio changes will eventually be merged into DCMIP25 or other repo.

Materials:
- Guide to installation: https://nvidia.github.io/earth2studio/userguide/about/install.html#install-using-uv-recommended
- uv install guide: https://docs.astral.sh/uv/getting-started/installation/
- 

Add to .bashrc: `export UV_CACHE_DIR=/N/slate/jmelms/software/.uv_cache_real"

Setup Steps
1. `cd /N/u/jmelms/BigRed200/projects/earth2studio_setup/`
2. `mkdir earth2studio-project && cd earth2studio-project`
3. `curl -LsSf https://astral.sh/uv/install.sh | sh`
4. `uv init --python=3.12`
5. `uv add "earth2studio --extra sfno @ git+https://github.com/NVIDIA/earth2studio.git"`
6. `uv pip install matplotlib jupyter uv earth2studio[dlwp]` - needed for vis and interaction
7. `source .venv/bin/activate; cd ..` - to use python env and return to repo level
8. `srun -p gpu -A r00389 --mem=200GB --time=02:00:00 --gpus-per-node v100:1 --pty bash` - to get a GPU job on quartz
9. `jupyter notebook --NotebookApp.allow_origin='*' --NotebookApp.ip='0.0.0.0' --port 9999` - to open a jupyter notebook
10. `mkdir /N/slate/jmelms/projects/.E2S_cache;echo EARTH2STUDIO_CACHE=/N/slate/jmelms/projects/.E2S_cache > .env` - create cache and populate dotenv file
11. 

Notes:
1. You may have to play around with the cache location for uv to get it right. 
2. If you don't link an [NGC](https://org.ngc.nvidia.com/) account from `test.py`, you'll get: "WARNING  | earth2studio.models.auto.ngc:__init__:126 - Using NGC guest mode, which may fail due to unauthorized access. Consider using a valid NGC API key and org". Not breaking yet, so I'll wait on the auth. 
3. 
conda deactivate; cd earth2studio-project/;source .venv/bin/activate;cd ..