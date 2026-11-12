/**
 * PDF FIF — Minimalist & Modern Frontend Controller
 */

const state = {
  sessionId: null,
  filename: null,
  totalPages: 0,
  detectedAno: null,
  detectedMes: null,
  suggestedPrefix: null,
  groups: [], // Array de arquivos a serem gerados: { id, person_name, matricula, cargo, source, page_numbers, selected }
  rawPages: [], // Páginas originais extraídas
  systemStatus: null,
};

// Element references
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const heroSection = document.getElementById('heroSection');
const loadingSection = document.getElementById('loadingSection');
const reviewSection = document.getElementById('reviewSection');
const resultsSection = document.getElementById('resultsSection');
const pagesGrid = document.getElementById('pagesGrid');
const inputPrefixo = document.getElementById('inputPrefixo');
const nameFormatSelect = document.getElementById('nameFormatSelect');
const filenamePreview = document.getElementById('filenamePreview');
const splitBtn = document.getElementById('splitBtn');
const resetBtn = document.getElementById('resetBtn');
const summaryCount = document.getElementById('summaryCount');
const bottomSummaryText = document.getElementById('bottomSummaryText');
const selectionToolbar = document.getElementById('selectionToolbar');
const selectionCount = document.getElementById('selectionCount');
const btnMergeSelected = document.getElementById('btnMergeSelected');
const btnClearSelection = document.getElementById('btnClearSelection');
const settingsModal = document.getElementById('settingsModal');
const imageViewerModal = document.getElementById('imageViewerModal');
const modalImg = document.getElementById('modalImg');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  const now = new Date();
  const defYear = now.getFullYear();
  const defMonth = String(now.getMonth() + 1).padStart(2, '0');
  state.detectedAno = String(defYear);
  state.detectedMes = defMonth;
  if (!inputPrefixo.value) {
    inputPrefixo.value = `${defYear}_${defMonth}_`;
  }
  loadSystemStatus();
  loadAvailableUploads();
  setupEventListeners();
  updateAllFilenamePreviews();
});

// Fetch system status
async function loadSystemStatus() {
  const dot = document.getElementById('engineDot');
  const text = document.getElementById('engineStatusText');
  if (dot && text) {
    dot.className = 'engine-dot';
    text.textContent = 'OCR Local Ativo';
  }
}

// Check uploads folder
async function loadAvailableUploads() {
  try {
    const res = await fetch('/api/available-uploads');
    const data = await res.json();
    const section = document.getElementById('availableUploadsSection');
    const list = document.getElementById('availableUploadsList');

    if (data.files && data.files.length > 0) {
      list.innerHTML = '';
      data.files.forEach(filename => {
        const btn = document.createElement('button');
        btn.className = 'btn-quick';
        btn.innerHTML = `📄 ${escapeHtml(filename)}`;
        btn.addEventListener('click', () => handleLoadUploadFile(filename));
        list.appendChild(btn);
      });
      section.style.display = 'flex';
    } else {
      section.style.display = 'none';
    }
  } catch (err) {
    console.warn('Uploads list error:', err);
  }
}

// Setup Event Listeners
function setupEventListeners() {
  ['dragenter', 'dragover'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
      handleFileUpload(files[0]);
    } else {
      alert('Selecione um arquivo PDF.');
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });

  inputPrefixo.addEventListener('input', updateAllFilenamePreviews);
  nameFormatSelect.addEventListener('change', updateAllFilenamePreviews);

  splitBtn.addEventListener('click', handleSplitPdf);
  resetBtn.addEventListener('click', resetWorkspace);

  // Grouping selection actions
  btnMergeSelected.addEventListener('click', mergeSelectedGroups);
  btnClearSelection.addEventListener('click', clearGroupSelection);

  // Settings (se o botão existir)
  const openBtn = document.getElementById('openSettingsBtn');
  if (openBtn) {
    openBtn.addEventListener('click', () => {
      const modal = document.getElementById('settingsModal');
      if (modal) modal.style.display = 'flex';
    });
  }
  const closeBtn = document.getElementById('closeSettingsBtn');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      const modal = document.getElementById('settingsModal');
      if (modal) modal.style.display = 'none';
    });
  }
  const cancelBtn = document.getElementById('cancelSettingsBtn');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      const modal = document.getElementById('settingsModal');
      if (modal) modal.style.display = 'none';
    });
  }
  const settingsForm = document.getElementById('settingsForm');
  if (settingsForm) {
    settingsForm.addEventListener('submit', handleSaveSettings);
  }

  // Modal zoom
  imageViewerModal.addEventListener('click', () => {
    imageViewerModal.style.display = 'none';
  });
}

// Handle Upload / Analysis
async function handleFileUpload(file) {
  heroSection.style.display = 'none';
  loadingSection.style.display = 'block';
  document.getElementById('loadingTitle').textContent = `Carregando ${file.name}...`;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const uploadRes = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    });
    if (!uploadRes.ok) throw new Error('Falha no upload');

    const uploadData = await uploadRes.json();
    initSession(uploadData.session_id, uploadData.filename, uploadData.total_pages, uploadData);
  } catch (err) {
    alert(`Erro: ${err.message}`);
    resetWorkspace();
  }
}

async function handleLoadUploadFile(filename) {
  heroSection.style.display = 'none';
  loadingSection.style.display = 'block';
  document.getElementById('loadingTitle').textContent = `Carregando ${filename}...`;

  try {
    const loadRes = await fetch(`/api/load-upload/${encodeURIComponent(filename)}`, {
      method: 'POST',
    });
    if (!loadRes.ok) throw new Error('Falha ao abrir arquivo');

    const uploadData = await loadRes.json();
    initSession(uploadData.session_id, uploadData.filename, uploadData.total_pages, uploadData);
  } catch (err) {
    alert(`Erro: ${err.message}`);
    resetWorkspace();
  }
}

async function initSession(sessionId, filename, totalPages, initialData = {}) {
  state.sessionId = sessionId;
  state.filename = filename;
  state.totalPages = totalPages;

  if (initialData && initialData.suggested_prefix) {
    state.detectedAno = initialData.detected_ano;
    state.detectedMes = initialData.detected_mes;
    state.suggestedPrefix = initialData.suggested_prefix;
    inputPrefixo.value = initialData.suggested_prefix;
  }

  document.getElementById('loadingTitle').textContent = `Identificando servidores nas ${totalPages} páginas...`;
  try {
    const analyzeRes = await fetch(`/api/analyze/${sessionId}?use_gemini=true`, {
      method: 'POST',
    });
    if (!analyzeRes.ok) throw new Error('Falha ao analisar documento');

    const analyzeData = await analyzeRes.json();
    state.rawPages = analyzeData.pages;

    if (analyzeData.suggested_prefix) {
      state.detectedAno = analyzeData.detected_ano;
      state.detectedMes = analyzeData.detected_mes;
      state.suggestedPrefix = analyzeData.suggested_prefix;
      inputPrefixo.value = analyzeData.suggested_prefix;
    }

    // Inicializa: por padrão 1 folha por arquivo
    state.groups = state.rawPages.map((p, idx) => ({
      id: `group_${idx}_${p.page_num}`,
      person_name: p.nome,
      matricula: p.matricula,
      cargo: p.cargo,
      source: p.source,
      page_numbers: [p.page_num],
      selected: false,
    }));

    loadingSection.style.display = 'none';
    renderReview();
  } catch (err) {
    alert(`Erro na análise: ${err.message}`);
    resetWorkspace();
  }
}

// Render Cards Grid
function renderReview() {
  reviewSection.style.display = 'block';
  document.getElementById('docInfoTitle').textContent = state.filename;
  document.getElementById('docInfoSub').textContent = `${state.totalPages} páginas`;

  updateCounts();
  pagesGrid.innerHTML = '';

  state.groups.forEach((group, index) => {
    const card = document.createElement('div');
    card.className = `file-card ${group.selected ? 'selected' : ''}`;

    const isMultiPage = group.page_numbers.length > 1;
    const pageLabel = isMultiPage
      ? `Páginas ${group.page_numbers.join(', ')} (${group.page_numbers.length} folhas)`
      : `Página ${group.page_numbers[0]}`;

    // Monta miniaturas das páginas deste arquivo
    const thumbsHtml = group.page_numbers.map(pNum => `
      <img class="card-thumb-img" src="/api/thumbnail/${state.sessionId}/${pNum}" alt="Pág ${pNum}" loading="lazy" data-zoom="/api/thumbnail/${state.sessionId}/${pNum}">
    `).join('');

    card.innerHTML = `
      <div class="card-header">
        <label class="card-select-wrap">
          <input type="checkbox" class="custom-checkbox" data-index="${index}" ${group.selected ? 'checked' : ''}>
          <span class="page-tag ${isMultiPage ? 'multi' : ''}">${pageLabel}</span>
        </label>
        <span style="font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase;">
          ${group.source === 'gemini' ? 'Gemini AI' : 'OCR Local'}
        </span>
      </div>

      <div class="card-thumbs" title="Clique para ampliar">
        ${thumbsHtml}
        <span class="thumb-zoom-badge" style="display: inline-flex; align-items: center; gap: 4px;">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          Ampliar
        </span>
      </div>

      <div class="card-body">
        <label style="font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; font-weight: 600;">
          Nome do Servidor
        </label>
        <input type="text" class="card-input-name" value="${escapeHtml(group.person_name)}" data-index="${index}">

        <div class="card-meta-chips">
          ${group.matricula ? `<span class="meta-chip">Mat: <b>${escapeHtml(group.matricula)}</b></span>` : ''}
          ${group.cargo ? `<span class="meta-chip" title="${escapeHtml(group.cargo)}">${escapeHtml(group.cargo.substring(0, 22))}...</span>` : ''}
        </div>

        <!-- Preview individual do arquivo deste card -->
        <div class="card-file-preview">
          <div class="card-file-preview-header">
            <span class="file-preview-label" style="display: inline-flex; align-items: center; gap: 4px;">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
              PDF Gerado
            </span>
          </div>
          <div class="card-file-preview-name" id="card-filename-${index}">
            ...
          </div>
        </div>
      </div>

      <div class="card-footer">
        <div>
          ${index < state.groups.length - 1 ? `
            <button class="btn-card-action" data-action="merge-next" data-index="${index}" title="Juntar esta folha com a próxima em 1 só arquivo" style="display: inline-flex; align-items: center; gap: 4px;">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
              Juntar com próxima
            </button>
          ` : '<span style="font-size: 0.72rem; color: var(--text-dim);">Última folha</span>'}
        </div>

        <div>
          ${isMultiPage ? `
            <button class="btn-card-action danger" data-action="ungroup" data-index="${index}" title="Separar as páginas deste arquivo">
              ✂️ Separar páginas
            </button>
          ` : ''}
        </div>
      </div>
    `;

    // Eventos do card
    const chk = card.querySelector('.custom-checkbox');
    chk.addEventListener('change', (e) => {
      group.selected = e.target.checked;
      card.classList.toggle('selected', group.selected);
      updateSelectionToolbar();
    });

    const thumbsContainer = card.querySelector('.card-thumbs');
    thumbsContainer.addEventListener('click', () => {
      modalImg.src = `/api/thumbnail/${state.sessionId}/${group.page_numbers[0]}`;
      imageViewerModal.style.display = 'flex';
    });

    const nameInput = card.querySelector('.card-input-name');
    nameInput.addEventListener('input', (e) => {
      group.person_name = e.target.value.trim();
      updateAllFilenamePreviews();
    });

    const btnMergeNext = card.querySelector('[data-action="merge-next"]');
    if (btnMergeNext) {
      btnMergeNext.addEventListener('click', () => mergeWithNext(index));
    }

    const btnUngroup = card.querySelector('[data-action="ungroup"]');
    if (btnUngroup) {
      btnUngroup.addEventListener('click', () => ungroup(index));
    }

    pagesGrid.appendChild(card);
  });

  updateAllFilenamePreviews();
  updateSelectionToolbar();
}

// Merge card with next card
function mergeWithNext(index) {
  if (index >= state.groups.length - 1) return;
  const current = state.groups[index];
  const next = state.groups[index + 1];

  current.page_numbers = [...current.page_numbers, ...next.page_numbers].sort((a, b) => a - b);
  // Mantém matrícula/cargo se o atual não tiver e o próximo tiver
  if (!current.matricula && next.matricula) current.matricula = next.matricula;
  if (!current.cargo && next.cargo) current.cargo = next.cargo;

  state.groups.splice(index + 1, 1);
  renderReview();
}

// Ungroup multi-page card back into individual pages
function ungroup(index) {
  const current = state.groups[index];
  if (current.page_numbers.length <= 1) return;

  const newCards = current.page_numbers.map(pNum => {
    const raw = state.rawPages.find(rp => rp.page_num === pNum) || {};
    return {
      id: `group_${Date.now()}_${pNum}`,
      person_name: raw.nome || current.person_name,
      matricula: raw.matricula || current.matricula,
      cargo: raw.cargo || current.cargo,
      source: raw.source || current.source,
      page_numbers: [pNum],
      selected: false,
    };
  });

  state.groups.splice(index, 1, ...newCards);
  renderReview();
}

// Multi-select merge
function updateSelectionToolbar() {
  const selected = state.groups.filter(g => g.selected);
  if (selected.length >= 2) {
    selectionCount.textContent = `${selected.length} selecionadas`;
    selectionToolbar.style.display = 'flex';
  } else {
    selectionToolbar.style.display = 'none';
  }
}

function mergeSelectedGroups() {
  const selectedIndices = [];
  state.groups.forEach((g, idx) => {
    if (g.selected) selectedIndices.push(idx);
  });

  if (selectedIndices.length < 2) return;

  const firstIdx = selectedIndices[0];
  const target = state.groups[firstIdx];

  let combinedPages = [...target.page_numbers];
  for (let i = 1; i < selectedIndices.length; i++) {
    const idx = selectedIndices[i];
    combinedPages = [...combinedPages, ...state.groups[idx].page_numbers];
  }
  target.page_numbers = Array.from(new Set(combinedPages)).sort((a, b) => a - b);
  target.selected = false;

  // Remove os outros grupos mesclados (em ordem reversa)
  for (let i = selectedIndices.length - 1; i >= 1; i--) {
    state.groups.splice(selectedIndices[i], 1);
  }

  renderReview();
}

function clearGroupSelection() {
  state.groups.forEach(g => g.selected = false);
  renderReview();
}

function updateCounts() {
  const count = state.groups.length;
  summaryCount.textContent = `${count} ${count === 1 ? 'arquivo' : 'arquivos'}`;
  bottomSummaryText.textContent = `${count} ${count === 1 ? 'arquivo pronto' : 'arquivos prontos'} para gerar`;
}

// Filename formatting and live preview for each card
function formatFilenameForPerson(rawName, matricula, prefix, format) {
  if (!rawName) rawName = 'servidor';

  const cleanName = rawName
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\w\s-]/g, '')
    .trim()
    .toLowerCase()
    .replace(/[\s_]+/g, '_');

  const rawParts = cleanName.split('_').filter(Boolean);
  let primeiroNome = 'nome';
  let sobrenome = 'sobrenome';

  if (rawParts.length > 0) {
    primeiroNome = rawParts[0];
    sobrenome = rawParts[rawParts.length - 1];

    // Se o último sobrenome for preposição/partícula de ligação (ex: de, da, do, das, dos, e), tenta o anterior
    const preposicoes = new Set(['da', 'de', 'do', 'das', 'dos', 'e']);
    if (rawParts.length > 2 && preposicoes.has(sobrenome)) {
      sobrenome = rawParts[rawParts.length - 2];
    }
  }

  const cleanMatricula = (matricula || '')
    .toString()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\w\s-]/g, '')
    .trim()
    .replace(/[\s_]+/g, '_');

  let namePart = format
    .replace(/{nome}/g, cleanName)
    .replace(/{primeiro_nome}/g, primeiroNome)
    .replace(/{sobrenome}/g, sobrenome)
    .replace(/{matricula}/g, cleanMatricula);

  let finalName = `${prefix || ''}${namePart}`;
  finalName = finalName
    .replace(/_{2,}/g, '_')
    .replace(/-_+/g, '-')
    .replace(/[<>:"/\\|?*]/g, '');

  if (!finalName.toLowerCase().endsWith('.pdf')) {
    finalName += '.pdf';
  }
  return finalName;
}

function updateAllFilenamePreviews() {
  const prefix = (inputPrefixo.value || '').trim();
  const format = nameFormatSelect.value || '{primeiro_nome}_{sobrenome}';
  const used = {};

  if (state.groups && state.groups.length > 0) {
    state.groups.forEach((group, idx) => {
      let baseFilename = formatFilenameForPerson(group.person_name, group.matricula, prefix, format);
      let finalFilename = baseFilename;

      if (used[baseFilename]) {
        used[baseFilename]++;
        const stem = baseFilename.toLowerCase().endsWith('.pdf') ? baseFilename.slice(0, -4) : baseFilename;
        finalFilename = `${stem}_${used[baseFilename]}.pdf`;
      } else {
        used[baseFilename] = 1;
      }

      group.computedFilename = finalFilename;

      const el = document.getElementById(`card-filename-${idx}`);
      if (el) {
        el.textContent = finalFilename;
      }
    });

    if (filenamePreview) {
      filenamePreview.textContent = state.groups[0].computedFilename || formatFilenameForPerson(state.groups[0].person_name, state.groups[0].matricula, prefix, format);
    }
  } else {
    const demo = formatFilenameForPerson('carlos_bruno_freitas_sardinha', '1188477', prefix, format);
    if (filenamePreview) {
      filenamePreview.textContent = demo;
    }
  }
}

// Split & Download
async function handleSplitPdf() {
  splitBtn.disabled = true;
  splitBtn.innerHTML = '⏳ Gerando PDFs...';

  const prefix = inputPrefixo.value.trim();
  const format = nameFormatSelect.value || '{primeiro_nome}_{sobrenome}';
  const template = `{prefixo}${format}.pdf`;

  const payload = {
    template: template,
    prefixo: prefix,
    ano: state.detectedAno,
    mes: state.detectedMes,
    groups: state.groups.map(g => ({
      person_name: g.person_name,
      page_numbers: g.page_numbers,
      matricula: g.matricula,
      cargo: g.cargo,
    })),
  };

  try {
    const res = await fetch(`/api/split/${state.sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erro ao gerar');
    }

    const data = await res.json();
    renderResults(data);
  } catch (err) {
    alert(`Erro ao separar: ${err.message}`);
  } finally {
    splitBtn.disabled = false;
    splitBtn.innerHTML = '✨ Separar e Baixar ZIP';
  }
}

function renderResults(data) {
  resultsSection.style.display = 'block';
  document.getElementById('downloadZipBtn').href = data.zip_url;
  document.getElementById('resultsSub').textContent = `${data.total_files} arquivos gerados em: ${data.output_directory}`;

  const resultsList = document.getElementById('resultsList');
  resultsList.innerHTML = '';

  data.files.forEach(f => {
    const row = document.createElement('div');
    row.className = 'file-row';
    row.innerHTML = `
      <div>
        <div class="file-row-name">📄 ${escapeHtml(f.filename)}</div>
        <div class="file-row-meta">${escapeHtml(f.person_name)} • Páginas: [${f.page_numbers.join(', ')}]</div>
      </div>
      <a class="btn-quick" href="${f.download_url}" download="${f.filename}" style="text-decoration: none;">
        ⬇ Baixar
      </a>
    `;
    resultsList.appendChild(row);
  });

  resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function resetWorkspace() {
  state.sessionId = null;
  state.filename = null;
  state.totalPages = 0;
  state.groups = [];
  state.rawPages = [];
  fileInput.value = '';

  const now = new Date();
  const defYear = now.getFullYear();
  const defMonth = String(now.getMonth() + 1).padStart(2, '0');
  state.detectedAno = String(defYear);
  state.detectedMes = defMonth;
  inputPrefixo.value = `${defYear}_${defMonth}_`;

  heroSection.style.display = 'block';
  loadingSection.style.display = 'none';
  reviewSection.style.display = 'none';
  resultsSection.style.display = 'none';

  loadAvailableUploads();
  updateAllFilenamePreviews();
}

async function handleSaveSettings(e) {
  e.preventDefault();
  const apiKey = document.getElementById('geminiApiKeyInput').value.trim();
  const model = document.getElementById('geminiModelSelect').value;

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        gemini_api_key: apiKey || null,
        gemini_model: model,
      }),
    });
    if (!res.ok) throw new Error('Falha ao salvar');

    alert('Configurações salvas!');
    settingsModal.style.display = 'none';
    loadSystemStatus();
  } catch (err) {
    alert(`Erro: ${err.message}`);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
