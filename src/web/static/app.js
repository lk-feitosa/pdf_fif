/**
 * PDF FIF — Minimalist & Modern Frontend Controller
 */

const state = {
  sessionId: null,
  filename: null,
  totalPages: 0,
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
  loadSystemStatus();
  loadAvailableUploads();
  setupEventListeners();
  updateFilenamePreview();
});

// Fetch system status
async function loadSystemStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    state.systemStatus = data;

    const dot = document.getElementById('engineDot');
    const text = document.getElementById('engineStatusText');

    if (data.gemini && data.gemini.available) {
      dot.className = 'engine-dot';
      text.textContent = `Gemini AI (${data.gemini.model})`;
    } else {
      dot.className = 'engine-dot offline';
      text.textContent = 'OCR Local (Offline)';
    }

    if (data.gemini && data.gemini.masked_key) {
      document.getElementById('geminiApiKeyInput').placeholder = data.gemini.masked_key;
    }
  } catch (err) {
    console.warn('Status error:', err);
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

  inputPrefixo.addEventListener('input', updateFilenamePreview);
  nameFormatSelect.addEventListener('change', updateFilenamePreview);

  splitBtn.addEventListener('click', handleSplitPdf);
  resetBtn.addEventListener('click', resetWorkspace);

  // Grouping selection actions
  btnMergeSelected.addEventListener('click', mergeSelectedGroups);
  btnClearSelection.addEventListener('click', clearGroupSelection);

  // Settings
  document.getElementById('openSettingsBtn').addEventListener('click', () => {
    settingsModal.style.display = 'flex';
  });
  document.getElementById('closeSettingsBtn').addEventListener('click', () => {
    settingsModal.style.display = 'none';
  });
  document.getElementById('cancelSettingsBtn').addEventListener('click', () => {
    settingsModal.style.display = 'none';
  });
  document.getElementById('settingsForm').addEventListener('submit', handleSaveSettings);

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
    initSession(uploadData.session_id, uploadData.filename, uploadData.total_pages);
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
    initSession(uploadData.session_id, uploadData.filename, uploadData.total_pages);
  } catch (err) {
    alert(`Erro: ${err.message}`);
    resetWorkspace();
  }
}

async function initSession(sessionId, filename, totalPages) {
  state.sessionId = sessionId;
  state.filename = filename;
  state.totalPages = totalPages;

  document.getElementById('loadingTitle').textContent = `Identificando servidores nas ${totalPages} páginas...`;
  try {
    const analyzeRes = await fetch(`/api/analyze/${sessionId}?use_gemini=true`, {
      method: 'POST',
    });
    if (!analyzeRes.ok) throw new Error('Falha ao analisar documento');

    const analyzeData = await analyzeRes.json();
    state.rawPages = analyzeData.pages;

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
          ${group.source === 'gemini' ? '✨ Gemini AI' : 'OCR Local'}
        </span>
      </div>

      <div class="card-thumbs" title="Clique para ampliar">
        ${thumbsHtml}
        <span class="thumb-zoom-badge">🔍 Ampliar</span>
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
      </div>

      <div class="card-footer">
        <div>
          ${index < state.groups.length - 1 ? `
            <button class="btn-card-action" data-action="merge-next" data-index="${index}" title="Juntar esta folha com a próxima em 1 só arquivo">
              🔗 Juntar com próxima
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
      if (index === 0) updateFilenamePreview();
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

  updateFilenamePreview();
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

// Filename preview
function updateFilenamePreview() {
  const prefix = (inputPrefixo.value || '').trim();
  const format = nameFormatSelect.value || '{nome}';

  let rawName = 'alvaro_nunes_prestes';
  let primeiroNome = 'alvaro';
  let sobrenome = 'prestes';
  let matricula = '7971';

  if (state.groups && state.groups.length > 0) {
    const first = state.groups[0];
    rawName = first.person_name || 'servidor';
    matricula = first.matricula || '';
  }

  const cleanName = rawName
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\w\s-]/g, '')
    .trim()
    .toLowerCase()
    .replace(/[\s_]+/g, '_');

  const parts = cleanName.split('_').filter(Boolean);
  primeiroNome = parts[0] || 'nome';
  sobrenome = parts.length > 1 ? parts[parts.length - 1] : parts[0];

  let namePart = format
    .replace('{nome}', cleanName)
    .replace('{primeiro_nome}', primeiroNome)
    .replace('{sobrenome}', sobrenome)
    .replace('{matricula}', matricula);

  let finalName = `${prefix}${namePart}`;
  finalName = finalName.replace(/_{2,}/g, '_').replace(/[<>:"/\\|?*]/g, '');
  if (!finalName.toLowerCase().endsWith('.pdf')) {
    finalName += '.pdf';
  }

  filenamePreview.textContent = finalName;
}

// Split & Download
async function handleSplitPdf() {
  splitBtn.disabled = true;
  splitBtn.innerHTML = '⏳ Gerando PDFs...';

  const prefix = inputPrefixo.value.trim();
  const format = nameFormatSelect.value || '{nome}';
  const template = `{prefixo}${format}.pdf`;

  const payload = {
    template: template,
    prefixo: prefix,
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
  state.groups = [];
  state.rawPages = [];
  fileInput.value = '';
  heroSection.style.display = 'block';
  loadingSection.style.display = 'none';
  reviewSection.style.display = 'none';
  resultsSection.style.display = 'none';
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
