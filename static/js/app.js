// Minimal interactivity that supports real-world presence, not endless engagement loops.
(function () {
  const slider = document.querySelector('[data-slider]');
  if (!slider) return;

  const track = slider.querySelector('[data-slider-track]');
  const slides = Array.from(slider.querySelectorAll('[data-slide]'));
  const prev = slider.querySelector('[data-prev]');
  const next = slider.querySelector('[data-next]');
  const dots = Array.from(slider.querySelectorAll('[data-dot]'));

  if (!track || slides.length === 0) return;

  let index = 0;
  let timer;

  function render() {
    track.style.transform = `translateX(-${index * 100}%)`;
    dots.forEach((dot, i) => dot.classList.toggle('active', i === index));
  }

  function goTo(i) {
    index = (i + slides.length) % slides.length;
    render();
  }

  function autoplay() {
    timer = setInterval(() => goTo(index + 1), 6000);
  }

  function resetAutoplay() {
    clearInterval(timer);
    autoplay();
  }

  prev?.addEventListener('click', () => { goTo(index - 1); resetAutoplay(); });
  next?.addEventListener('click', () => { goTo(index + 1); resetAutoplay(); });
  dots.forEach((dot, i) => dot.addEventListener('click', () => { goTo(i); resetAutoplay(); }));

  slider.addEventListener('mouseenter', () => clearInterval(timer));
  slider.addEventListener('mouseleave', autoplay);

  render();
  autoplay();
})();
