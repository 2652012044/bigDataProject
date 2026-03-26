import math
import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    """正弦/余弦位置编码"""

    def __init__(self, d_model, max_len=512, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class TransformerClassifier(nn.Module):
    """
    基于 Transformer Encoder 的文本二分类模型。
    输入：字符级 token id 序列
    输出：[消极, 积极] 的 logits
    """

    def __init__(
        self,
        vocab_size,
        d_model=128,
        nhead=4,
        num_layers=2,
        dim_feedforward=256,
        num_classes=2,
        max_len=256,
        dropout=0.1,
    ):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=0)
        self.pos_encoding = PositionalEncoding(d_model, max_len, dropout)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.classifier = nn.Linear(d_model, num_classes)
        self.dropout = nn.Dropout(dropout)

    def forward(self, input_ids, attention_mask=None):
        # input_ids: (batch, seq_len)
        x = self.embedding(input_ids)        # (batch, seq_len, d_model)
        x = self.pos_encoding(x)

        # padding mask：True 表示该位置是填充，需忽略
        src_key_padding_mask = None
        if attention_mask is not None:
            src_key_padding_mask = (attention_mask == 0)

        x = self.transformer(x, src_key_padding_mask=src_key_padding_mask)

        # 对非填充位置做均值池化
        if attention_mask is not None:
            mask = attention_mask.unsqueeze(-1).float()
            x = (x * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        else:
            x = x.mean(dim=1)

        x = self.dropout(x)
        logits = self.classifier(x)
        return logits
