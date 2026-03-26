import sys
import json
import csv
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
        epilog="""输出格式 (--format) 说明：
  human  默认，人类可读的多行格式
  simple 每行仅输出 0 或 1，最简洁
  json   JSON 数组，每项含 text/label/confidence 字段
  csv    CSV 格式，含 text,label,confidence 表头

使用示例：
  python predict.py --text "这家酒店非常棒，强烈推荐！"
  python predict.py --text "服务很好" "太差了" --format json
  python predict.py --file input.txt --format csv
  python predict.py --text "服务很好" --format simple
""",
    )
    parser.add_argument(
        '--text', nargs='+', metavar='TEXT',
        help='待分析的文本，可提供多条（含空格的文本用引号括起）',
    )
    parser.add_argument(
        '--file', metavar='FILE',
        help='文本文件路径，每行一条文本',
    )
    parser.add_argument(
        '--format', choices=['human', 'simple', 'json', 'csv'],
        default='human', dest='fmt',
        help='输出格式：human | simple | json | csv（默认 human）',
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
    if args.fmt == 'human':
        print('加载模型...')
    model, vocab = load_model(device)

    # 批量推理
    results = []
    for text in texts:
        label, conf = predict(text, model, vocab, device)
        flag = 1 if '积极' in label else 0
        results.append({'text': text, 'label': flag, 'confidence': round(conf, 4)})

    # 按格式输出
    if args.fmt == 'simple':
        for r in results:
            print(r['label'])

    elif args.fmt == 'json':
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif args.fmt == 'csv':
        writer = csv.DictWriter(sys.stdout, fieldnames=['text', 'label', 'confidence'],
                                lineterminator='\n')
        writer.writeheader()
        writer.writerows(results)

    else:  # human
        print('\n──── 情感分析结果 ────')
        for r in results:
            sentiment = '积极 😊 (Positive)' if r['label'] == 1 else '消极 😞 (Negative)'
            print(f'【输入】{r["text"]}')
            print(f'【预测】{sentiment}  置信度: {r["confidence"]:.2%}  结果: {r["label"]}\n')
