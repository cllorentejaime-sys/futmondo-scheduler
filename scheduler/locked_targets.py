from __future__ import annotations

import json
import os
from pathlib import Path

summary = Path(os.environ["SUMMARY_PATH"])
data = json.loads(summary.read_text(encoding="utf-8"))
ids = []

for player in ((data.get("mi_equipo") or {}).get("plantilla") or []):
    detail = player.get("clausula_detalle") or {}
    pid = str(player.get("id") or "").strip()
    if pid and detail.get("bloqueado"):
        ids.append(pid)

value = ",".join(ids)
with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
    fh.write(f"targets={value}\n")
print(f"Objetivos bloqueados detectados: {len(ids)}")
