// DOM Element References
const statusLight = document.getElementById('status-light');
const statusText = document.getElementById('status-text');

const companyInput = document.getElementById('company-input');
const coverLetterInput = document.getElementById('cover-letter-input');
const clipboardToast = document.getElementById('clipboard-toast');

const progressCircle = document.getElementById('progress-circle');
const metricScoreText = document.getElementById('metric-score');
const robotBadge = document.getElementById('robot-badge');
const inputPodFrame = document.getElementById('input-pod-frame');

const rewriteBtn = document.getElementById('rewrite-btn');

// Output states
const emptyState = document.getElementById('empty-state');
const filledState = document.getElementById('filled-state');
const rewriteOutput = document.getElementById('rewrite-output');
const clicheTagsContainer = document.getElementById('cliche-tags');
const clicheReasonBox = document.getElementById('cliche-reason-box');
const selectedPhraseTitle = document.getElementById('selected-phrase-title');
const selectedPhraseReason = document.getElementById('selected-phrase-reason');

// History logs
const historyCount = document.getElementById('history-count');
const historyTbody = document.getElementById('history-tbody');

// SVG Ring Circumference
const CIRCUMFERENCE = 263.89; // 2 * Math.PI * 42

/**
 * Updates the UI circular progress meter and colors.
 */
function updateRobotScore(score) {
  metricScoreText.textContent = `${score}%`;
  
  // Animate SVG Ring
  const offset = CIRCUMFERENCE - (score / 100) * CIRCUMFERENCE;
  progressCircle.style.strokeDashoffset = Math.max(0, Math.min(CIRCUMFERENCE, offset));

  // Determine threshold warnings
  if (score > 15.0) {
    // Fire amber warning frames
    inputPodFrame.classList.add('jargon-alert');
    robotBadge.textContent = "CLICHÉ ALERT";
    robotBadge.className = "metric-badge alert";
    progressCircle.style.stroke = "var(--surface-coral)";
  } else {
    // Safe mode
    inputPodFrame.classList.remove('jargon-alert');
    robotBadge.textContent = "SAFE";
    robotBadge.className = "metric-badge";
    progressCircle.style.stroke = "var(--accent-blue)";
  }
}

/**
 * Shows temporary clipboard toast when intercepted.
 */
function showClipboardToast() {
  clipboardToast.classList.add('show');
  setTimeout(() => {
    clipboardToast.classList.remove('show');
  }, 2500);
}

/**
 * Render dynamic list of cliché tags and hover behavior.
 */
function renderClicheTags(flags) {
  clicheTagsContainer.innerHTML = '';
  clicheReasonBox.classList.add('hidden');

  if (!flags || flags.length === 0) {
    clicheTagsContainer.innerHTML = '<span style="font-style:italic; font-size:0.8rem; opacity:0.6;">No jargon flagged in this session.</span>';
    return;
  }

  flags.forEach(flag => {
    const tag = document.createElement('span');
    tag.className = 'cliche-tag';
    tag.textContent = flag.phrase;
    
    tag.addEventListener('click', () => {
      // Toggle selected class on sibling tags
      const siblings = clicheTagsContainer.querySelectorAll('.cliche-tag');
      siblings.forEach(s => s.classList.remove('selected'));
      
      tag.classList.add('selected');
      
      // Update Reason box
      selectedPhraseTitle.textContent = flag.phrase;
      selectedPhraseReason.textContent = flag.reason || "Devalued business jargon. Avoid filler words.";
      clicheReasonBox.classList.remove('hidden');
    });

    clicheTagsContainer.appendChild(tag);
  });
}

/**
 * Render SQLite database logs into the history table.
 */
function renderHistoryTable(items) {
  historyCount.textContent = items.length;
  historyTbody.innerHTML = '';

  if (items.length === 0) {
    historyTbody.innerHTML = `
      <tr>
        <td colspan="5" class="empty-table-msg">No logs currently archived. Try rewriting a cover letter to persist it!</td>
      </tr>
    `;
    return;
  }

  items.forEach(item => {
    const tr = document.createElement('tr');
    
    // Formatting date
    const dateStr = new Date(item.timestamp).toLocaleString();
    const scoreClass = item.robot_score > 15 ? 'high' : 'low';
    const clicheCount = item.clichés_found ? item.clichés_found.length : 0;
    
    tr.innerHTML = `
      <td>${dateStr}</td>
      <td style="font-weight: 600;">${escapeHtml(item.company_name)}</td>
      <td>
        <span class="score-badge ${scoreClass}">${item.robot_score}%</span>
      </td>
      <td>${clicheCount} flags</td>
      <td class="actions-col">
        <button class="table-btn load-btn" title="Load into workspace" data-id="${item.id}">
          <svg class="table-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
        </button>
        <button class="table-btn del-btn" title="Delete record" data-id="${item.id}">
          <svg class="table-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      </td>
    `;
    
    // Load button listener
    tr.querySelector('.load-btn').addEventListener('click', () => {
      companyInput.value = item.company_name;
      coverLetterInput.value = item.original_text;
      updateRobotScore(item.robot_score);
      
      // Load outputs
      emptyState.classList.add('hidden');
      filledState.classList.remove('hidden');
      rewriteOutput.innerHTML = formatMarkdown(item.cleaned_text);
      
      renderClicheTags(item.clichés_found);
    });

    // Delete button listener
    tr.querySelector('.del-btn').addEventListener('click', () => {
      if (confirm(`Delete the archive entry for ${item.company_name}?`)) {
        window.api.send({
          type: "delete_history_item",
          id: item.id
        });
      }
    });

    historyTbody.appendChild(tr);
  });
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// --------------------------------------------------------------------------
// API Event Listening & IPC Communication
// --------------------------------------------------------------------------

// Listen for updates from Python Daemon
window.api.onReceive((data) => {
  // Turn indicator to Green (daemon online)
  statusLight.className = "status-indicator-light connected";
  statusText.textContent = "Daemon Active";

  switch (data.type) {
    case 'clipboard_trigger':
      coverLetterInput.value = data.text;
      updateRobotScore(data.score);
      showClipboardToast();
      break;
      
    case 'rewrite_result':
      // Reset button state
      rewriteBtn.disabled = false;
      rewriteBtn.querySelector('span').textContent = "REWRITE COVER LETTER";
      
      emptyState.classList.add('hidden');
      filledState.classList.remove('hidden');
      
      // Render text and clichés
      rewriteOutput.innerHTML = formatMarkdown(data.rewritten_output);
      renderClicheTags(data.flags);
      break;
      
    case 'history_list':
      renderHistoryTable(data.items);
      break;
      
    case 'error':
      rewriteBtn.disabled = false;
      rewriteBtn.querySelector('span').textContent = "REWRITE COVER LETTER";
      statusLight.className = "status-indicator-light active"; // Pulsing coral error light
      statusText.textContent = "Error occurred";
      alert(`Backend Error: ${data.message}`);
      break;
  }
});

// Trigger manual rewrite action
rewriteBtn.addEventListener('click', () => {
  const text = coverLetterInput.value.strip ? coverLetterInput.value.strip() : coverLetterInput.value.trim();
  const company = companyInput.value.trim() || "Unknown Company";
  
  if (!text) {
    alert("Please enter or paste a cover letter draft first.");
    return;
  }
  
  // Set UI state to processing
  rewriteBtn.disabled = true;
  rewriteBtn.querySelector('span').textContent = "REWRITING Narrative...";
  statusLight.className = "status-indicator-light active";
  statusText.textContent = "Rewriting via Gemini API...";
  
  window.api.send({
    type: "request_rewrite",
    text: text,
    company_name: company
  });
});

// Helper to format basic markdown bold syntax to HTML
function formatMarkdown(text) {
  if (!text) return "";
  // Escape HTML first to prevent XSS, then replace bold tags
  const escaped = escapeHtml(text);
  return escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

// Default Hardcoded Sample Data
const defaultSample = {
  originalText: "To whom it may concern, I am a highly motivated results-oriented leader. I have a proven track record of deep dive engineering metrics.",
  companyName: "JuiceBox Inc",
  score: 65.2,
  rewrittenOutput: "As a **Software Engineering Lead** applying for the role at **JuiceBox Inc**, I focus on building high-performance systems rather than hiding behind buzzwords. Previously, I designed a distributed task queuing architecture that handled **10M+ daily transactions** and improved resource utilization by **40%**. I also spearheaded a comprehensive pipeline migration that slashed deployment times by **25%**.",
  flags: [
    { phrase: "To whom it may concern", reason: "Generic greeting. Address the hiring team or manager directly to make a stronger connection." },
    { phrase: "highly motivated", reason: "Overused filler phrase. Let your technical accomplishments speak for your motivation." },
    { phrase: "results-oriented", reason: "Hollow term. Focus instead on describing the actual metrics and outcomes you delivered." },
    { phrase: "proven track record", reason: "Vague. Show, don't tell, by detailing your past software deployments and achievements." },
    { phrase: "deep dive", reason: "Corporate buzzword. Use 'thorough analysis' or specify the exact research methodology." }
  ]
};

function loadDefaultSample() {
  companyInput.value = defaultSample.companyName;
  coverLetterInput.value = defaultSample.originalText;
  updateRobotScore(defaultSample.score);
  
  // Show outputs
  emptyState.classList.add('hidden');
  filledState.classList.remove('hidden');
  rewriteOutput.innerHTML = formatMarkdown(defaultSample.rewrittenOutput);
  
  renderClicheTags(defaultSample.flags);
}

// Initial Setup on startup
setTimeout(() => {
  // Pre-load our hardcoded demo sample
  loadDefaultSample();
  
  // Fetch initial history
  window.api.send({
    type: "get_history"
  });
}, 1000);
