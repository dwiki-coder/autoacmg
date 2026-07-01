/* ====================================================
   AutoACMG — Frontend application
   ==================================================== */

(function () {
    'use strict';

    const API = '/api/v1';

    /* ── State ── */
    let resultsCache = [];
    let currentMode = 'single';

    /* ── Helpers ── */
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    function toast(msg, type = 'info') {
        const c = document.createElement('div');
        c.className = `toast toast-${type}`;
        c.textContent = msg;
        const container = document.getElementById('toast-container') || (() => {
            const el = document.createElement('div');
            el.id = 'toast-container';
            el.className = 'toast-container';
            document.body.appendChild(el);
            return el;
        })();
        container.appendChild(c);
        setTimeout(() => { c.style.opacity = '0'; setTimeout(() => c.remove(), 300); }, 4000);
    }

    function setLoading(on) {
        $('#loading-overlay').style.display = on ? 'flex' : 'none';
        if (on) {
            $('#btn-classify').disabled = true;
            $('#btn-batch-classify').disabled = true;
        } else {
            $('#btn-classify').disabled = false;
            $('#btn-batch-classify').disabled = false;
        }
    }

    function getClassificationClass(cls) {
        if (!cls) return 'cls-vus';
        const c = cls.toLowerCase().replace(/[^a-z]/g, '');
        if (c.includes('pathogenic') && !c.includes('likely')) return 'cls-pathogenic';
        if (c.includes('pathogenic') || c.includes('likelypathogenic')) return 'cls-likely-pathogenic';
        if (c.includes('likelybenign') || c.includes('benign')) return 'cls-benign';
        if (c.includes('likely') || c.includes('benign')) return 'cls-likely-benign';
        return 'cls-vus';
    }

    function getShortClassification(cls) {
        if (!cls) return 'VUS';
        const c = cls.trim();
        if (c.includes('Pathogenic') && !c.includes('Likely')) return 'Pathogenic';
        if (c.includes('Likely Pathogenic')) return 'Likely Pathogenic';
        if (c.includes('Uncertain') || c.includes('Uncertain Significance')) return 'VUS';
        if (c.includes('Likely Benign')) return 'Likely Benign';
        if (c.includes('Benign')) return 'Benign';
        return c;
    }

    /* ── API calls ── */
    async function apiStatus() {
        const r = await fetch(`${API}/status`);
        return r.json();
    }

    async function apiAnnotate(payload) {
        const r = await fetch(`${API}/annotate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!r.ok) throw new Error(`API error ${r.status}: ${await r.text()}`);
        return r.json();
    }

    async function apiBatch(payload) {
        const r = await fetch(`${API}/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!r.ok) throw new Error(`API error ${r.status}: ${await r.text()}`);
        return r.json();
    }

    async function apiExport(format) {
        const r = await fetch(`${API}/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ results: resultsCache, format }),
        });
        if (!r.ok) throw new Error(`API error ${r.status}`);
        return r.json();
    }

    /* ── Status check on load ── */
    async function checkStatus() {
        const dot = document.querySelector('.indicator-dot');
        const label = document.querySelector('.indicator-label');
        try {
            const s = await apiStatus();
            dot.className = 'indicator-dot online';
            label.textContent = 'Online';
            if (s.version) $('#app-version').textContent = `v${s.version}`;
        } catch {
            dot.className = 'indicator-dot offline';
            label.textContent = 'Offline';
        }
    }

    /* ── Mode toggle ── */
    function setMode(mode) {
        currentMode = mode;
        $$('.mode-tab').forEach(t => t.classList.toggle('active', t.dataset.mode === mode));
        $('#form-single').style.display = mode === 'single' ? 'block' : 'none';
        $('#form-batch').style.display = mode === 'batch' ? 'block' : 'none';
    }

    $$('#tab-single, #tab-batch').forEach(btn => {
        btn.addEventListener('click', () => setMode(btn.dataset.mode));
    });

    /* ── Chromosome custom input ── */
    const chrSelect = $('#chromosome');
    const chrCustom = $('#chromosome-custom');
    chrSelect.addEventListener('change', () => {
        if (chrSelect.value === 'custom') {
            chrCustom.style.display = 'block';
            chrCustom.focus();
        } else {
            chrCustom.style.display = 'none';
        }
        validateSingle();
    });
    chrCustom.addEventListener('input', validateSingle);

    /* ── Form validation ── */
    function validateSingle() {
        const chr = chrSelect.value === 'custom' ? chrCustom.value.trim() : chrSelect.value;
        const pos = $('#position').value;
        const ref = $('#ref').value.trim();
        const alt = $('#alt').value.trim();
        $('#btn-classify').disabled = !(chr && pos && ref && alt);
    }
    ['chromosome', 'position', 'ref', 'alt'].forEach(id => {
        const el = document.getElementById(id);
        el.addEventListener('input', validateSingle);
        el.addEventListener('change', validateSingle);
    });

    /* ── Build single payload ── */
    function buildSinglePayload() {
        let chr = chrSelect.value === 'custom' ? chrCustom.value.trim() : chrSelect.value;
        return {
            chromosome: chr,
            position: parseInt($('#position').value),
            ref: $('#ref').value.trim().toUpperCase(),
            alt: $('#alt').value.trim().toUpperCase(),
            sample_id: $('#sample-id').value.trim() || 'unknown',
            annotate: $('#annotate-cb').checked,
            sources: [...$$('.source-cb:checked')].map(c => c.value),
        };
    }

    /* ── Classify single ── */
    $('#btn-classify').addEventListener('click', async () => {
        const payload = buildSinglePayload();
        if (!payload.chromosome || !payload.position || !payload.ref || !payload.alt) {
            toast('Please fill in all required fields.', 'error');
            return;
        }
        setLoading(true);
        $('#loading-text').textContent = 'Classifying variant...';
        try {
            const result = await apiAnnotate(payload);
            resultsCache = [result];
            renderResults([result]);
            toast('Variant classified successfully.', 'success');
        } catch (err) {
            toast(`Classification failed: ${err.message}`, 'error');
            console.error(err);
        } finally {
            setLoading(false);
        }
    });

    /* ── Parse batch lines ── */
    function parseBatchLines(text) {
        return text.split('\n')
            .map(l => l.trim())
            .filter(l => l && !l.startsWith('#'))
            .map(l => {
                const parts = l.split(':');
                if (parts.length < 4) throw new Error(`Invalid format: "${l}". Expected chrom:pos:ref:alt[:sample_id]`);
                return {
                    chromosome: parts[0].trim(),
                    position: parseInt(parts[1]),
                    ref: parts[2].trim().toUpperCase(),
                    alt: parts[3].trim().toUpperCase(),
                    sample_id: (parts[4] || 'unknown').trim(),
                };
            });
    }

    /* ── Batch classify ── */
    $('#btn-batch-classify').addEventListener('click', async () => {
        const text = $('#batch-input').value.trim();
        if (!text) {
            toast('Please enter at least one variant.', 'error');
            return;
        }
        let variants;
        try {
            variants = parseBatchLines(text);
        } catch (e) {
            toast(e.message, 'error');
            return;
        }

        const annotate = $('#batch-annotate-cb').checked;
        const sources = [...$$('.batch-source-cb:checked')].map(c => c.value);

        setLoading(true);
        $('#loading-text').textContent = `Classifying ${variants.length} variant${variants.length > 1 ? 's' : ''}...`;

        try {
            const payload = {
                variants: variants.map(v => ({ ...v, annotate, sources })),
                annotate,
                sources,
            };
            const results = await apiBatch(payload);
            resultsCache = results;
            renderResults(results);
            toast(`Batch classification complete: ${results.length} variant${results.length > 1 ? 's' : ''}.`, 'success');
        } catch (err) {
            toast(`Batch failed: ${err.message}`, 'error');
            console.error(err);
        } finally {
            setLoading(false);
        }
    });

    /* ── Render results ── */
    function renderResults(results) {
        const panel = $('#results-panel');
        const body = $('#results-body');
        const count = $('#results-count');
        panel.style.display = 'block';
        count.textContent = `${results.length} result${results.length !== 1 ? 's' : ''}`;

        body.innerHTML = '';

        results.forEach((r, i) => {
            const card = document.createElement('div');
            card.className = 'result-card';

            const variantKey = buildVariantKey(r);
            const sampleId = r.sample_id || 'unknown';
            const cls = r.classification || r.final_classification || 'Uncertain Significance';
            const shortCls = getShortClassification(cls);
            const clsClass = getClassificationClass(cls);
            const confidence = typeof r.confidence === 'number' ? Math.round(r.confidence * 100) : 0;

            card.innerHTML = `
                <div class="result-header" onclick="this.nextElementSibling.classList.toggle('open')">
                    <div>
                        <span class="variant-identifier">${variantKey}</span>
                        <span class="variant-sample">${sampleId !== 'unknown' ? '· ' + sampleId : ''}</span>
                    </div>
                    <span class="classification-badge ${clsClass}">${shortCls}</span>
                </div>
                <div class="result-body">
                    ${renderCriteria(r)}
                    ${renderEvidence(r)}
                    ${renderConfidence(confidence)}
                </div>
            `;
            body.appendChild(card);
        });

        // Scroll to results
        panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function buildVariantKey(r) {
        const chr = r.chromosome || r.chr || r.variant || '';
        const pos = r.position || r.pos || '';
        const ref = r.ref || '';
        const alt = r.alt || '';
        if (chr && pos && ref && alt) {
            return `${chr}:${pos}:${ref.toUpperCase()}:${alt.toUpperCase()}`;
        }
        return r.variant || r.id || 'Unknown variant';
    }

    function renderCriteria(r) {
        const criteria = r.criteria || r.applied_criteria || r.criteria_details || [];
        if (!criteria || (Array.isArray(criteria) && criteria.length === 0)) {
            if (typeof criteria === 'string' && criteria) {
                return `
                    <div class="criteria-section">
                        <h4>Applied Criteria</h4>
                        <ul class="criteria-list">
                            <li class="criteria-item">
                                <span class="criteria-code">—</span>
                                <span class="criteria-desc">${escapeHtml(criteria)}</span>
                            </li>
                        </ul>
                    </div>`;
            }
            return '';
        }
        if (Array.isArray(criteria)) {
            const items = criteria.map(c => {
                const code = typeof c === 'object' ? (c.code || c.criteria || c.code || '—') : c;
                const desc = typeof c === 'object' ? (c.description || c.evidence || '') : '';
                return `<li class="criteria-item">
                    <span class="criteria-code">${escapeHtml(String(code))}</span>
                    ${desc ? `<span class="criteria-desc">${escapeHtml(desc)}</span>` : ''}
                </li>`;
            }).join('');
            return `
                <div class="criteria-section">
                    <h4>Applied Criteria</h4>
                    <ul class="criteria-list">${items}</ul>
                </div>`;
        }
        return '';
    }

    function renderEvidence(r) {
        const evidence = r.evidence || r.evidence_summary || r.annotations || {};
        if (!evidence || typeof evidence !== 'object' || Object.keys(evidence).length === 0) return '';
        let rows = '';
        for (const [key, val] of Object.entries(evidence)) {
            const displayVal = typeof val === 'object' ? JSON.stringify(val) : String(val);
            rows += `<tr><td>${escapeHtml(key)}</td><td>${escapeHtml(displayVal.substring(0, 200))}</td></tr>`;
        }
        return `
            <div class="criteria-section">
                <h4>Evidence Summary</h4>
                <table class="evidence-table">
                    <thead><tr><th>Source</th><th>Value</th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>`;
    }

    function renderConfidence(pct) {
        return `
            <div class="confidence-section">
                <div class="confidence-label">
                    <span>Confidence</span>
                    <span>${pct}%</span>
                </div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width:${pct}%"></div>
                </div>
            </div>`;
    }

    function escapeHtml(s) {
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    /* ── Export ── */
    async function doExport(format) {
        if (resultsCache.length === 0) {
            toast('No results to export. Classify a variant first.', 'error');
            return;
        }
        setLoading(true);
        $('#loading-text').textContent = `Generating ${format.toUpperCase()} report...`;
        try {
            const response = await apiExport(format);
            let content = response.content || '';

            if (format === 'json') {
                if (typeof content === 'string') content = content;
                else content = JSON.stringify(content, null, 2);
                downloadFile(content, 'autoacmg-report.json', 'application/json');
            } else if (format === 'csv') {
                downloadFile(content, 'autoacmg-report.csv', 'text/csv');
            } else if (format === 'html') {
                downloadFile(content, 'autoacmg-report.html', 'text/html');
            }
            toast(`${format.toUpperCase()} report exported.`, 'success');
        } catch (err) {
            // Fallback: generate client-side
            const fallback = clientSideExport(format);
            downloadFile(fallback, `autoacmg-report.${format}`, format === 'json' ? 'application/json' : 'text/plain');
            toast(`Report exported (client-side fallback).`, 'info');
        } finally {
            setLoading(false);
        }
    }

    function clientSideExport(format) {
        if (format === 'json') return JSON.stringify(resultsCache, null, 2);
        if (format === 'csv') {
            const headers = ['variant', 'classification', 'sample_id', 'confidence'];
            const rows = resultsCache.map(r => {
                return headers.map(h => {
                    const v = r[h] || '';
                    return `"${String(v).replace(/"/g, '""')}"`;
                }).join(',');
            });
            return [headers.join(','), ...rows].join('\n');
        }
        return JSON.stringify(resultsCache, null, 2);
    }

    function downloadFile(content, filename, mime) {
        const blob = new Blob([content], { type: mime });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    $('#btn-export-json').addEventListener('click', () => doExport('json'));
    $('#btn-export-csv').addEventListener('click', () => doExport('csv'));
    $('#btn-export-html').addEventListener('click', () => doExport('html'));

    /* ── Clear ── */
    $('#btn-clear').addEventListener('click', () => {
        resultsCache = [];
        $('#results-panel').style.display = 'none';
        $('#results-body').innerHTML = '';
    });

    /* ── Status modal ── */
    $('#btn-status').addEventListener('click', async () => {
        const modal = $('#status-modal');
        const body = $('#modal-body');
        modal.style.display = 'flex';
        body.innerHTML = '<div class="spinner" style="margin:20px auto"></div>';
        try {
            const s = await apiStatus();
            body.innerHTML = `
                <pre>${JSON.stringify(s, null, 2)}</pre>
            `;
        } catch (err) {
            body.innerHTML = `<p style="color:var(--danger)">Could not reach API: ${err.message}</p>`;
        }
    });

    $('#btn-close-modal').addEventListener('click', () => {
        $('#status-modal').style.display = 'none';
    });
    $('#status-modal').addEventListener('click', (e) => {
        if (e.target === $('#status-modal')) $('#status-modal').style.display = 'none';
    });

    /* ── Init ── */
    checkStatus();
    // Re-check every 30s
    setInterval(checkStatus, 30000);

})();
