import math
import warnings
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, ConcatDataset
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
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    with torch.no_grad():
        for batch in loader:
            input_ids = batch['input_ids'].to(device)
            mask      = batch['attention_mask'].to(device)
            labels    = batch['label'].to(device)
            logits    = model(input_ids, mask)
            total_loss += criterion(logits, labels).item()
            correct    += (logits.argmax(dim=-1) == labels).sum().item()
            total      += labels.size(0)
    return total_loss / len(loader), correct / total


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

    # ── 验证集一：原始 ChnSentiCorp dev ──
    dev_ds    = SentimentDataset(BASE_DIR / 'dev' / 'part.0', vocab, MAX_LEN)
    print(f'  原始验证集(ChnSentiCorp): {len(dev_ds):6d} 条')

    # ── 验证集二：小说评论 val ──
    novel_val_path = BASE_DIR / 'novel_comment_data' / 'val.txt'
    novel_val_ds   = SentimentDataset(novel_val_path, vocab, MAX_LEN)
    print(f'  小说评论验证集:           {len(novel_val_ds):6d} 条\n')

    train_loader     = DataLoader(train_ds,     batch_size=BATCH_SIZE, shuffle=True,  num_workers=4)
    dev_loader       = DataLoader(dev_ds,       batch_size=BATCH_SIZE, shuffle=False, num_workers=4)
    novel_val_loader = DataLoader(novel_val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

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

    # 标签平滑：label_smoothing > 0 时对噪声标签更鲁棒
    criterion = nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING)
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

        val_loss,       val_acc       = evaluate(model, dev_loader,       criterion, device)
        novel_val_loss, novel_val_acc = evaluate(model, novel_val_loader, criterion, device)
        print(
            f'Epoch {epoch:2d}/{EPOCHS} | '
            f'Train Loss: {total_loss/len(train_loader):.4f} | '
            f'ChnSenti Val Acc: {val_acc:.4f} | '
            f'Novel Val Acc: {novel_val_acc:.4f}'
        )

        if novel_val_acc > best_novel_acc:
            best_novel_acc = novel_val_acc
            torch.save(model.state_dict(), BASE_DIR / 'best_model.pth')
            print(f'  -> 最优模型已保存 (小说评论验证集 acc={best_novel_acc:.4f})')

    print(f'\n训练完成，最优小说评论验证集准确率: {best_novel_acc:.4f}')


if __name__ == '__main__':
    train()
