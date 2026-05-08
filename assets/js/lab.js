/* ============================================================
   BooMiLabs — Lab Guide Framework JS
   ============================================================ */
(function () {
  'use strict';

  var labId = document.documentElement.dataset.labId || location.pathname;
  var STORAGE_KEY = 'boomilabs:' + labId;

  function loadState() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
    catch (e) { return {}; }
  }

  function saveState(s) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); }
    catch (e) {}
  }

  var pages = Array.from(document.querySelectorAll('.step-page'));
  var navLinks = Array.from(document.querySelectorAll('.sidebar-nav a[data-step]'));
  var stepCounter = document.getElementById('stepCounter');
  var currentStep = 0;
  var state = loadState();
  var nextExerciseHref = document.documentElement.dataset.nextExerciseHref || null;
  var finishHref = document.documentElement.dataset.finishHref || 'index.html';

  // Get the nav buttons from the currently active page
  function activePage() { return pages[currentStep]; }
  function prevBtn() { return activePage().querySelector('#prevBtn'); }
  function nextBtn() { return activePage().querySelector('#nextBtn'); }
  function markDoneBtn() { return activePage().querySelector('#markDoneBtn'); }

  function showStep(idx, pushHistory) {
    if (pushHistory === undefined) pushHistory = true;
    idx = Math.max(0, Math.min(pages.length - 1, idx));
    currentStep = idx;

    pages.forEach(function (p, i) { p.classList.toggle('active', i === idx); });
    navLinks.forEach(function (a) {
      a.classList.toggle('active', parseInt(a.dataset.step, 10) === idx);
    });

    // Update buttons in the now-active page
    var pb = prevBtn(), nb = nextBtn();
    if (pb) pb.disabled = idx === 0;
    if (nb) {
      var onLast = idx === pages.length - 1;
      if (onLast && nextExerciseHref) {
        nb.disabled = false;
        nb.textContent = 'Next exercise →';
      } else if (onLast) {
        nb.disabled = false;
        nb.textContent = 'Finish ✓';
      } else {
        nb.disabled = false;
        nb.textContent = 'Next →';
      }
    }

    if (stepCounter) stepCounter.textContent = (idx + 1) + ' / ' + pages.length;

    updateMarkDoneBtn();
    updateProgress();
    window.scrollTo({ top: 0, behavior: 'instant' });

    if (pushHistory) history.pushState({ step: idx }, '', '#step-' + idx);
  }

  function updateProgress() {
    var done = Object.keys(state).filter(function (k) { return state[k]; }).length;
    var total = pages.length;
    var pct = total ? Math.round(done / total * 100) : 0;

    var fill = document.querySelector('.progress-fill');
    var label = document.querySelector('.progress-pct');
    if (fill) fill.style.width = pct + '%';
    if (label) label.textContent = pct + '%';

    navLinks.forEach(function (a) {
      a.classList.toggle('done', !!state[parseInt(a.dataset.step, 10)]);
    });
  }

  function updateMarkDoneBtn() {
    var btn = markDoneBtn();
    if (!btn) return;
    var done = !!state[currentStep];
    btn.classList.toggle('marked', done);
    btn.innerHTML = done
      ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg> Completed'
      : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 8 12 12 14.5 14.5"/></svg> Mark complete';
  }

  // Wire up nav buttons on all pages (not just active)
  pages.forEach(function (page, i) {
    var pb = page.querySelector('#prevBtn');
    var nb = page.querySelector('#nextBtn');
    var mdb = page.querySelector('#markDoneBtn');

    if (pb) pb.addEventListener('click', function () { showStep(currentStep - 1); });
    if (nb) nb.addEventListener('click', function () {
      if (currentStep === pages.length - 1) {
        location.href = nextExerciseHref || finishHref;
      } else {
        showStep(currentStep + 1);
      }
    });
    if (mdb) {
      mdb.addEventListener('click', function () {
        state[currentStep] = !state[currentStep];
        saveState(state);
        updateMarkDoneBtn();
        updateProgress();
        if (state[currentStep] && currentStep < pages.length - 1) {
          setTimeout(function () { showStep(currentStep + 1); }, 350);
        }
      });
    }
  });

  // Sidebar links
  navLinks.forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      showStep(parseInt(a.dataset.step, 10));
      var sb = document.querySelector('.lab-sidebar');
      if (sb) sb.classList.remove('open');
    });
  });

  // Mobile sidebar toggle
  var menuBtn = document.getElementById('menuBtn');
  var sidebar = document.querySelector('.lab-sidebar');
  if (menuBtn && sidebar) {
    menuBtn.addEventListener('click', function () { sidebar.classList.toggle('open'); });
    document.addEventListener('click', function (e) {
      if (!sidebar.contains(e.target) && !menuBtn.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  // Copy buttons on <pre> blocks
  document.querySelectorAll('pre').forEach(function (pre) {
    var btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'Copy';
    pre.appendChild(btn);
    btn.addEventListener('click', function () {
      var code = (pre.querySelector('code') || pre).textContent.replace(/\nCopy$/, '').trim();
      if (!navigator.clipboard) return;
      navigator.clipboard.writeText(code).then(function () {
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(function () { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
      }).catch(function () { btn.textContent = 'Error'; });
    });
  });

  // Keyboard navigation
  document.addEventListener('keydown', function (e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === 'ArrowRight') showStep(currentStep + 1);
    if (e.key === 'ArrowLeft')  showStep(currentStep - 1);
  });

  // Browser back/forward
  window.addEventListener('popstate', function (e) {
    if (e.state && e.state.step !== undefined) showStep(e.state.step, false);
  });

  // Init
  var hash = location.hash.match(/^#step-(\d+)$/);
  showStep(hash ? parseInt(hash[1], 10) : 0, false);
  updateProgress();

}());
