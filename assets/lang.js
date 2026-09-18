try {
  var l = localStorage.getItem('intellora-lang');
  if (l === 'fr') document.documentElement.setAttribute('data-lang', 'fr');
} catch (e) {}
