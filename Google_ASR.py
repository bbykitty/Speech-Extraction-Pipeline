#!/usr/bin/env python3
# asrBlks.py  <ctl file of session paths>
from __future__ import absolute_import
from pydub.audio_segment import AudioSegment, effects
import os
from datetime import datetime
import shutil
import csv
from rosy_asr_utils import *

def transcribe(client, segment):
    seg_audio = AudioSegment.from_file(segment)
    srate = seg_audio.frame_rate
    print(f'srate:{srate}')
    seg_audio = effects.normalize(seg_audio)
    bytes=seg_audio.raw_data
    return transcribe_bytestream(bytes, client, srate)

def get_asr(client,sesslist):
    client = speech.SpeechClient.from_service_account_file(client)
    for sesspath in sesslist: 
        print(f'sesspath: {sesspath}')
        sesspath = sesspath.strip()
        sessname = os.path.basename(sesspath)
        wavfile = os.path.join(sesspath, f'{sessname}.wav')
        asrDir = os.path.join(sesspath,'clean_google_asr')
        asrBlockDir = asrDir + '_reblocked' # segment-wise ASR will be concatenated to distinguish from ASR results run on entire block
        asrFullFile = os.path.join(sesspath,"clean_google_asr.txt") # full session ASR results
        open(asrFullFile, 'w').close() # clear file before appending
        blkmapFile = os.path.join(sesspath,f'{sessname}.blk')

        audio = AudioSegment.from_file(wavfile)
        srate = audio.frame_rate
        print(f'srate:{srate}')

        # check if asr files already exist, if so, zip them up to make a backup then delete   
        if not os.path.exists(asrDir):
            os.makedirs(asrDir)
        if not os.path.exists(asrBlockDir):
            os.makedirs(asrBlockDir)
        # check if asr file already existed, and backup if so
        if os.path.isfile(asrDir):
            now = datetime.now()
            datestr = now.strftime("%d-%m-%Y_%H%M%S")
            zipfile = shutil.make_archive(base_name =os.path.join(asrDir,f'backup_{datestr}'), 
            format='zip', 
            root_dir = asrDir,
            base_dir = asrDir)
            print(f"ASR already existed. Backed the file up to {zipfile}") 
            os.remove(asrfile)

        segDir = os.path.join(sesspath, 'timestamp_segments')
        if os.path.exists(segDir):
            for segment in os.listdir(segDir):
                seg_count = segment.split("utterance")[-1].split(".")[0]
                segment = os.path.join(segDir,segment)
                res = transcribe(client, segment)
                # write segmentwise ASR result
                asrfile = f'{seg_count}.txt'
                asrfile = os.path.join(asrDir, asrfile)
                with open(asrfile,'w') as outfile:
                    outfile.write(res + '\n')
        else:
            print(f"Segment directory {segDir} not found.")

