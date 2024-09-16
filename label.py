# Todo map labels to samples
#todo segment to noisy
import numpy as np
import os
import csv
import math
import statistics
import pandas as pd

def get_timestamps(sesslist):
    times = []
    for sess in sesslist:
        group = os.path.basename(sess)
        print(f"Timestamps for {group}")
        timestamps = os.path.join(sess,group+"_Google.csv")
        timesdf = pd.read_csv(timestamps, usecols = ['Start', 'End'])
        for i in range(len(timesdf['Start'])):
            utterance_ID = group + "_" + str(i)
            times.append([group, utterance_ID,timesdf['Start'].iloc[i],timesdf['End'].iloc[i]])
            print(times[-1])
    all_times_df = pd.DataFrame(times, columns = ["Group", "utteranceID", "Start", "End"])
    return all_times_df


def get_labels(all_times_df,labelcsv):
    labeldf = pd.read_csv(labelcsv)
    labels = []
    for i in range(len(all_times_df["Group"])):#todo: not ordered, handle by group names
        labels_exist = False
        for j in range(len(labeldf["Group"])):
            if(all_times_df["Group"].iloc[i]==labeldf["Group"].iloc[j]):
                if(float(all_times_df["Start"].iloc[i]) <= float(labeldf["End"].iloc[j])):
                    if(float(all_times_df["End"].iloc[i]) >= float(labeldf["Start"].iloc[j])):
                        if(labels_exist):
                            new_labels = [int(x) for x in list(labeldf.iloc[j])[4:]]
                            labels[i][-19:] = [sum(x) for x in zip(labels[i][-19:], new_labels)]
                            labels[i][-19:] = [1 if x>0 else 0 for x in labels[i][-19:]]
                        else:
                            curr_labels = list(all_times_df.iloc[i])
                            curr_labels.extend([int(x) for x in list(labeldf.iloc[j])[4:]])
                            labels_exist = True
                            labels.append(curr_labels)
        if not labels_exist:
            curr_labels = list(all_times_df.iloc[i])
            curr_labels.extend([0 for x in range(19)])
            labels_exist = True
            labels.append(curr_labels)
    headers = list(all_times_df.columns)
    headers.extend(list(labeldf.columns)[4:])
    all_labels_df = pd.DataFrame(labels,columns=headers)
    return all_labels_df

def get_verbal(sesslist, all_labels_df):
    bertembedding = {}
    verbal = []
    for sess in sesslist:
        group = os.path.basename(sess)
        header = ['bert_' + str(i) for i in range(512)]
        bertCSV = os.path.join(sess,"clean_bert", group + "_google-asr_bert.csv")
        with open(bertCSV, newline='') as bertfile:
            csvreader = csv.reader(bertfile)
            for row in csvreader:
                embedding = row[1]
                embedding = embedding.split('[[')[1]
                embedding = embedding.split(']]')[0]
                listembedding = embedding.split()
                utterance = group + "_" + row[0]
                bertembedding[utterance] = listembedding
    for i in range(len(all_labels_df["utteranceID"])):
        bert = bertembedding[all_labels_df["utteranceID"].iloc[i]]
        curr_bert = list(all_labels_df.iloc[i])
        curr_bert.extend(bert)
        verbal.append(curr_bert)
    headers = list(all_labels_df.columns)
    headers.extend(header)
    all_verbal_df = pd.DataFrame(verbal, columns=headers)
    return all_verbal_df

def get_acoustic(sesslist, all_labels_df):
    openSMILEDict = {}
    acoustic = []
    for sess in sesslist:
        openSMILE = []
        group = os.path.basename(sess)
        openSMILECSV = os.path.join(sess,group + "_clean_opensmile.csv")
        with open(openSMILECSV, newline='') as smilefile:
            csvreader = csv.reader(smilefile)
            header = next(csvreader, None)[3:]
            for row in csvreader:
                openSMILE.append(row)
            for utterance in range(len(openSMILE)):
                openSMILE[utterance][0] = openSMILE[utterance][0].split("_")[-1]
                openSMILE[utterance][0] = openSMILE[utterance][0].split(".")[0]
                utteranceID = group +"_"+openSMILE[utterance][0]
                # print(utteranceID) #todo: Group_01_0 key error???
                openSMILEDict[utteranceID] = openSMILE[utterance][3:]
    for i in range(len(all_labels_df["utteranceID"])):
        smile = openSMILEDict[all_labels_df["utteranceID"].iloc[i]]
        curr_acoustic = list(all_labels_df.iloc[i])
        curr_acoustic.extend(smile)
        acoustic.append(curr_acoustic)
    headers = list(all_labels_df.columns)
    headers.extend(header)
    all_verbal_df = pd.DataFrame(acoustic, columns=headers)
    return all_verbal_df

def create_csv(sesslist,labels,features,verbal=True,acoustic=True):
    timestamps_df = get_timestamps(sesslist)
    labels_df = get_labels(timestamps_df,labels)
    if(verbal):
        labels_df = get_verbal(sesslist, labels_df)
    if(acoustic):
        labels_df = get_acoustic(sesslist,labels_df)
    labels_df.to_csv(features, index=False)
    