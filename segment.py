import subprocess
import os
import csv
import ffmpeg

def segment_audio(sesslist):
    '''
    segment session audio file according to given timestamps
    here the timestamps are expeced to be in a file named as "<sess>_Google.csv"
    '''

    for sess in sesslist:
        group = os.path.basename(sess)
        print(f"Splitting {group}...")
        audio_file = os.path.join(sess, group + ".wav")
        output_folder = os.path.join(sess,"timestamp_segments")
        if not os.path.isdir(output_folder):
            os.mkdir(output_folder)
        timestamp_file = os.path.join(sess, group+"_Google.csv")
        with open(timestamp_file) as timecsv:
            csvreader = csv.reader(timecsv)
            header = next(csvreader, None)
            utterance_num = 0
            for row in csvreader:
                start = row[1]
                stop = row[2]
                output_wav = os.path.join(output_folder,f"{group}_{utterance_num}.wav")
                utterance_num+=1
                split_audio_command = ["ffmpeg", "-i", audio_file,"-ss", start, "-to", stop, "-c", "copy", output_wav]
                print(split_audio_command)
                subprocess.call(split_audio_command)
