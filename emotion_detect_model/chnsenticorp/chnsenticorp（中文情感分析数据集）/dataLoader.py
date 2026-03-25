import json
import torch
from pathlib import Path
from torch.utils.data import Dataset


class Vocabulary:
    """字符级词表：将每个汉字/字符映射为整数索引"""

    def __init__(self):
        self.char2idx = {'<PAD>': 0, '<UNK>': 1}
        self.idx2char = {0: '<PAD>', 1: '<UNK>'}

    def build(self, texts):
        for text in texts:
            for char in text:
                if char not in self.char2idx:
                    idx = len(self.char2idx)
                    self.char2idx[char] = idx
                    self.idx2char[idx] = char

    def encode(self, text):
        return [self.char2idx.get(c, 1) for c in text]

    def __len__(self):
        return len(self.char2idx)

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.char2idx, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        vocab = cls()
        with open(path, 'r', encoding='utf-8') as f:
            vocab.char2idx = json.load(f)
        vocab.idx2char = {v: k for k, v in vocab.char2idx.items()}
        return vocab


class SentimentDataset(Dataset):
    """读取 tab 分隔的情感数据集，格式：文本\t标签(0/1)"""

    def __init__(self, data_path, vocab, max_len=256):
        self.vocab = vocab
        self.max_len = max_len
        self.data = self._load(data_path)

    def _load(self, path):
        data = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) == 2:
                    text, label = parts[0], int(parts[1])
                    data.append((text, label))
        return data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        text, label = self.data[idx]
        ids = self.vocab.encode(text)[:self.max_len]
        attention_mask = [1] * len(ids)
        # 补齐到 max_len
        pad_len = self.max_len - len(ids)
        ids += [0] * pad_len
        attention_mask += [0] * pad_len
        return {
            'input_ids': torch.tensor(ids, dtype=torch.long),
            'attention_mask': torch.tensor(attention_mask, dtype=torch.long),
            'label': torch.tensor(label, dtype=torch.long),
        }
