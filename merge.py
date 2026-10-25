import pandas as pd

obzor = pd.read_csv("data/2026-10-25/Обзор.csv")
dinamika = pd.read_csv("data/2026-10-25/Динамика.csv")
teh = pd.read_csv("data/2026-10-25/Теханализ.csv")

merged = (
    obzor.merge(dinamika, on=["pair_id", "name"], how="inner")
         .merge(teh, on=["pair_id", "name"], how="inner")
)
merged.to_csv("data/2026-10-25/Итог.csv", index=False, encoding="utf-8-sig")
print(f"Итог: {len(merged)} пар")
