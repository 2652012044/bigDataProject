import math
import warnings
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, ConcatDataset, WeightedRandomSampler
from pathlib import Path

warnings.filterwarnings(
    'ignore',
    message='.*nested tensor.*',
    category=UserWarning,
    module='torch',
)

from dataLoader import SentimentDataset, Vocabulary
from model import TransformerClassifier

# ── 超参数 ──────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
MAX_LEN         = 256
BATCH_SIZE      = 32
EPOCHS          = 15           # 适当增加训练轮数
LR              = 5e-4         # 降低学习率，训练更稳定
D_MODEL         = 128
NHEAD           = 4
NUM_LAYERS      = 2
DIM_FFN         = 256
DROPOUT         = 0.2          # 适当增大 dropout 缓解过拟合
LABEL_SMOOTHING = 0.1          # 标签平滑，增强对噪声标签的鲁棒性
WARMUP_STEPS    = 200          # 学习率 warmup 步数
# ─────────────────────────────────────────────────────────


def build_vocab():
    vocab = Vocabulary()
    vocab_sources = [
        BASE_DIR / 'train' / 'part.0',
        BASE_DIR / 'train' / 'part.0_expanded',
        BASE_DIR / 'novel_comment_data' / 'train.txt',
        BASE_DIR / 'novel_comment_data' / 'train_expend.txt',
    ]
    texts = []
    for path in vocab_sources:
        if not path.exists():
            continue
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    texts.append(parts[0])
    vocab.build(texts)
    return vocab


def evaluate(model, loader, criterion, device):
    """返回 (loss, acc, neg_recall, pos_recall, macro_f1)"""
    model.eval()
    total_loss = 0.0
    all_preds, all_labels = [], []
    with torch.no_grad():
        for batch in loader:
            input_ids = batch['input_ids'].to(device)
            mask      = batch['attention_mask'].to(device)
            labels    = batch['label'].to(device)
            logits    = model(input_ids, mask)
            total_loss += criterion(logits, labels).item()
            all_preds.extend(logits.argmax(dim=-1).cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

    total   = len(all_labels)
    correct = sum(p == l for p, l in zip(all_preds, all_labels))
    acc = correct / total

    # 每类 precision / recall / F1（手动计算，无需 sklearn）
    recalls, f1s = [], []
    for c in range(2):
        tp = sum(1 for p, l in zip(all_preds, all_labels) if p == c and l == c)
        fp = sum(1 for p, l in zip(all_preds, all_labels) if p == c and l != c)
        fn = sum(1 for p, l in zip(all_preds, all_labels) if p != c and l == c)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        recalls.append(rec)
        f1s.append(f1)

    macro_f1 = sum(f1s) / 2
    return total_loss / len(loader), acc, recalls[0], recalls[1], macro_f1


def train():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'使用设备: {device}')

    print('构建词表...')
    vocab = build_vocab()
    vocab.save(BASE_DIR / 'vocab.json')
    print(f'词表大小: {len(vocab)}')

    # ── 训练集：原始 + ChnSentiCorp扩充 + 小说评论train + 小说评论扩充 ──
    all_train_parts = []

    base_train_ds = SentimentDataset(BASE_DIR / 'train' / 'part.0', vocab, MAX_LEN, augment=True)
    all_train_parts.append(base_train_ds)
    print(f'  原始训练集:           {len(base_train_ds):6d} 条')

    expanded_path = BASE_DIR / 'train' / 'part.0_expanded'
    if expanded_path.exists():
        ds = SentimentDataset(expanded_path, vocab, MAX_LEN)
        all_train_parts.append(ds)
        print(f'  ChnSentiCorp 扩充集: {len(ds):6d} 条')

    novel_train_path = BASE_DIR / 'novel_comment_data' / 'train.txt'
    if novel_train_path.exists():
        ds = SentimentDataset(novel_train_path, vocab, MAX_LEN)
        all_train_parts.append(ds)
        print(f'  小说评论训练集:       {len(ds):6d} 条')

    novel_expend_path = BASE_DIR / 'novel_comment_data' / 'train_expend.txt'
    if novel_expend_path.exists():
        ds = SentimentDataset(novel_expend_path, vocab, MAX_LEN)
        all_train_parts.append(ds)
        print(f'  小说评论扩充集:       {len(ds):6d} 条')

    train_ds = ConcatDataset(all_train_parts) if len(all_train_parts) > 1 else all_train_parts[0]
    print(f'  训练集合计:           {len(train_ds):6d} 条\n')

    # ── 计算类别权重（用于 WeightedRandomSampler 和 Loss） ──
    label_counts = [0, 0]
    all_train_labels = []
    for ds in all_train_parts:
        for _, label in ds.data:   # SentimentDataset.data 暴露了标签列表
            all_train_labels.append(label)
            label_counts[label] += 1
    total_samples = len(all_train_labels)
    # 权重 = total / (num_classes * count[c])，少数类权重更大
    class_weight_values = [
        total_samples / (2.0 * max(label_counts[c], 1)) for c in range(2)
    ]
    print(f'  类别分布: 消极={label_counts[0]}, 积极={label_counts[1]}')
    print(f'  类别权重: 消极={class_weight_values[0]:.3f}, 积极={class_weight_values[1]:.3f}\n')

    # ── 验证集一：原始 ChnSentiCorp dev ──
    dev_ds    = SentimentDataset(BASE_DIR / 'dev' / 'part.0', vocab, MAX_LEN)
    print(f'  原始验证集(ChnSentiCorp): {len(dev_ds):6d} 条')

    # ── 验证集二：小说评论 val ──
    novel_val_path = BASE_DIR / 'novel_comment_data' / 'val.txt'
    novel_val_ds   = SentimentDataset(novel_val_path, vocab, MAX_LEN)
    print(f'  小说评论验证集:           {len(novel_val_ds):6d} 条\n')

    # WeightedRandomSampler：每个样本的采样权重 = 其所属类别的权重
    sample_weights = torch.tensor(
        [class_weight_values[label] for label in all_train_labels],
        dtype=torch.float32,
    )
    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(all_train_labels),
        replacement=True,
    )

    train_loader     = DataLoader(train_ds,     batch_size=BATCH_SIZE, sampler=sampler,      num_workers=4)
    dev_loader       = DataLoader(dev_ds,       batch_size=BATCH_SIZE, shuffle=False,        num_workers=4)
    novel_val_loader = DataLoader(novel_val_ds, batch_size=BATCH_SIZE, shuffle=False,        num_workers=4)

    model = TransformerClassifier(
        vocab_size     = len(vocab),
        d_model        = D_MODEL,
        nhead          = NHEAD,
        num_layers     = NUM_LAYERS,
        dim_feedforward= DIM_FFN,
        num_classes    = 2,
        max_len        = MAX_LEN,
        dropout        = DROPOUT,
    ).to(device)

    # 标签平滑 + 类别权重：同时应对噪声标签和类别不平衡
    class_weight_tensor = torch.tensor(class_weight_values, dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weight_tensor, label_smoothing=LABEL_SMOOTHING)
    # AdamW 相比 Adam 增加了权重衰减，防止过拟合
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-2)
    # warmup + 余弦退火：前 WARMUP_STEPS 步线性升温，之后余弦衰减
    total_steps = EPOCHS * len(train_loader)
    def lr_lambda(step):
        if step < WARMUP_STEPS:
            return step / max(1, WARMUP_STEPS)
        progress = (step - WARMUP_STEPS) / max(1, total_steps - WARMUP_STEPS)
        return max(0.05, 0.5 * (1.0 + math.cos(math.pi * progress)))
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

    best_novel_acc = 0.0
    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            input_ids = batch['input_ids'].to(device)
            mask      = batch['attention_mask'].to(device)
            labels    = batch['label'].to(device)

            optimizer.zero_grad()
            logits = model(input_ids, mask)
            loss   = criterion(logits, labels)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()   # LambdaLR 按 step 更新
            total_loss += loss.item()

        val_loss,  val_acc,  val_neg_rec,  val_pos_rec,  val_f1  = evaluate(model, dev_loader,       criterion, device)
        nvl_loss,  nvl_acc,  nvl_neg_rec,  nvl_pos_rec,  nvl_f1  = evaluate(model, novel_val_loader, criterion, device)
        print(
            f'Epoch {epoch:2d}/{EPOCHS} | Train Loss: {total_loss/len(train_loader):.4f} | '
            f'ChnSenti acc={val_acc:.4f} neg_rec={val_neg_rec:.4f} f1={val_f1:.4f} | '
            f'Novel    acc={nvl_acc:.4f} neg_rec={nvl_neg_rec:.4f} f1={nvl_f1:.4f}'
        )

        # 以小说验证集 macro F1 为准保存最优模型（避免准确率被多数类主导）
        if nvl_f1 > best_novel_acc:
            best_novel_acc = nvl_f1
            torch.save(model.state_dict(), BASE_DIR / 'best_model.pth')
            print(f'  -> 最优模型已保存 (小说评论验证集 macro_f1={best_novel_acc:.4f}, neg_recall={nvl_neg_rec:.4f})')

    print(f'\n训练完成，最优小说评论验证集 macro_f1: {best_novel_acc:.4f}')


if __name__ == '__main__':
    train()
