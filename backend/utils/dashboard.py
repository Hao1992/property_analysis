"""Generate the admin analytics dashboard as a self-contained HTML page."""
import json


def render(stats: dict, token: str = "") -> str:
    data_json = json.dumps(stats, default=str)
    token_js  = json.dumps(token)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Beyond Price — Analytics</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f1117;color:#e2e8f0;font-size:14px;line-height:1.5}}
  .hdr{{background:#1a1f2e;border-bottom:1px solid #2d3748;padding:16px 24px;display:flex;align-items:center;gap:12px}}
  .hdr h1{{font-size:18px;font-weight:700;color:#fff}}
  .hdr .tag{{background:#c8956c;color:#fff;font-size:11px;font-weight:600;padding:2px 8px;border-radius:4px}}
  .body{{padding:24px;max-width:1400px;margin:0 auto}}
  .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:24px}}
  .card{{background:#1a1f2e;border:1px solid #2d3748;border-radius:10px;padding:16px}}
  .card .label{{font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px}}
  .card .value{{font-size:28px;font-weight:700;color:#fff}}
  .card .sub{{font-size:12px;color:#718096;margin-top:2px}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}}
  .grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:16px}}
  @media(max-width:900px){{.grid2,.grid3{{grid-template-columns:1fr}}}}
  .panel{{background:#1a1f2e;border:1px solid #2d3748;border-radius:10px;padding:16px}}
  .panel h2{{font-size:13px;font-weight:600;color:#a0aec0;text-transform:uppercase;letter-spacing:.06em;margin-bottom:14px}}
  .chart-wrap{{position:relative;height:200px}}
  table{{width:100%;border-collapse:collapse;font-size:12px}}
  th{{text-align:left;padding:6px 10px;color:#718096;border-bottom:1px solid #2d3748;font-weight:500}}
  td{{padding:6px 10px;border-bottom:1px solid #1e2535;color:#e2e8f0}}
  tr:last-child td{{border-bottom:none}}
  .pill{{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:600}}
  .pill-en{{background:#2b4c7e;color:#90cdf4}}
  .pill-zh{{background:#2d3748;color:#fc8181}}
  .badge-ok{{color:#68d391}}.badge-fail{{color:#fc8181}}
  .metric{{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #1e2535}}
  .metric:last-child{{border-bottom:none}}
  .metric .k{{color:#a0aec0;font-size:12px}}
  .metric .v{{font-weight:600;color:#fff}}
  .bar-row{{display:flex;align-items:center;gap:8px;margin-bottom:6px}}
  .bar-row .bl{{width:100px;font-size:11px;color:#a0aec0;text-align:right;flex-shrink:0}}
  .bar-row .bc{{flex:1;background:#2d3748;border-radius:3px;height:14px;overflow:hidden}}
  .bar-row .bf{{background:#c8956c;height:100%;border-radius:3px;transition:width .3s}}
  .bar-row .bv{{width:40px;font-size:11px;color:#e2e8f0;flex-shrink:0}}
</style>
</head>
<body>
<div class="hdr">
  <div>
    <h1>Beyond Price <span style="font-weight:400;color:#718096">Analytics</span></h1>
  </div>
  <span class="tag">Admin</span>
  <span style="margin-left:auto;font-size:12px;color:#718096" id="refresh-label"></span>
</div>

<div class="body">
  <!-- Summary cards -->
  <div class="cards" id="cards"></div>

  <!-- DAU + Score dist -->
  <div class="grid2">
    <div class="panel">
      <h2>Daily Analyses (14 days)</h2>
      <div class="chart-wrap"><canvas id="dauChart"></canvas></div>
    </div>
    <div class="panel">
      <h2>Score Distribution</h2>
      <div class="chart-wrap"><canvas id="scoreChart"></canvas></div>
    </div>
  </div>

  <!-- Districts + Price + Language -->
  <div class="grid3">
    <div class="panel">
      <h2>Top Districts</h2>
      <div id="districtBars"></div>
    </div>
    <div class="panel">
      <h2>Price Range</h2>
      <div class="chart-wrap" style="height:160px"><canvas id="priceChart"></canvas></div>
    </div>
    <div class="panel">
      <h2>API Health</h2>
      <div id="apiHealth"></div>
    </div>
  </div>

  <!-- Frontend events + Profiles -->
  <div class="grid2">
    <div class="panel">
      <h2>Section Views (frontend tracking)</h2>
      <div id="sectionBars"></div>
    </div>
    <div class="panel">
      <h2>Buyer Profiles</h2>
      <div id="profileBars"></div>
    </div>
  </div>

  <!-- Recent analyses -->
  <div class="panel" style="margin-bottom:0">
    <h2>Recent Analyses</h2>
    <div style="overflow-x:auto">
      <table id="recentTable">
        <thead><tr>
          <th>Time</th><th>Address</th><th>District</th>
          <th>Score</th><th>Price</th><th>Lang</th>
          <th>Duration</th><th>Fotocasa</th>
        </tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</div>

<script>
const D = {data_json};
const TOKEN = {token_js};

// Summary cards
const cards = [
  {{label:'Total Analyses', value:D.total, sub:'all time'}},
  {{label:'Today',          value:D.today, sub:'analyses'}},
  {{label:'This Week',      value:D.week,  sub:'analyses'}},
  {{label:'Unique IPs',     value:D.unique_ips, sub:'all time'}},
  {{label:'Avg Score',      value:D.avg_score ?? '—', sub:'/100'}},
  {{label:'Fotocasa Rate',  value:D.fc_rate!=null ? D.fc_rate+'%' : '—', sub:`of ${{D.fc_total}} calls`}},
  {{label:'P50 Duration',   value:D.dur_p50 ? (D.dur_p50/1000).toFixed(1)+'s' : '—', sub:'fresh analysis'}},
  {{label:'PDF Downloads',  value:D.pdf_downloads, sub:'all time'}},
];
document.getElementById('cards').innerHTML = cards.map(c=>
  `<div class="card"><div class="label">${{c.label}}</div><div class="value">${{c.value}}</div><div class="sub">${{c.sub}}</div></div>`
).join('');

// Chart defaults
Chart.defaults.color = '#718096';
Chart.defaults.borderColor = '#2d3748';
const barCfg = (labels, data, color='#c8956c') => ({{
  type:'bar', data:{{labels, datasets:[{{data, backgroundColor:color, borderRadius:4}}]}},
  options:{{responsive:true, maintainAspectRatio:false, plugins:{{legend:{{display:false}}}}, scales:{{y:{{beginAtZero:true,ticks:{{precision:0}}}},x:{{ticks:{{maxRotation:45}}}}}}}}
}});

// DAU chart
const dauLabels = D.daily.map(d=>d.date.slice(5));
const dauData   = D.daily.map(d=>d.count);
new Chart(document.getElementById('dauChart'), barCfg(dauLabels, dauData));

// Score distribution
const scoreLabels = D.score_dist.map(d=>d.range);
const scoreData   = D.score_dist.map(d=>d.count);
new Chart(document.getElementById('scoreChart'), barCfg(scoreLabels, scoreData, '#68d391'));

// Price chart
const priceFiltered = D.price_dist.filter(d=>d.count>0);
new Chart(document.getElementById('priceChart'), {{
  type:'doughnut',
  data:{{
    labels: priceFiltered.map(d=>d.bucket),
    datasets:[{{data: priceFiltered.map(d=>d.count),
      backgroundColor:['#c8956c','#e8a87c','#68d391','#4299e1','#9f7aea','#f6ad55','#718096'],
      borderWidth:0}}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'right',labels:{{boxWidth:10,font:{{size:11}}}}}}}}}}
}});

// Bar rows helper
function barRows(containerId, items, keyField, valField) {{
  const max = Math.max(...items.map(i=>i[valField]), 1);
  document.getElementById(containerId).innerHTML = items.map(i=>
    `<div class="bar-row"><span class="bl">${{i[keyField]}}</span><div class="bc"><div class="bf" style="width:${{Math.round(i[valField]/max*100)}}%"></div></div><span class="bv">${{i[valField]}}</span></div>`
  ).join('') || '<span style="color:#718096;font-size:12px">No data yet</span>';
}}

barRows('districtBars', D.districts.slice(0,8), 'district', 'count');
barRows('sectionBars', D.top_sections.slice(0,8), 'section', 'views');

// Profiles
const profileItems = Object.entries(D.profiles).map(([k,v])=>{{return {{profile:k, count:v}}}});
barRows('profileBars', profileItems, 'profile', 'count');

// API health
const health = [
  ['Fotocasa success', D.fc_rate!=null ? D.fc_rate+'%' : '—'],
  ['P50 duration',     D.dur_p50 ? (D.dur_p50/1000).toFixed(1)+'s' : '—'],
  ['P95 duration',     D.dur_p95 ? (D.dur_p95/1000).toFixed(1)+'s' : '—'],
  ['EN / ZH split',    `${{D.languages.en||0}} / ${{D.languages.zh||0}}`],
  ['Language switches', D.lang_switches],
];
document.getElementById('apiHealth').innerHTML = health.map(([k,v])=>
  `<div class="metric"><span class="k">${{k}}</span><span class="v">${{v}}</span></div>`
).join('');

// Recent table
const tbody = document.querySelector('#recentTable tbody');
tbody.innerHTML = D.recent.map(r=>
  `<tr>
    <td style="color:#718096">${{r.ts}}</td>
    <td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${{r.address}}</td>
    <td>${{r.district}}</td>
    <td style="font-weight:600;color:${{r.score>=70?'#68d391':r.score>=50?'#f6ad55':'#fc8181'}}">${{r.score??'—'}}</td>
    <td><span style="color:#a0aec0">${{r.price}}</span></td>
    <td><span class="pill pill-${{r.lang}}">${{r.lang}}</span></td>
    <td>${{r.dur_s}}s</td>
    <td class="${{r.fotocasa==='✓'?'badge-ok':'badge-fail'}}">${{r.fotocasa}}</td>
  </tr>`
).join('') || '<tr><td colspan="8" style="color:#718096;text-align:center;padding:20px">No analyses yet</td></tr>';

// Timestamp
document.getElementById('refresh-label').textContent = 'Generated ' + new Date().toLocaleTimeString();
</script>
</body>
</html>"""
