import os
import time
import numpy as np
import pandas as pd
import opensmile
import configparser

def get_opensmile(sesslist):
    smile = opensmile.Smile(
        feature_set=opensmile.FeatureSet.eGeMAPSv02,
        feature_level=opensmile.FeatureLevel.Functionals,
    )
    print(smile.feature_names)

    for sess in sesslist:
        group = os.path.basename(sess)
        print("Running ", group)
        segaudio = os.path.join(sess, "timestamp_segments")
        segaudio = segaudio.replace('\\', '/')
        print(type(segaudio))
        y = smile.process_folder(str(segaudio))
        y.to_csv(os.path.join(sess, f"{group}_clean_opensmile.csv"))

