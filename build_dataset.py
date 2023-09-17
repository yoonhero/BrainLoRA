import glob
import os
import json
import numpy as np
import pandas as pd

from edf_helper import read_edf_file, process_raw_data, get_roi_content, draw_spectrogram

def build_dataset_from_one_exp(target_folder):
    file = glob.glob(target_folder + "/*.edf")[0]
    csv_key = os.path.split(target_folder)[-1]
    experiement_interval = 6
    hz = 128
    hz_experiement_interval = hz * experiement_interval

    with open("./raw/list.json", "r", encoding="utf-8") as f:
        table = json.load(f)

    raw_data, info, channels = read_edf_file(file)
    print(f"INFO: {info}")
    roi_data, timestamp = process_raw_data(raw_data, channels)

    record_data = table[csv_key]
    df = pd.read_csv(f"./raw/{csv_key}/{record_data}")
    json_df = df.to_dict(orient='records')

    channels = ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4']

    dataset = []
    for row in json_df:
    #    id,src,caption,start,end,width,height
        out = "./dataset/{id}_c_{channel}.png"
        start = float(f"{(row['start']/1000):.3f}")
        expected_end = start + experiement_interval
        if expected_end > row["end"]: continue

        target_edf_data = get_roi_content(roi_data, timestamp, start, expected_end)
        row["spectrogram"] = []

        if target_edf_data.shape[1] > hz_experiement_interval:
            target_edf_data = target_edf_data[:, :hz_experiement_interval]
        length = target_edf_data.shape[1]
        target_edf_data = np.pad(target_edf_data, (0, hz_experiement_interval-length), mode="mean")

        for i in range(target_edf_data.shape[0]):
            out_name = out.format(id=row['id'], channel=i)
            draw_spectrogram(target_edf_data[i, :], out_name)
            row["spectrogram"].append(out_name)

        dataset.append(row)
    
    return dataset


def build_dataset(excludes=[]):
    temp_dests = glob.glob("./raw/*")

    dataset = []

    for dest in temp_dests:
        if ".json" not in dest and dest.split("/")[-1] not in excludes:
            temp_dataset = build_dataset_from_one_exp(dest)

            dataset = dataset + temp_dataset

    with open("dataset.json", "a", encoding="utf-8") as f:
        json.dump(dataset, f)
    
