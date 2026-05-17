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

  document.querySelectorAll('a[href*="spot.fund/9s54l27sc"]').forEach((link) => {
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


(function wireFormspreeSubmit() {
  const form = document.querySelector('#founding-list-form');
  if (!form) return;

  const action = form.getAttribute('action') || '';
  if (!/formspree\.io\//i.test(action)) return;

  const status = document.querySelector('#founding-list-status');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const data = new FormData(form);

    try {
      const response = await fetch(action, {
        method: 'POST',
        body: data,
        headers: { Accept: 'application/json' },
      });

      if (!response.ok) throw new Error('submit_failed');

      if (status) {
        status.hidden = false;
        status.textContent = 'Thanks — your Founding List form was received successfully.';
      }
      form.reset();
      if (typeof window.fbq === 'function') {
        fbq('track', 'Lead', { content_name: 'Founding List Form Submit' });
        fbq('trackCustom', 'FoundingListConfirmed', { source: 'formspree_ajax' });
      }
      if (typeof window.gtag === 'function') {
        gtag('event', 'form_submit_success', { form_name: 'founding_list', source: 'formspree_ajax' });
      }
    } catch (_err) {
      if (status) {
        status.hidden = false;
        status.textContent = 'Something went wrong submitting the form. Please try again.';
      }
    }
  });
})();


(function trackGA4Events() {
  if (typeof window.gtag !== 'function') return;

  document.querySelectorAll('a[href*="spot.fund/9s54l27sc"]').forEach((link) => {
    link.addEventListener('click', () => {
      gtag('event', 'donate_click', {
        link_url: link.getAttribute('href') || '',
        link_text: (link.textContent || '').trim(),
        location: 'site'
      });
    });
  });

  document.querySelectorAll('a[href="#founding-list"]').forEach((link) => {
    link.addEventListener('click', () => {
      gtag('event', 'cta_click', {
        cta_name: 'join_founding_list',
        location: 'hero'
      });
    });
  });

  const foundingForm = document.querySelector('#founding-list-form');
  foundingForm?.addEventListener('submit', () => {
    gtag('event', 'generate_lead', {
      form_name: 'founding_list',
      method: 'form_submit'
    });
  });

  const successMessage = document.querySelector('#founding-list-status');
  if (successMessage && !successMessage.hasAttribute('hidden') && successMessage.textContent.trim()) {
    gtag('event', 'form_submit_success', {
      form_name: 'founding_list'
    });
  }
})();
