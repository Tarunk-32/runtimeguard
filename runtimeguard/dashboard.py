"""Builds a single self-contained HTML dashboard summarizing multiple agent runs.

No server and no build step: generate_dashboard() writes one .html file with
its data baked in, a bar chart (via a Chart.js CDN <script> tag), and a table.
Opening the file directly in a browser is enough - it just needs internet
access to fetch the Chart.js library from the CDN, nothing local to run.
"""

import html
import json
import os

# Fixed categorical color order (light/dark pair per slot), so the same label
# always gets the same color and colors are never picked ad hoc. Cycles if
# there are more distinct labels than slots.
_CATEGORICAL_PALETTE = [
    ("#2a78d6", "#3987e5"),  # blue
    ("#eb6834", "#d95926"),  # orange
    ("#1baf7a", "#199e70"),  # aqua
    ("#eda100", "#c98500"),  # yellow
    ("#e87ba4", "#d55181"),  # magenta
    ("#008300", "#008300"),  # green
    ("#4a3aa7", "#9085e9"),  # violet
    ("#e34948", "#e66767"),  # red
]

_STATUS_GOOD = ("#0ca30c", "#0ca30c")
_STATUS_STOPPED = ("#d03b3b", "#e66767")


def _escape(value) -> str:
    """Turn any value into HTML-safe text (escapes <, >, &, quotes)."""
    return html.escape("" if value is None else str(value), quote=True)


def _color_map_for(labels):
    """Assign each distinct label a fixed color, in first-seen order."""
    color_map = {}
    for label in labels:
        if label not in color_map:
            slot = _CATEGORICAL_PALETTE[len(color_map) % len(_CATEGORICAL_PALETTE)]
            color_map[label] = slot
    return color_map


def _status_text(record: dict) -> str:
    """Human-readable status for a run: completed, or stopped + why."""
    if record.get("stopped"):
        reason = record.get("stop_reason") or "unknown reason"
        return f"Stopped: {reason}"
    return "Completed"


def generate_dashboard(run_records: list, output_path: str) -> None:
    """Write a single HTML file at output_path summarizing all given runs.

    Each item in run_records is a dict describing one agent run, expected to
    have at least: label, total_cost, step_count, stopped (bool),
    stop_reason, timestamp. The generated page has a bar chart of cost per
    run (bars colored by label, using a fixed color per distinct label) and
    a table listing every run's label, steps, cost, status, and timestamp.
    Everything - markup, styles, data, and chart-drawing script - lives in
    this one file; only the Chart.js library itself is loaded from a CDN.
    """
    labels = [str(r.get("label") or "Unlabeled run") for r in run_records]
    color_map = _color_map_for(labels)

    # Data for Chart.js: one bar per run, colored by that run's label.
    chart_labels = labels
    chart_costs = [round(float(r.get("total_cost") or 0.0), 6) for r in run_records]
    chart_colors_light = [color_map[label][0] for label in labels]
    chart_colors_dark = [color_map[label][1] for label in labels]

    chart_data = {
        "labels": chart_labels,
        "costs": chart_costs,
        "colorsLight": chart_colors_light,
        "colorsDark": chart_colors_dark,
    }
    # Embed as JSON, but neutralize "</" so a value like a stop_reason
    # containing "</script>" can't prematurely close the <script> block.
    chart_data_json = json.dumps(chart_data).replace("</", "<\\/")

    legend_items = "".join(
        f'<span class="legend-item">'
        f'<span class="swatch" style="--swatch:{color_map[label][0]};'
        f'--swatch-dark:{color_map[label][1]}"></span>'
        f"{_escape(label)}</span>"
        for label in dict.fromkeys(labels)  # de-duplicated, first-seen order
    )

    table_rows = []
    for record in run_records:
        label = str(record.get("label") or "Unlabeled run")
        stopped = bool(record.get("stopped"))
        status_icon = "⚠️" if stopped else "✅"
        status_color = _STATUS_STOPPED if stopped else _STATUS_GOOD
        status_label = _status_text(record)
        cost_text = _escape(f"{float(record.get('total_cost') or 0.0):.6f}")
        table_rows.append(
            "<tr>"
            f'<td>{_escape(label)}</td>'
            f'<td class="num">{_escape(record.get("step_count"))}</td>'
            f'<td class="num">${cost_text}</td>'
            f'<td><span class="status" style="--status:{status_color[0]};'
            f'--status-dark:{status_color[1]}">{status_icon} {_escape(status_label)}'
            "</span></td>"
            f'<td>{_escape(record.get("timestamp"))}</td>'
            "</tr>"
        )
    table_rows_html = "\n".join(table_rows)

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RuntimeGuard Dashboard</title>
<style>
  :root {{
    color-scheme: light;
    --surface-1:      #fcfcfb;
    --page:           #f9f9f7;
    --text-primary:   #0b0b0b;
    --text-secondary: #52514e;
    --text-muted:     #898781;
    --gridline:       #e1e0d9;
    --baseline:       #c3c2b7;
    --border:         rgba(11,11,11,0.10);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      color-scheme: dark;
      --surface-1:      #1a1a19;
      --page:           #0d0d0d;
      --text-primary:   #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted:     #898781;
      --gridline:       #2c2c2a;
      --baseline:       #383835;
      --border:         rgba(255,255,255,0.10);
    }}
  }}

  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--page);
    color: var(--text-primary);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  }}
  main {{
    max-width: 900px;
    margin: 0 auto;
    padding: 32px 20px 64px;
  }}
  h1 {{
    font-size: 20px;
    font-weight: 600;
    margin: 0 0 4px;
  }}
  .subtitle {{
    color: var(--text-secondary);
    font-size: 13px;
    margin: 0 0 24px;
  }}
  .card {{
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
  }}
  .card h2 {{
    font-size: 14px;
    font-weight: 600;
    color: var(--text-secondary);
    margin: 0 0 16px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  .chart-wrap {{
    position: relative;
    height: 320px;
  }}
  .legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px 20px;
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid var(--gridline);
  }}
  .legend-item {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--text-secondary);
  }}
  .swatch {{
    width: 10px;
    height: 10px;
    border-radius: 3px;
    background: var(--swatch);
  }}
  @media (prefers-color-scheme: dark) {{
    .swatch {{ background: var(--swatch-dark); }}
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }}
  th, td {{
    text-align: left;
    padding: 10px 12px;
    border-bottom: 1px solid var(--gridline);
  }}
  th {{
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.04em;
  }}
  td.num {{
    font-variant-numeric: tabular-nums;
  }}
  .status {{
    color: var(--status);
    font-weight: 500;
  }}
  @media (prefers-color-scheme: dark) {{
    .status {{ color: var(--status-dark); }}
  }}
</style>
</head>
<body>
<main>
  <h1>RuntimeGuard Dashboard</h1>
  <p class="subtitle">Cost and outcome summary across {len(run_records)} run(s)</p>

  <section class="card">
    <h2>Cost per run</h2>
    <div class="chart-wrap">
      <canvas id="costChart"></canvas>
    </div>
    <div class="legend">{legend_items}</div>
  </section>

  <section class="card">
    <h2>Run details</h2>
    <table>
      <thead>
        <tr>
          <th>Label</th>
          <th>Steps</th>
          <th>Cost</th>
          <th>Status</th>
          <th>Timestamp</th>
        </tr>
      </thead>
      <tbody>
{table_rows_html}
      </tbody>
    </table>
  </section>
</main>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<script>
  const RUN_DATA = {chart_data_json};

  const prefersDark = window.matchMedia
    ? window.matchMedia("(prefers-color-scheme: dark)").matches
    : false;
  const barColors = prefersDark ? RUN_DATA.colorsDark : RUN_DATA.colorsLight;
  const inkMuted = prefersDark ? "#898781" : "#898781";
  const gridline = prefersDark ? "#2c2c2a" : "#e1e0d9";
  const inkPrimary = prefersDark ? "#ffffff" : "#0b0b0b";

  new Chart(document.getElementById("costChart"), {{
    type: "bar",
    data: {{
      labels: RUN_DATA.labels,
      datasets: [{{
        label: "Cost ($)",
        data: RUN_DATA.costs,
        backgroundColor: barColors,
        borderRadius: 4,
        maxBarThickness: 48,
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label: (ctx) => "$" + ctx.parsed.y.toFixed(6)
          }}
        }}
      }},
      scales: {{
        x: {{
          ticks: {{ color: inkMuted, font: {{ size: 11 }} }},
          grid: {{ display: false }},
        }},
        y: {{
          beginAtZero: true,
          ticks: {{
            color: inkMuted,
            font: {{ size: 11 }},
            callback: (value) => "$" + value
          }},
          grid: {{ color: gridline }},
        }}
      }}
    }}
  }});
</script>
</body>
</html>
"""

    parent_dir = os.path.dirname(output_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
