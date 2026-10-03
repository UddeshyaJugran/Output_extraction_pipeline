import json
import pathlib

from extractor import extract

RAW_DIR = pathlib.Path("data/raw")
OUT_DIR = pathlib.Path("data/output")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    files = sorted(RAW_DIR.glob("*.txt"))
    if not files:
        print("data/raw mein koi .txt file nahi mili.")
        return

    ok_count = bad_count = 0
    with open(OUT_DIR / "valid.jsonl", "w", encoding="utf-8") as ok, \
         open(OUT_DIR / "failed.jsonl", "w", encoding="utf-8") as bad:
        for f in files:
            try:
                invoice = extract(f.read_text(encoding="utf-8"))
                record = {"source": f.name, **invoice.model_dump(mode="json")}
                ok.write(json.dumps(record) + "\n")
                ok_count += 1
            except Exception as e:
                bad.write(json.dumps({"source": f.name, "error": str(e)}) + "\n")
                bad_count += 1

    print(f"Done. Valid: {ok_count}, Failed: {bad_count}")


if __name__ == "__main__":
    main()