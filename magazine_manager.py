import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class MagazineManager:
    """Şarjör yönetim ve olay kayıt sistemi."""

    def __init__(self, data_file: str = "data/magazines.json"):
        self.data_file = data_file
        self.data_dir = Path(data_file).parent
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """JSON verisini yükler."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "magazines" in data and "events" in data:
                        return data
            except (json.JSONDecodeError, OSError):
                pass

        return {"magazines": {}, "events": []}

    def _save_data(self):
        """JSON verisini diske yazar."""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_magazine(self, nfc_id: str, name: str, initial_rounds: int) -> Dict:
        """Yeni şarjör ekler."""
        nfc_id = str(nfc_id).strip()
        name = str(name).strip()

        if not nfc_id or not name:
            return {"success": False, "message": "NFC ID ve şarjör adı gereklidir."}

        if nfc_id in self.data["magazines"]:
            return {"success": False, "message": f"NFC ID '{nfc_id}' zaten kayıtlı."}

        if initial_rounds <= 0:
            return {"success": False, "message": "Şarjör kapasitesi 1'den büyük olmalıdır."}

        self.data["magazines"][nfc_id] = {
            "id": nfc_id,
            "name": name,
            "initial_rounds": initial_rounds,
            "current_rounds": initial_rounds,
            "fired_rounds": 0,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "last_used": None,
            "status": "ready",
        }

        self._add_event("MAGAZINE_ADDED", nfc_id, f"{name} şarjörü eklendi.")
        self._save_data()
        return {"success": True, "message": f"{name} şarjörü başarıyla eklendi."}

    def remove_magazine(self, nfc_id: str) -> Dict:
        """Şarjörü kaldırır."""
        if nfc_id not in self.data["magazines"]:
            return {"success": False, "message": "Şarjör bulunamadı."}

        name = self.data["magazines"][nfc_id]["name"]
        del self.data["magazines"][nfc_id]

        self._add_event("MAGAZINE_REMOVED", nfc_id, f"{name} şarjörü kaldırıldı.")
        self._save_data()
        return {"success": True, "message": f"{name} şarjörü kaldırıldı."}

    def fire_round(self, nfc_id: str) -> Dict:
        """Bir atış simülasyonu yapar."""
        if nfc_id not in self.data["magazines"]:
            return {"success": False, "message": "Şarjör bulunamadı.", "is_uncertain": True}

        mag = self.data["magazines"][nfc_id]

        if mag["current_rounds"] <= 0:
            self._add_event(
                "FIRE_FAILED_EMPTY",
                nfc_id,
                f"{mag['name']} şarjörü boş olduğu için ateş denemesi başarısız oldu.",
                is_uncertain=True,
            )
            self._save_data()
            return {"success": False, "message": "Şarjör boş.", "is_uncertain": True}

        mag["current_rounds"] -= 1
        mag["fired_rounds"] += 1
        mag["last_used"] = datetime.now().isoformat(timespec="seconds")
        mag["status"] = "fired"

        self._add_event(
            "FIRE_SUCCESS",
            nfc_id,
            f"{mag['name']} şarjöründen atış yapıldı. Kalan fişek: {mag['current_rounds']}",
            is_uncertain=False,
        )
        self._save_data()
        return {
            "success": True,
            "message": f"{mag['name']} şarjöründen atış yapıldı.",
            "remaining": mag["current_rounds"],
            "fired": mag["fired_rounds"],
        }

    def reload_magazine(self, nfc_id: str) -> Dict:
        """Şarjörü doldurur."""
        if nfc_id not in self.data["magazines"]:
            return {"success": False, "message": "Şarjör bulunamadı."}

        mag = self.data["magazines"][nfc_id]
        mag["current_rounds"] = mag["initial_rounds"]
        mag["fired_rounds"] = 0
        mag["status"] = "ready"
        mag["last_used"] = datetime.now().isoformat(timespec="seconds")

        self._add_event("MAGAZINE_RELOADED", nfc_id, f"{mag['name']} şarjörü dolduruldu.")
        self._save_data()
        return {"success": True, "message": f"{mag['name']} şarjörü dolduruldu."}

    def get_all_magazines(self) -> Dict:
        """Tüm şarjörleri döndürür."""
        return self.data["magazines"]

    def get_events(self, limit: int = 100) -> List[Dict]:
        """Olay geçmişini döndürür."""
        events = self.data["events"]
        return sorted(events, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def _add_event(self, event_type: str, nfc_id: str, description: str, is_uncertain: bool = False):
        """Yeni olay kaydı ekler."""
        self.data["events"].append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "type": event_type,
                "nfc_id": nfc_id,
                "description": description,
                "is_uncertain": is_uncertain,
            }
        )

    def get_statistics(self) -> Dict:
        """Özet istatistikleri hesaplar."""
        magazines = self.data["magazines"]
        total_initial = sum(m["initial_rounds"] for m in magazines.values())
        total_fired = sum(m["fired_rounds"] for m in magazines.values())
        total_remaining = sum(m["current_rounds"] for m in magazines.values())
        uncertain_count = sum(1 for e in self.data["events"] if e.get("is_uncertain"))

        return {
            "total_magazines": len(magazines),
            "total_rounds_initial": total_initial,
            "total_rounds_fired": total_fired,
            "total_rounds_remaining": total_remaining,
            "uncertain_events": uncertain_count,
        }

    def clear_all_data(self):
        """Tüm veriyi siler."""
        self.data = {"magazines": {}, "events": []}
        self._save_data()


if __name__ == "__main__":
    manager = MagazineManager()
    print(manager.get_statistics())
    print(manager.get_all_magazines())
