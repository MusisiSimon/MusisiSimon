try {
  var t = localStorage.getItem('intellora-theme');
  if (t) document.documentElement.setAttribute('data-theme', t);
} catch (e) {}
