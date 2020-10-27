export default {
  mode: 'spa',
  telemetry: false,
  /*
  ** Headers of the page
  */
  head: {
    titleTemplate: '%s - ' + process.env.npm_package_name,
    title: process.env.npm_package_name || '',
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { hid: 'description', name: 'description', content: process.env.npm_package_description || '' }
    ],
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
      {
        rel: 'stylesheet',
        href:
          'https://fonts.googleapis.com/css?family=Roboto:300,400,500,700|Material+Icons'
      },
      {
        rel: 'stylesheet',
        href:
          'https://use.fontawesome.com/releases/v5.0.13/css/all.css'
      }
    ]
  },
  /*
  ** Customize the progress-bar color
  */
  loading: { color: '#ffbb42' },
  /*
  ** Global CSS
  */
  css: [
    '~/assets/main.css'
  ],
  /*
  ** Plugins to load before mounting the App
  */
  plugins: [
    // '@plugins/vuetify',
    '@plugins/i18n',
    '@plugins/axios',
    '@plugins/global',
    '@plugins/fontawesome',
    '@plugins/dragdrop'
  ],
  router: {
    middleware: ['router'],
    mode: 'hash'
  },
  /*
  ** Nuxt.js dev-modules
  */
  buildModules: [
    // Doc: https://github.com/nuxt-community/eslint-module
    '@nuxtjs/eslint-module',
    '@nuxtjs/vuetify'
  ],
  /*
  ** Nuxt.js modules
  */
  modules: [
    // Doc: https://axios.nuxtjs.org/usage
    '@nuxtjs/axios',
    '@nuxtjs/auth',
    '@nuxtjs/eslint-module'
  ],
  /*
  ** Axios module configuration
  ** See https://axios.nuxtjs.org/options
  */
  axios: {
    baseURL: process.env.BASE_URL || 'http://0.0.0.0:8000',
    credentials: true
  },

  auth: {
    strategies: {
      local: {
        endpoints: {
          login: { url: '/api/auth/login/', method: 'post', propertyName: 'token' },
          logout: { url: '/api/auth/logout/', method: 'post' },
          user: { url: '/api/auth/user/', method: 'get', propertyName: 'user' }
        }
        // tokenRequired: true,
        // tokenType: 'bearer'
      }
    }
  },
  /*
  ** vuetify module configuration
  ** https://github.com/nuxt-community/vuetify-module
  */
  vuetify: {
    customVariables: ['~/assets/variables.scss'],
    theme: {
      themes: {
        light: {
          primary: '#ffbb42',
          secondary: '#67aaf9',
          accent: '#67aaf9',
          error: '#e74c3c',
          action: '#23DB2A',
          success: '#4c5f6b',
          dark: '#4C5F6B'
        }
      }
    }
  },
  /*
  ** Build configuration
  */
  build: {
    /*
    ** You can extend webpack config here
    */
    extend (config, ctx) {
    }
  },
  generate: {
    dir: '../back/static/js/'
  }
}
