import os
import numpy as np
import collections
import librosa
import torch
import random
from torch.utils.data import Dataset

from utils.text import text_to_sequence
from utils.data import (prepare_data, pad_per_step, prepare_tensor,
                        prepare_stop_target)


class MyDataset(Dataset):
    def __init__(self,
                 root_path,
                 meta_file,
                 outputs_per_step,
                 text_cleaner,
                 ap,
                 preprocessor,
                 batch_group_size=0,
                 min_seq_len=0):
        self.root_path = root_path
        self.batch_group_size = batch_group_size
        self.items = preprocessor(root_path, meta_file)
        self.outputs_per_step = outputs_per_step
        self.sample_rate = ap.sample_rate
        self.cleaners = text_cleaner
        self.min_seq_len = min_seq_len
        self.ap = ap
        print(" > Reading LJSpeech from - {}".format(root_path))
        print(" | > Number of instances : {}".format(len(self.items)))
        self.sort_items()

    def load_wav(self, filename):
        try:
            audio = self.ap.load_wav(filename)
            return audio
        except RuntimeError as e:
            print(" !! Cannot read file : {}".format(filename))

    def sort_items(self):
        r"""Sort text sequences in ascending order"""
        lengths = np.array([len(ins[0]) for ins in self.items])

        print(" | > Max length sequence {}".format(np.max(lengths)))
        print(" | > Min length sequence {}".format(np.min(lengths)))
        print(" | > Avg length sequence {}".format(np.mean(lengths)))

        idxs = np.argsort(lengths)
        new_items = []
        ignored = []
        for i, idx in enumerate(idxs):
            length = lengths[idx]
            if length < self.min_seq_len:
                ignored.append(idx)
            else:
                new_items.append(self.items[idx])
        print(" | > {} instances are ignored by min_seq_len ({})".format(
            len(ignored), self.min_seq_len))
        # shuffle batch groups
        if self.batch_group_size > 0:
            print(" | > Batch group shuffling is active.")
            for i in range(len(new_items) // self.batch_group_size):
                offset = i * self.batch_group_size
                end_offset = offset + self.batch_group_size
                temp_items = new_items[offset : end_offset]
                random.shuffle(temp_items)
                new_items[offset : end_offset] = temp_items
        self.items = new_items

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        text, wav_file = self.items[idx]
        text = np.asarray(
            text_to_sequence(text, [self.cleaners]), dtype=np.int32)
        wav = np.asarray(self.load_wav(wav_file), dtype=np.float32)
        sample = {'text': text, 'wav': wav, 'item_idx': self.items[idx][1]}
        return sample

    def collate_fn(self, batch):
        r"""
            Perform preprocessing and create a final data batch:
            1. PAD sequences with the longest sequence in the batch
            2. Convert Audio signal to Spectrograms.
            3. PAD sequences that can be divided by r.
            4. Convert Numpy to Torch tensors.
        """

        # Puts each data field into a tensor with outer dimension batch size
        if isinstance(batch[0], collections.Mapping):
            keys = list()

            wav = [d['wav'] for d in batch]
            item_idxs = [d['item_idx'] for d in batch]
            text = [d['text'] for d in batch]

            text_lenghts = np.array([len(x) for x in text])
            max_text_len = np.max(text_lenghts)

            linear = [self.ap.spectrogram(w).astype('float32') for w in wav]
            mel = [self.ap.melspectrogram(w).astype('float32') for w in wav]
            mel_lengths = [m.shape[1] + 1 for m in mel]  # +1 for zero-frame

            # compute 'stop token' targets
            stop_targets = [
                np.array([0.] * (mel_len - 1)) for mel_len in mel_lengths
            ]

            # PAD stop targets
            stop_targets = prepare_stop_target(stop_targets,
                                               self.outputs_per_step)

            # PAD sequences with largest length of the batch
            text = prepare_data(text).astype(np.int32)
            wav = prepare_data(wav)

            # PAD features with largest length + a zero frame
            linear = prepare_tensor(linear, self.outputs_per_step)
            mel = prepare_tensor(mel, self.outputs_per_step)
            assert mel.shape[2] == linear.shape[2]
            timesteps = mel.shape[2]

            # B x T x D
            linear = linear.transpose(0, 2, 1)
            mel = mel.transpose(0, 2, 1)

            # convert things to pytorch
            text_lenghts = torch.LongTensor(text_lenghts)
            text = torch.LongTensor(text)
            linear = torch.FloatTensor(linear).contiguous()
            mel = torch.FloatTensor(mel).contiguous()
            mel_lengths = torch.LongTensor(mel_lengths)
            stop_targets = torch.FloatTensor(stop_targets)

            return text, text_lenghts, linear, mel, mel_lengths, stop_targets, item_idxs

        raise TypeError(("batch must contain tensors, numbers, dicts or lists;\
                         found {}".format(type(batch[0]))))
