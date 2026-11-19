// Lead Management System - Interactive Frontend Script

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Sidebar Toggle
  const sidebar = document.querySelector('.sidebar');
  const toggleBtn = document.getElementById('sidebarToggleBtn');
  const backdrop = document.getElementById('sidebarBackdrop');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('show');
      if (backdrop) backdrop.classList.toggle('show');
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', function () {
      sidebar.classList.remove('show');
      backdrop.classList.remove('show');
    });
  }

  // 2. Initialize Bootstrap Tooltips & Popovers
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // 3. Quick Copy-to-Clipboard helper
  document.querySelectorAll('.btn-copy').forEach(button => {
    button.addEventListener('click', function () {
      const text = this.getAttribute('data-copy');
      if (text) {
        navigator.clipboard.writeText(text).then(() => {
          const originalHtml = this.innerHTML;
          this.innerHTML = '<i class="bi bi-check2"></i> Copied!';
          setTimeout(() => {
            this.innerHTML = originalHtml;
          }, 2000);
        });
      }
    });
  });

  // 4. Kanban Drag and Drop (Native HTML5 Drag & Drop)
  const draggables = document.querySelectorAll('.kanban-card[draggable="true"]');
  const dropzones = document.querySelectorAll('.kanban-cards-wrapper');

  draggables.forEach(draggable => {
    draggable.addEventListener('dragstart', () => {
      draggable.classList.add('dragging');
      draggable.style.opacity = '0.4';
    });

    draggable.addEventListener('dragend', () => {
      draggable.classList.remove('dragging');
      draggable.style.opacity = '1';
    });
  });

  dropzones.forEach(zone => {
    zone.addEventListener('dragover', e => {
      e.preventDefault();
      zone.classList.add('bg-light');
    });

    zone.addEventListener('dragleave', () => {
      zone.classList.remove('bg-light');
    });

    zone.addEventListener('drop', e => {
      e.preventDefault();
      zone.classList.remove('bg-light');
      const draggingCard = document.querySelector('.dragging');
      if (draggingCard) {
        zone.appendChild(draggingCard);
        const leadId = draggingCard.getAttribute('data-lead-id');
        const newStatus = zone.getAttribute('data-stage-id');

        // Send AJAX request to update status in Django
        updateLeadStatus(leadId, newStatus);
      }
    });
  });

  function updateLeadStatus(leadId, newStatus) {
    const csrfToken = getCsrfToken();
    fetch('/leads/update-status-ajax/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrfToken
      },
      body: new URLSearchParams({
        'lead_id': leadId,
        'status': newStatus
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showToast('Lead Status Updated', `Lead #${leadId} moved to '${newStatus}'`, 'success');
      } else {
        showToast('Update Failed', data.error || 'Could not update lead status', 'danger');
      }
    })
    .catch(err => {
      console.error(err);
      showToast('Error', 'Network or server error updating lead status', 'danger');
    });
  }

  // Toast notification helper
  function showToast(title, message, type = 'primary') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${type} border-0 show mb-2`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          <strong>${title}:</strong> ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;
    toastContainer.appendChild(toastEl);
    setTimeout(() => {
      toastEl.remove();
    }, 4000);
  }

  // Django CSRF token extractor (from DOM or cookie)
  function getCsrfToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input && input.value) return input.value;
    return getCookie('leadflow_csrftoken') || getCookie('csrftoken') || '';
  }

  // Django CSRF cookie extractor
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  window.showToast = showToast;
  window.getCookie = getCookie;
  window.getCsrfToken = getCsrfToken;
});

