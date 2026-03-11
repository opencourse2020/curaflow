/* =============================================================
   CuraFlow — app.js
   Minimal vanilla JS for UI interactivity
   ============================================================= */

document.addEventListener('DOMContentLoaded', function () {

  // -------------------------------------------------------
  // 1. Sidebar mobile toggle
  // -------------------------------------------------------
  const sidebarToggleBtn = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('open');
    if (sidebarOverlay) sidebarOverlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (sidebarOverlay) sidebarOverlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  if (sidebarToggleBtn) {
    sidebarToggleBtn.addEventListener('click', openSidebar);
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
  }

  // -------------------------------------------------------
  // 2. Profile dropdown toggle
  // -------------------------------------------------------
  const profileTrigger = document.getElementById('profileTrigger');
  const profileDropdown = document.getElementById('profileDropdown');

  if (profileTrigger && profileDropdown) {
    profileTrigger.addEventListener('click', function (e) {
      e.stopPropagation();
      profileDropdown.classList.toggle('open');
    });

    document.addEventListener('click', function () {
      profileDropdown.classList.remove('open');
    });

    profileDropdown.addEventListener('click', function (e) {
      e.stopPropagation();
    });
  }

  // -------------------------------------------------------
  // 3. Active nav state
  // -------------------------------------------------------
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(function (item) {
    const href = item.getAttribute('href');
    if (href && href !== '#' && currentPath.includes(href)) {
      item.classList.add('active');
    }
  });

  // -------------------------------------------------------
  // 4. Dismissible alerts
  // -------------------------------------------------------
  document.querySelectorAll('.alert-dismiss').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const alert = btn.closest('.alert-card');
      if (alert) {
        alert.style.transition = 'all 0.2s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(8px)';
        setTimeout(function () {
          alert.remove();
        }, 200);
      }
    });
  });

  // -------------------------------------------------------
  // 5. Tab switcher
  // -------------------------------------------------------
  document.querySelectorAll('.tabs').forEach(function (tabGroup) {
    const tabs = tabGroup.querySelectorAll('.tab-item[data-tab]');
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        const targetId = tab.getAttribute('data-tab');

        // Deactivate all tabs in this group
        tabs.forEach(function (t) { t.classList.remove('active'); });
        tab.classList.add('active');

        // Find parent container to scope panels
        const container = tabGroup.closest('[data-tab-container]') || document;
        container.querySelectorAll('.tab-panel').forEach(function (panel) {
          panel.style.display = 'none';
        });

        const target = container.querySelector('#' + targetId);
        if (target) target.style.display = 'block';
      });
    });
  });

  // -------------------------------------------------------
  // 6. Frequency selectors in program builder
  // -------------------------------------------------------
  document.querySelectorAll('.frequency-selector').forEach(function (sel) {
    const minusBtn = sel.querySelector('[data-freq-minus]');
    const plusBtn = sel.querySelector('[data-freq-plus]');
    const valueEl = sel.querySelector('.freq-value');

    if (minusBtn && plusBtn && valueEl) {
      minusBtn.addEventListener('click', function () {
        let val = parseInt(valueEl.textContent, 10);
        if (val > 1) {
          valueEl.textContent = val - 1;
        }
      });

      plusBtn.addEventListener('click', function () {
        let val = parseInt(valueEl.textContent, 10);
        if (val < 7) {
          valueEl.textContent = val + 1;
        }
      });
    }
  });

  // -------------------------------------------------------
  // 7. Service card select / deselect
  // -------------------------------------------------------
  document.querySelectorAll('.service-card[data-selectable]').forEach(function (card) {
    card.addEventListener('click', function () {
      card.classList.toggle('selected');
      const addBtn = card.querySelector('.service-add-btn');
      if (addBtn) {
        if (card.classList.contains('selected')) {
          addBtn.textContent = 'Remove';
          addBtn.classList.remove('btn-secondary');
          addBtn.classList.add('btn-primary');
        } else {
          addBtn.textContent = 'Add';
          addBtn.classList.remove('btn-primary');
          addBtn.classList.add('btn-secondary');
        }
      }
    });
  });

  // -------------------------------------------------------
  // 8. Simple search filter (client-side table filter)
  // -------------------------------------------------------
  const tableSearch = document.querySelector('[data-table-search]');
  const tableRows = document.querySelectorAll('[data-searchable-row]');

  if (tableSearch && tableRows.length > 0) {
    tableSearch.addEventListener('input', function () {
      const query = tableSearch.value.toLowerCase().trim();
      let visible = 0;
      tableRows.forEach(function (row) {
        const text = row.textContent.toLowerCase();
        if (text.includes(query)) {
          row.style.display = '';
          visible++;
        } else {
          row.style.display = 'none';
        }
      });

      const counter = document.querySelector('[data-table-count]');
      if (counter) {
        counter.textContent = visible + ' result' + (visible !== 1 ? 's' : '');
      }
    });
  }

  // -------------------------------------------------------
  // 9. Progress ring animation on load
  // -------------------------------------------------------
  document.querySelectorAll('.adherence-ring-fill[data-pct]').forEach(function (ring) {
    const pct = parseFloat(ring.getAttribute('data-pct')) / 100;
    const circumference = 188;
    const offset = circumference * (1 - pct);
    ring.style.strokeDashoffset = circumference; // start at 0
    requestAnimationFrame(function () {
      setTimeout(function () {
        ring.style.strokeDashoffset = offset;
      }, 300);
    });
  });

  // -------------------------------------------------------
  // 10. Smooth notifications badge pulse
  // -------------------------------------------------------
  const notifDots = document.querySelectorAll('.notif-dot');
  notifDots.forEach(function (dot) {
    dot.style.animation = 'pulse 2.5s ease-in-out infinite';
  });

  // -------------------------------------------------------
  // 11. Program builder — add service to panel
  // -------------------------------------------------------
  document.querySelectorAll('.btn-add-service').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      const card = btn.closest('.service-card');
      const serviceName = card ? card.querySelector('.service-card-name').textContent : 'Service';
      const panel = document.getElementById('builderSelectedList');
      if (panel) {
        const msg = panel.querySelector('.empty-state');
        if (msg) msg.remove();

        const item = document.createElement('div');
        item.className = 'builder-item';
        item.innerHTML = `
          <div class="builder-item-icon" style="background:var(--primary-soft)">💪</div>
          <div>
            <div class="builder-item-name">${serviceName}</div>
            <div class="builder-item-meta">2x / week · 45 min</div>
          </div>
          <div class="builder-item-actions" style="margin-left:auto">
            <button class="btn btn-ghost btn-sm btn-remove-item">Remove</button>
          </div>
        `;
        panel.appendChild(item);

        item.querySelector('.btn-remove-item').addEventListener('click', function () {
          item.remove();
        });
      }
      btn.textContent = btn.textContent === 'Add' ? 'Added ✓' : 'Add';
      btn.disabled = true;
    });
  });

  // -------------------------------------------------------
  // 12. Misc: highlight active settings nav
  // -------------------------------------------------------
  document.querySelectorAll('.settings-nav-item').forEach(function (item) {
    item.addEventListener('click', function () {
      document.querySelectorAll('.settings-nav-item').forEach(function (i) {
        i.classList.remove('active');
      });
      item.classList.add('active');
    });
  });

});