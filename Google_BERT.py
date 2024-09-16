# todo
import os
import shutil

import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text as text
from official.nlp import optimization  # to create AdamW optimizer

import matplotlib.pyplot as plt
import csv

def get_BERT(sesslist):
    tf.get_logger().setLevel('ERROR')
    bert_model = "https://tfhub.dev/tensorflow/small_bert/bert_en_uncased_L-2_H-512_A-8/1"
    bert_preprocess =  "https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3"
    bert_preprocess_model = hub.KerasLayer(bert_preprocess)
    bert_model = hub.KerasLayer(bert_model)
    
    for sess in sesslist:
        group = os.path.basename(sess)
        print("Running ", group)
        #audio = sess + "/" + group + "-audio_PCM"
        asrdir = sess + "/clean_google_asr"
        bertdir = sess + "/clean_bert"
        bertReps = []

        if not os.path.isdir(bertdir):
            os.mkdir(bertdir)

        for segASR in os.listdir(asrdir):
            with open(asrdir + '/' + segASR) as asr:
                segASRtxt = asr.read()#.splitlines()
            segASRtxt = segASRtxt.replace("\n", '')
            segASRtxt = segASRtxt.replace(",", '')
            segASRtxt = segASRtxt.replace('.', '')
            segASRtxt = [segASRtxt]
            print(segASRtxt)
            asr_preprocessed = bert_preprocess_model(segASRtxt)
            bert_results = bert_model(asr_preprocessed)
            bertReps.append([segASR.split("_")[-1].split('.')[0],bert_results["pooled_output"]])
            print(bert_results["pooled_output"])
        with open(bertdir + '/' + group + "_google-asr_bert.csv", "w", newline = '') as f:
            writer = csv.writer(f)
            writer.writerows(bertReps)


