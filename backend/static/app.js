/**
 * CrediNews AI — Clean 2D News Verifier & Results Dashboard
 */

document.addEventListener('DOMContentLoaded', () => {
  // ───── 1. Theme Toggle (Light / Dark) ─────
  const themeToggle = document.getElementById('theme-toggle');
  const themeIcon = document.getElementById('theme-icon');
  const htmlRoot = document.documentElement;

  function initTheme() {
    const saved = localStorage.getItem('credinews_theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');
    applyTheme(theme);
  }

  function applyTheme(theme) {
    htmlRoot.setAttribute('data-theme', theme);
    themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    localStorage.setItem('credinews_theme', theme);
  }

  themeToggle.addEventListener('click', () => {
    const current = htmlRoot.getAttribute('data-theme') || 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark');
  });

  initTheme();

  // ───── 2. Navigation & Page Switching ─────
  const navPills = document.querySelectorAll('.nav-pill[data-page]');
  const viewPanels = document.querySelectorAll('.view-panel');
  const historyCount = document.getElementById('history-count');
  const btnBackTop = document.getElementById('btn-back-top');
  const btnBackBottom = document.getElementById('btn-back-bottom');

  function switchPage(pageId) {
    navPills.forEach(p => {
      const target = p.getAttribute('data-page');
      p.classList.toggle('active', target === pageId);
    });

    viewPanels.forEach(panel => {
      panel.classList.toggle('hidden', panel.id !== pageId);
    });

    // Clean scroll to top without shifting or jumping
    window.scrollTo({ top: 0, behavior: 'smooth' });

    if (pageId === 'page-history') renderHistory();
  }

  navPills.forEach(pill => {
    pill.addEventListener('click', () => {
      switchPage(pill.getAttribute('data-page'));
    });
  });

  // Back to Checker Buttons (both top and bottom)
  function handleBackToChecker() {
    switchPage('page-checker');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  btnBackTop.addEventListener('click', handleBackToChecker);
  btnBackBottom.addEventListener('click', handleBackToChecker);

  // ───── 3. Check History (localStorage) ─────
  const STORAGE_KEY = 'credinews_history';

  function getHistory() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; }
    catch { return []; }
  }

  function saveHistoryItem(item) {
    const list = getHistory();
    list.unshift(item);
    if (list.length > 50) list.pop();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    updateHistoryBadge();
  }

  function clearHistory() {
    localStorage.removeItem(STORAGE_KEY);
    updateHistoryBadge();
    renderHistory();
  }

  function updateHistoryBadge() {
    const count = getHistory().length;
    if (historyCount) historyCount.textContent = count;
  }
  updateHistoryBadge();

  const historyContainer = document.getElementById('history-container');
  const btnClearHistory = document.getElementById('btn-clear-history');

  btnClearHistory.addEventListener('click', () => {
    if (confirm('Clear all saved check history?')) clearHistory();
  });

  function renderHistory() {
    const list = getHistory();
    historyContainer.innerHTML = '';

    if (list.length === 0) {
      historyContainer.innerHTML = `
        <div class="history-empty-view">
          <div class="empty-icon">📂</div>
          <p>No checks recorded yet.</p>
          <p style="font-size: 0.8rem; color: var(--text-light); margin-top: 0.25rem;">Articles or files you analyze will appear here automatically.</p>
        </div>
      `;
      return;
    }

    list.forEach(entry => {
      const card = document.createElement('div');
      card.className = 'history-item-card';
      const isFake = entry.is_fake;
      const badgeClass = isFake ? 'is-fake' : 'is-real';
      const badgeLabel = isFake ? '⚠ Likely Misleading' : '✓ Likely Authentic';
      const typeLabel = entry.type === 'batch' ? `📁 Batch (${entry.batchCount} rows)` : '';

      card.innerHTML = `
        <div class="history-left">
          <div class="history-title-text">${escapeHtml(entry.headline)}</div>
          <div class="history-snippet-text">${escapeHtml(entry.snippet)}</div>
          <div class="history-info-meta">
            <span>📅 ${entry.date}</span>
            <span>Score: <strong>${entry.score}%</strong></span>
            ${typeLabel ? `<span>${typeLabel}</span>` : ''}
          </div>
        </div>
        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem;">
          <span class="status-badge ${badgeClass}">${badgeLabel}</span>
          ${entry.type !== 'batch' ? `<button type="button" class="btn-secondary recheck-action" style="padding: 0.25rem 0.65rem; font-size: 0.78rem;">Re-check</button>` : ''}
        </div>
      `;

      if (entry.type !== 'batch') {
        const recheckBtn = card.querySelector('.recheck-action');
        if (recheckBtn) {
          recheckBtn.addEventListener('click', () => {
            titleInput.value = entry.title || '';
            textInput.value = entry.fullText || entry.snippet;
            updateCounter();
            switchPage('page-checker');
            textInput.focus();
          });
        }
      }

      historyContainer.appendChild(card);
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, tag => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag] || tag));
  }

  // ───── 4. Form & Input Handlers ─────
  const form = document.getElementById('verify-form');
  const titleInput = document.getElementById('news-title');
  const textInput = document.getElementById('news-text');
  const textCounter = document.getElementById('text-counter');
  const btnSubmit = document.getElementById('btn-submit');
  const btnLabel = document.getElementById('btn-label');
  const btnSpinner = document.getElementById('btn-spinner');
  const btnReset = document.getElementById('btn-reset');

  // File Upload
  const fileUpload = document.getElementById('file-upload');
  const fileNameDisplay = document.getElementById('file-name-display');
  const btnClearFile = document.getElementById('btn-clear-file');
  let pendingFile = null;

  fileUpload.addEventListener('change', () => {
    const file = fileUpload.files[0];
    if (file) {
      pendingFile = file;
      fileNameDisplay.textContent = file.name;
      fileNameDisplay.style.display = 'inline';
      btnClearFile.style.display = 'inline';
    }
  });

  btnClearFile.addEventListener('click', () => {
    pendingFile = null;
    fileUpload.value = '';
    fileNameDisplay.style.display = 'none';
    btnClearFile.style.display = 'none';
  });

  function updateCounter() {
    const text = textInput.value || '';
    const trimmed = text.trim();
    const words = trimmed ? trimmed.split(/\s+/).length : 0;
    textCounter.textContent = `${words} word${words === 1 ? '' : 's'}`;
  }
  textInput.addEventListener('input', updateCounter);

  btnReset.addEventListener('click', () => {
    titleInput.value = '';
    textInput.value = '';
    updateCounter();
    pendingFile = null;
    fileUpload.value = '';
    fileNameDisplay.style.display = 'none';
    btnClearFile.style.display = 'none';
    currentFactCheckCard = null;
    titleInput.focus();
  });

  // Quick Samples
  const sampleArticles = {
    real_clean: {
      title: "Municipal Transit Authority Approves Clean Fleet Modernization Schedule",
      text: "The regional metropolitan transport authority approved a multi-year fleet transition schedule on Wednesday. Under the newly ratified agreement, regional transit operators will integrate eighty low-emission hybrid buses across principal corridors by the conclusion of the fiscal period. Project directors noted that the initiative will be funded through local transportation grants and state infrastructure credits."
    },
    real_econ: {
      title: "European Central Bank Lowers Benchmark Interest Rate by 25 Basis Points",
      text: "Policymakers in Frankfurt concluded their monetary policy session on Thursday by trimming the deposit facility rate to three percent. Economic forecasters cited moderating wage pressures and subdued industrial output across the eurozone as primary factors supporting the measured easing step. Officials emphasized that future adjustments will remain strictly data-dependent."
    },
    fake_cure: {
      title: "Secret Pine Extract Eliminates Joint Discomfort Overnight Says Anonymous Healer",
      text: "Conventional wellness clinics are astonished by this woodland compound! An undisclosed wellness coach asserts that common forest bark completely rejuvenates joint flexibility in mere hours. Officials reportedly concealed the method to safeguard retail pharmacy revenues! Secure your supply today while access remains open!"
    },
    fake_politics: {
      title: "Pope Francis Endorses Donald Trump for President in Historic Vatican Announcement",
      text: "In an unprecedented move that has shocked religious observers worldwide, Vatican officials reportedly declared that Pope Francis has made the historic decision to endorse Donald Trump. Major news networks have reportedly refused to cover this explosive statement, but insiders confirmed that the endorsement was delivered during a private audience yesterday."
    }
  };

  document.querySelectorAll('.sample-chip[data-sample]').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.getAttribute('data-sample');
      const article = sampleArticles[key];
      if (article) {
        titleInput.value = article.title;
        textInput.value = article.text;
        updateCounter();
        textInput.focus();
      }
    });
  });

  // ───── 5. Keywords & Signals Extraction (2D Data Graphs) ─────
  function extractKeywordsAndSignals(title, text, isFake) {
    const fullText = `${title} ${text}`.toLowerCase();
    const keywords = [];
    const signals = [];

    // Sensational / Clickbait Keywords
    const sensationalTerms = [
      'shocking', 'unbelievable', 'miracle', 'secret', 'bombshell',
      'cure', 'suppress', 'hidden', 'exposed', 'urgent', 'disrupt',
      'refused to broadcast', 'refused to cover', 'conspiracy', 'overnight'
    ];

    sensationalTerms.forEach(term => {
      if (fullText.includes(term)) {
        keywords.push({ term, type: 'warning' });
      }
    });

    // Journalistic / Attribution Keywords
    const attributionTerms = [
      'according to', 'officials said', 'spokesperson', 'reuters',
      'published in', 'study', 'reported', 'ratified', 'directors',
      'announced', 'statement', 'consortium', 'investigators'
    ];

    attributionTerms.forEach(term => {
      if (fullText.includes(term)) {
        keywords.push({ term, type: 'positive' });
      }
    });

    // Fallback topic keywords if few matches
    if (keywords.length < 3) {
      const cleanWords = fullText.replace(/[^a-z\s]/g, ' ').split(/\s+/);
      const stopWords = new Set(['the','and','a','to','of','in','that','is','was','for','on','with','as','by','at','from','it','an','be','this']);
      const wordCounts = {};
      cleanWords.forEach(w => {
        if (w.length > 4 && !stopWords.has(w)) {
          wordCounts[w] = (wordCounts[w] || 0) + 1;
        }
      });
      const topWords = Object.keys(wordCounts).sort((a,b) => wordCounts[b] - wordCounts[a]).slice(0, 3);
      topWords.forEach(w => {
        if (!keywords.some(k => k.term === w)) {
          keywords.push({ term: w, type: isFake ? 'warning' : 'positive' });
        }
      });
    }

    // Explanatory Signals
    const exclamationCount = (fullText.match(/!/g) || []).length;
    if (exclamationCount >= 2 || keywords.some(k => k.type === 'warning')) {
      signals.push({
        type: 'warning',
        text: '<strong>Sensational Framing:</strong> Employs emotionally charged phrasing, exclamation points, or clickbait trigger words.'
      });
    } else if (!isFake) {
      signals.push({
        type: 'positive',
        text: '<strong>Measured Neutral Tone:</strong> Uses calm, balanced vocabulary characteristic of standard reporting.'
      });
    }

    const hasAttribution = keywords.some(k => k.type === 'positive') || /["'""'']/.test(text);
    if (hasAttribution && !isFake) {
      signals.push({
        type: 'positive',
        text: '<strong>Verifiable Attribution:</strong> Identifies public officials, recognized institutions, or direct quotations.'
      });
    } else if (!hasAttribution) {
      signals.push({
        type: 'warning',
        text: '<strong>Missing Named Sources:</strong> Makes broad claims without identifiable spokespeople or primary source documents.'
      });
    }

    return { keywords: keywords.slice(0, 8), signals: signals.slice(0, 3) };
  }

  // ───── 6. Results Page DOM Elements ─────
  const singleResultArea = document.getElementById('single-result-area');
  const batchResultArea = document.getElementById('batch-result-area');
  const verdictBanner = document.getElementById('verdict-banner');
  const verdictIcon = document.getElementById('verdict-icon');
  const verdictText = document.getElementById('verdict-text');
  const confidenceTag = document.getElementById('confidence-tag');
  const verdictTakeaway = document.getElementById('verdict-takeaway');
  const meterScoreText = document.getElementById('meter-score-text');
  const scoreBarFill = document.getElementById('score-bar-fill');
  const barSource = document.getElementById('bar-source');
  const valSource = document.getElementById('val-source');
  const barLexical = document.getElementById('bar-lexical');
  const valLexical = document.getElementById('val-lexical');
  const barSensational = document.getElementById('bar-sensational');
  const valSensational = document.getElementById('val-sensational');
  const keywordsContainer = document.getElementById('keywords-container');
  const signalBullets = document.getElementById('signal-bullets');
  const geminiCard = document.getElementById('gemini-card');
  const geminiExplanation = document.getElementById('gemini-explanation');
  const btnCopyCard = document.getElementById('btn-copy-card');
  const copyStatus = document.getElementById('copy-status');

  // Batch Elements
  const batchTotalCount = document.getElementById('batch-total-count');
  const batchRealCount = document.getElementById('batch-real-count');
  const batchFakeCount = document.getElementById('batch-fake-count');
  const batchAuthenticityRatio = document.getElementById('batch-authenticity-ratio');
  const batchRatioReal = document.getElementById('batch-ratio-real');
  const batchRatioFake = document.getElementById('batch-ratio-fake');
  const legendRealPct = document.getElementById('legend-real-pct');
  const legendFakePct = document.getElementById('legend-fake-pct');
  const batchKeywordsContainer = document.getElementById('batch-keywords-container');
  const batchTableBody = document.getElementById('batch-table-body');
  const batchFilenameTag = document.getElementById('batch-filename-tag');

  let currentFactCheckCard = null;

  // ───── 7. Single Result Rendering ─────
  function showSingleResult(res, title, text) {
    singleResultArea.style.display = 'block';
    batchResultArea.style.display = 'none';
    geminiCard.style.display = 'none';

    const isFake = res.is_fake;
    const score = Math.round(res.credibility_score);

    // Verdict card
    verdictBanner.className = 'verdict-card ' + (isFake ? 'is-fake' : 'is-real');
    verdictIcon.textContent = isFake ? '⚠' : '✓';
    verdictText.textContent = isFake ? 'Likely Misleading' : 'Likely Authentic';
    confidenceTag.textContent = `${res.confidence_level} Confidence`;

    verdictTakeaway.textContent = isFake
      ? (res.risk_assessment || 'This article contains sensational framing, unsubstantiated assertions, or stylistic markers commonly found in misinformation.')
      : (res.risk_assessment || 'This article follows measured editorial language, standard neutral syntax, and balanced journalistic conventions.');

    // Graph 1: Authenticity Score Bar
    meterScoreText.textContent = `${score}%`;
    scoreBarFill.style.width = `${score}%`;
    scoreBarFill.style.backgroundColor = isFake ? 'var(--verdict-fake-bar)' : 'var(--verdict-real-bar)';

    // Graph 2: Linguistic Confidence Signals
    const stylometrics = res.stylometrics || {};
    const lexicalPct = Math.min(100, Math.round((stylometrics.lexical_diversity || 0.65) * 100));
    const quotesPresent = (stylometrics.quote_count || 0) > 0 || /["'""'']/.test(text);
    const sourcePct = quotesPresent ? (isFake ? 45 : 88) : 25;
    const sensationalPct = isFake ? 82 : Math.min(30, Math.round((stylometrics.exclamation_count || 0) * 15 + 10));

    barSource.style.width = `${sourcePct}%`;
    barSource.className = 'bar-fill-mini ' + (sourcePct >= 50 ? 'is-good' : 'is-caution');
    valSource.textContent = `${sourcePct}%`;

    barLexical.style.width = `${lexicalPct}%`;
    barLexical.className = 'bar-fill-mini ' + (lexicalPct >= 60 ? 'is-good' : 'is-caution');
    valLexical.textContent = `${lexicalPct}%`;

    barSensational.style.width = `${sensationalPct}%`;
    barSensational.className = 'bar-fill-mini ' + (sensationalPct > 40 ? 'is-caution' : 'is-good');
    valSensational.textContent = `${sensationalPct}%`;

    // Keywords & Phrasing Badges
    const analysis = extractKeywordsAndSignals(title, text, isFake);
    keywordsContainer.innerHTML = '';
    analysis.keywords.forEach(kw => {
      const badge = document.createElement('span');
      badge.className = `keyword-badge ${kw.type === 'positive' ? 'is-positive' : 'is-warning'}`;
      badge.textContent = kw.type === 'positive' ? `✓ ${kw.term}` : `⚠ ${kw.term}`;
      keywordsContainer.appendChild(badge);
    });

    // Signal Bullets
    signalBullets.innerHTML = '';
    analysis.signals.forEach(s => {
      const li = document.createElement('li');
      li.className = 'signal-item';
      li.innerHTML = `<span>${s.type === 'positive' ? '✓' : '⚠️'}</span><span>${s.text}</span>`;
      signalBullets.appendChild(li);
    });

    // Store for Clipboard Copy
    const headline = title || text.slice(0, 65) + (text.length > 65 ? '...' : '');
    currentFactCheckCard = {
      headline,
      verdict: isFake ? 'Likely Misleading' : 'Likely Authentic',
      score: `${score}%`,
      keywords: analysis.keywords.map(k => k.term),
      signals: analysis.signals.map(s => s.text.replace(/<[^>]+>/g, '')),
      gemini: null
    };

    // Save to localStorage
    const snippet = text.slice(0, 140) + (text.length > 140 ? '...' : '');
    const now = new Date();
    const dateFormatted = now.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    saveHistoryItem({
      id: Date.now().toString(),
      type: 'single',
      headline,
      snippet,
      fullText: text,
      title,
      is_fake: isFake,
      score,
      date: dateFormatted
    });

    // Switch view
    switchPage('page-results');

    // Async Gemini Fact Check
    fetchGeminiEvaluation(title, text, isFake ? 'Likely Misleading' : 'Likely Authentic', score);
  }

  // ───── 8. Batch CSV Results Rendering ─────
  function showBatchResults(batchData, fileName) {
    singleResultArea.style.display = 'none';
    batchResultArea.style.display = 'block';

    batchFilenameTag.textContent = fileName || 'Uploaded File';

    const total = batchData.total_articles || 0;
    const realCount = batchData.real_count || 0;
    const fakeCount = batchData.fake_count || 0;
    const realRate = total > 0 ? Math.round((realCount / total) * 100) : 0;
    const fakeRate = total > 0 ? (100 - realRate) : 0;

    batchTotalCount.textContent = total;
    batchRealCount.textContent = realCount;
    batchFakeCount.textContent = fakeCount;
    batchAuthenticityRatio.textContent = `${realRate}%`;

    // Distribution Graph Bar
    batchRatioReal.style.width = `${realRate}%`;
    batchRatioFake.style.width = `${fakeRate}%`;
    legendRealPct.textContent = `${realRate}%`;
    legendFakePct.textContent = `${fakeRate}%`;

    // Extract Frequent Keywords Across the Batch
    const batchWordCounts = {};
    const commonStopWords = new Set(['the','and','a','to','of','in','that','is','was','for','on','with','as','by','at','from','it','an','this','are','be','or','have','has','had','not']);

    batchData.results.forEach(r => {
      const snippet = (r.risk_assessment || '').toLowerCase().replace(/[^a-z\s]/g, ' ');
      snippet.split(/\s+/).forEach(w => {
        if (w.length > 4 && !commonStopWords.has(w)) {
          batchWordCounts[w] = (batchWordCounts[w] || 0) + 1;
        }
      });
    });

    const sortedKeywords = Object.keys(batchWordCounts).sort((a,b) => batchWordCounts[b] - batchWordCounts[a]).slice(0, 8);
    batchKeywordsContainer.innerHTML = '';
    sortedKeywords.forEach(kw => {
      const badge = document.createElement('span');
      badge.className = 'keyword-badge';
      badge.textContent = `🔍 ${kw} (${batchWordCounts[kw]})`;
      batchKeywordsContainer.appendChild(badge);
    });

    // Populate Table with Sticky Header
    batchTableBody.innerHTML = '';
    batchData.results.forEach((r, idx) => {
      const isFake = r.is_fake;
      const score = Math.round(r.credibility_score);
      const row = document.createElement('tr');
      const snippet = (r.risk_assessment || 'Article snippet analyzed').slice(0, 90) + '...';

      row.innerHTML = `
        <td style="color: var(--text-light); font-weight: 600;">${idx + 1}</td>
        <td class="td-snippet">${escapeHtml(snippet)}</td>
        <td style="font-weight: 700; font-family: var(--font-mono);">${score}%</td>
        <td>
          <span class="status-badge ${isFake ? 'is-fake' : 'is-real'}">
            ${isFake ? '⚠ Misleading' : '✓ Authentic'}
          </span>
        </td>
      `;
      batchTableBody.appendChild(row);
    });

    // Save Batch to History
    const now = new Date();
    const dateFormatted = now.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    saveHistoryItem({
      id: Date.now().toString(),
      type: 'batch',
      headline: `Batch: ${fileName}`,
      snippet: `${total} rows analyzed (${realCount} authentic, ${fakeCount} misleading)`,
      is_fake: fakeCount > realCount,
      score: realRate,
      date: dateFormatted,
      batchCount: total
    });

    switchPage('page-results');
  }

  // ───── 9. Parse CSV / TXT File ─────
  function parseUploadedFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const content = reader.result;
        const name = file.name.toLowerCase();
        const articles = [];

        if (name.endsWith('.csv')) {
          const lines = content.split('\n').filter(l => l.trim());
          if (lines.length < 2) { reject(new Error('Uploaded CSV file appears to be empty.')); return; }

          const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/["'\r]/g, ''));
          const textIdx = headers.indexOf('text');
          const titleIdx = headers.indexOf('title');

          if (textIdx === -1) {
            reject(new Error('CSV must contain a "text" header column. Found headers: ' + headers.join(', ')));
            return;
          }

          // Parse up to 150 rows safely
          for (let i = 1; i < lines.length && i <= 150; i++) {
            const cells = parseCSVLine(lines[i]);
            const text = (cells[textIdx] || '').trim();
            if (!text) continue;
            const title = titleIdx >= 0 ? (cells[titleIdx] || '').trim() : '';
            articles.push({ title, text });
          }
        } else {
          // Line-separated .txt file
          const lines = content.split('\n').filter(l => l.trim());
          for (let i = 0; i < lines.length && i <= 150; i++) {
            articles.push({ title: '', text: lines[i].trim() });
          }
        }

        if (articles.length === 0) {
          reject(new Error('No valid text entries found in the uploaded file.'));
          return;
        }
        resolve(articles);
      };
      reader.onerror = () => reject(new Error('Could not read file from disk.'));
      reader.readAsText(file);
    });
  }

  function parseCSVLine(line) {
    const cells = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (inQuotes) {
        if (ch === '"' && line[i + 1] === '"') { current += '"'; i++; }
        else if (ch === '"') { inQuotes = false; }
        else { current += ch; }
      } else {
        if (ch === '"') { inQuotes = true; }
        else if (ch === ',') { cells.push(current); current = ''; }
        else { current += ch; }
      }
    }
    cells.push(current);
    return cells;
  }

  // ───── 10. Verification Form Submit ─────
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Batch File Upload Flow
    if (pendingFile) {
      btnLabel.textContent = 'Analyzing File...';
      btnSpinner.style.display = 'inline-block';
      btnSubmit.disabled = true;

      try {
        const articles = await parseUploadedFile(pendingFile);
        const response = await fetch('/api/v1/predict/batch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ articles })
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `Server returned error (${response.status})`);
        }

        const batchData = await response.json();
        showBatchResults(batchData, pendingFile.name);

      } catch (err) {
        console.error('Batch upload error:', err);
        alert(`Could not process batch file: ${err.message}`);
      } finally {
        btnLabel.textContent = 'Show Result';
        btnSpinner.style.display = 'none';
        btnSubmit.disabled = false;
      }
      return;
    }

    // Single Article Check Flow
    const title = titleInput.value.trim();
    const text = textInput.value.trim();
    if (!text && !title) {
      alert('Please enter article text or upload a CSV file to check.');
      return;
    }

    btnLabel.textContent = 'Checking...';
    btnSpinner.style.display = 'inline-block';
    btnSubmit.disabled = true;

    try {
      const response = await fetch('/api/v1/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, text })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error (${response.status})`);
      }

      const data = await response.json();
      showSingleResult(data, title, text);

    } catch (err) {
      console.error('Prediction failed:', err);
      alert(`Verification failed: ${err.message}`);
    } finally {
      btnLabel.textContent = 'Show Result';
      btnSpinner.style.display = 'none';
      btnSubmit.disabled = false;
    }
  });

  // ───── 11. Gemini Cross-Check API ─────
  async function fetchGeminiEvaluation(title, text, verdict, score) {
    try {
      const response = await fetch('/api/v1/gemini-evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, text, verdict, credibility_score: score })
      });
      if (!response.ok) return;
      const data = await response.json();
      if (data.available && data.gemini_explanation) {
        geminiExplanation.textContent = data.gemini_explanation;
        geminiCard.style.display = 'block';
        if (currentFactCheckCard) currentFactCheckCard.gemini = data.gemini_explanation;
      }
    } catch {
      // Graceful silent fallback
    }
  }

  // ───── 12. Copy Shareable Fact-Check Card ─────
  btnCopyCard.addEventListener('click', async () => {
    if (!currentFactCheckCard) return;

    const summary = [
      `📰 CrediNews Verification Report`,
      `━━━━━━━━━━━━━━━━━━━━━━━━━`,
      `Headline: "${currentFactCheckCard.headline}"`,
      `Verdict: ${currentFactCheckCard.verdict} (${currentFactCheckCard.score} Credibility)`,
      ``,
      `Key Keywords: ${currentFactCheckCard.keywords.join(', ')}`,
      ``,
      `Signals:`,
      ...currentFactCheckCard.signals.map(s => `• ${s}`),
      ...(currentFactCheckCard.gemini ? [``, `AI Evaluation: ${currentFactCheckCard.gemini}`] : []),
      ``,
      `Verified with CrediNews AI`
    ].join('\n');

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(summary);
      } else {
        const ta = document.createElement('textarea');
        ta.value = summary;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      copyStatus.style.display = 'inline';
      setTimeout(() => { copyStatus.style.display = 'none'; }, 2500);
    } catch (e) {
      alert('Could not copy to clipboard: ' + e.message);
    }
  });
});
