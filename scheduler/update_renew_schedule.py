from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

MADRID = ZoneInfo("Europe/Madrid")
ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "renew.yml"
STATE = ROOT / "scheduler" / "next_renewal.json"
SUMMARY = Path(os.environ["SUMMARY_PATH"])

START = "# DYNAMIC_SCHEDULE_START"
END = "# DYNAMIC_SCHEDULE_END"


def parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MADRID)
    return dt.astimezone(MADRID)


def locked_players(data: dict) -> list[dict]:
    rows = []
    now = datetime.now(MADRID)
    for player in ((data.get("mi_equipo") or {}).get("plantilla") or []):
        detail = player.get("clausula_detalle") or {}
        if not detail.get("bloqueado"):
            continue
        expiry = parse_dt(str(detail.get("bloqueado_hasta_local") or ""))
        if not expiry or expiry <= now:
            continue
        rows.append({
            "id": str(player.get("id") or ""),
            "jugador": str(player.get("jugador") or "").strip(),
            "posicion": str(player.get("posicion") or ""),
            "vence_local": expiry.isoformat(),
            "_expiry": expiry,
        })
    rows.sort(key=lambda x: x["_expiry"])
    return rows


def cron_for(dt: datetime) -> str:
    # GitHub Actions interpreta cron en UTC. Convertimos siempre la fecha local
    # calculada (Europe/Madrid) a UTC antes de escribir el schedule.
    utc = dt.astimezone(ZoneInfo("UTC"))
    return f"{utc.minute} {utc.hour} {utc.day} {utc.month} *"


def main() -> int:
    data = json.loads(SUMMARY.read_text(encoding="utf-8"))
    players = locked_players(data)
    now = datetime.now(MADRID)

    state_payload = {
        "actualizado_local": now.isoformat(),
        "bloqueos": [
            {k: v for k, v in p.items() if not k.startswith("_")}
            for p in players
        ],
        "proxima_renovacion": None,
    }

    if players:
        expiry = players[0]["_expiry"]
        primary = expiry - timedelta(minutes=60)
        backup = expiry - timedelta(minutes=20)

        if primary <= now:
            primary = (now + timedelta(minutes=2)).replace(second=0, microsecond=0)
        if backup <= primary:
            backup = primary + timedelta(minutes=10)

        block = (
            f"{START}\n"
            f"      - cron: '{cron_for(primary)}'\n"
            f""
            f"      - cron: '{cron_for(backup)}'\n"
            f""
            f"{END}"
        )
        state_payload["proxima_renovacion"] = {
            "jugador": players[0]["jugador"],
            "vence_local": expiry.isoformat(),
            "despertar_principal_local": primary.isoformat(),
            "respaldo_local": backup.isoformat(),
        }
    else:
        block = (
            f"{START}\n"
            "      - cron: '0 0 31 2 *'\n"
            ""
            f"{END}"
        )

    text = WORKFLOW.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        raise RuntimeError("No se encontraron los marcadores dinámicos en renew.yml")
    WORKFLOW.write_text(pattern.sub(block, text), encoding="utf-8")

    STATE.write_text(
        json.dumps(state_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(state_payload["proxima_renovacion"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
