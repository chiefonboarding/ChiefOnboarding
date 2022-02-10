/**
 * @typedef {object} Form
 * @property {string} type - can be ordered or unordered
 * @property {Array} items - li elements
 */

/**
 * Form Tool for the Editor.js 2.0
 */
class Form {

  /**
   * Notify core that read-only mode is supported
   *
   * @returns {boolean}
   */
  static get isReadOnlySupported() {
    return true;
  }

  /**
   * Disallow to use native Enter behaviour
   *
   * @returns {boolean}
   * @public
   */
  static get enableLineBreaks() {
    return false;
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
      title: 'Form',
      icon: '<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-arrow-bar-to-right" width="24" height="24" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"> <path stroke="none" d="M0 0h24v24H0z" fill="none"></path> <line x1="14" y1="12" x2="4" y2="12"></line> <line x1="14" y1="12" x2="10" y2="16"></line> <line x1="14" y1="12" x2="10" y2="8"></line> <line x1="20" y1="4" x2="20" y2="20"></line> </svg>'
    };
  }

  /**
   * Render plugin`s main Element and fill it with saved data
   *
   * @param {object} params - tool constructor options
   * @param {formData} params.data - previously saved data
   * @param {object} params.config - user config for Tool
   * @param {object} params.api - Editor.js API
   * @param {boolean} params.readOnly - read-only mode flag
   */
  constructor({ data, config, api, readOnly }) {
    /**
     * HTML nodes
     *
     * @private
     */
    this._elements = {
      wrapper: null,
    };

    this.api = api;
    this.readOnly = readOnly;

    this.settings = [
      {
        name: 'input',
        title: this.api.i18n.t('Single line'),
        icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-type"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>',
        default: true,
      },
      {
        name: 'text',
        title: this.api.i18n.t('Multiple lines'),
        icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-align-justify"><line x1="21" y1="10" x2="3" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="3" y2="14"/><line x1="21" y1="18" x2="3" y2="18"/></svg>',
        default: false,
      },
      {
        name: 'check',
        title: this.api.i18n.t('Checking boxes'),
        icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-check"><polyline points="20 6 9 17 4 12"/></svg>',
        default: false,
      },
      {
        name: 'select',
        title: this.api.i18n.t('Selectbox'),
        icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-list"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>',
        default: false,
      },
      {
        name: 'upload',
        title: this.api.i18n.t('Upload file'),
        icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-file-plus"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>',
        default: false,
      },
    ];

    /**
     * Tool's data
     *
     * @type {FormData}
     */
    this._data = {
      type: this.settings.find((tune) => tune.default === true).name,
      text: "",
    };

    this.data = data;
  }

  /**
   * Returns wrapper with elemnt
   *
   * @returns {Element}
   * @public
   */
  render() {
    this._elements.wrapper = this.makeMainTag(this._data.type);

    // fill with data
    console.log(this._elements.wrapper)
    console.log(this._data.text.length)
    if (this._data.text != "") {
      console.log("got here")
      this._elements.wrapper.textContent = this._data.text
    }
    // if (this._data.text.length) {
    //   this._elements.wrapper.appendChild(this._make('p', this.CSS.item));
    // }

    console.log(this._elements.wrapper)
    return this._elements.wrapper;
  }

  /**
   * @returns {FormData}
   * @public
   */
  save() {
    console.log(this.data)
    return this.data;
  }

  /**
   * Sanitizer rules
   *
   * @returns {object}
   */
  static get sanitize() {
    return {
      type: {},
      text: {},
    };
  }

  /**
   * Settings
   *
   * @public
   * @returns {Element}
   */
  renderSettings() {
    const wrapper = this._make('div', [ this.CSS.settingsWrapper ], {});

    this.settings.forEach((item) => {
      const itemEl = this._make('div', this.CSS.settingsButton, {
        innerHTML: item.icon,
      });

      itemEl.addEventListener('click', () => {
        this.toggleTune(item.name);

        // clear other buttons
        const buttons = itemEl.parentNode.querySelectorAll('.' + this.CSS.settingsButton);

        Array.from(buttons).forEach((button) =>
          button.classList.remove(this.CSS.settingsButtonActive)
        );

        // mark active
        itemEl.classList.toggle(this.CSS.settingsButtonActive);
      });

      this.api.tooltip.onHover(itemEl, item.title, {
        placement: 'top',
        hidingDelay: 500,
      });

      if (this._data.type === item.name) {
        itemEl.classList.add(this.CSS.settingsButtonActive);
      }

      wrapper.appendChild(itemEl);
    });

    return wrapper;
  }


  /**
   * Creates main <p>
   *
   * @param {string} type - any of the form options
   * @returns {HTMLOListElement|HTMLUListElement}
   */
  makeMainTag(type){
    const typeClass = 'border-left';
    const tag = 'p';

    return this._make(tag, [this.CSS.baseBlock, this.CSS.wrapper, typeClass], {
      contentEditable: true,
    });
  }

  /**
   * Toggles Form type
   *
   * @param {string} type - any of the form options
   */
  toggleTune(type) {
    this._data.type = type;
  }

  /**
   * Styles
   *
   * @private
   */
  get CSS() {
    return {
      baseBlock: this.api.styles.block,
      wrapper: 'ce-paragraph',
      item: 'item',
      settingsWrapper: 'cdx-list-settings',
      settingsButton: this.api.styles.settingsButton,
      settingsButtonActive: this.api.styles.settingsButtonActive,
    };
  }

  /**
   * Form data setter
   *
   * @param {FormData} formData
   */
  set data(formData) {
    if (!formData) {
      formData = {};
    }

    this._data.type = formData.type || this.settings.find((tune) => tune.default === true).name;
    this._data.text = formData.text || '';

    const oldView = this._elements.wrapper;

    if (oldView) {
      oldView.parentNode.replaceChild(this.render(), oldView);
    }
  }

  /**
   * Return Form data
   *
   * @returns {FormData}
   */
  get data() {
    this._data.text = this._elements.wrapper.innerText
    console.log(this._data.text)
    console.log(this._data)

    return this._data;
  }

  /**
   * Helper for making Elements with attributes
   *
   * @param  {string} tagName           - new Element tag name
   * @param  {Array|string} classNames  - list or name of CSS classname(s)
   * @param  {object} attributes        - any attributes
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

}

