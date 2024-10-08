from rosy_asr_utils import * 
from pathlib import Path
from pydub import AudioSegment
import io
import csv

def get_vad(sesslist):
    # segmentation options
    agg = 1 # aggressiveness
    frame_msec = 30 # frame length sent to VAD
    win_size = 300 # ms, ring buffer used for VAD 
    min_seg_dur = 2000 # ms. minimum segment duration
    blksecs = 59 # Google has refused some blocks if exactly 60 seconds 
    split_overlap = 1 # for long segments, overlap by this duration in seconds to avoid word splitting
    # .wav audio output options:
    channels = 1 # audio channels
    sample_width = 2 # bytes per sample, should usually be 2
    sample_rate = 48000 # sample rate (16k suffices for ASR, but loses high frequency content)

    for sesspath in sesslist: 
        print(f'\nsesspath: {sesspath}')
        # sessname = Path(sesspath).stem
        # sesspath = os.path.join(sesspath)

        wavlist = [f for f in os.listdir(sesspath) if f.endswith('.wav')]

        segDir = os.path.join(sesspath, 'segments')
        blkDir = os.path.join(sesspath, 'blocks')

        if not os.path.exists(segDir):
            os.makedirs(segDir)
        if not os.path.exists(blkDir):
            os.makedirs(blkDir)

        for w in wavlist:       
            wbasename = Path(w).stem
            print(f'Processing wav file: {wbasename}')
            audio, sample_rate = read_wave(os.path.join(sesspath,w))
            vad = webrtcvad.Vad(int(agg))
            frames = frame_generator(frame_msec, audio, sample_rate)
            frames = list(frames)
            segment_generator = vad_collector(sample_rate,frame_msec,int(win_size), vad, frames, min_seg_dur)

            blkmapFile = os.path.join(sesspath,f'{wbasename}.blk')
            
            blkmap = []
            blknum= 0
            this_block = AudioSegment.empty() # for raw audio data
            curlen = 0.0
            added_segs = 0
            seg_beg = []
            seg_end = []
            for i, (segment, info) in enumerate(segment_generator):

                snum,beg,end = info
                seg_beg.append(beg)
                seg_end.append(end)
                dur = end - beg
                stream = io.BytesIO(segment)
                seg_audio = AudioSegment.from_raw(stream, sample_width=sample_width, frame_rate=sample_rate, channels=channels)

                # Note that soon an XVector-based target activity filter will be inserted at this point to select segments to keep

                # split segments longer than requested block duration
                if dur > blksecs:
                    nsplits = int(np.floor((dur-split_overlap)/(blksecs-split_overlap)))
                    print(f'VAD segment at block {blknum} is longer than requested block duration, will split into {nsplits+1}')
                    seg_beg.pop()
                    seg_end.pop()
                    for k in range(0,nsplits):
                        beg_trim = k*(blksecs-split_overlap)
                        end_trim = beg_trim + blksecs
                        segment_trim = seg_audio[np.round(beg_trim*1000):np.round(end_trim*1000)]
                        # print(f'trimmed AudioSegment length:{segment_trim.duration_seconds}')
                        blkmap.append( (blknum, added_segs+snum, beg+beg_trim, beg+end_trim)) 
                        blkwavpath = os.path.join(blkDir,f'{wbasename}_{blknum}.wav' )
                        segment_trim.export(blkwavpath, format='wav')
                        
                        segwavpath = os.path.join(segDir,f'{wbasename}_{added_segs+snum}.wav' )
                        segment_trim.export(segwavpath, format='wav')
                        seg_beg.append(beg+beg_trim)
                        seg_end.append(beg+end_trim)

                        added_segs +=1 # will offset all future segment numbers by this count 
                        # start new audio block
                        blknum += 1
                        this_block = AudioSegment.empty()
                        curlen = 0.0
                    # for final split leave the block incomplete to append to other segments
                    seg_audio = seg_audio[end_trim*1000: dur*1000] 
                    this_block += seg_audio
                    curlen += dur-end_trim
                    seg_beg.append(beg+end_trim)
                    seg_end.append(end)
                    blkmap.append( (blknum, added_segs+snum, beg+end_trim, end) )
                    segwavpath = os.path.join(segDir,f'{wbasename}_{added_segs+snum}.wav' )
                    seg_audio.export(segwavpath, format='wav') 
                    continue 

                # add segment to current block
                if (curlen + dur) <= blksecs:
                    this_block += seg_audio
                    blkmap.append( (blknum, added_segs+snum, beg,end) )
                    curlen += dur
                    segwavpath = os.path.join(segDir,f'{wbasename}_{added_segs+snum}.wav' )
                    seg_audio.export(segwavpath, format='wav') 
                    continue

                # export audio
                else:
                    # complete block and write audio
                    blkwavpath = os.path.join(blkDir,f'{wbasename}_{blknum}.wav' )
                    this_block.export(blkwavpath, format='wav')
                    segwavpath = os.path.join(segDir,f'{wbasename}_{added_segs+snum}.wav' )
                    seg_audio.export(segwavpath, format='wav') 
                    # start new audio block
                    blknum += 1
                    this_block = AudioSegment.empty()
                    this_block += seg_audio
                    blkmap.append( (blknum, added_segs+snum, beg,end) )
                    curlen = dur

    

            # end of loop over segments: write out any remaining audio to final block
            blkwavpath = os.path.join(blkDir,f'{wbasename}_{blknum}.wav' )
            this_block.export(blkwavpath, format='wav')
            timestamps = zip(seg_beg, seg_end)
            timestampscsv = os.path.join(sesspath,f'{wbasename}_timestamps.csv')
            with open(timestampscsv, "w", newline = '') as f:
                writer = csv.writer(f)
                for row in timestamps:
                    writer.writerow(row)

            with open(blkmapFile, 'w') as outfile:
                for b in blkmap:
                    line = ' '.join(str(x) for x in b)
                    outfile.write(line + '\n')

            # segment coverage - how much audio remains after VAD filtering. 
            coverage = segment_coverage(blkmapFile, os.path.join(sesspath,w))
            print(f'SEGMENT COVERAGE: {100*coverage:.2f}% of original audio [{w}]')
            if coverage >1:
                print('--coverage greater than 100%% because of overlap between split segments')