module.exports = {
  root: true,
  env: {
    browser: true,
    node: true
  },
  parserOptions: {
    parser: 'babel-eslint'
  },
  extends: [
    '@nuxtjs',
    'plugin:nuxt/recommended'
  ],
  globals: {
    "handle-callback-err": "off"
  },
  // add your custom rules here
  rules: {
    "no-return-assign": "off",
    "import/default": "off",
    "handle-callback-err": "off",
    "no-console": "off",
    "vue/require-prop-type-constructor": "off"
  }
}
