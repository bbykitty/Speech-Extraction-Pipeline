from rosy_asr_utils import * 
from pathlib import Path
import Google_VAD
import Google_ASR
import Google_BERT
import openSMILE
import segment
import label
import configparser

def read_ini(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    datadir = config["data"]["datadir"]
    labels = config["data"]["labels"]
    features = config["data"]["features"]
    groups = config["data"]["groups"].split(" ")
    sesslist = []
    for group in groups:
        sesslist.append(os.path.join(datadir,group))
    client = config["google"]["client"]
    return datadir, sesslist, client, labels, features


if __name__ == "__main__":
    datadir, sesslist, client, labels, features = read_ini(r"C:\Users\bradf\OneDrive - Colostate\Research\Interruptions\Interruption-Detection\config.ini")
    # Google_VAD.get_vad(sesslist)
    # segment.segment_audio(sesslist)
    # Google_ASR.get_asr(client, sesslist)
    # Google_BERT.get_BERT(sesslist)
    # openSMILE.get_opensmile(sesslist)
    label.create_csv(sesslist, labels, features, acoustic=False)
