from pathlib import Path
import random


def split_data(
	input_file: Path,
	train_file: Path,
	val_file: Path,
	train_ratio: float = 0.8,
	seed: int = 42,
) -> None:
	lines: list[str] = []
	with input_file.open("r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if line:
				lines.append(line)

	if not lines:
		raise ValueError(f"输入文件为空: {input_file}")

	random.seed(seed)
	random.shuffle(lines)

	split_index = int(len(lines) * train_ratio)
	train_lines = lines[:split_index]
	val_lines = lines[split_index:]

	train_file.parent.mkdir(parents=True, exist_ok=True)

	with train_file.open("w", encoding="utf-8") as f:
		f.write("\n".join(train_lines) + "\n")

	with val_file.open("w", encoding="utf-8") as f:
		f.write("\n".join(val_lines) + "\n")

	total = len(lines)
	print(f"总样本数: {total}")
	print(f"训练集: {len(train_lines)} ({len(train_lines) / total:.2%})")
	print(f"验证集: {len(val_lines)} ({len(val_lines) / total:.2%})")
	print(f"训练集文件: {train_file}")
	print(f"验证集文件: {val_file}")


if __name__ == "__main__":
	base_dir = Path(__file__).resolve().parent
	input_path = base_dir / "novel_comment_data" / "data"
	train_path = base_dir / "novel_comment_data" / "train.txt"
	val_path = base_dir / "novel_comment_data" / "val.txt"

	split_data(
		input_file=input_path,
		train_file=train_path,
		val_file=val_path,
		train_ratio=0.8,
		seed=42,
	)
