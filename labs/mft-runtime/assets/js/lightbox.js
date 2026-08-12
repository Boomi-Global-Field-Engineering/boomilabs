document.addEventListener('DOMContentLoaded', function () {
  var overlay = document.createElement('div');
  overlay.className = 'lightbox-overlay';
  overlay.innerHTML = '<button class="lightbox-close" aria-label="Close">&times;</button><img src="" alt="">';
  document.body.appendChild(overlay);
  var img = overlay.querySelector('img');

  function open(src, alt) {
    img.src = src;
    img.alt = alt;
    overlay.classList.add('active');
  }
  function close() {
    overlay.classList.remove('active');
    img.src = '';
  }

  document.querySelectorAll('figure.shot img').forEach(function (el) {
    el.addEventListener('click', function () { open(el.src, el.alt); });
  });
  overlay.addEventListener('click', close);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') close();
  });
});
