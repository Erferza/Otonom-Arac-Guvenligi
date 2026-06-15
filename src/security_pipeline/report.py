from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
import html
import json
from typing import Any


def build_report(
    events: list[dict[str, Any]],
    llm_interpretation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    attack_counter = Counter(e["decision"]["final_attack_type"] for e in events)
    risk_counter = Counter(e["decision"]["risk_level"] for e in events)
    review_count = sum(1 for e in events if e["decision"]["needs_human_review"])
    safe_mode_required_count = sum(
        1 for e in events if e.get("threshold_decision", {}).get("safe_mode_required")
    )
    durations = _durations_by_attack(events)
    threshold_summary = _threshold_summary(events)
    top_threats = [
        {"attack_type": attack, "count": count}
        for attack, count in attack_counter.most_common()
        if attack != "normal"
    ]
    critical_events = [e for e in events if e["decision"]["risk_level"] == "attack"][:25]

    return {
        "summary": {
            "event_count": len(events),
            "risk_distribution": dict(risk_counter),
            "review_required_count": review_count,
            "safe_mode_required_count": safe_mode_required_count,
            "top_threats": top_threats,
            "recommended_safe_mode": threshold_summary["recommended_safe_mode"],
        },
        "threshold_summary": threshold_summary,
        "durations": durations,
        "critical_findings": critical_events,
        "llm_interpretation": llm_interpretation
        or {"enabled": False, "status": "not_requested"},
        "events": events,
    }


def event_to_dict(**kwargs: Any) -> dict[str, Any]:
    result = {}
    for key, value in kwargs.items():
        result[key] = asdict(value) if hasattr(value, "__dataclass_fields__") else value
    return result


def render_readable_report(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    threshold = report.get("threshold_summary", {})
    event_count = int(summary.get("event_count", 0) or 0)
    risk_distribution = summary.get("risk_distribution", {}) or {}
    attack_count = int(risk_distribution.get("attack", 0) or 0)
    normal_count = int(risk_distribution.get("normal", 0) or 0)
    safe_mode = str(summary.get("recommended_safe_mode", "unknown"))
    safe_mode_required = int(summary.get("safe_mode_required_count", 0) or 0)
    review_required = int(summary.get("review_required_count", 0) or 0)

    lines = [
        "# Otonom Arac Guvenlik Izleme Raporu",
        "",
        "## 1. Yonetici Ozeti",
        "",
        f"Bu rapor {event_count} olaylik izleme penceresi icin uretilmistir. "
        f"Sistem {attack_count} olayda saldiri/anomali, {normal_count} olayda normal durum karari vermistir. "
        f"Nihai guvenli mod onerisi: **{_human_mode(safe_mode)}**.",
        "",
        "| Metrik | Deger |",
        "|---|---:|",
        f"| Toplam olay | {event_count} |",
        f"| Attack/anomali karari | {attack_count} ({_pct(attack_count, event_count)}) |",
        f"| Normal karar | {normal_count} ({_pct(normal_count, event_count)}) |",
        f"| Insan incelemesi gereken olay | {review_required} ({_pct(review_required, event_count)}) |",
        f"| Guvenli mod gerektiren olay | {safe_mode_required} ({_pct(safe_mode_required, event_count)}) |",
        f"| Onerilen guvenli mod | {_human_mode(safe_mode)} |",
        "",
        "## 2. Nihai Karar",
        "",
        _decision_paragraph(summary, threshold),
        "",
        "## 3. Katman Bazli Bulgular",
        "",
        _layer_section(threshold),
        "",
        "## 4. Tehdit Sikliklari",
        "",
        _top_threats_section(summary.get("top_threats", []), event_count),
        "",
        "## 5. Guvenli Mod Dagilimi",
        "",
        _counter_table(threshold.get("safe_mode_distribution", {}) or {}, event_count, mode_names=True),
        "",
        "## 6. Oncelikli Olay Ornekleri",
        "",
        _critical_events_section(report.get("critical_findings", []) or []),
        "",
        "## 7. Nihai Yorum ve Oneriler",
        "",
        _analyst_section(summary, threshold),
        "",
        "## 8. Ollama Durumu",
        "",
        _llm_status_section(report.get("llm_interpretation", {})),
        "",
        "## 9. Notlar",
        "",
        "- Bu rapor karar destek amaclidir; nihai operasyon karari sistem politikasi ve insan denetimiyle birlikte verilmelidir.",
        "- Safe mode karari CIC, CARLA, nuScenes gorsel tutarlilik ve fusion karar katmaninin birlikte degerlendirilmesiyle uretilmistir.",
        "- Kritik siniflarda temkinli karar verilmesi, otonom arac guvenligi acisindan tercih edilen davranistir.",
        "",
    ]
    return "\n".join(lines)


def render_dashboard(
    report: dict[str, Any],
    metrics: dict[str, Any] | None = None,
    json_filename: str = "report.json",
    markdown_filename: str = "report.md",
) -> str:
    summary = report.get("summary", {}) or {}
    threshold = report.get("threshold_summary", {}) or {}
    events = report.get("events", []) or []
    metrics = metrics or {}
    event_count = int(summary.get("event_count", 0) or 0)
    risk_distribution = summary.get("risk_distribution", {}) or {}
    attack_count = int(risk_distribution.get("attack", 0) or 0)
    normal_count = int(risk_distribution.get("normal", 0) or 0)
    safe_mode = str(summary.get("recommended_safe_mode", "unknown"))
    safe_mode_required = int(summary.get("safe_mode_required_count", 0) or 0)
    review_required = int(summary.get("review_required_count", 0) or 0)
    top_threats = summary.get("top_threats", []) or []
    layer_distribution = threshold.get("layer_level_distribution", {}) or {}
    triggered_layers = threshold.get("triggered_layers", {}) or {}
    safe_mode_distribution = threshold.get("safe_mode_distribution", {}) or {}
    final_levels = threshold.get("final_level_distribution", {}) or {}
    critical_count = int(final_levels.get("critical", 0) or 0)
    event_rows = _dashboard_event_rows(events)
    attack_rate = _pct(attack_count, event_count)
    safe_mode_rate = _pct(safe_mode_required, event_count)
    dominant_threat = _dominant_threat(top_threats)
    dominant_layer = _dominant_layer(triggered_layers)

    return f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Otonom Arac Guvenlik Dashboard</title>
  <style>
    :root {{
      --bg: #f7f8fb;
      --panel: #ffffff;
      --panel-soft: #fbfcfe;
      --ink: #1f2937;
      --muted: #6b7280;
      --line: #dbe3ee;
      --accent: #4f9a9a;
      --accent-soft: #e8f6f4;
      --danger: #c0392b;
      --danger-soft: #fdecea;
      --warn: #c6922f;
      --warn-soft: #fff6df;
      --ok: #5ca87a;
      --ok-soft: #edf8f1;
      --blue: #6f91c9;
      --blue-soft: #edf3ff;
      --violet: #9a8bc7;
      --violet-soft: #f2effb;
      --shadow: 0 14px 36px rgba(31, 41, 55, 0.06);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    .shell {{ max-width: 1320px; margin: 0 auto; padding: 28px; }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(360px, 0.95fr);
      gap: 22px;
      align-items: stretch;
      margin-bottom: 22px;
    }}
    .hero-main, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }}
    .hero-main {{
      padding: 26px;
      display: grid;
      gap: 18px;
      height: 100%;
      background:
        linear-gradient(135deg, rgba(79, 154, 154, 0.08), rgba(154, 139, 199, 0.06) 44%, rgba(255,255,255,0) 72%),
        var(--panel);
    }}
    .hero-copy {{ max-width: 820px; }}
    .eyebrow {{ color: var(--accent); font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 0; }}
    h1 {{ margin: 8px 0 10px; font-size: 34px; line-height: 1.12; letter-spacing: 0; }}
    h2 {{ margin: 0 0 16px; font-size: 20px; letter-spacing: 0; }}
    h3 {{ margin: 0 0 8px; font-size: 15px; letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); }}
    .status-card {{ padding: 18px; display: flex; flex-direction: column; gap: 14px; overflow: hidden; height: 100%; }}
    .mode-badge {{
      display: inline-flex;
      width: fit-content;
      padding: 8px 12px;
      border-radius: 999px;
      font-weight: 800;
      color: #fff;
      background: var(--danger);
    }}
    .mode-badge.warn {{ background: var(--warn); }}
    .mode-badge.ok {{ background: var(--ok); }}
    .vehicle-scene {{
      position: relative;
      min-height: 260px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background:
        linear-gradient(180deg, #fbfdff 0%, #eef5fb 56%, #e7edf4 56%, #e7edf4 100%);
      overflow: hidden;
    }}
    .road {{
      position: absolute;
      left: -10%;
      right: -10%;
      bottom: -18px;
      height: 120px;
      background: #344250;
      transform: perspective(180px) rotateX(18deg);
      transform-origin: bottom;
    }}
    .lane-line {{
      position: absolute;
      left: 50%;
      bottom: 4px;
      width: 5px;
      height: 108px;
      background: repeating-linear-gradient(180deg, #fff 0 18px, transparent 18px 34px);
      opacity: 0.8;
    }}
    .car-svg {{
      position: absolute;
      left: 50%;
      bottom: 40px;
      width: min(260px, 72%);
      transform: translateX(-50%);
      filter: drop-shadow(0 18px 20px rgba(16, 24, 40, 0.22));
    }}
    .sensor-ring {{
      position: absolute;
      left: 50%;
      bottom: 66px;
      width: 260px;
      height: 260px;
      border: 2px solid rgba(79, 154, 154, 0.26);
      border-radius: 50%;
      transform: translateX(-50%);
    }}
    .sensor-ring.r2 {{ width: 340px; height: 340px; bottom: 26px; opacity: 0.55; }}
    .threat-dot {{
      position: absolute;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: var(--danger);
      box-shadow: 0 0 0 8px rgba(192, 57, 43, 0.12);
    }}
    .threat-dot.d1 {{ left: 18%; top: 28%; }}
    .threat-dot.d2 {{ right: 18%; top: 36%; background: var(--warn); box-shadow: 0 0 0 8px rgba(198, 146, 47, 0.16); }}
    .threat-dot.d3 {{ left: 62%; top: 16%; background: var(--blue); box-shadow: 0 0 0 8px rgba(111, 145, 201, 0.16); }}
    .scene-label {{
      position: absolute;
      left: 14px;
      top: 14px;
      right: 14px;
      display: flex;
      justify-content: space-between;
      gap: 10px;
      font-size: 12px;
      color: var(--muted);
      font-weight: 800;
    }}
    .risk-meter {{
      display: grid;
      grid-template-columns: 92px 1fr;
      gap: 12px;
      align-items: center;
      margin-top: 12px;
    }}
    .gauge {{
      width: 92px;
      height: 92px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background:
        conic-gradient(var(--danger) 0 {safe_mode_rate}, #edf1f6 {safe_mode_rate} 100%);
      position: relative;
      font-weight: 900;
    }}
    .gauge::after {{
      content: "";
      position: absolute;
      inset: 11px;
      background: #fff;
      border-radius: 50%;
    }}
    .gauge span {{ position: relative; z-index: 1; }}
    .decision-evidence {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-top: 16px;
    }}
    .evidence-box {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: var(--panel-soft);
    }}
    .evidence-box .label {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      margin-bottom: 4px;
    }}
    .evidence-box strong {{
      display: block;
      font-size: 18px;
      line-height: 1.18;
    }}
    .status-actions {{
      margin-top: 14px;
      display: grid;
      gap: 8px;
    }}
    .status-action {{
      display: grid;
      grid-template-columns: 24px 1fr;
      gap: 9px;
      align-items: start;
      color: var(--muted);
      font-size: 13px;
    }}
    .check {{
      width: 24px;
      height: 24px;
      border-radius: 7px;
      display: grid;
      place-items: center;
      background: var(--danger-soft);
      color: var(--danger);
      font-weight: 900;
      line-height: 1;
    }}
    .architecture {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .arch-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      position: relative;
      min-height: 112px;
    }}
    .arch-card::after {{
      content: "";
      position: absolute;
      top: 50%;
      right: -12px;
      width: 12px;
      height: 2px;
      background: var(--line);
    }}
    .arch-card:last-child::after {{ display: none; }}
    .arch-icon {{
      width: 34px;
      height: 34px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      font-weight: 900;
      margin-bottom: 10px;
      background: var(--blue-soft);
      color: var(--blue);
    }}
    .arch-card.carla .arch-icon {{ background: var(--accent-soft); color: var(--accent); }}
    .arch-card.visual .arch-icon {{ background: var(--warn-soft); color: var(--warn); }}
    .arch-card.fusion .arch-icon {{ background: var(--danger-soft); color: var(--danger); }}
    .arch-card .meta {{ color: var(--muted); font-size: 12px; margin-top: 5px; }}
    .insights {{ grid-template-columns: repeat(3, minmax(0, 1fr)); margin-bottom: 18px; }}
    .insight {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .insight strong {{ display: block; font-size: 22px; margin: 4px 0; }}
    .hero-diagnostics {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}
    .diag-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.76);
      padding: 13px;
      min-height: 116px;
    }}
    .diag-card .label {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
    }}
    .diag-card strong {{
      display: block;
      margin: 5px 0 4px;
      font-size: 21px;
      line-height: 1.12;
    }}
    .diag-card p {{ font-size: 13px; }}
    .hero-comment {{
      display: grid;
      grid-template-columns: 34px 1fr;
      gap: 12px;
      align-items: start;
      border: 1px solid #d7e5ef;
      background: #f8fbfd;
      border-radius: 8px;
      padding: 14px;
    }}
    .comment-icon {{
      width: 34px;
      height: 34px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      color: var(--blue);
      background: var(--blue-soft);
      font-weight: 900;
    }}
    .mini-bars {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    .mini-panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-soft);
      padding: 12px;
    }}
    .mini-panel h3 {{ margin-bottom: 10px; }}
    .mini-panel .bar-row {{ grid-template-columns: 112px 1fr 52px; gap: 8px; }}
    .mini-panel .bar-label, .mini-panel .bar-value {{ font-size: 12px; }}
    .mini-panel .bar-track {{ height: 9px; }}
    .actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: auto; }}
    .btn {{
      appearance: none;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      padding: 9px 12px;
      border-radius: 7px;
      text-decoration: none;
      font-weight: 700;
      font-size: 13px;
      cursor: pointer;
    }}
    .btn.primary {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
    .grid {{ display: grid; gap: 16px; }}
    .kpis {{ grid-template-columns: repeat(5, minmax(0, 1fr)); margin-bottom: 18px; }}
    .kpi {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }}
    .kpi .label {{ color: var(--muted); font-size: 13px; font-weight: 650; }}
    .kpi .value {{ font-size: 28px; font-weight: 850; margin-top: 8px; letter-spacing: 0; }}
    .kpi .sub {{ color: var(--muted); font-size: 12px; margin-top: 4px; }}
    .two {{ grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }}
    .three {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .panel {{ padding: 18px; margin-bottom: 16px; }}
    .bar-list {{ display: grid; gap: 11px; }}
    .bar-row {{ display: grid; grid-template-columns: 150px 1fr 72px; gap: 10px; align-items: center; }}
    .bar-label {{ font-size: 13px; font-weight: 700; overflow-wrap: anywhere; }}
    .bar-track {{ height: 12px; border-radius: 999px; background: #edf1f6; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: inherit; background: var(--accent); }}
    .bar-fill.danger {{ background: var(--danger); }}
    .bar-fill.warn {{ background: var(--warn); }}
    .bar-fill.blue {{ background: var(--blue); }}
    .bar-value {{ text-align: right; color: var(--muted); font-size: 13px; font-weight: 700; }}
    .layer-table, .event-table, .metric-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{ padding: 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0; background: #f8fafc; }}
    tr:hover td {{ background: #fbfcfe; }}
    .pill {{ display: inline-flex; padding: 4px 8px; border-radius: 999px; font-weight: 800; font-size: 12px; }}
    .pill.danger {{ background: var(--danger-soft); color: var(--danger); }}
    .pill.warn {{ background: var(--warn-soft); color: var(--warn); }}
    .pill.ok {{ background: var(--ok-soft); color: var(--ok); }}
    .pill.neutral {{ background: #edf1f6; color: #4b5563; }}
    .callout {{
      border-left: 4px solid var(--danger);
      background: #fff9f8;
      padding: 14px;
      border-radius: 6px;
      color: #5f2923;
    }}
    .filters {{ display: flex; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }}
    input, select {{
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 9px 10px;
      font: inherit;
      min-height: 38px;
      background: #fff;
    }}
    .footer {{ color: var(--muted); font-size: 12px; padding: 20px 0 10px; }}
    @media (max-width: 980px) {{
      .hero, .two, .three, .kpis, .architecture, .insights, .hero-diagnostics, .mini-bars, .decision-evidence {{ grid-template-columns: 1fr; }}
      .arch-card::after {{ display: none; }}
      .shell {{ padding: 16px; }}
      h1 {{ font-size: 28px; }}
      .bar-row {{ grid-template-columns: 1fr; gap: 6px; }}
      .bar-value {{ text-align: left; }}
    }}
    @media print {{
      body {{ background: #fff; }}
      .actions, .filters {{ display: none; }}
      .shell {{ max-width: none; padding: 0; }}
      .panel, .hero-main, .status-card, .kpi {{ box-shadow: none; break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="hero-main">
        <div class="hero-copy">
          <div class="eyebrow">AI Destekli Otonom Arac Guvenlik Izleme</div>
          <h1>Katmanli Anomali Tespiti ve Guvenli Mod Karari</h1>
          <p>{_e(_dashboard_summary_sentence(event_count, attack_count, normal_count, safe_mode))}</p>
        </div>
        <div class="hero-diagnostics">
          {_diagnostic_card("Attack orani", attack_rate, f"{attack_count} attack/anomali, {normal_count} normal karar")}
          {_diagnostic_card("Guvenli mod", safe_mode_rate, f"{safe_mode_required} olay safe-mode politikasi gerektirdi")}
          {_diagnostic_card("Baskin tehdit", dominant_threat, "En sik gorulen attack/anomali sinifi")}
        </div>
        <div class="hero-comment">
          <div class="comment-icon">i</div>
          <p>{_e(_executive_comment(summary, threshold))}</p>
        </div>
        <div class="mini-bars">
          <div class="mini-panel">
            <h3>Risk Dagilimi</h3>
            {_bar_dict(risk_distribution, event_count, "blue")}
          </div>
          <div class="mini-panel">
            <h3>Safe Mode Dagilimi</h3>
            {_bar_dict(safe_mode_distribution, event_count, "warn", human_modes=True)}
          </div>
        </div>
        <div class="actions">
          <a class="btn primary" href="{_e(json_filename)}" download>JSON indir</a>
          <a class="btn" href="{_e(markdown_filename)}" download>Markdown rapor indir</a>
          <button class="btn" onclick="window.print()">PDF/Print</button>
        </div>
      </div>
      <aside class="panel status-card">
        {_vehicle_scene(safe_mode)}
        <div>
          <h2>Nihai Karar</h2>
          <span class="mode-badge {_e(_mode_class(safe_mode))}">{_e(_human_mode(safe_mode))}</span>
          <p style="margin-top:10px">{_e(_dashboard_decision_text(safe_mode, critical_count))}</p>
          <div class="risk-meter">
            <div class="gauge"><span>{_e(safe_mode_rate)}</span></div>
            <p>Guvenli mod gerektiren olay orani. Bu oran karar katmaninin operasyonel mod onerisine temel olusturur.</p>
          </div>
          {_status_evidence(summary, threshold)}
        </div>
      </aside>
    </section>

    <section class="architecture">
      {_architecture_card("CIC", "Ag Katmani", "Binary + saldiri turu", triggered_layers.get("cic", 0), "cic")}
      {_architecture_card("CAR", "Davranis/Sensor", "CARLA tabular model", triggered_layers.get("carla", 0), "carla")}
      {_architecture_card("VIS", "Gorsel Tutarlilik", "nuScenes cevre kaniti", triggered_layers.get("visual", 0), "visual")}
      {_architecture_card("AI", "Karar Katmani", "Risk + safe mode", triggered_layers.get("fusion", 0), "fusion")}
    </section>

    <section class="grid kpis">
      {_kpi("Toplam Olay", event_count, "Izlenen pencere")}
      {_kpi("Attack/Anomali", attack_count, attack_rate)}
      {_kpi("Normal", normal_count, _pct(normal_count, event_count))}
      {_kpi("Insan Incelemesi", review_required, _pct(review_required, event_count))}
      {_kpi("Guvenli Mod", safe_mode_required, safe_mode_rate)}
    </section>

    <section class="grid insights">
      {_insight_card("Baskin tehdit", dominant_threat, "Top threat listesi rapor olaylarindan hesaplandi.")}
      {_insight_card("Ana sinyal kaynagi", dominant_layer, "En cok esik tetikleyen katman.")}
      {_insight_card("Karar ozeti", _human_mode(safe_mode), _dashboard_decision_text(safe_mode, critical_count))}
    </section>

    <section class="grid two">
      <div class="panel">
        <h2>Tehdit Onceliklendirmesi</h2>
        {_bar_list(top_threats, event_count, "attack_type", "count", "danger")}
      </div>
      <div class="panel">
        <h2>Risk ve Safe Mode Dagilimi</h2>
        <h3>Risk</h3>
        {_bar_dict(risk_distribution, event_count, "blue")}
        <div style="height:14px"></div>
        <h3>Safe Mode</h3>
        {_bar_dict(safe_mode_distribution, event_count, "warn", human_modes=True)}
      </div>
    </section>

    <section class="panel">
      <h2>Katman Analizi</h2>
      {_layer_dashboard_table(layer_distribution, triggered_layers)}
    </section>

    <section class="grid two">
      <div class="panel">
        <h2>Model Performans Ozeti</h2>
        {_metrics_table(metrics)}
      </div>
      <div class="panel">
        <h2>Operasyonel Aksiyon Plani</h2>
        {_action_plan(summary, threshold)}
      </div>
    </section>

    <section class="panel">
      <h2>Oncelikli Olaylar</h2>
      <div class="filters">
        <input id="eventSearch" type="search" placeholder="Saldiri turu ara">
        <select id="modeFilter">
          <option value="">Tum safe mode kararları</option>
          <option value="emergency_safe_mode">Acil Guvenli Mod</option>
          <option value="degraded_safe_mode">Kisitli Guvenli Mod</option>
          <option value="monitoring_mode">Izleme Modu</option>
          <option value="normal_mode">Normal Mod</option>
        </select>
      </div>
      {_event_table(event_rows)}
    </section>

    <section class="panel">
      <h2>Sunum Notu</h2>
      <p>Bu dashboard, karar destek amaclidir. Nihai operasyon karari kurum politikasi, arac durumu ve insan operator onayi ile birlikte verilmelidir.</p>
    </section>

    <div class="footer">Olusturulan rapor: {event_count} olay, onerilen mod: {_e(_human_mode(safe_mode))}.</div>
  </main>
  <script>
    const search = document.getElementById('eventSearch');
    const modeFilter = document.getElementById('modeFilter');
    const rows = Array.from(document.querySelectorAll('[data-event-row]'));
    function filterRows() {{
      const q = (search.value || '').toLowerCase();
      const mode = modeFilter.value || '';
      for (const row of rows) {{
        const attack = row.dataset.attack || '';
        const rowMode = row.dataset.mode || '';
        const visible = (!q || attack.includes(q)) && (!mode || rowMode === mode);
        row.style.display = visible ? '' : 'none';
      }}
    }}
    search.addEventListener('input', filterRows);
    modeFilter.addEventListener('change', filterRows);
  </script>
</body>
</html>
"""


def _threshold_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    final_levels = Counter()
    safe_modes = Counter()
    layer_levels: dict[str, Counter[str]] = defaultdict(Counter)
    triggered_layers = Counter()

    for event in events:
        threshold = event.get("threshold_decision") or {}
        final_level = threshold.get("final_level")
        safe_mode = threshold.get("safe_mode")
        if final_level:
            final_levels[str(final_level)] += 1
        if safe_mode:
            safe_modes[str(safe_mode)] += 1
        for layer in ("cic", "carla", "visual", "fusion"):
            layer_result = threshold.get(layer)
            if not layer_result:
                continue
            level = layer_result.get("level")
            if level:
                layer_levels[layer][str(level)] += 1
            if layer_result.get("triggered"):
                triggered_layers[layer] += 1

    recommended_safe_mode = _recommended_safe_mode(safe_modes)
    return {
        "final_level_distribution": dict(final_levels),
        "safe_mode_distribution": dict(safe_modes),
        "recommended_safe_mode": recommended_safe_mode,
        "triggered_layers": dict(triggered_layers),
        "layer_level_distribution": {
            layer: dict(counter) for layer, counter in layer_levels.items()
        },
    }


def _recommended_safe_mode(safe_modes: Counter[str]) -> str:
    for mode in ("emergency_safe_mode", "degraded_safe_mode", "monitoring_mode"):
        if safe_modes.get(mode, 0) > 0:
            return mode
    return "normal_mode"


def _decision_paragraph(summary: dict[str, Any], threshold: dict[str, Any]) -> str:
    mode = str(summary.get("recommended_safe_mode", threshold.get("recommended_safe_mode", "unknown")))
    final_levels = threshold.get("final_level_distribution", {}) or {}
    critical = int(final_levels.get("critical", 0) or 0)
    high = int(final_levels.get("high", 0) or 0)
    medium = int(final_levels.get("medium", 0) or 0)
    if mode == "emergency_safe_mode":
        return (
            f"Sistem **{_human_mode(mode)}** onermektedir. "
            f"Bu karar, izleme penceresinde {critical} kritik, {high} yuksek ve {medium} orta seviye "
            "bulgu olusmasi nedeniyle verilmistir. Aracin operasyonel riski yuksek kabul edilmeli, "
            "hiz/rota kontrolu kisitlanmali ve guvenli durus veya kontrollu devralma senaryosu uygulanmalidir."
        )
    if mode == "degraded_safe_mode":
        return (
            f"Sistem **{_human_mode(mode)}** onermektedir. "
            "Arac gorevine devam edebilir ancak hareket kabiliyeti sinirlandirilmali, riskli manevralar "
            "engellenmeli ve izleme sikligi artirilmalidir."
        )
    if mode == "monitoring_mode":
        return (
            f"Sistem **{_human_mode(mode)}** onermektedir. "
            "Anomali sinyalleri izlenmelidir; su an icin agresif guvenli mod gerekli gorulmemektedir."
        )
    return "Sistem **Normal Mod** onermektedir. Kritik veya yuksek riskli bulgu tespit edilmemistir."


def _layer_section(threshold: dict[str, Any]) -> str:
    layer_dist = threshold.get("layer_level_distribution", {}) or {}
    triggered = threshold.get("triggered_layers", {}) or {}
    names = {
        "cic": "CIC ag katmani",
        "carla": "CARLA davranis/sensor katmani",
        "visual": "nuScenes gorsel tutarlilik katmani",
        "fusion": "Fusion karar katmani",
    }
    lines = [
        "| Katman | Tetiklenen olay | Seviye dagilimi | Yorum |",
        "|---|---:|---|---|",
    ]
    for key in ("cic", "carla", "visual", "fusion"):
        dist = layer_dist.get(key, {}) or {}
        dist_text = ", ".join(f"{level}: {count}" for level, count in sorted(dist.items())) or "-"
        trig = int(triggered.get(key, 0) or 0)
        lines.append(f"| {names[key]} | {trig} | {dist_text} | {_layer_comment(key, dist, trig)} |")
    return "\n".join(lines)


def _layer_comment(layer: str, dist: dict[str, Any], triggered: int) -> str:
    if triggered == 0:
        return "Bu pencerede esik ustu bulgu uretmedi."
    if layer == "carla":
        return "Davranis/sensor anomalileri karar uzerinde belirleyici oldu."
    if layer == "fusion":
        return "Katman sinyallerini birlestirerek nihai risk kararini destekledi."
    if layer == "visual":
        return "Gorsel tutarlilik sinyali izlenmistir."
    return "Ag katmani bulgulari izlenmistir."


def _top_threats_section(threats: list[dict[str, Any]], event_count: int) -> str:
    if not threats:
        return "Attack/anomali turu tespit edilmedi."
    lines = [
        "| Tehdit/anomali turu | Olay sayisi | Oran |",
        "|---|---:|---:|",
    ]
    for item in threats:
        attack = str(item.get("attack_type", "unknown"))
        count = int(item.get("count", 0) or 0)
        lines.append(f"| {attack} | {count} | {_pct(count, event_count)} |")
    return "\n".join(lines)


def _counter_table(counter: dict[str, Any], event_count: int, mode_names: bool = False) -> str:
    if not counter:
        return "Dagilim bilgisi bulunamadi."
    lines = [
        "| Sinif | Olay sayisi | Oran |",
        "|---|---:|---:|",
    ]
    for key, value in sorted(counter.items(), key=lambda item: str(item[0])):
        count = int(value or 0)
        label = _human_mode(str(key)) if mode_names else str(key)
        lines.append(f"| {label} | {count} | {_pct(count, event_count)} |")
    return "\n".join(lines)


def _critical_events_section(events: list[dict[str, Any]]) -> str:
    if not events:
        return "Oncelikli olay bulunmadi."
    lines = [
        "| # | Zaman | Risk | Saldiri turu | Safe mode | CARLA p | CIC p | Gorsel p |",
        "|---:|---:|---|---|---|---:|---:|---:|",
    ]
    for event in events[:12]:
        decision = event.get("decision", {}) or {}
        carla = event.get("carla_prediction", {}) or {}
        cic = event.get("cic_prediction", {}) or {}
        visual = event.get("visual_consistency", {}) or {}
        lines.append(
            "| "
            f"{event.get('index', '-')} | "
            f"{event.get('timestamp', '-')} | "
            f"{decision.get('risk_level', '-')} | "
            f"{decision.get('final_attack_type', '-')} | "
            f"{_human_mode(str(decision.get('safe_mode', '-')))} | "
            f"{_fmt_float(carla.get('attack_probability'))} | "
            f"{_fmt_float(cic.get('attack_probability'))} | "
            f"{_fmt_float(visual.get('hallucination_probability'))} |"
        )
    return "\n".join(lines)


def _llm_section(llm: Any) -> str:
    if not isinstance(llm, dict) or not llm.get("enabled"):
        return "LLM yorumu istenmedi."
    if llm.get("status") != "ok":
        return f"LLM yorumu alinamadi: `{llm.get('error', 'unknown error')}`"
    text = str(llm.get("text", "")).strip()
    if not text:
        return "LLM bos yanit dondu."
    return text


def _analyst_section(summary: dict[str, Any], threshold: dict[str, Any]) -> str:
    event_count = int(summary.get("event_count", 0) or 0)
    risk_distribution = summary.get("risk_distribution", {}) or {}
    attack_count = int(risk_distribution.get("attack", 0) or 0)
    top_threats = summary.get("top_threats", []) or []
    mode = str(summary.get("recommended_safe_mode", threshold.get("recommended_safe_mode", "unknown")))
    threat_text = ", ".join(
        f"{item.get('attack_type')} ({item.get('count')})"
        for item in top_threats[:5]
    ) or "belirgin tehdit yok"
    return "\n".join(
        [
            f"- Izleme penceresinde {event_count} olay incelenmis, {attack_count} olay saldiri/anomali olarak degerlendirilmistir.",
            f"- En baskin tehditler: {threat_text}.",
            f"- Nihai karar **{_human_mode(mode)}** olarak atanmistir; bu karar CARLA davranis/sensor katmani ve fusion karar katmanindaki kritik bulgularla desteklenmektedir.",
            "- Onerilen operasyonel aksiyon: araci kontrollu sekilde kisitli/guvenli davranisa almak, riskli manevralari engellemek, telemetriyi kaydetmek ve insan operator incelemesine aktarmak.",
            "- CIC ve gorsel katman bu pencerede esik ustu bulgu uretmedigi icin ana risk kaynagi davranis/sensor anomalileri olarak yorumlanmalidir.",
        ]
    )


def _llm_status_section(llm: Any) -> str:
    if not isinstance(llm, dict) or not llm.get("enabled"):
        return "Ollama yorumu istenmedi."
    model = llm.get("model", "unknown")
    status = llm.get("status", "unknown")
    if status == "ok":
        return (
            f"Ollama servisi calisti (`model={model}`). "
            "Ham LLM metni JSON raporda saklanmistir; kullaniciya sunulan nihai yorum bu raporda sade ve yapilandirilmis bicimde verilmistir."
        )
    return f"Ollama yorumu alinamadi (`model={model}`): `{llm.get('error', 'unknown error')}`"


def _human_mode(mode: str) -> str:
    return {
        "normal_mode": "Normal Mod",
        "monitoring_mode": "Izleme Modu",
        "degraded_safe_mode": "Kisitli Guvenli Mod",
        "emergency_safe_mode": "Acil Guvenli Mod",
    }.get(mode, mode)


def _pct(count: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{(100.0 * count / total):.1f}%"


def _fmt_float(value: Any) -> str:
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "-"


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _mode_class(mode: str) -> str:
    if mode == "degraded_safe_mode":
        return "warn"
    if mode in {"normal_mode", "monitoring_mode"}:
        return "ok"
    return "danger"


def _dominant_threat(top_threats: list[dict[str, Any]]) -> str:
    if not top_threats:
        return "Belirgin tehdit yok"
    first = top_threats[0]
    return f"{first.get('attack_type', 'unknown')} ({int(first.get('count', 0) or 0)})"


def _dominant_layer(triggered_layers: dict[str, Any]) -> str:
    if not triggered_layers:
        return "Esik ustu katman yok"
    layer, count = max(triggered_layers.items(), key=lambda item: int(item[1] or 0))
    names = {
        "cic": "CIC ag katmani",
        "carla": "CARLA davranis/sensor",
        "visual": "nuScenes gorsel",
        "fusion": "Fusion karar katmani",
    }
    return f"{names.get(str(layer), str(layer))} ({int(count or 0)})"


def _vehicle_scene(safe_mode: str) -> str:
    mode_label = _human_mode(safe_mode)
    return f"""
        <div class="vehicle-scene" aria-label="Otonom arac sensor guvenlik sahnesi">
          <div class="scene-label">
            <span>Sensor Fusion</span>
            <span>{_e(mode_label)}</span>
          </div>
          <div class="sensor-ring"></div>
          <div class="sensor-ring r2"></div>
          <div class="threat-dot d1"></div>
          <div class="threat-dot d2"></div>
          <div class="threat-dot d3"></div>
          <div class="road"><div class="lane-line"></div></div>
          <svg class="car-svg" viewBox="0 0 360 170" role="img" aria-label="Otonom arac">
            <path d="M72 104 L96 58 C103 45 116 38 132 38 H225 C241 38 254 46 263 60 L291 104 Z" fill="#4f9a9a"/>
            <path d="M111 61 H164 V94 H88 Z" fill="#e8f6f4"/>
            <path d="M174 61 H229 L252 94 H174 Z" fill="#e8f6f4"/>
            <rect x="54" y="92" width="252" height="42" rx="17" fill="#2f3d4b"/>
            <rect x="70" y="102" width="55" height="12" rx="6" fill="#8fcfca"/>
            <rect x="235" y="102" width="55" height="12" rx="6" fill="#8fcfca"/>
            <circle cx="111" cy="135" r="23" fill="#1f2937"/>
            <circle cx="111" cy="135" r="10" fill="#a9b4c4"/>
            <circle cx="249" cy="135" r="23" fill="#1f2937"/>
            <circle cx="249" cy="135" r="10" fill="#a9b4c4"/>
            <path d="M169 26 H191 M180 15 V38" stroke="#c0392b" stroke-width="8" stroke-linecap="round"/>
            <circle cx="180" cy="26" r="18" fill="none" stroke="#c0392b" stroke-width="5"/>
          </svg>
        </div>
    """


def _architecture_card(
    code: str,
    title: str,
    subtitle: str,
    triggered: Any,
    layer_class: str,
) -> str:
    count = int(triggered or 0)
    return (
        f'<div class="arch-card {_e(layer_class)}">'
        f'<div class="arch-icon">{_e(code)}</div>'
        f'<h3>{_e(title)}</h3>'
        f'<p>{_e(subtitle)}</p>'
        f'<div class="meta">Esik tetikleme: {count}</div>'
        '</div>'
    )


def _insight_card(title: str, value: str, detail: str) -> str:
    return (
        '<div class="insight">'
        f'<p>{_e(title)}</p>'
        f'<strong>{_e(value)}</strong>'
        f'<p>{_e(detail)}</p>'
        '</div>'
    )


def _diagnostic_card(label: str, value: str, detail: str) -> str:
    return (
        '<div class="diag-card">'
        f'<div class="label">{_e(label)}</div>'
        f'<strong>{_e(value)}</strong>'
        f'<p>{_e(detail)}</p>'
        '</div>'
    )


def _executive_comment(summary: dict[str, Any], threshold: dict[str, Any]) -> str:
    event_count = int(summary.get("event_count", 0) or 0)
    risk_distribution = summary.get("risk_distribution", {}) or {}
    attack_count = int(risk_distribution.get("attack", 0) or 0)
    top_threats = summary.get("top_threats", []) or []
    triggered_layers = threshold.get("triggered_layers", {}) or {}
    mode = str(summary.get("recommended_safe_mode", threshold.get("recommended_safe_mode", "unknown")))
    main_threat = str(top_threats[0].get("attack_type", "belirgin tehdit yok")) if top_threats else "belirgin tehdit yok"
    main_layer = _dominant_layer(triggered_layers)
    return (
        f"Bu izleme penceresinde {event_count} olay analiz edildi ve {attack_count} olay attack/anomali olarak isaretlendi. "
        f"En baskin bulgu {main_threat}; en belirgin sinyal kaynagi {main_layer}. "
        f"Bu nedenle karar katmani {_human_mode(mode)} onerisi uretmistir."
    )


def _status_evidence(summary: dict[str, Any], threshold: dict[str, Any]) -> str:
    top_threats = summary.get("top_threats", []) or []
    final_levels = threshold.get("final_level_distribution", {}) or {}
    triggered_layers = threshold.get("triggered_layers", {}) or {}
    safe_modes = threshold.get("safe_mode_distribution", {}) or {}
    dominant = _dominant_threat(top_threats)
    active_layer = _dominant_layer(triggered_layers)
    critical = int(final_levels.get("critical", 0) or 0)
    emergency = int(safe_modes.get("emergency_safe_mode", 0) or 0)
    return (
        '<div class="decision-evidence">'
        '<div class="evidence-box">'
        '<div class="label">Karar kaniti</div>'
        f'<strong>{_e(dominant)}</strong>'
        f'<p>En sik raporlanan tehdit/anomali sinifi.</p>'
        '</div>'
        '<div class="evidence-box">'
        '<div class="label">Aktif katman</div>'
        f'<strong>{_e(active_layer)}</strong>'
        f'<p>Esik mekanizmasinda en cok tetiklenen kaynak.</p>'
        '</div>'
        '<div class="evidence-box">'
        '<div class="label">Kritik bulgu</div>'
        f'<strong>{critical}</strong>'
        f'<p>Final risk seviyesi kritik olan olay sayisi.</p>'
        '</div>'
        '<div class="evidence-box">'
        '<div class="label">Acil mod</div>'
        f'<strong>{emergency}</strong>'
        f'<p>Emergency safe-mode politikasi uretilen olay sayisi.</p>'
        '</div>'
        '</div>'
        '<div class="status-actions">'
        f'{_status_action("Telemetri ve karar kayitlarini dondur, olay paketini operator incelemesine aktar.")}'
        f'{_status_action("Riskli manevralari kisitla; hiz, rota ve devralma politikasini guvenli moda gore uygula.")}'
        f'{_status_action("Baskin tehdit sinifini ham sensor/ag kayitlariyla capraz dogrula.")}'
        '</div>'
    )


def _status_action(text: str) -> str:
    return (
        '<div class="status-action">'
        '<span class="check">!</span>'
        f'<span>{_e(text)}</span>'
        '</div>'
    )


def _action_plan(summary: dict[str, Any], threshold: dict[str, Any]) -> str:
    mode = str(summary.get("recommended_safe_mode", threshold.get("recommended_safe_mode", "unknown")))
    top_threats = summary.get("top_threats", []) or []
    triggered_layers = threshold.get("triggered_layers", {}) or {}
    threat_text = ", ".join(str(item.get("attack_type")) for item in top_threats[:4]) or "belirgin tehdit yok"
    active_layers = [
        name
        for key, name in {
            "cic": "CIC ag",
            "carla": "CARLA davranis/sensor",
            "visual": "nuScenes gorsel",
            "fusion": "Fusion karar",
        }.items()
        if int(triggered_layers.get(key, 0) or 0) > 0
    ]
    layer_text = ", ".join(active_layers) if active_layers else "esik ustu katman yok"
    if mode == "emergency_safe_mode":
        headline = "Acil aksiyon: araci kontrollu sekilde guvenli moda al."
    elif mode == "degraded_safe_mode":
        headline = "Kisitli aksiyon: hiz, rota ve riskli manevralari sinirla."
    elif mode == "monitoring_mode":
        headline = "Izleme aksiyonu: anomali sinyallerini yakin takip et."
    else:
        headline = "Normal aksiyon: operasyonu surdur ve telemetriyi kaydet."
    return (
        '<div class="callout">'
        f'<strong>{_e(headline)}</strong>'
        f'<p style="margin-top:8px">Aktif katmanlar: {_e(layer_text)}. Oncelikli tehditler: {_e(threat_text)}.</p>'
        '</div>'
        '<ul>'
        '<li>Katman ciktikalari olay bazinda saklanmali ve operator incelemesine acilmalidir.</li>'
        '<li>Yuksek olasilikli CARLA/CIC bulgulari ham sensor ve ag kayitlariyla capraz kontrol edilmelidir.</li>'
        '<li>Safe-mode karari arac politikasi, yol durumu ve insan operator onayi ile birlikte uygulanmalidir.</li>'
        '</ul>'
    )


def _kpi(label: str, value: Any, sub: str) -> str:
    return (
        '<div class="kpi">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e(value)}</div>'
        f'<div class="sub">{_e(sub)}</div>'
        '</div>'
    )


def _dashboard_summary_sentence(
    event_count: int,
    attack_count: int,
    normal_count: int,
    safe_mode: str,
) -> str:
    return (
        f"{event_count} olaylik izleme penceresinde {attack_count} saldiri/anomali ve "
        f"{normal_count} normal karar uretildi. Nihai onerilen mod: {_human_mode(safe_mode)}."
    )


def _dashboard_decision_text(safe_mode: str, critical_count: int) -> str:
    if safe_mode == "emergency_safe_mode":
        return (
            f"{critical_count} kritik bulgu nedeniyle arac icin hiz/rota kisitlama, "
            "riskli manevra engelleme ve kontrollu devralma/onlem senaryosu onerilir."
        )
    if safe_mode == "degraded_safe_mode":
        return "Arac goreve kisitli yetenekle devam etmeli, izleme sikligi artirilmalidir."
    if safe_mode == "monitoring_mode":
        return "Anomali sinyalleri izlenmeli, ek kritik bulgu olusursa mod yukseltilmelidir."
    return "Kritik bulgu yok; normal operasyon surdurulebilir."


def _bar_list(
    items: list[dict[str, Any]],
    total: int,
    label_key: str,
    value_key: str,
    color: str,
) -> str:
    if not items:
        return '<p>Veri bulunamadi.</p>'
    max_value = max(int(item.get(value_key, 0) or 0) for item in items) or 1
    rows = []
    for item in items:
        label = str(item.get(label_key, "unknown"))
        value = int(item.get(value_key, 0) or 0)
        width = 100.0 * value / max_value
        rows.append(
            '<div class="bar-row">'
            f'<div class="bar-label">{_e(label)}</div>'
            '<div class="bar-track">'
            f'<div class="bar-fill {color}" style="width:{width:.1f}%"></div>'
            '</div>'
            f'<div class="bar-value">{value} / {_pct(value, total)}</div>'
            '</div>'
        )
    return '<div class="bar-list">' + "\n".join(rows) + '</div>'


def _bar_dict(
    values: dict[str, Any],
    total: int,
    color: str,
    human_modes: bool = False,
) -> str:
    items = [
        {"label": _human_mode(str(key)) if human_modes else str(key), "value": int(value or 0)}
        for key, value in values.items()
    ]
    items.sort(key=lambda item: item["value"], reverse=True)
    return _bar_list(items, total, "label", "value", color)


def _layer_dashboard_table(
    layer_distribution: dict[str, Any],
    triggered_layers: dict[str, Any],
) -> str:
    names = {
        "cic": "CIC ag katmani",
        "carla": "CARLA davranis/sensor katmani",
        "visual": "nuScenes gorsel tutarlilik katmani",
        "fusion": "Fusion karar katmani",
    }
    rows = []
    for layer in ("cic", "carla", "visual", "fusion"):
        dist = layer_distribution.get(layer, {}) or {}
        triggered = int(triggered_layers.get(layer, 0) or 0)
        dist_text = ", ".join(f"{level}: {count}" for level, count in sorted(dist.items())) or "-"
        rows.append(
            "<tr>"
            f"<td><strong>{_e(names[layer])}</strong></td>"
            f"<td>{triggered}</td>"
            f"<td>{_e(dist_text)}</td>"
            f"<td>{_e(_layer_comment(layer, dist, triggered))}</td>"
            "</tr>"
        )
    return (
        '<table class="layer-table">'
        "<thead><tr><th>Katman</th><th>Tetiklenen</th><th>Seviye Dagilimi</th><th>Yorum</th></tr></thead>"
        "<tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def _metrics_table(metrics: dict[str, Any]) -> str:
    if not metrics:
        return "<p>Model metrik dosyalari bulunamadi.</p>"
    rows = []
    for model_name, model_metrics in metrics.items():
        risk = model_metrics.get("risk", {}) or {}
        safe = model_metrics.get("safe_mode", {}) or {}
        rows.append(
            "<tr>"
            f"<td>{_e(model_name)}</td>"
            f"<td>{_fmt_float(risk.get('accuracy'))}</td>"
            f"<td>{_fmt_float(risk.get('macro_f1'))}</td>"
            f"<td>{_fmt_float(safe.get('accuracy'))}</td>"
            f"<td>{_fmt_float(safe.get('macro_f1'))}</td>"
            "</tr>"
        )
    return (
        '<table class="metric-table">'
        "<thead><tr><th>Model</th><th>Risk Acc.</th><th>Risk Macro F1</th><th>Safe Mode Acc.</th><th>Safe Mode Macro F1</th></tr></thead>"
        "<tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def _dashboard_event_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for event in events:
        decision = event.get("decision", {}) or {}
        if decision.get("risk_level") != "attack":
            continue
        carla = event.get("carla_prediction", {}) or {}
        cic = event.get("cic_prediction", {}) or {}
        visual = event.get("visual_consistency", {}) or {}
        rows.append(
            {
                "index": event.get("index", "-"),
                "timestamp": event.get("timestamp", "-"),
                "risk": decision.get("risk_level", "-"),
                "attack": decision.get("final_attack_type", "-"),
                "mode": decision.get("safe_mode", "-"),
                "carla_p": carla.get("attack_probability"),
                "cic_p": cic.get("attack_probability"),
                "visual_p": visual.get("hallucination_probability"),
            }
        )
    return rows[:80]


def _event_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        mode = str(row["mode"])
        pill_class = {
            "emergency_safe_mode": "danger",
            "degraded_safe_mode": "warn",
            "monitoring_mode": "neutral",
            "normal_mode": "ok",
        }.get(mode, "neutral")
        body.append(
            f'<tr data-event-row data-attack="{_e(str(row["attack"]).lower())}" data-mode="{_e(mode)}">'
            f'<td>{_e(row["index"])}</td>'
            f'<td>{_e(row["timestamp"])}</td>'
            f'<td><span class="pill danger">{_e(row["risk"])}</span></td>'
            f'<td>{_e(row["attack"])}</td>'
            f'<td><span class="pill {pill_class}">{_e(_human_mode(mode))}</span></td>'
            f'<td>{_fmt_float(row["carla_p"])}</td>'
            f'<td>{_fmt_float(row["cic_p"])}</td>'
            f'<td>{_fmt_float(row["visual_p"])}</td>'
            "</tr>"
        )
    if not body:
        body.append('<tr><td colspan="8">Oncelikli olay bulunamadi.</td></tr>')
    return (
        '<table class="event-table">'
        "<thead><tr><th>#</th><th>Zaman</th><th>Risk</th><th>Saldiri turu</th><th>Safe mode</th><th>CARLA p</th><th>CIC p</th><th>Gorsel p</th></tr></thead>"
        "<tbody>"
        + "\n".join(body)
        + "</tbody></table>"
    )


def _durations_by_attack(events: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for event in events:
        attack_type = event["decision"]["final_attack_type"]
        timestamp = event.get("timestamp")
        if timestamp is not None:
            grouped[attack_type].append(float(timestamp))

    durations: dict[str, dict[str, float]] = {}
    for attack, timestamps in grouped.items():
        if len(timestamps) < 2:
            durations[attack] = {"seconds": 0.0, "samples": float(len(timestamps))}
            continue
        seconds = max(timestamps) - min(timestamps)
        if seconds > 1_000_000_000:
            seconds = seconds / 1_000_000.0
        durations[attack] = {"seconds": round(seconds, 3), "samples": float(len(timestamps))}
    return durations
