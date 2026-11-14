/**
 * Auth Guard and User Session Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  const token = Api.getToken();
  const path = window.location.pathname;

  const isAuthPage = path.endsWith('login.html') || path.endsWith('register.html') || path === '/' || path.endsWith('index.html');

  if (!token && !isAuthPage) {
    window.location.href = 'login.html';
    return;
  }

  if (token && (path.endsWith('login.html') || path.endsWith('register.html'))) {
    window.location.href = 'dashboard.html';
    return;
  }

  // Populate user profile info in sidebar
  const user = Api.getUser();
  if (user) {
    const nameEl = document.getElementById('sidebar-user-name');
    const roleEl = document.getElementById('sidebar-user-role');
    const avatarEl = document.getElementById('sidebar-user-avatar');
    const bizEl = document.getElementById('sidebar-business-name');

    if (nameEl) nameEl.textContent = user.full_name;
    if (roleEl) roleEl.textContent = (user.role || 'Admin').toUpperCase();
    if (avatarEl) {
      const initials = user.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
      avatarEl.textContent = initials || 'FS';
    }
    if (bizEl) bizEl.textContent = Api.getBusinessName();
  }

  // Logout button binding
  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      Api.clearSession();
      showToast('Logged out successfully', 'info');
      setTimeout(() => {
        window.location.href = 'login.html';
      }, 500);
    });
  }

  // Mobile menu toggle
  const mobileToggle = document.getElementById('mobile-menu-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }
});
