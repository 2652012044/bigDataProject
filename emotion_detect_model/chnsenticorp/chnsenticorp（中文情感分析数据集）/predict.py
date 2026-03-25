import torch
from pathlib import Path

from dataLoader import Vocabulary
from model import TransformerClassifier

# ── 与 train.py 保持一致 ────────────────────────────────
BASE_DIR = Path(__file__).parent
MAX_LEN  = 256
D_MODEL  = 128
NHEAD    = 4
NUM_LAYERS   = 2
DIM_FFN      = 256
# ─────────────────────────────────────────────────────────

LABELS = {0: '消极 😞 (Negative)', 1: '积极 😊 (Positive)'}


def load_model(device='cpu'):
    vocab = Vocabulary.load(BASE_DIR / 'vocab.json')
    model = TransformerClassifier(
        vocab_size      = len(vocab),
        d_model         = D_MODEL,
        nhead           = NHEAD,
        num_layers      = NUM_LAYERS,
        dim_feedforward = DIM_FFN,
        num_classes     = 2,
        max_len         = MAX_LEN,
    )
    model.load_state_dict(
        torch.load(BASE_DIR / 'best_model.pth', map_location=device)
    )
    model.eval()
    return model, vocab


def predict(text, model, vocab, device='cpu'):
    ids = vocab.encode(text)[:MAX_LEN]
    attention_mask = [1] * len(ids)
    pad_len = MAX_LEN - len(ids)
    ids            += [0] * pad_len
    attention_mask += [0] * pad_len

    input_ids = torch.tensor([ids],            dtype=torch.long).to(device)
    mask      = torch.tensor([attention_mask], dtype=torch.long).to(device)

    with torch.no_grad():
        logits = model(input_ids, mask)
        probs  = torch.softmax(logits, dim=-1)
        pred   = probs.argmax(dim=-1).item()
        conf   = probs[0][pred].item()

    return LABELS[pred], conf


if __name__ == '__main__':
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print('加载模型...')
    model, vocab = load_model(device)

    # 示例文本，可自行替换
    test_texts = [
        '这家酒店非常棒，服务很好，强烈推荐！',
        '太差了，完全不值这个价格，非常失望。',
        '房间还算整洁，位置不错，性价比一般。',
        '笔记本电脑质量很好，用着特别顺手。',
        '产品有质量问题，客服态度差，不会再买了。',
    ]

    print('\n──── 情感分析结果 ────')
    for text in test_texts:
        label, conf = predict(text, model, vocab, device)
        print(f'【输入】{text}')
        print(f'【预测】{label}  置信度: {conf:.2%}\n')
