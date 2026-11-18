# PathSnap: Distributed Map-Matching & Route Reconstruction

Team: <names>   |   Course: UE24CS352A Machine Learning, PES University

## Setup
```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```
Place the dataset folder `Student folder/` in the repo root (it is git-ignored),
or set the environment variable `PATHSNAP_DATA` to its path.

## Run
```bash
python -m data_processing.eda                 # dataset inventory -> results/
python -m maps.plot_trip train 00000005       # Folium map -> results/
```
(More sections to be added: feature engineering, training, tuning, HMM, API, UI.)
