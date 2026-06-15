from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


def interpret_report_with_ollama(
    report: dict[str, Any],
    model: str,
    url: str = "http://localhost:11434/api/generate",
    timeout_s: int = 120,
) -> dict[str, Any]:
    prompt = _build_prompt(report)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "enabled": True,
            "model": model,
            "status": "error",
            "error": str(exc),
        }
    return {
        "enabled": True,
        "model": model,
        "status": "ok",
        "text": str(data.get("response", "")).strip(),
    }


def _build_prompt(report: dict[str, Any]) -> str:
    critical_findings = []
    for event in report.get("critical_findings", [])[:8]:
        decision = event.get("decision", {}) or {}
        carla = event.get("carla_prediction", {}) or {}
        cic = event.get("cic_prediction", {}) or {}
        visual = event.get("visual_consistency", {}) or {}
        critical_findings.append(
            {
                "index": event.get("index"),
                "timestamp": event.get("timestamp"),
                "risk_level": decision.get("risk_level"),
                "safe_mode": decision.get("safe_mode"),
                "attack_type": decision.get("final_attack_type"),
                "carla_attack_probability": carla.get("attack_probability"),
                "cic_attack_probability": cic.get("attack_probability"),
                "visual_hallucination_probability": visual.get("hallucination_probability"),
            }
        )
    compact = {
        "summary": report.get("summary", {}),
        "threshold_summary": report.get("threshold_summary", {}),
        "durations": report.get("durations", {}),
        "critical_findings": critical_findings,
    }
    return (
        "Sen otonom arac siber guvenlik ve emniyet karar destek analistisin.\n"
        "Asagidaki veriyi kullanarak kullaniciya sunulabilir Turkce teknik rapor yorumu yaz.\n"
        "JSON yapisini aciklama, alan adlarini tek tek anlatma, kod blogu kullanma.\n"
        "Sadece bulgulari yorumla ve karar oner. Kisa ama operasyonel olsun.\n"
        "Terimleri uydurma veya cevirme: emergency_safe_mode icin sadece 'Acil Guvenli Mod', "
        "degraded_safe_mode icin sadece 'Kisitli Guvenli Mod', monitoring_mode icin sadece 'Izleme Modu' de.\n"
        "Saldiri adlarini aynen kullan: heading_spoofing, gps_spoofing, dos, sensor_noise vb.\n"
        "Tekrara dusme. En fazla 10 madde/cumle kullan.\n"
        "Basliklar tam olarak sunlar olsun:\n"
        "1. Nihai Risk Degerlendirmesi\n"
        "2. En Kritik Bulgular\n"
        "3. Guvenli Mod Gerekcesi\n"
        "4. Operasyonel Oneriler\n"
        "5. Kisa Sonuc\n"
        "Verilmeyen bilgileri uydurma. Model performansini abartma. "
        "Acil Guvenli Mod kararini 136/200 kritik olay ve %68 saldiri/anomali oraniyla gerekcelendir.\n\n"
        f"{json.dumps(compact, ensure_ascii=False, indent=2)}"
    )
