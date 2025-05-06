// Admin Onboarding Overlay
class AdminOnboardingOverlay {
  constructor() {
    this.currentStep = 0;
    this.steps = [];
    this.overlay = null;
    this.content = null;
    this.navigation = null;
    this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    this.isAnimating = false;
  }

  async initialize() {
    // Fetch the onboarding content
    try {
      const response = await fetch('/admin/onboarding/content/');
      const data = await response.json();

      if (data.status === 'in_progress' && data.items && data.items.length > 0) {
        this.steps = data.items;
        this.createOverlay();
        this.showStep(0);

        // Add keyboard navigation
        document.addEventListener('keydown', this.handleKeyPress.bind(this));
      }
    } catch (error) {
      console.error('Error initializing admin onboarding:', error);
    }
  }

  createOverlay() {
    // Create the overlay container
    this.overlay = document.createElement('div');
    this.overlay.className = 'admin-onboarding-overlay';

    // Create the content area
    this.content = document.createElement('div');
    this.content.className = 'admin-onboarding-content';
    this.overlay.appendChild(this.content);

    // Create the navigation controls
    this.navigation = document.createElement('div');
    this.navigation.className = 'admin-onboarding-navigation';

    // Left side of navigation (skip button)
    const navLeft = document.createElement('div');

    const skipButton = document.createElement('button');
    skipButton.className = 'btn btn-link';
    skipButton.innerHTML = '<i class="fas fa-times"></i> Overslaan';
    skipButton.addEventListener('click', () => this.confirmSkip());

    navLeft.appendChild(skipButton);

    // Right side of navigation (prev/next buttons)
    const navRight = document.createElement('div');

    const prevButton = document.createElement('button');
    prevButton.className = 'btn btn-outline-primary me-2';
    prevButton.innerHTML = '<i class="fas fa-arrow-left"></i> Vorige';
    prevButton.addEventListener('click', () => this.prevStep());

    const nextButton = document.createElement('button');
    nextButton.className = 'btn btn-primary';
    nextButton.innerHTML = 'Volgende <i class="fas fa-arrow-right"></i>';
    nextButton.addEventListener('click', () => this.nextStep());

    const completeButton = document.createElement('button');
    completeButton.className = 'btn btn-success';
    completeButton.innerHTML = 'Voltooien <i class="fas fa-check"></i>';
    completeButton.style.display = 'none';
    completeButton.addEventListener('click', () => this.completeOnboarding());

    navRight.appendChild(prevButton);
    navRight.appendChild(nextButton);
    navRight.appendChild(completeButton);

    this.navigation.appendChild(navLeft);
    this.navigation.appendChild(navRight);

    this.overlay.appendChild(this.navigation);

    // Add the overlay to the page
    document.body.appendChild(this.overlay);

    // Store references to the buttons for later use
    this.prevButton = prevButton;
    this.nextButton = nextButton;
    this.completeButton = completeButton;
    this.skipButton = skipButton;
  }

  showStep(stepIndex) {
    if (stepIndex < 0 || stepIndex >= this.steps.length || this.isAnimating) {
      return;
    }

    this.isAnimating = true;

    // Fade out current content
    this.content.style.opacity = '0';

    setTimeout(() => {
      this.currentStep = stepIndex;
      const step = this.steps[stepIndex];

      // Update content
      this.content.innerHTML = '';

      const title = document.createElement('h2');
      title.textContent = step.title;
      title.style.marginBottom = '25px';
      title.style.color = '#206bc4';
      this.content.appendChild(title);

      const description = document.createElement('div');
      description.innerHTML = step.content;
      this.content.appendChild(description);

      // Update navigation buttons
      this.prevButton.disabled = stepIndex === 0;

      if (stepIndex === this.steps.length - 1) {
        this.nextButton.style.display = 'none';
        this.completeButton.style.display = 'inline-block';
      } else {
        this.nextButton.style.display = 'inline-block';
        this.completeButton.style.display = 'none';
      }

      // Add progress indicator
      const progress = document.createElement('div');
      progress.className = 'admin-onboarding-progress';
      progress.innerHTML = `<span>Stap ${stepIndex + 1} van ${this.steps.length}</span>`;

      // Add progress dots
      const progressDots = document.createElement('div');
      progressDots.style.display = 'flex';
      progressDots.style.justifyContent = 'center';
      progressDots.style.marginTop = '10px';

      for (let i = 0; i < this.steps.length; i++) {
        const dot = document.createElement('div');
        dot.style.width = '8px';
        dot.style.height = '8px';
        dot.style.borderRadius = '50%';
        dot.style.margin = '0 4px';
        dot.style.backgroundColor = i === stepIndex ? '#206bc4' : '#d1d5db';
        progressDots.appendChild(dot);
      }

      progress.appendChild(progressDots);
      this.content.appendChild(progress);

      // Fade in new content
      setTimeout(() => {
        this.content.style.opacity = '1';
        this.isAnimating = false;
      }, 50);
    }, 200);
  }

  nextStep() {
    if (this.currentStep < this.steps.length - 1) {
      this.showStep(this.currentStep + 1);
    }
  }

  prevStep() {
    if (this.currentStep > 0) {
      this.showStep(this.currentStep - 1);
    }
  }

  confirmSkip() {
    if (confirm('Weet u zeker dat u de onboarding wilt overslaan? U kunt deze later voltooien via het dashboard.')) {
      this.closeOverlay();
    }
  }

  closeOverlay() {
    if (this.overlay && this.overlay.parentNode) {
      // Remove keyboard event listener
      document.removeEventListener('keydown', this.handleKeyPress.bind(this));

      // Fade out overlay
      this.overlay.style.opacity = '0';

      setTimeout(() => {
        this.overlay.parentNode.removeChild(this.overlay);
      }, 300);
    }
  }

  handleKeyPress(event) {
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      this.nextStep();
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      this.prevStep();
    } else if (event.key === 'Escape') {
      this.confirmSkip();
    }
  }

  async completeOnboarding() {
    try {
      const response = await fetch('/admin/onboarding/complete/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.csrfToken,
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (response.ok) {
        // Show success message
        const successMessage = document.createElement('div');
        successMessage.className = 'admin-onboarding-success';
        successMessage.innerHTML = `
          <div class="onboarding-content-section">
            <div style="text-align: center;">
              <div style="font-size: 60px; margin-bottom: 20px;">🎉</div>
              <h3>Onboarding voltooid!</h3>
              <p>Bedankt voor het voltooien van de admin onboarding. U kunt nu beginnen met het gebruik van ChiefOnboarding om geweldige onboarding ervaringen te creëren voor uw nieuwe medewerkers.</p>
            </div>
          </div>
        `;

        this.content.innerHTML = '';
        this.content.appendChild(successMessage);

        // Hide navigation buttons except for a close button
        this.navigation.innerHTML = '';
        const closeButton = document.createElement('button');
        closeButton.className = 'btn btn-primary';
        closeButton.innerHTML = 'Aan de slag <i class="fas fa-rocket"></i>';
        closeButton.addEventListener('click', () => {
          this.closeOverlay();
          window.location.reload();
        });
        this.navigation.appendChild(closeButton);

        // Remove the alert from the page
        const alert = document.querySelector('.alert-info');
        if (alert) {
          alert.remove();
        }
      } else {
        console.error('Failed to complete onboarding');
      }
    } catch (error) {
      console.error('Error completing onboarding:', error);
    }
  }
}

// Initialize the overlay when the page loads
document.addEventListener('DOMContentLoaded', () => {
  // Add a slight delay to ensure the page is fully loaded
  setTimeout(() => {
    const adminOnboarding = new AdminOnboardingOverlay();
    adminOnboarding.initialize();
  }, 500);
});
