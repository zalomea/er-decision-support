(function (global) {
    'use strict';

    function toDisplayScore(rawScore) {
        return rawScore + 1;
    }

    function labelForScore(displayScore, labels, fallback) {
        const index = Math.round(displayScore) - 1;
        if (index < 0 || index >= labels.length) return fallback;
        return labels[index];
    }

    function verdictClassForPriority(displayScore) {
        if (displayScore <= 2) return 'priority-high';
        if (displayScore <= 3) return 'priority-medium';
        return 'priority-low';
    }

    function dischargeVerdict(noul) {
        return noul > 0.5 ? 'yes' : 'no';
    }

    function noulConfidence(noul) {
        return Math.abs(noul - 0.5) * 2;
    }

    const EDInsight = {
        toDisplayScore: toDisplayScore,
        labelForScore: labelForScore,
        verdictClassForPriority: verdictClassForPriority,
        dischargeVerdict: dischargeVerdict,
        noulConfidence: noulConfidence,
    };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = EDInsight;
    }
    global.EDInsight = EDInsight;

    if (typeof document === 'undefined') return;

    const I18N = {
        en: {
            subtitle: 'Explore how a language model interprets emergency-care narratives for triage and disposition support.',
            safetyTitle: 'Research use only — not for patient care',
            safetyBody: 'This prototype is not a medical device and must not be used to diagnose, triage, or make treatment decisions. Use fictional or de-identified examples only; never enter protected health information.',
            reportHeading: 'Clinical narrative',
            reportHint: 'Paste a fictional or de-identified report, or load one of the sample cases.',
            reportPlaceholder: 'Enter a fictional or de-identified patient report...',
            searchBtn: 'Search examples',
            dispositionBtn: 'Disposition assessment',
            priorityBtn: 'ESI triage estimate',
            bothBtn: 'Run both evaluations',
            dispositionTitle: 'Disposition assessment',
            priorityTitle: 'ESI triage estimate',
            footer: 'AI-generated output can be incomplete or incorrect. A qualified clinician must independently assess any real patient.',
            modalTitle: 'Search examples',
            close: 'Close',
            keyword: 'Keyword',
            searchPlaceholder: 'Type a keyword...',
            searching: 'Searching…',
            noResults: 'No results found.',
            error: 'Error',
            couldNotLoad: 'Could not load file',
            enterReport: 'Please enter a patient report.',
            evalDisposition: 'Evaluating disposition…',
            evalPriority: 'Estimating triage level…',
            confidence: 'Confidence',
            severity: 'Severity',
            riskFactor: 'Risk Factor',
            triage: 'Triage',
            resources: 'Resources',
            yes: 'Yes',
            no: 'No',
            unknown: 'Unknown',
            severityLabels: ['Minor', 'Moderate', 'Serious', 'Critical'],
            esiLabels: ['Immediate (ESI-1)', 'High risk (ESI-2)', 'Urgent (ESI-3)', 'Less urgent (ESI-4)', 'Non-urgent (ESI-5)'],
            fullMode: 'Full mode',
            simpleMode: 'Simple mode',
        },
        es: {
            subtitle: 'Explore cómo un modelo de lenguaje interpreta narrativas de urgencias para triaje y decisión de destino.',
            safetyTitle: 'Solo uso de investigación — no para atención médica',
            safetyBody: 'Este prototipo no es un dispositivo médico y no debe usarse para diagnosticar, triajar o tomar decisiones de tratamiento. Use solo ejemplos ficticios o desidentificados; nunca ingrese información de salud protegida.',
            reportHeading: 'Narrativa clínica',
            reportHint: 'Pegue un informe ficticio o desidentificado, o cargue uno de los casos de ejemplo.',
            reportPlaceholder: 'Ingrese un informe de paciente ficticio o desidentificado...',
            searchBtn: 'Buscar ejemplos',
            dispositionBtn: 'Evaluación de destino',
            priorityBtn: 'Estimación de triaje ESI',
            bothBtn: 'Ejecutar ambas evaluaciones',
            dispositionTitle: 'Evaluación de destino',
            priorityTitle: 'Estimación de triaje ESI',
            footer: 'La salida generada por IA puede ser incompleta o incorrecta. Un clínico calificado debe evaluar independientemente a cualquier paciente real.',
            modalTitle: 'Buscar ejemplos',
            close: 'Cerrar',
            keyword: 'Palabra clave',
            searchPlaceholder: 'Escriba una palabra clave...',
            searching: 'Buscando…',
            noResults: 'No se encontraron resultados.',
            error: 'Error',
            couldNotLoad: 'No se pudo cargar el archivo',
            enterReport: 'Por favor ingrese un informe de paciente.',
            evalDisposition: 'Evaluando destino…',
            evalPriority: 'Estimando nivel de triaje…',
            confidence: 'Confianza',
            severity: 'Severidad',
            riskFactor: 'Factor de riesgo',
            triage: 'Triaje',
            resources: 'Recursos',
            yes: 'Sí',
            no: 'No',
            unknown: 'Desconocido',
            severityLabels: ['Menor', 'Moderada', 'Grave', 'Crítica'],
            esiLabels: ['Inmediato (ESI-1)', 'Alto riesgo (ESI-2)', 'Urgente (ESI-3)', 'Menos urgente (ESI-4)', 'No urgente (ESI-5)'],
            fullMode: 'Modo completo',
            simpleMode: 'Modo simple',
        }
    };

    let currentLang = 'en';
    function setMode(simple) {
        document.getElementById('fullModeBtn').classList.toggle('active', !simple);
        document.getElementById('simpleModeBtn').classList.toggle('active', simple);
        document.getElementById('fullModeBtn').textContent = t('fullMode');
        document.getElementById('simpleModeBtn').textContent = t('simpleMode');
    }

    function setLang(lang) {
        currentLang = lang;
        document.getElementById('langEn').classList.toggle('active', lang === 'en');
        document.getElementById('langEs').classList.toggle('active', lang === 'es');
        applyLang();
    }

    function t(key) {
        return I18N[currentLang][key] || key;
    }

    function applyLang() {
        document.querySelector('.subtitle').textContent = t('subtitle');
        document.querySelector('.safety-notice strong').textContent = t('safetyTitle');
        document.querySelector('.safety-notice div').childNodes[1].textContent = ' ' + t('safetyBody');
        document.getElementById('reportHeading').textContent = t('reportHeading');
        document.getElementById('reportHint').textContent = t('reportHint');
        document.getElementById('patientReport').placeholder = t('reportPlaceholder');
        document.querySelector('.btn-search').textContent = t('searchBtn');
        document.querySelector('.btn-discharge').textContent = t('dispositionBtn');
        document.querySelector('.btn-priority').textContent = t('priorityBtn');
        document.querySelector('.btn-both').textContent = t('bothBtn');
        document.querySelector('#dischargeCard h3').textContent = t('dispositionTitle');
        document.querySelector('#priorityCard h3').textContent = t('priorityTitle');
        document.querySelector('.page-footer').textContent = t('footer');
        document.getElementById('searchModalTitle').textContent = t('modalTitle');
        document.querySelector('.modal-close').setAttribute('aria-label', t('close'));
        document.getElementById('searchInput').placeholder = t('searchPlaceholder');
        document.getElementById('searchInput').setAttribute('aria-label', t('keyword'));
        document.getElementById('fullModeBtn').textContent = t('fullMode');
        document.getElementById('simpleModeBtn').textContent = t('simpleMode');
    }

    function openSearchModal() {
        const modal = document.getElementById('searchModal');
        modal.hidden = false;
        document.getElementById('searchInput').focus();
    }

    function closeSearchModal() {
        document.getElementById('searchModal').hidden = true;
    }

    function highlightMatch(context, query) {
        const escaped = escapeHtml(context);
        const escapedQuery = escapeHtml(query);
        const regex = new RegExp(`(${escapedQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return escaped.replace(regex, '<mark>$1</mark>');
    }

    async function searchExamples() {
        const input = document.getElementById('searchInput');
        const query = input.value.trim();
        const container = document.getElementById('searchResults');
        if (!query) { container.innerHTML = ''; input.classList.remove('searching'); return; }
        input.classList.add('searching');
        try {
            const resp = await fetch(`/api/examples/search?q=${encodeURIComponent(query)}`);
            if (!resp.ok) throw new Error(`Error (${resp.status})`);
            const data = await resp.json();
            const results = data.results || [];
            if (results.length === 0) {
                container.innerHTML = `<div class="search-empty">${t('noResults')}</div>`;
                return;
            }
            container.innerHTML = results.map(r => `
                <div class="search-result" style="cursor:pointer" data-file="${escapeHtml(r.file)}">
                    <div class="result-file">${escapeHtml(r.file)}</div>
                    <div class="result-context">${highlightMatch(r.context, query)}</div>
                </div>
            `).join('');
        } catch (e) {
            container.innerHTML = `<div class="search-empty">${t('error')}: ${escapeHtml(e.message)}</div>`;
        } finally {
            input.classList.remove('searching');
        }
    }

    async function loadExampleFile(filePath) {
        try {
            const resp = await fetch(`/api/examples/file?path=${encodeURIComponent(filePath)}`);
            if (!resp.ok) throw new Error(`Error (${resp.status})`);
            const data = await resp.json();
            document.getElementById('patientReport').value = data.content || '';
            closeSearchModal();
        } catch (e) {
            showError(`${t('couldNotLoad')}: ${e.message}`);
        }
    }

    function showError(msg) {
        const box = document.getElementById('errorBox');
        box.textContent = msg;
        box.style.display = 'block';
        setTimeout(() => box.style.display = 'none', 8000);
    }

    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, char => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        })[char]);
    }

    function numericValue(value, fallback = 0) {
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : fallback;
    }

    async function requestEvaluation(endpoint, report, container, render) {
        try {
            const simple = document.getElementById('simpleModeBtn').classList.contains('active');
            const sep = endpoint.includes('?') ? '&' : '?';
            const url = simple ? `${endpoint}${sep}simple=true` : endpoint;
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ report })
            });
            if (!response.ok) throw new Error(`Evaluation failed (${response.status}). Check that the model service is available.`);
            render(container, await response.json());
        } catch (error) {
            container.innerHTML = `<div class="error" role="alert">${escapeHtml(error.message || 'Unable to complete evaluation.')}</div>`;
        }
    }

    async function runEvaluation(task) {
        const report = document.getElementById('patientReport').value.trim();
        if (!report) {
            showError(t('enterReport'));
            return;
        }

        const dischargeCard = document.getElementById('dischargeCard');
        const priorityCard = document.getElementById('priorityCard');
        const dischargeContent = document.getElementById('dischargeContent');
        const priorityContent = document.getElementById('priorityContent');

        dischargeCard.classList.remove('visible');
        priorityCard.classList.remove('visible');

        const runDischarge = task === 'discharge' || task === 'both';
        const runPriority = task === 'priority' || task === 'both';

        const buttons = [...document.querySelectorAll('.actions button')];
        buttons.forEach(button => { button.disabled = true; });
        const promises = [];
        if (runDischarge) {
            dischargeCard.classList.add('visible');
            dischargeContent.innerHTML = `<div class="loading" role="status">${t('evalDisposition')}</div>`;
            promises.push(requestEvaluation('/api/discharge', report, dischargeContent, renderDischarge));
        }
        if (runPriority) {
            priorityCard.classList.add('visible');
            priorityContent.innerHTML = `<div class="loading" role="status">${t('evalPriority')}</div>`;
            promises.push(requestEvaluation('/api/priority', report, priorityContent, renderPriority));
        }
        try { await Promise.all(promises); }
        finally { buttons.forEach(button => { button.disabled = false; }); }
    }

    function renderDischarge(container, data) {
        try {
            const answers = data.answers || data;
            const discharge = answers.discharge || {};
            const severity = answers.severity || {};
            const risk = answers.risk_factors || {};

            const noulProb = numericValue(discharge.noul);
            const isDischarge = EDInsight.dischargeVerdict(noulProb) === 'yes';
            const dischargeLabel = isDischarge ? t('yes') : t('no');
            const verdictClass = isDischarge ? 'yes' : 'no';
            const dischargeConf = EDInsight.noulConfidence(noulProb);

            let html = `
                <div class="verdict ${verdictClass}">${dischargeLabel}</div>
                <div class="result-item">
                    <span class="result-label">${t('confidence')}</span>
                    <span class="result-value">${(numericValue(dischargeConf) * 100).toFixed(1)}%</span>
                </div>
            `;

            if (severity.score !== undefined) {
                const severityDisplay = EDInsight.toDisplayScore(numericValue(severity.score));
                const severityLabels = t('severityLabels');
                html += `
                    <div class="result-item">
                        <span class="result-label">${t('severity')}</span>
                        <span class="result-value">${severityDisplay.toFixed(2)} - ${EDInsight.labelForScore(severityDisplay, severityLabels, t('unknown'))}</span>
                    </div>
                `;
            }

            if (risk.choice !== undefined) {
                const riskConf = risk.confidence || 0;
                html += `
                    <div class="result-item">
                        <span class="result-label">${t('riskFactor')}</span>
                        <span class="result-value">${escapeHtml(risk.choice)} (${(numericValue(riskConf) * 100).toFixed(1)}%)</span>
                    </div>
                `;
            }

            container.innerHTML = html;
        } catch (e) {
            container.textContent = `Unable to interpret the model response: ${e.message}`;
        }
    }

    function renderPriority(container, data) {
        try {
            const answers = data.answers || data;
            const priority = answers.priority || {};
            const triage = answers.triage_category || {};
            const resources = answers.resource_needs || {};

            const p = EDInsight.toDisplayScore(numericValue(priority.score));
            const verdictClass = EDInsight.verdictClassForPriority(p);
            const labels = t('esiLabels');

            let html = `
                <div class="verdict ${verdictClass}">${p.toFixed(1)} - ${EDInsight.labelForScore(p, labels, t('unknown'))}</div>
                <div class="result-item">
                    <span class="result-label">${t('confidence')}</span>
                    <span class="result-value">${((priority.confidence || 0) * 100).toFixed(1)}%</span>
                </div>
            `;

            if (triage.choice !== undefined) {
                html += `
                    <div class="result-item">
                        <span class="result-label">${t('triage')}</span>
                        <span class="result-value">${escapeHtml(triage.choice)}</span>
                    </div>
                `;
            }

            if (resources.choice !== undefined) {
                html += `
                    <div class="result-item">
                        <span class="result-label">${t('resources')}</span>
                        <span class="result-value">${escapeHtml(resources.choice)}</span>
                    </div>
                `;
            }

            container.innerHTML = html;
        } catch (e) {
            container.textContent = `Unable to interpret the model response: ${e.message}`;
        }
    }

    function debounce(fn, wait) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn(...args), wait);
        };
    }

    document.getElementById('searchInput').addEventListener('input', debounce(searchExamples, 300));
    document.getElementById('searchBtn').addEventListener('click', openSearchModal);
    document.querySelector('.modal-close').addEventListener('click', closeSearchModal);
    document.getElementById('fullModeBtn').addEventListener('click', () => setMode(false));
    document.getElementById('simpleModeBtn').addEventListener('click', () => setMode(true));
    document.getElementById('dischargeBtn').addEventListener('click', () => runEvaluation('discharge'));
    document.getElementById('priorityBtn').addEventListener('click', () => runEvaluation('priority'));
    document.getElementById('bothBtn').addEventListener('click', () => runEvaluation('both'));
    document.getElementById('langEn').addEventListener('click', () => setLang('en'));
    document.getElementById('langEs').addEventListener('click', () => setLang('es'));
    document.getElementById('searchResults').addEventListener('click', (e) => {
        const item = e.target.closest('.search-result');
        if (item) loadExampleFile(item.dataset.file);
    });
    document.getElementById('searchModal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) closeSearchModal();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeSearchModal();
    });
})(typeof window !== 'undefined' ? window : globalThis);
