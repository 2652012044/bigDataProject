import sys
import argparse
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
    model.to(device)
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
    parser = argparse.ArgumentParser(
        description='情感分类命令行工具（1=积极，0=消极）',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""使用示例：
  # 直接输入单条文本
  python predict.py --text "这家酒店非常棒，强烈推荐！"

  # 输入多条文本
  python predict.py --text "服务很好" "太差了"

  # 从文件读取（每行一条文本）
  python predict.py --file input.txt

  # 只输出 0/1（适合脚本调用）
  python predict.py --text "服务很好" --simple
""",
    )
    parser.add_argument(
        '--text', nargs='+', metavar='TEXT',
        help='待分析的文本，可提供多条（空格分隔，含空格的文本用引号括起）',
    )
    parser.add_argument(
        '--file', metavar='FILE',
        help='文本文件路径，每行一条文本',
    )
    parser.add_argument(
        '--simple', action='store_true',
        help='简洁输出模式：每行只输出 0 或 1，适合脚本调用',
    )
    args = parser.parse_args()

    # 收集待分析文本
    texts = []
    if args.text:
        texts.extend(args.text)
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f'错误：文件不存在 -> {file_path}', file=sys.stderr)
            sys.exit(1)
        with open(file_path, 'r', encoding='utf-8') as f:
            texts.extend(line.strip() for line in f if line.strip())

    if not texts:
        parser.print_help()
        sys.exit(0)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    if not args.simple:
        print('加载模型...')
    model, vocab = load_model(device)

    if args.simple:
        # 简洁模式：每行只输出 0/1
        for text in texts:
            label, _ = predict(text, model, vocab, device)
            flag = 1 if '积极' in label else 0
            print(flag)
    else:
        print('\n──── 情感分析结果 ────')
        for text in texts:
            label, conf = predict(text, model, vocab, device)
            flag = 1 if '积极' in label else 0
            print(f'【输入】{text}')
            print(f'【预测】{label}  置信度: {conf:.2%}  结果: {flag}\n')
