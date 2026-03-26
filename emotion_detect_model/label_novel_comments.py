"""
label_novel_comments.py
=======================
从 fqDataAPI_mitproxy/data/comtJson 目录中提取所有小说读者评论，
调用 DeepSeek API 为每条评论标注情感标签（1=积极，0=消极），
并将结果以与 part.0 相同的 `text\tlabel` 格式保存到
emotion_detect_model/novel_comment_data/data。

特性：
  - 50 个并发线程，批量 API 调用（每批 20 条）
  - 线程安全的文件写入与进度缓存
  - 断点续传：中断后重新运行会跳过已完成批次
  - 评论去重，过滤无效文本

运行：
    pip install openai tqdm
    python label_novel_comments.py
"""

import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm
from openai import OpenAI

# ── 路径配置 ────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
COMT_DIR      = BASE_DIR.parent / 'fqDataAPI_mitproxy' / 'data' / 'comtJson'
OUTPUT_DIR    = BASE_DIR / 'novel_comment_data'
OUTPUT_FILE   = OUTPUT_DIR / 'data'
PROGRESS_FILE = BASE_DIR / 'label_progress.json'

# ── API 配置 ────────────────────────────────────────────────
API_KEY       = "sk-5307ffa372b0443c990d5ea92a9d2496"
API_BASE      = "https://api.deepseek.com"
MODEL         = "deepseek-chat"

# ── 运行参数 ────────────────────────────────────────────────
BATCH_SIZE    = 20    # 每次 API 调用处理的评论数
MAX_WORKERS   = 50    # 并发线程数
RETRY_LIMIT   = 3     # API 错误时的最大重试次数
MIN_TEXT_LEN  = 5     # 忽略过短的评论（字符数）
# ────────────────────────────────────────────────────────────

client    = OpenAI(api_key=API_KEY, base_url=API_BASE)
file_lock = threading.Lock()
prog_lock = threading.Lock()


# ── 数据提取 ─────────────────────────────────────────────────

def extract_comments(comt_dir: Path) -> list[str]:
    """遍历 comtJson 目录，提取所有去重后的评论文本。"""
    comments: list[str] = []
    seen:     set[str]  = set()

    body_files = sorted(comt_dir.rglob('body_*.json'))
    print(f"   发现 {len(body_files)} 个 body 文件，开始提取评论...")

    for body_file in body_files:
        try:
            with open(body_file, encoding='utf-8') as f:
                d = json.load(f)
            items = d.get('data', {}).get('data_list', [])
            for item in items:
                try:
                    text = item['comment']['common']['content']['text'].strip()
                    if text and len(text) >= MIN_TEXT_LEN and text not in seen:
                        seen.add(text)
                        comments.append(text)
                except (KeyError, TypeError):
                    continue
        except Exception as e:
            print(f"   [警告] 跳过 {body_file.name} ({body_file.parent.name}): {e}")

    return comments


# ── API 调用 ─────────────────────────────────────────────────

def call_api(prompt: str, max_tokens: int = 1500) -> str:
    """带重试的 DeepSeek API 调用，返回模型输出文本。"""
    for attempt in range(RETRY_LIMIT):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是中文情感分析专家。只输出纯 JSON 数组，"
                            "不附加任何解释或 markdown 标记。"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.1,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            wait = 2 ** attempt
            print(f"   [API 错误] 第{attempt + 1}次: {exc}，{wait}s 后重试...")
            time.sleep(wait)
    return ""


def parse_json_array(text: str):
    """从模型返回文本中提取第一个合法 JSON 数组。"""
    text = text.strip()
    # 去掉 ```json ... ``` 包裹
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(ln for ln in lines if not ln.startswith("```"))
    # 找到最外层的 [ ... ]
    start = text.find('[')
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    break
    return None


# ── 批次标注 ─────────────────────────────────────────────────

def label_batch(texts: list[str]) -> list[tuple[str, int]]:
    """
    调用 DeepSeek 对一批评论进行情感标注。
    返回 [(text, label), ...]，label=1 积极，0 消极。
    """
    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(texts))
    prompt = (
        f"请判断以下 {len(texts)} 条小说读者评论的情感倾向：积极=1，消极=0。\n"
        "只输出 JSON 数组，每项格式为 {\"idx\": <序号>, \"label\": <0或1>}，序号从 1 开始。\n\n"
        f"评论：\n{numbered}"
    )
    raw     = call_api(prompt)
    results = parse_json_array(raw)

    if not results or not isinstance(results, list):
        # API 失败时默认全部标记为积极，避免丢弃数据
        return [(t, 1) for t in texts]

    label_map: dict[int, int] = {}
    for item in results:
        try:
            idx   = int(item.get("idx", 0)) - 1
            label = int(item.get("label", 1))
            if 0 <= idx < len(texts):
                label_map[idx] = label if label in (0, 1) else 1
        except (ValueError, TypeError):
            continue

    return [(t, label_map.get(i, 1)) for i, t in enumerate(texts)]


# ── 进度管理 ─────────────────────────────────────────────────

def load_progress() -> set[int]:
    """加载已完成的批次索引集合。"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, encoding='utf-8') as f:
                data = json.load(f)
            return set(data.get("finished_batches", []))
        except Exception:
            pass
    return set()


def save_progress(finished: set[int]) -> None:
    """持久化已完成批次列表（需在 prog_lock 持有时调用）。"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"finished_batches": sorted(finished)}, f)


# ── 批次处理 ─────────────────────────────────────────────────

def process_batch(
    batch_idx: int,
    texts:     list[str],
    finished:  set[int],
) -> int:
    """标注单个批次 → 写文件 → 更新进度，返回写入行数。"""
    # 早返回检查（断点续传安全保障）
    with prog_lock:
        if batch_idx in finished:
            return 0

    labeled = label_batch(texts)

    lines = []
    for text, label in labeled:
        clean = text.replace('\t', ' ').replace('\n', ' ').replace('\r', '').strip()
        if clean:
            lines.append(f"{clean}\t{label}")

    if lines:
        with file_lock:
            with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                f.write("\n".join(lines) + "\n")

    with prog_lock:
        finished.add(batch_idx)
        save_progress(finished)

    return len(lines)


# ── 主流程 ──────────────────────────────────────────────────

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ① 提取评论
    print("📖 正在扫描 comtJson 目录，提取评论...")
    comments = extract_comments(COMT_DIR)
    print(f"   共提取到 {len(comments)} 条去重评论（≥{MIN_TEXT_LEN} 字）\n")

    if not comments:
        print("❌ 未找到任何评论，请检查 COMT_DIR 路径。")
        return

    # ② 划分批次
    batches = [
        comments[i: i + BATCH_SIZE]
        for i in range(0, len(comments), BATCH_SIZE)
    ]
    total_batches = len(batches)
    print(f"📦 共 {total_batches} 个批次，每批最多 {BATCH_SIZE} 条")

    # ③ 加载断点进度
    finished   = load_progress()
    remaining  = [i for i in range(total_batches) if i not in finished]
    print(f"   已完成 {len(finished)} 批，剩余 {len(remaining)} 批\n")

    if not remaining:
        print("✅ 所有批次已处理完毕！")
        return

    # ④ 首次运行时清空旧输出，避免重复追加
    if not finished and OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()
        print("   （检测到旧输出文件，已清空）\n")

    # ⑤ 50 线程并发标注
    total_written = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_batch, i, batches[i], finished): i
            for i in remaining
        }
        with tqdm(total=len(remaining), desc="标注进度", unit="批") as pbar:
            for future in as_completed(futures):
                try:
                    n = future.result()
                    total_written += n
                except Exception as exc:
                    batch_i = futures[future]
                    print(f"   [批次 {batch_i} 异常] {exc}")
                finally:
                    pbar.update(1)

    # ⑥ 最终保存
    with prog_lock:
        save_progress(finished)

    print(f"\n✅ 标注完成！共写入 {total_written} 条标注数据")
    print(f"   输出文件：{OUTPUT_FILE}")
    print(f"   进度缓存：{PROGRESS_FILE}")


if __name__ == '__main__':
    main()
