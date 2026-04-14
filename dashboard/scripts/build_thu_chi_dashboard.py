#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'memory' / 'notes' / 'so_thu_chi.md'
OUT_JSON = ROOT / 'dashboard' / 'data' / 'thu_chi_data.json'
OUT_HTML = ROOT / 'dashboard' / 'thu_chi_dashboard.html'


def parse_amount(text: str) -> int:
    digits = re.sub(r'[^0-9-]', '', text)
    return int(digits) if digits else 0


def format_vnd(value: int) -> str:
    sign = '-' if value < 0 else ''
    value = abs(value)
    return f"{sign}{value:,}".replace(',', '.') + 'đ'


content = SOURCE.read_text(encoding='utf-8')
lines = content.splitlines()

overall_balance = 0
months = []
current = None
section = None

for line in lines:
    line = line.rstrip()

    m = re.match(r'^\*\*Tổng kết dư \(tất cả các tháng\):\s*([0-9.\-]+)đ\*\*$', line)
    if m:
        overall_balance = parse_amount(m.group(1))
        continue

    m = re.match(r'^##\s+(\d{4}-\d{2})$', line)
    if m:
        if current:
            months.append(current)
        current = {
            'month': m.group(1),
            'incomeItems': [],
            'expenseItems': [],
            'wasteItems': [],
            'incomeTotal': 0,
            'expenseTotal': 0,
            'wasteTotal': 0,
            'balance': 0,
        }
        section = None
        continue

    if current is None:
        continue

    m = re.match(r'^###\s+(Thu|Chi|Lãng phí|Kết dư)$', line)
    if m:
        section = m.group(1)
        continue

    m = re.match(r'^-\s+(.+?):\s*([+-][0-9.]+)đ$', line)
    if m and section in {'Thu', 'Chi', 'Lãng phí'}:
        item = {'label': m.group(1), 'amount': parse_amount(m.group(2))}
        if section == 'Thu':
            current['incomeItems'].append(item)
        elif section == 'Chi':
            current['expenseItems'].append(item)
        else:
            current['wasteItems'].append(item)
        continue

    m = re.match(r'^\*\*Tổng thu\s+\d{4}-\d{2}:\s*([0-9.\-]+)đ\*\*$', line)
    if m:
        current['incomeTotal'] = parse_amount(m.group(1))
        continue

    m = re.match(r'^\*\*Tổng chi\s+\d{4}-\d{2}:\s*([0-9.\-]+)đ\*\*$', line)
    if m:
        current['expenseTotal'] = parse_amount(m.group(1))
        continue

    m = re.match(r'^\*\*Tổng lãng phí\s+\d{4}-\d{2}:\s*([0-9.\-]+)đ\*\*$', line)
    if m:
        current['wasteTotal'] = parse_amount(m.group(1))
        continue

    m = re.match(r'^\*\*Kết dư\s+\d{4}-\d{2}:\s*([0-9.\-]+)đ\*\*$', line)
    if m:
        current['balance'] = parse_amount(m.group(1))
        continue

if current:
    months.append(current)

summary = {
    'overallBalance': overall_balance,
    'totalIncome': sum(m['incomeTotal'] for m in months),
    'totalExpense': sum(m['expenseTotal'] for m in months),
    'totalWaste': sum(m['wasteTotal'] for m in months),
    'latestMonth': months[-1]['month'] if months else None,
}

payload = {'summary': summary, 'months': months}
OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

template = '''<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Dashboard Thu Chi</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: #111827;
      --card: #1f2937;
      --text: #e5e7eb;
      --muted: #94a3b8;
      --green: #22c55e;
      --red: #ef4444;
      --yellow: #f59e0b;
      --blue: #38bdf8;
      --purple: #a78bfa;
      --border: rgba(148, 163, 184, 0.18);
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: linear-gradient(180deg, #0b1220 0%, #111827 100%); color: var(--text); }}
    .wrap {{ max-width: 1280px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 32px; }}
    .sub {{ color: var(--muted); margin-bottom: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 16px; margin-bottom: 20px; }}
    .card {{ background: rgba(31, 41, 55, 0.9); border: 1px solid var(--border); border-radius: 18px; padding: 18px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); backdrop-filter: blur(8px); }}
    .label {{ color: var(--muted); font-size: 14px; margin-bottom: 8px; }}
    .value {{ font-size: 28px; font-weight: 700; }}
    .green {{ color: var(--green); }} .red {{ color: var(--red); }} .yellow {{ color: var(--yellow); }} .blue {{ color: var(--blue); }} .purple {{ color: var(--purple); }}
    .charts {{ display: grid; grid-template-columns: 2fr 1fr; gap: 16px; margin-bottom: 20px; }}
    .lower {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; margin-bottom: 20px; }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: right; white-space: nowrap; }}
    th:first-child, td:first-child {{ text-align: left; }}
    tr:last-child td {{ border-bottom: none; }}
    select {{ width: 100%; background: #0f172a; color: var(--text); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; margin-bottom: 14px; }}
    ul {{ margin: 0; padding-left: 18px; }}
    li {{ margin-bottom: 8px; color: #dbe4ee; }}
    .empty {{ color: var(--muted); font-style: italic; }}
    .footer-note {{ color: var(--muted); font-size: 13px; margin-top: 12px; }}
    @media (max-width: 1100px) {{ .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .charts, .lower {{ grid-template-columns: 1fr; }} }}
    @media (max-width: 640px) {{ .grid {{ grid-template-columns: 1fr; }} h1 {{ font-size: 24px; }} .value {{ font-size: 22px; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Dashboard thu chi hàng tháng</h1>
    <div class="sub">Tự động sinh từ file <code>memory/notes/so_thu_chi.md</code></div>

    <div class="grid">
      <div class="card"><div class="label">Tổng kết dư</div><div class="value blue" id="overallBalance"></div></div>
      <div class="card"><div class="label">Tổng thu</div><div class="value green" id="totalIncome"></div></div>
      <div class="card"><div class="label">Tổng chi</div><div class="value red" id="totalExpense"></div></div>
      <div class="card"><div class="label">Tổng lãng phí</div><div class="value yellow" id="totalWaste"></div></div>
      <div class="card"><div class="label">Tháng gần nhất</div><div class="value purple" id="latestMonth"></div></div>
    </div>

    <div class="charts">
      <div class="card">
        <div class="label">So sánh thu, chi, kết dư theo tháng</div>
        <canvas id="barChart" height="120"></canvas>
      </div>
      <div class="card">
        <div class="label">Tỷ trọng chi theo tháng đang chọn</div>
        <select id="monthSelect"></select>
        <canvas id="pieChart" height="220"></canvas>
      </div>
    </div>

    <div class="lower">
      <div class="card table-wrap">
        <div class="label">Bảng tổng hợp theo tháng</div>
        <table>
          <thead>
            <tr>
              <th>Tháng</th>
              <th>Thu</th>
              <th>Chi</th>
              <th>Lãng phí</th>
              <th>Kết dư</th>
            </tr>
          </thead>
          <tbody id="monthlyTableBody"></tbody>
        </table>
      </div>

      <div class="card">
        <div class="label">Chi tiết các khoản của tháng đang chọn</div>
        <div style="display:grid; grid-template-columns:1fr; gap:14px;">
          <div>
            <div class="label green">Thu</div>
            <ul id="incomeList"></ul>
          </div>
          <div>
            <div class="label red">Chi</div>
            <ul id="expenseList"></ul>
          </div>
          <div>
            <div class="label yellow">Lãng phí</div>
            <ul id="wasteList"></ul>
          </div>
        </div>
        <div class="footer-note">Mỗi khi sửa sổ thu chi, chạy lại script để cập nhật dashboard.</div>
      </div>
    </div>
  </div>

  <script>
    const data = __DATA__;

    const formatVnd = (value) => new Intl.NumberFormat('vi-VN').format(value) + 'đ';

    document.getElementById('overallBalance').textContent = formatVnd(data.summary.overallBalance);
    document.getElementById('totalIncome').textContent = formatVnd(data.summary.totalIncome);
    document.getElementById('totalExpense').textContent = formatVnd(data.summary.totalExpense);
    document.getElementById('totalWaste').textContent = formatVnd(data.summary.totalWaste);
    document.getElementById('latestMonth').textContent = data.summary.latestMonth || '-';

    const months = data.months;
    const labels = months.map(m => m.month);
    const income = months.map(m => m.incomeTotal);
    const expense = months.map(m => m.expenseTotal);
    const waste = months.map(m => m.wasteTotal);
    const balance = months.map(m => m.balance);

    const tableBody = document.getElementById('monthlyTableBody');
    months.forEach((m) => {{
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${{m.month}}</td>
        <td class="green">${{formatVnd(m.incomeTotal)}}</td>
        <td class="red">${{formatVnd(m.expenseTotal)}}</td>
        <td class="yellow">${{formatVnd(m.wasteTotal)}}</td>
        <td class="${{m.balance >= 0 ? 'blue' : 'red'}}">${{formatVnd(m.balance)}}</td>
      `;
      tableBody.appendChild(tr);
    }});

    new Chart(document.getElementById('barChart'), {{
      type: 'bar',
      data: {{
        labels,
        datasets: [
          {{ label: 'Thu', data: income, backgroundColor: '#22c55e' }},
          {{ label: 'Chi', data: expense, backgroundColor: '#ef4444' }},
          {{ label: 'Lãng phí', data: waste, backgroundColor: '#f59e0b' }},
          {{ label: 'Kết dư', data: balance, type: 'line', borderColor: '#38bdf8', backgroundColor: '#38bdf8', tension: 0.3 }}
        ]
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{ labels: {{ color: '#e5e7eb' }} }},
          tooltip: {{ callbacks: {{ label: (ctx) => `${{ctx.dataset.label}}: ${{formatVnd(ctx.raw)}}` }} }}
        }},
        scales: {{
          x: {{ ticks: {{ color: '#cbd5e1' }}, grid: {{ color: 'rgba(148,163,184,0.12)' }} }},
          y: {{ ticks: {{ color: '#cbd5e1', callback: (value) => formatVnd(value) }}, grid: {{ color: 'rgba(148,163,184,0.12)' }} }}
        }}
      }}
    }});

    const monthSelect = document.getElementById('monthSelect');
    months.forEach((m, index) => {{
      const option = document.createElement('option');
      option.value = index;
      option.textContent = m.month;
      monthSelect.appendChild(option);
    }});
    monthSelect.value = String(Math.max(months.length - 1, 0));

    let pieChart;
    const renderList = (el, items, cls) => {{
      el.innerHTML = '';
      if (!items.length) {{
        const li = document.createElement('li');
        li.className = 'empty';
        li.textContent = 'Chưa có';
        el.appendChild(li);
        return;
      }}
      items.forEach((item) => {{
        const li = document.createElement('li');
        li.className = cls;
        li.textContent = `${{item.label}}: ${{formatVnd(item.amount)}}`;
        el.appendChild(li);
      }});
    }};

    const updateMonthDetail = (index) => {{
      const month = months[index];
      renderList(document.getElementById('incomeList'), month.incomeItems, 'green');
      renderList(document.getElementById('expenseList'), month.expenseItems, 'red');
      renderList(document.getElementById('wasteList'), month.wasteItems, 'yellow');

      const expenseItems = month.expenseItems.length ? month.expenseItems : [{{ label: 'Chưa có chi tiêu', amount: 1 }}];
      const pieData = {{
        labels: expenseItems.map(i => i.label),
        datasets: [{{
          data: expenseItems.map(i => i.amount),
          backgroundColor: ['#60a5fa', '#ef4444', '#f59e0b', '#22c55e', '#a78bfa', '#f472b6', '#34d399', '#f97316', '#2dd4bf', '#fb7185']
        }}]
      }};

      if (pieChart) pieChart.destroy();
      pieChart = new Chart(document.getElementById('pieChart'), {{
        type: 'doughnut',
        data: pieData,
        options: {{
          responsive: true,
          plugins: {{
            legend: {{ position: 'bottom', labels: {{ color: '#e5e7eb' }} }},
            tooltip: {{ callbacks: {{ label: (ctx) => `${{ctx.label}}: ${{formatVnd(ctx.raw)}}` }} }}
          }}
        }}
      }});
    }};

    monthSelect.addEventListener('change', (e) => updateMonthDetail(Number(e.target.value)));
    updateMonthDetail(Number(monthSelect.value || 0));
  </script>
</body>
</html>
'''

html = template.replace('__DATA__', json.dumps(payload, ensure_ascii=False))

OUT_HTML.write_text(html, encoding='utf-8')
print(f'Built {OUT_HTML.relative_to(ROOT)} and {OUT_JSON.relative_to(ROOT)}')
