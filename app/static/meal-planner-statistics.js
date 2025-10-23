// meal-planner-statistics.js
// This file handles rendering the meal planner statistics charts using Chart.js
(() => {
  const raf = () => new Promise(r => requestAnimationFrame(r));
  const onDOMReady = () =>
    document.readyState === 'loading'
      ? new Promise(res => document.addEventListener('DOMContentLoaded', res, { once: true }))
      : Promise.resolve();

  const readVars = () => {
    const css = getComputedStyle(document.documentElement);
    return {
      theme: document.documentElement.getAttribute('data-theme') || '',
      COLOR: (css.getPropertyValue('--color') || '').trim(),
      CHART_TEXT: (css.getPropertyValue('--color-chart-text') || '').trim(),
      PIE_COLORS_RAW: (css.getPropertyValue('--colors-pie-chart') || '').trim(),
    };
  };

  async function waitForCssVarsReady({ timeoutMs = 3000 } = {}) {
    const start = performance.now();
    const initial = readVars();

    const readyNow = () => {
        const cur = readVars();
        const colorReady = !!cur.COLOR;
        const paletteReady = !!cur.PIE_COLORS_RAW;
        const changed =
            (cur.COLOR && cur.COLOR !== initial.COLOR) ||
            (cur.PIE_COLORS_RAW && cur.PIE_COLORS_RAW !== initial.PIE_COLORS_RAW) ||
            (cur.theme && cur.theme !== initial.theme);
        const themeApplied = ['light','dark'].includes(cur.theme);
        return themeApplied && (colorReady || paletteReady);
    };

    if (readyNow()) return;
    const mo = new MutationObserver(() => { if (readyNow()) mo.disconnect(); });
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme', 'style'] });

    while (performance.now() - start < timeoutMs) {
      await raf();
      if (readyNow()) break;
      await new Promise(r => setTimeout(r, 16));
    }
    mo.disconnect();
    await raf();
  }

  async function waitForChartJs({ timeoutMs = 3000 } = {}) {
    const start = performance.now();
    while (typeof window.Chart === 'undefined') {
      if (performance.now() - start > timeoutMs) {
        console.error('Chart.js not loaded (expect chart.umd.min.js with defer).');
        throw new Error('ChartMissing');
      }
      await raf();
    }
  }

  function last12MonthLabels() {
    const out = [];
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth() - 11, 1);
    for (let i = 0; i < 12; i++) {
      const d = new Date(start.getFullYear(), start.getMonth() + i, 1);
      out.push(d.toLocaleDateString(undefined, { month: 'short', year: 'numeric' }));
    }
    return out;
  }

  async function fetchStatJSON() {
    try {
      const r = await fetch('/meal-planner/stat-data', { cache: 'no-store', credentials: 'same-origin' });
      if (!r.ok) throw new Error('BadStatus ' + r.status);
      const data = await r.json();
      if (!data || !data.line || !data.pie) throw new Error('BadShape');
      return data;
    } catch (e) {
      console.warn('Falling back: could not load /meal-planner/stat-data:', e);

      // Fallback: 0 days for each of last 12 months; pie has only Miscellaneous: 0
      return {
        line: {
          legend: 'Days Cooked',
          xAxisTitle: 'Months',
          yAxisTitle: 'Days',
          labels: last12MonthLabels(),
          values: Array(12).fill(0)
        },
        pie: {
          labels: ['Miscellaneous'],
          values: [0]
        }
      };
    }
  }

  (async () => {
    await onDOMReady();
    await waitForCssVarsReady();
    await waitForChartJs();

    // Reading theme CSS variables
    const css = getComputedStyle(document.documentElement);
    const BRAND = (css.getPropertyValue('--color') || '').trim() || '#2980b9';
    const CHART_TEXT = (css.getPropertyValue('--color-chart-text') || '').trim() || '#808080';
    const rawPie = (css.getPropertyValue('--colors-pie-chart') || '').trim();
    const PIE_COLORS = (rawPie && rawPie.length
      ? rawPie
      : '#2980b9, #218c74, #7b00bb, #ae0085, #d46a47'
    ).split(',').map(s => s.trim());

    const chartDataJSON = await fetchStatJSON();
    // If there are 0 total recipes, show Miscellaneous as 100% so the pie still renders
    let pieLabels = (chartDataJSON.pie && chartDataJSON.pie.labels) || [];
    let pieValues = (chartDataJSON.pie && chartDataJSON.pie.values) || [];
    const pieTotal = pieValues.reduce((a, b) => a + (Number(b) || 0), 0);
    if (pieTotal <= 0) {
        pieLabels = ['Miscellaneous'];
        // Slice value must be non-zero to render as a full circle
        pieValues = [1];
    }

    // Pie Chart
    const pieEl = document.getElementById('pieChart');
    if (pieEl) {
      new Chart(pieEl, {
        type: 'pie',
        data: {
          labels: pieLabels,
          datasets: [{
            data: pieValues,
            backgroundColor: PIE_COLORS,
            borderColor: 'transparent',
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: { color: CHART_TEXT, boxWidth: 12, boxHeight: 12 }
            },
            tooltip: {
              callbacks: {
                label: (ctx) => {
                  const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                  const val = ctx.parsed;
                  const pct = total ? (val / total * 100).toFixed(1) : 0;
                  return `${ctx.label}: ${val} (${pct}%)`;
                }
              }
            }
          }
        }
      });
    } else {
      console.warn('#pieChart canvas not found');
    }

    // Line Chart
    const lineEl = document.getElementById('lineChart');
    if (lineEl) {
      new Chart(lineEl, {
        type: 'line',
        data: {
          labels: chartDataJSON.line.labels,
          datasets: [{
            label: chartDataJSON.line.legend,
            data: chartDataJSON.line.values,
            fill: false,
            tension: 0.25,
            pointRadius: 3,
            borderWidth: 2,
            borderColor: BRAND,
            pointBackgroundColor: BRAND,
            pointBorderColor: BRAND,
            backgroundColor: BRAND,
            pointStyle: 'rect'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 300 },
          plugins: {
            legend: { display: true, labels: { color: CHART_TEXT, boxWidth: 12, boxHeight: 12, usePointStyle: true } },
            tooltip: { mode: 'index', intersect: false }
          },
          scales: {
            x: {
              title: { display: true, text: chartDataJSON.line.xAxisTitle, color: CHART_TEXT },
              ticks: { color: CHART_TEXT },
              grid: { color: CHART_TEXT + '33' },
              border: { color: CHART_TEXT }
            },
            y: {
              beginAtZero: true,
              suggestedMax: 5,
              title: { display: true, text: chartDataJSON.line.yAxisTitle, color: CHART_TEXT },
              ticks: { color: CHART_TEXT, precision: 0 },
              grid: { color: CHART_TEXT + '33' },
              border: { color: CHART_TEXT }
            }
          }
        }
      });
    } else {
      console.warn('#lineChart canvas not found');
    }
  })();
})();
