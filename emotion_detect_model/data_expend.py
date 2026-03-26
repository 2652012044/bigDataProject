"""
data_expend.py
==============
利用 DeepSeek API 对 ChnSentiCorp 训练集做三类扩充：
  1. 将每条长句拆分为有语义的短句，判断短句情感，加入扩充训练集
  2. 提取每句中对情感影响最大的关键词，构建正/负向情感词汇表
  3. 基于词汇表让 DeepSeek 生成 1000 条新句子，加入扩充训练集

支持断点续传：中断后重新运行会从上次进度继续。

运行：
    pip install openai tqdm
    python data_expend.py

输出：
    train/part.0_expanded   — 扩充后的完整训练集
    expand_vocab.json        — 提取到的情感关键词词汇表
"""

import json
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI

# ── 配置 ──────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
TRAIN_FILE    = BASE_DIR / 'train' / 'part.0'
OUTPUT_FILE   = BASE_DIR / 'train' / 'part.0_expanded'
VOCAB_FILE    = BASE_DIR / 'expand_vocab.json'
PROGRESS_FILE = BASE_DIR / 'expand_progress.json'

API_KEY       = "sk-5307ffa372b0443c990d5ea92a9d2496"
API_BASE      = "https://api.deepseek.com"
MODEL         = "deepseek-chat"

BATCH_SIZE    = 10      # 每次 API 调用处理的句子数
MAX_SAMPLES   = 9600    # 处理原始数据的上限
GEN_COUNT     = 1000    # 最终生成新句子的数量
RETRY_LIMIT   = 3       # API 报错时的重试次数
SLEEP_BETWEEN = 0.5     # 线程内两次失败重试之间的等待（秒）
MAX_WORKERS   = 50       # 并发线程数（建议不超过 API 并发限制）
# ──────────────────────────────────────────────────────────

client = OpenAI(api_key=API_KEY, base_url=API_BASE)


# ── API 调用工具 ───────────────────────────────────────────
def call_api(prompt: str, max_tokens: int = 3000) -> str:
    """带重试的 API 调用，返回模型输出文本。"""
    for attempt in range(RETRY_LIMIT):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是中文情感分析专家，只输出题目要求格式的JSON，不附加任何解释或markdown标记。",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            wait = 2 ** attempt
            print(f"  [API 错误] 第{attempt + 1}次: {exc}，{wait}s 后重试...")
            time.sleep(wait)
    return ""


def parse_json_safe(text: str):
    """从模型返回文本中提取第一个合法 JSON 对象或数组。"""
    text = text.strip()
    # 去掉 ```json ... ``` 包裹
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
    try:
        return json.loads(text)
    except Exception:
        for start_char, end_char in [('{', '}'), ('[', ']')]:
            s = text.find(start_char)
            e = text.rfind(end_char)
            if s != -1 and e != -1 and e > s:
                try:
                    return json.loads(text[s: e + 1])
                except Exception:
                    pass
    return None


# ── 核心处理函数 ───────────────────────────────────────────
def process_batch(
    batch: list[tuple[str, int]],
) -> tuple[list[tuple[str, int]], list[str], list[str]]:
    """
    处理一批原始样本（最多 BATCH_SIZE 条）。

    返回：
        new_samples  : 拆分后的短句列表 [(text, label), ...]
        pos_keywords : 本批次提取的正向关键词
        neg_keywords : 本批次提取的负向关键词
    """
    batch_json = json.dumps(
        [{"id": i, "text": t, "label": l} for i, (t, l) in enumerate(batch)],
        ensure_ascii=False,
    )

    prompt = f"""请对以下中文句子列表完成两项任务：

任务1：将每个句子拆分为若干完整语义的短句（每句2~20字），判断每个短句的情感极性：
  - 正向 → label=1
  - 负向 → label=0
  - 中性或无法判断 → 跳过，不输出

任务2：从每个句子中提取对整体情感影响最强的关键词（1~4个字），每句最多3个词，按照该词触发的情感分为正向或负向。

输入数据：
{batch_json}

严格以如下JSON格式输出（不要有任何其他文字）：
{{
  "phrases": [
    {{"text": "短句", "label": 0}},
    {{"text": "短句", "label": 1}}
  ],
  "pos_keywords": ["正向词1", "正向词2"],
  "neg_keywords": ["负向词1", "负向词2"]
}}"""

    raw = call_api(prompt, max_tokens=4000)
    if not raw:
        return [], [], []

    data = parse_json_safe(raw)
    if not isinstance(data, dict):
        return [], [], []

    new_samples: list[tuple[str, int]] = []
    for item in data.get("phrases", []):
        text = str(item.get("text", "")).strip()
        label = item.get("label")
        if text and label in (0, 1) and 2 <= len(text) <= 60:
            new_samples.append((text, int(label)))

    pos_kw = [str(w).strip() for w in data.get("pos_keywords", []) if str(w).strip()]
    neg_kw = [str(w).strip() for w in data.get("neg_keywords", []) if str(w).strip()]
    return new_samples, pos_kw, neg_kw


def _gen_one_batch(
    pos_pool: list[str],
    neg_pool: list[str],
    this_count: int,
) -> list[tuple[str, int]]:
    """生成一批新句子（单次 API 调用），供多线程调用。"""
    this_half = this_count // 2
    pos_sample = random.sample(pos_pool, min(40, len(pos_pool)))
    neg_sample = random.sample(neg_pool, min(40, len(neg_pool)))

    prompt = f"""你是中文评论数据生成专家。请根据提供的情感关键词，生成{this_count}条真实风格的中文评论：
- 前{this_half}条：积极评论，label=1
- 后{this_half}条：消极评论，label=0
- 每条长度8~60字
- 风格贴近真实用户（酒店/商品/图书/餐厅评论），多样化，不重复
- 积极关键词参考：{', '.join(pos_sample)}
- 消极关键词参考：{', '.join(neg_sample)}

只输出JSON数组，每项含text和label，示例：
[{{"text": "房间很干净，服务态度好", "label": 1}}, {{"text": "质量太差了", "label": 0}}]"""

    raw = call_api(prompt, max_tokens=6000)
    if not raw:
        return []
    data = parse_json_safe(raw)
    if not isinstance(data, list):
        return []
    result = []
    for item in data:
        text = str(item.get("text", "")).strip()
        label = item.get("label")
        if text and label in (0, 1) and 4 <= len(text) <= 100:
            result.append((text, int(label)))
    return result


def generate_sentences(
    pos_words: list[str],
    neg_words: list[str],
    count: int = 1000,
) -> list[tuple[str, int]]:
    """多线程生成 count 条新评论句子。"""
    per_call = 200
    pos_pool = pos_words if pos_words else ["好", "满意", "推荐"]
    neg_pool = neg_words if neg_words else ["差", "失望", "不推荐"]

    calls = count // per_call + (1 if count % per_call else 0)
    print(f"  共 {calls} 个生成任务，使用 {min(MAX_WORKERS, calls)} 线程并发...")

    all_samples: list[tuple[str, int]] = []
    lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, calls)) as executor:
        futures = [
            executor.submit(
                _gen_one_batch, pos_pool, neg_pool,
                min(per_call, count - i * per_call),
            )
            for i in range(calls)
        ]
        for fut in tqdm(as_completed(futures), total=len(futures), desc="生成新句子"):
            batch = fut.result()
            with lock:
                all_samples.extend(batch)

    print(f"  实际生成 {len(all_samples)} 条")
    return all_samples[:count]


# ── 进度存取 ───────────────────────────────────────────────
def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"finished_batches": [], "pos_keywords": [], "neg_keywords": []}


def save_progress(prog: dict):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(prog, f, ensure_ascii=False, indent=2)


# ── 主流程 ─────────────────────────────────────────────────
def main():
    # 读取原始训练集
    print("读取训练集...")
    raw_data: list[tuple[str, int]] = []
    with open(TRAIN_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                try:
                    raw_data.append((parts[0], int(parts[1])))
                except ValueError:
                    pass
    raw_data = raw_data[:MAX_SAMPLES]
    print(f"共 {len(raw_data)} 条原始训练数据")

    # 断点续传
    prog = load_progress()
    finished_batches: set[int] = set(prog.get("finished_batches", []))
    pos_keywords: list[str] = prog["pos_keywords"]
    neg_keywords: list[str] = prog["neg_keywords"]

    # 输出文件：只保存扩充数据（追加模式）
    out_f = open(OUTPUT_FILE, "a", encoding="utf-8")
    file_lock = threading.Lock()
    kw_lock   = threading.Lock()
    prog_lock = threading.Lock()

    # 分批
    batches = [raw_data[i: i + BATCH_SIZE] for i in range(0, len(raw_data), BATCH_SIZE)]
    pending = [i for i in range(len(batches)) if i not in finished_batches]
    print(f"\n共 {len(batches)} 个批次，已完成 {len(finished_batches)} 个，"
          f"待处理 {len(pending)} 个，使用 {MAX_WORKERS} 线程并发...")

    def handle_batch(b_idx: int):
        batch = batches[b_idx]
        new_samples, pos_kw, neg_kw = process_batch(batch)

        # 线程安全写入文件
        with file_lock:
            for text, label in new_samples:
                out_f.write(f"{text}\t{label}\n")
            out_f.flush()

        # 线程安全更新关键词
        with kw_lock:
            for w in pos_kw:
                if w not in pos_keywords:
                    pos_keywords.append(w)
            for w in neg_kw:
                if w not in neg_keywords:
                    neg_keywords.append(w)

        # 线程安全保存进度（每批完成后立即落盘）
        with prog_lock:
            finished_batches.add(b_idx)
            save_progress({
                "finished_batches": list(finished_batches),
                "pos_keywords": pos_keywords,
                "neg_keywords": neg_keywords,
            })

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(handle_batch, i): i for i in pending}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="拆分短句 & 提取关键词"):
            try:
                fut.result()
            except Exception as exc:
                print(f"  [批次 {futures[fut]} 异常] {exc}")

    out_f.close()

    # 保存词汇表
    vocab_data = {"positive": pos_keywords, "negative": neg_keywords}
    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(vocab_data, f, ensure_ascii=False, indent=2)
    print(f"\n情感词汇表已保存: {VOCAB_FILE}")
    print(f"  正向词 {len(pos_keywords)} 个，负向词 {len(neg_keywords)} 个")

    # 生成 1000 条新句子
    print(f"\n生成 {GEN_COUNT} 条新句子...")
    gen_samples = generate_sentences(pos_keywords, neg_keywords, GEN_COUNT)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for text, label in gen_samples:
            f.write(f"{text}\t{label}\n")
    print(f"生成完成，写入 {len(gen_samples)} 条")

    # 清理进度文件
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()

    # 统计结果
    expanded_count = sum(1 for _ in open(OUTPUT_FILE, encoding="utf-8"))
    print(f"\n{'='*50}")
    print(f"扩充完成！扩充数据文件: {OUTPUT_FILE}")
    print(f"原始数据: {len(raw_data)} 条（未写入扩充文件）")
    print(f"扩充数据: {expanded_count} 条")
    print(f"{'='*50}")
    print(f"\n训练时同时使用原始数据和扩充数据，train.py 示例：")
    print(f"  train_ds = ConcatDataset([")
    print(f"      SentimentDataset('train/part.0', vocab, MAX_LEN),")
    print(f"      SentimentDataset('train/part.0_expanded', vocab, MAX_LEN),")
    print(f"  ])")


if __name__ == "__main__":
    main()