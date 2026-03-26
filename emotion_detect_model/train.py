import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from pathlib import Path

from dataLoader import SentimentDataset, Vocabulary
from model import TransformerClassifier

# ── 超参数 ──────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
MAX_LEN         = 256
BATCH_SIZE      = 32
EPOCHS          = 10
LR              = 1e-3
D_MODEL         = 128
NHEAD           = 4
NUM_LAYERS      = 2
DIM_FFN         = 256
DROPOUT         = 0.1
# ─────────────────────────────────────────────────────────


def build_vocab():
    vocab = Vocabulary()
    train_path = BASE_DIR / 'train' / 'part.0'
    texts = []
    with open(train_path, 'r', encoding='utf-8') as f:
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

    train_ds = SentimentDataset(BASE_DIR / 'train' / 'part.0', vocab, MAX_LEN)
    dev_ds   = SentimentDataset(BASE_DIR / 'dev'   / 'part.0', vocab, MAX_LEN)
    print(f'训练集: {len(train_ds)} 条  验证集: {len(dev_ds)} 条')

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
    dev_loader   = DataLoader(dev_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

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

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)

    best_acc = 0.0
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
            total_loss += loss.item()

        scheduler.step()
        val_loss, val_acc = evaluate(model, dev_loader, criterion, device)
        print(
            f'Epoch {epoch:2d}/{EPOCHS} | '
            f'Train Loss: {total_loss/len(train_loader):.4f} | '
            f'Val Loss: {val_loss:.4f} | '
            f'Val Acc: {val_acc:.4f}'
        )

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), BASE_DIR / 'best_model.pth')
            print(f'  -> 最优模型已保存 (acc={best_acc:.4f})')

    print(f'\n训练完成，最优验证准确率: {best_acc:.4f}')


if __name__ == '__main__':
    train()
