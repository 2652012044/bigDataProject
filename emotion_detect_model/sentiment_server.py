"""
情感分析 Flask API 服务
包装 Transformer 模型为 HTTP 接口，供 Spring Boot 后端调用
启动: python sentiment_server.py
"""
import torch
from flask import Flask, request, jsonify
from pathlib import Path

from dataLoader import Vocabulary
from model import TransformerClassifier

app = Flask(__name__)

# ── 模型参数（与 train.py 保持一致） ──
BASE_DIR   = Path(__file__).parent
MAX_LEN    = 256
D_MODEL    = 128
NHEAD      = 4
NUM_LAYERS = 2
DIM_FFN    = 256

NEUTRAL_THRESHOLD = 0.60  # 置信度低于此值 → 中性

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model  = None
vocab  = None


def load_model():
    global model, vocab
    vocab = Vocabulary.load(BASE_DIR / 'vocab.json')
    model = TransformerClassifier(
        vocab_size=len(vocab), d_model=D_MODEL, nhead=NHEAD,
        num_layers=NUM_LAYERS, dim_feedforward=DIM_FFN,
        num_classes=2, max_len=MAX_LEN,
    )
    model.load_state_dict(
        torch.load(BASE_DIR / 'best_model.pth', map_location=device)
    )
    model.to(device).eval()


def _encode(text):
    ids = vocab.encode(text)[:MAX_LEN]
    mask = [1] * len(ids)
    pad = MAX_LEN - len(ids)
    ids  += [0] * pad
    mask += [0] * pad
    return ids, mask


def _to_result(pred, conf, pos_prob, neg_prob):
    if conf < NEUTRAL_THRESHOLD:
        label = 'neutral'
    elif pred == 1:
        label = 'positive'
    else:
        label = 'negative'
    return {
        'label': label,
        'confidence': round(conf, 4),
        'raw_label': pred,
        'positive_prob': round(pos_prob, 4),
        'negative_prob': round(neg_prob, 4),
    }


# ── 单条预测 ──
@app.route('/predict', methods=['POST'])
def predict_single():
    text = (request.json or {}).get('text', '')
    if not text:
        return jsonify({'error': 'text is required'}), 400

    ids, mask = _encode(text)
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    att_mask  = torch.tensor([mask], dtype=torch.long, device=device)

    with torch.no_grad():
        logits = model(input_ids, att_mask)
        probs  = torch.softmax(logits, dim=-1)
        pred   = probs.argmax(dim=-1).item()
        conf   = probs[0][pred].item()

    return jsonify(_to_result(pred, conf, probs[0][1].item(), probs[0][0].item()))


# ── 批量预测 ──
@app.route('/batch_predict', methods=['POST'])
def predict_batch():
    texts = (request.json or {}).get('texts', [])
    if not texts:
        return jsonify({'results': []})

    CHUNK = 64
    all_results = []

    for start in range(0, len(texts), CHUNK):
        chunk = texts[start:start + CHUNK]
        batch_ids, batch_masks = [], []
        for t in chunk:
            ids, mask = _encode(t)
            batch_ids.append(ids)
            batch_masks.append(mask)

        input_ids = torch.tensor(batch_ids,   dtype=torch.long, device=device)
        att_mask  = torch.tensor(batch_masks,  dtype=torch.long, device=device)

        with torch.no_grad():
            logits = model(input_ids, att_mask)
            probs  = torch.softmax(logits, dim=-1)
            preds  = probs.argmax(dim=-1)

        for i in range(len(chunk)):
            p = preds[i].item()
            c = probs[i][p].item()
            all_results.append(_to_result(p, c, probs[i][1].item(), probs[i][0].item()))

    return jsonify({'results': all_results})


# ── 模型信息 ──
@app.route('/model_info', methods=['GET'])
def model_info():
    return jsonify({
        'algorithm': 'Transformer Encoder (字符级二分类)',
        'model_name': 'TransformerClassifier',
        'd_model': D_MODEL,
        'nhead': NHEAD,
        'num_layers': NUM_LAYERS,
        'dim_feedforward': DIM_FFN,
        'max_len': MAX_LEN,
        'vocab_size': len(vocab),
        'num_classes': 2,
        'neutral_threshold': NEUTRAL_THRESHOLD,
        'device': device,
        'trained': True,
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    print('正在加载 Transformer 情感分析模型...')
    load_model()
    print(f'模型加载完成 | device={device} | vocab_size={len(vocab)}')
    app.run(host='0.0.0.0', port=5001, debug=False)
