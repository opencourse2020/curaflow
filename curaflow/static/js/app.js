/* =============================================================
   CuraFlow — app.js
   Minimal vanilla JS for core UI interactions.
   Covers: sidebar mobile toggle, profile dropdown, dismissible alerts.
   ============================================================= */

document.addEventListener('DOMContentLoaded', function () {

  // -------------------------------------------------------
  // 1. Mobile Sidebar Toggle
  // -------------------------------------------------------
  var sidebarToggleBtn = document.getElementById('sidebarToggle');
  var sidebar          = document.getElementById('sidebar');
  var sidebarOverlay   = document.getElementById('sidebarOverlay');

  function openSidebar() {
    if (sidebar)        sidebar.classList.add('open');
    if (sidebarOverlay) sidebarOverlay.classList.add('open');
    if (sidebarToggleBtn) sidebarToggleBtn.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    if (sidebar)        sidebar.classList.remove('open');
    if (sidebarOverlay) sidebarOverlay.classList.remove('open');
    if (sidebarToggleBtn) sidebarToggleBtn.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  if (sidebarToggleBtn) {
    sidebarToggleBtn.addEventListener('click', openSidebar);
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
  }

  // Close sidebar on ESC key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeSidebar(); }
  });

  // -------------------------------------------------------
  // 2. Profile Dropdown Toggle
  // -------------------------------------------------------
  var profileTrigger  = document.getElementById('profileTrigger');
  var profileDropdown = document.getElementById('profileDropdown');

  if (profileTrigger && profileDropdown) {

    profileTrigger.addEventListener('click', function (e) {
      e.stopPropagation();
      var isOpen = profileDropdown.classList.toggle('open');
      profileTrigger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    // Close when clicking outside
    document.addEventListener('click', function () {
      profileDropdown.classList.remove('open');
      profileTrigger.setAttribute('aria-expanded', 'false');
    });

    // Prevent clicks inside dropdown from closing it
    profileDropdown.addEventListener('click', function (e) {
      e.stopPropagation();
    });
  }

  // -------------------------------------------------------
  // 3. Dismissible Alerts
  // -------------------------------------------------------
  document.querySelectorAll('.alert-dismiss').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var alertEl = btn.closest('.alert-card');
      if (!alertEl) return;

      alertEl.style.transition = 'opacity 200ms ease, transform 200ms ease';
      alertEl.style.opacity    = '0';
      alertEl.style.transform  = 'translateX(8px)';

      setTimeout(function () {
        alertEl.remove();
      }, 200);
    });
  });

});