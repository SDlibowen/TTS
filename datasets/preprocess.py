import os
import random

def tts_cache(root_path, meta_file):
    txt_file = os.path.join(root_path, meta_file)
    items = []
    with open(txt_file, 'r', encoding='utf8') as f:
        for line in f:
            cols = line.split('| ')
            items.append(cols)  # wav_full_path, mel_name, linear_name, wav_len, mel_len, text
    random.shuffle(items)
    return items            


def tweb(root_path, meta_file):
    # TODO
    pass
    return 
    

def kusal(root_path, meta_file):
    txt_file = os.path.join(root_path, meta_file)
    texts = []
    wavs = []
    with open(txt_file, "r", encoding="utf8") as f:
        frames = [
            line.split('\t') for line in f
            if line.split('\t')[0] in self.wav_files_dict.keys()
        ]
    # TODO: code the rest
    return  {'text': texts, 'wavs': wavs}


def ljspeech(root_path, meta_file):
    """Normalizes the Nancy meta data file to TTS format"""
    txt_file = os.path.join(root_path, meta_file)
    items = []
    with open(txt_file, 'r') as ttf:
        for line in ttf:
            cols = line.split('|')
            wav_file = os.path.join(root_path, 'wavs', cols[0]+'.wav')
            text = cols[1]
            items.append([text, wav_file])
    random.shuffle(items)
    return items


def nancy(root_path, meta_file):
    """Normalizes the Nancy meta data file to TTS format"""
    txt_file = os.path.join(root_path, meta_file)
    items = []
    with open(txt_file, 'r') as ttf:
        for line in ttf:
            id = line.split()[1]
            text = line[line.find('"')+1:line.rfind('"')-1]
            wav_file = root_path + 'wavn/' + id + '.wav'
            items.append(text, wav_file)
    random.shuffle(items)    
    return items