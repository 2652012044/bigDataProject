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

    # 补充短文本样本，覆盖模型未见过的极短负/正面表达
    _EXTRA_SAMPLES = [
        ('恶心', 0), ('恶心透了', 0), ('垃圾', 0), ('太差了', 0), ('差劲', 0),
        ('糟透了', 0), ('失望', 0), ('后悔', 0), ('不推荐', 0), ('很差', 0),
        ('服务很差', 0), ('质量差', 0), ('太烂了', 0), ('坑人', 0), ('骗人', 0),
        ('差评', 0), ('不值', 0), ('一般般', 0), ('很一般', 0), ('不好', 0),
        ('棒', 1), ('很棒', 1), ('太棒了', 1), ('非常好', 1), ('超赞', 1),
        ('推荐', 1), ('满意', 1), ('值得', 1), ('好评', 1), ('不错', 1),
        ('服务很好', 1), ('质量好', 1), ('喜欢', 1), ('完美', 1), ('超值', 1),
    ]

    def __init__(self, data_path, vocab, max_len=256, augment=False):
        self.vocab = vocab
        self.max_len = max_len
        self.data = self._load(data_path)
        if augment:
            self.data.extend(self._EXTRA_SAMPLES * 10)  # 每条重复10次使权重适当

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
