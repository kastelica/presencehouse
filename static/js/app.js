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


(function () {
  const shell = document.querySelector("[data-nav-shell]");
  const toggle = document.querySelector("[data-menu-toggle]");
  if (!shell || !toggle) return;

  toggle.addEventListener("click", () => {
    const isOpen = shell.classList.toggle("nav-open");
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });
})();


(function trackMetaEvents() {
  if (typeof window.fbq !== 'function') return;

  document.querySelectorAll('a[href*="spot.fund/j2brwjqsc"]').forEach((link) => {
    link.addEventListener('click', () => {
      fbq('trackCustom', 'DonateLinkClick', {
        destination: link.getAttribute('href') || '',
        text: (link.textContent || '').trim(),
      });
    });
  });

  const foundingForm = document.querySelector('#founding-list form');
  foundingForm?.addEventListener('submit', () => {
    fbq('track', 'Lead', { content_name: 'Founding List Form Submit' });
    fbq('trackCustom', 'FoundingListSubmit', { source: 'homepage_form' });
  });

  const successFlash = document.querySelector('.flash.success');
  const flashMessage = (successFlash?.textContent || '').trim();
  if (flashMessage && /thanks|submit|supporting|received/i.test(flashMessage)) {
    fbq('track', 'CompleteRegistration', { status: 'success_flash' });
    fbq('trackCustom', 'FoundingListConfirmed', { message: flashMessage });
  }
})();


(function removeLegacyGallery2NavLink() {
  document.querySelectorAll('a[href*="gallery2"], a').forEach((link) => {
    const label = (link.textContent || '').trim().toLowerCase();
    const href = (link.getAttribute('href') || '').toLowerCase();
    if (label === 'gallery2' || label === 'galery2' || href.includes('gallery2')) {
      link.remove();
    }
  });
})();
