import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {}

class ApplicationsTracker:
    """Gerencia o registro e o histórico de candidaturas para evitar envios duplicados."""
    
    def __init__(self, json_path: Optional[str] = None, csv_path: Optional[str] = None):
        cfg = load_config()
        self.json_path = Path(json_path or cfg.get("arquivos", {}).get(
            "historico_candidaturas_json", 
            Path(__file__).parent / "applications_history.json"
        ))
        self.csv_path = Path(csv_path or cfg.get("arquivos", {}).get(
            "historico_candidaturas_csv", 
            Path(__file__).parent / "applications_history.csv"
        ))
        self._ensure_files()

    def _ensure_files(self):
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.json_path.exists():
            with open(self.json_path, "w", encoding="utf-8-sig") as f:
                json.dump([], f, indent=2, ensure_ascii=False)

    def get_all(self) -> List[Dict[str, Any]]:
        try:
            with open(self.json_path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            return []

    def is_already_applied(self, job_url: str, job_title: str = "", company: str = "") -> bool:
        """Verifica se a vaga já foi candidatada anteriormente por URL ou Título + Empresa."""
        items = self.get_all()
        clean_target_url = job_url.split("?")[0].rstrip("/").lower()
        target_slug = f"{company.lower().strip()}-{job_title.lower().strip()}"

        for item in items:
            item_url = item.get("job_url", "").split("?")[0].rstrip("/").lower()
            if clean_target_url and clean_target_url == item_url:
                return True
            if company and job_title:
                existing_slug = f"{item.get('company', '').lower().strip()}-{item.get('job_title', '').lower().strip()}"
                if existing_slug == target_slug and existing_slug != "-":
                    return True
        return False

    def record_application(
        self,
        job_title: str,
        company: str,
        platform: str,
        job_url: str,
        status: str = "Enviado",
        notes: str = "",
        resume_used: str = ""
    ) -> Dict[str, Any]:
        """Adiciona uma nova candidatura ao histórico JSON e CSV."""
        entry = {
            "id": len(self.get_all()) + 1,
            "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "job_title": job_title.strip(),
            "company": company.strip(),
            "platform": platform.strip(),
            "job_url": job_url.strip(),
            "status": status,
            "notes": notes,
            "resume_used": resume_used
        }

        items = self.get_all()
        items.append(entry)

        with open(self.json_path, "w", encoding="utf-8-sig") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

        # Atualiza CSV para fácil visualização em Excel/Google Sheets
        write_header = not self.csv_path.exists() or self.csv_path.stat().st_size == 0
        with open(self.csv_path, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(entry.keys()))
            if write_header:
                writer.writeheader()
            writer.writerow(entry)

        return entry

    def get_summary(self) -> Dict[str, Any]:
        items = self.get_all()
        total = len(items)
        by_platform: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for it in items:
            p = it.get("platform", "Outros")
            s = it.get("status", "Desconhecido")
            by_platform[p] = by_platform.get(p, 0) + 1
            by_status[s] = by_status.get(s, 0) + 1

        return {
            "total_candidaturas": total,
            "por_plataforma": by_platform,
            "por_status": by_status,
            "ultimas_5": items[-5:] if total > 5 else items
        }

if __name__ == "__main__":
    tracker = ApplicationsTracker()
    summary = tracker.get_summary()
    print("Resumo do Histórico de Candidaturas:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
