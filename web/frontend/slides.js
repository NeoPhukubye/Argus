(function () {
  const slides = document.querySelectorAll('.slide');
  const prev = document.getElementById('prev');
  const next = document.getElementById('next');
  const status = document.getElementById('status');
  let current = 0;

  function show(index) {
    slides.forEach((el, i) => {
      el.classList.toggle('active', i === index);
    });
    status.textContent = `${index + 1} / ${slides.length}`;
    current = index;
  }

  function goNext() {
    const nextIndex = (current + 1) % slides.length;
    show(nextIndex);
  }

  function goPrev() {
    const prevIndex = (current - 1 + slides.length) % slides.length;
    show(prevIndex);
  }

  if (next) next.addEventListener('click', goNext);
  if (prev) prev.addEventListener('click', goPrev);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === ' ') {
      e.preventDefault();
      goNext();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      goPrev();
    }
  });

  show(0);
})();
