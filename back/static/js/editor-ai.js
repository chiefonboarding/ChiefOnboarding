/**
 * AI Content Generation Tool for Editor.js
 */
class AITool {
  /**
   * Notify core that read-only mode is supported
   * @returns {boolean}
   */
  static get isReadOnlySupported() {
    return true;
  }

  /**
   * Get Tool toolbox settings
   * icon - Tool icon's SVG
   * title - title to show in toolbox
   *
   * @returns {{icon: string, title: string}}
   */
  static get toolbox() {
    return {
      title: 'AI Content',
      icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-cpu"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>'
    };
  }

  /**
   * Render plugin's main Element and fill it with saved data
   *
   * @param {object} params - tool constructor options
   * @param {object} params.data - previously saved data
   * @param {object} params.config - user config for Tool
   * @param {object} params.api - Editor.js API
   * @param {boolean} params.readOnly - read-only mode flag
   */
  constructor({ data, config, api, readOnly }) {
    this.api = api;
    this.readOnly = readOnly;
    this.data = {
      prompt: data.prompt || '',
      content: data.content || '',
      loading: false
    };

    this.nodes = {
      wrapper: null,
      promptInput: null,
      generateButton: null,
      contentContainer: null,
      loadingIndicator: null,
      variablesHelp: null,
      useContentButton: null
    };

    this.CSS = {
      baseBlock: this.api.styles.block,
      wrapper: 'ce-ai-tool',
      promptInput: 'ce-ai-tool__prompt',
      generateButton: 'ce-ai-tool__generate',
      contentContainer: 'ce-ai-tool__content',
      loadingIndicator: 'ce-ai-tool__loading',
      variablesHelp: 'ce-ai-tool__variables-help',
      useContentButton: 'ce-ai-tool__use-content'
    };
  }

  /**
   * Create and return the Tool's view
   * @returns {HTMLDivElement}
   */
  render() {
    this.nodes.wrapper = this._make('div', [this.CSS.baseBlock, this.CSS.wrapper]);

    if (this.readOnly) {
      this.nodes.contentContainer = this._make('div', this.CSS.contentContainer, {
        innerHTML: this.data.content
      });
      this.nodes.wrapper.appendChild(this.nodes.contentContainer);
      return this.nodes.wrapper;
    }

    // Create variables help text
    const variablesHelp = this._make('div', this.CSS.variablesHelp, {
      innerHTML: '<small><strong>Click a variable to insert it</strong> (works in both prompt and content):<br>' +
        '<span class="ce-ai-tool__variable" data-variable="{{ first_name }}">{{ first_name }}</span> ' +
        '<span class="ce-ai-tool__variable" data-variable="{{ last_name }}">{{ last_name }}</span> ' +
        '<span class="ce-ai-tool__variable" data-variable="{{ position }}">{{ position }}</span> ' +
        '<span class="ce-ai-tool__variable" data-variable="{{ department }}">{{ department }}</span> ' +
        '<span class="ce-ai-tool__variable" data-variable="{{ manager }}">{{ manager }}</span> ' +
        '<span class="ce-ai-tool__variable" data-variable="{{ buddy }}">{{ buddy }}</span>' +
        '</small>'
    });

    // Add click event listeners to variables
    const variables = variablesHelp.querySelectorAll('.ce-ai-tool__variable');
    variables.forEach(variable => {
      variable.addEventListener('click', (e) => {
        // Check if the prompt input is focused
        if (document.activeElement === this.nodes.promptInput) {
          this.insertVariableIntoPrompt(variable.dataset.variable);
        } else {
          // Otherwise insert into the content container
          this.insertVariable(variable.dataset.variable);
        }
        e.preventDefault();
      });
    });

    // Create prompt input
    this.nodes.promptInput = this._make('input', this.CSS.promptInput, {
      placeholder: 'Enter a prompt for AI content generation...',
      value: this.data.prompt
    });

    // Create generate button
    this.nodes.generateButton = this._make('button', this.CSS.generateButton, {
      textContent: 'Generate'
    });
    this.nodes.generateButton.addEventListener('click', () => {
      this.generateContent();
    });

    // Create loading indicator (hidden by default)
    this.nodes.loadingIndicator = this._make('div', this.CSS.loadingIndicator, {
      textContent: 'Generating content...',
      style: 'display: none;'
    });

    // Create content container
    this.nodes.contentContainer = this._make('div', this.CSS.contentContainer, {
      innerHTML: this.data.content,
      contentEditable: true
    });

    // Create use content button (hidden by default)
    this.nodes.useContentButton = this._make('button', this.CSS.useContentButton, {
      textContent: 'Use This Content',
      style: 'display: none;'
    });
    this.nodes.useContentButton.addEventListener('click', () => {
      this.useGeneratedContent();
    });

    // Add all elements to wrapper
    this.nodes.variablesHelp = variablesHelp;
    this.nodes.wrapper.appendChild(this.nodes.variablesHelp);
    this.nodes.wrapper.appendChild(this.nodes.promptInput);
    this.nodes.wrapper.appendChild(this.nodes.generateButton);
    this.nodes.wrapper.appendChild(this.nodes.loadingIndicator);
    this.nodes.wrapper.appendChild(this.nodes.contentContainer);
    this.nodes.wrapper.appendChild(this.nodes.useContentButton);

    return this.nodes.wrapper;
  }

  /**
   * Insert a variable into the prompt input field
   * @param {string} variable - The variable to insert
   */
  insertVariableIntoPrompt(variable) {
    const input = this.nodes.promptInput;
    const startPos = input.selectionStart;
    const endPos = input.selectionEnd;
    const currentValue = input.value;

    // Insert the variable at the cursor position
    const newValue = currentValue.substring(0, startPos) + variable + currentValue.substring(endPos);
    input.value = newValue;

    // Move the cursor after the inserted variable
    const newCursorPos = startPos + variable.length;
    input.setSelectionRange(newCursorPos, newCursorPos);

    // Keep focus on the input
    input.focus();
  }

  /**
   * Insert a variable at the cursor position in the content container
   * @param {string} variable - The variable to insert
   */
  insertVariable(variable) {
    // Focus the content container
    this.nodes.contentContainer.focus();

    // Get the current selection
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);

    // Create a text node with the variable
    const textNode = document.createTextNode(variable);

    // Insert the text node at the cursor position
    range.insertNode(textNode);

    // Move the cursor after the inserted variable
    range.setStartAfter(textNode);
    range.setEndAfter(textNode);
    selection.removeAllRanges();
    selection.addRange(range);

    // Update the data
    this.data.content = this.nodes.contentContainer.innerHTML;
  }

  /**
   * Use the generated content as the final content for this block
   */
  useGeneratedContent() {
    // Replace the entire block with the generated content
    const content = this.nodes.contentContainer.innerHTML;

    // Create a new paragraph block with the content
    const index = this.api.blocks.getCurrentBlockIndex();

    // Delete the current block
    this.api.blocks.delete(index);

    // Insert a new paragraph block with the content
    this.api.blocks.insert('paragraph', { text: content }, {}, index, true);
  }

  /**
   * Generate content using AI
   */
  async generateContent() {
    const prompt = this.nodes.promptInput.value.trim();

    if (!prompt) {
      return;
    }

    // Show loading indicator
    this.nodes.loadingIndicator.style.display = 'block';
    this.nodes.generateButton.disabled = true;
    this.nodes.useContentButton.style.display = 'none';

    try {
      // Get CSRF token from cookie
      const getCookie = (name) => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
      };

      const csrfToken = getCookie('csrftoken');

      // Show a message while we're waiting for the API response
      this.nodes.contentContainer.innerHTML = '<p>Generating content, please wait...</p>';

      const response = await fetch('/api/ai-content-generate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin', // Use same-origin for session cookies
        body: JSON.stringify({ prompt })
      });

      if (!response.ok) {
        let errorMessage = 'Failed to generate content';
        try {
          const errorData = await response.json();
          if (errorData && errorData.error) {
            errorMessage = errorData.error;
          }
        } catch (e) {
          // If we can't parse the JSON, use status code info
          errorMessage = `Error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      this.data.content = data.content;
      this.nodes.contentContainer.innerHTML = this.data.content;

      // Show the "Use This Content" button
      this.nodes.useContentButton.style.display = 'block';
    } catch (error) {
      console.error('Error generating content:', error);
      let errorMessage = error.message || 'Error generating content. Please try again.';

      // Add helpful message for common errors
      if (errorMessage.includes('AI API key not configured')) {
        errorMessage = 'AI API key not configured. Please go to Settings > AI Content to set up your OpenAI API key.';
      } else if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
        errorMessage = 'Authentication error. Please refresh the page and try again.';
      } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
        errorMessage = 'Network error. Please check your internet connection and try again.';
      }

      this.nodes.contentContainer.innerHTML = `<p style="color: red;">${errorMessage}</p>`;
    } finally {
      // Hide loading indicator
      this.nodes.loadingIndicator.style.display = 'none';
      this.nodes.generateButton.disabled = false;
    }
  }

  /**
   * Extract data from the tool's DOM
   * @returns {object} Tool data
   */
  save() {
    return {
      prompt: this.nodes.promptInput ? this.nodes.promptInput.value : this.data.prompt,
      content: this.nodes.contentContainer ? this.nodes.contentContainer.innerHTML : this.data.content
    };
  }

  /**
   * Helper for making Elements with attributes
   *
   * @param {string} tagName - new Element tag name
   * @param {Array|string} classNames - list or name of CSS class
   * @param {object} attributes - any attributes
   * @returns {Element}
   */
  _make(tagName, classNames = null, attributes = {}) {
    const el = document.createElement(tagName);

    if (Array.isArray(classNames)) {
      el.classList.add(...classNames);
    } else if (classNames) {
      el.classList.add(classNames);
    }

    for (const attrName in attributes) {
      el[attrName] = attributes[attrName];
    }

    return el;
  }

  /**
   * Sanitizer rules
   */
  static get sanitize() {
    return {
      prompt: {},
      content: {
        br: true,
        p: true,
        b: true,
        i: true,
        a: {
          href: true
        },
        ul: true,
        ol: true,
        li: true,
        h1: true,
        h2: true,
        h3: true,
        h4: true,
        h5: true,
        h6: true
      }
    };
  }
}
