// js/menu.js
// Contoh sederhana untuk highlight menu aktif berdasarkan URL
document.addEventListener('DOMContentLoaded', () => {
  const navLinks = document.querySelectorAll('nav.bottom-nav a');
  const currentPage = window.location.pathname.split('/').pop();

  navLinks.forEach(link => {
    if (link.getAttribute('href') === currentPage) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
});
