
// static/js/menu.js
// Script untuk menandai menu navigasi bawah yang aktif sesuai URL saat ini

document.addEventListener('DOMContentLoaded', () => {
  const navLinks = document.querySelectorAll('nav.bottom-nav a');
  const currentPath = window.location.pathname;

  navLinks.forEach(link => {
    // Ambil path dari href link, tanpa domain
    const linkPath = new URL(link.href).pathname;

    if (linkPath === currentPath) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
});


const menuToggle = document.getElementById('menuToggle');
const drawer = document.getElementById('drawer');
const backdrop = document.getElementById('backdrop');

menuToggle.addEventListener('click', () => {
  const isOpen = drawer.classList.toggle('open');
  backdrop.hidden = !isOpen;
  menuToggle.setAttribute('aria-expanded', isOpen);
});

backdrop.addEventListener('click', () => {
  drawer.classList.remove('open');
  backdrop.hidden = true;
  menuToggle.setAttribute('aria-expanded', false);
});
