import MomentTimezone from 'moment-timezone'

export const state = () => ({
  token: '',
  org: '',
  admins: [],
  tags: [],
  integrations: [],
  categories: [],
  timezones: MomentTimezone.tz.names(),
  languages: [],
  selectedLanguage: { id: 'en', language: 'English' },
  welcomeMessages: {},
  slackPeople: [],
  slackChannels: [],
  other: {},
  books: [],
  cards: [],
  admin: {},
  baseInfo: { org: {}, new_hire: {} },
  rightSideBar: false,
  toggleLeftDrawer: false,
  showNewHireMenu: true,
  snackbar: false,
  snackbarText: '',
  refreshEditor: false
})

export const mutations = {
  setCSRFToken (state, token) { state.token = token },
  refreshEditor (state) { state.refreshEditor = !state.refreshEditor },
  setSnackbar (state, text) {
    state.snackbarText = text
    state.snackbar = !state.snackbar
  },
  setOrg (state, org) { state.org = org },
  setTags (state, tags) { state.tags = tags },
  setCategories (state, categories) { state.categories = categories },
  setSlackPeople (state, slackPeople) { state.slackPeople = slackPeople },
  setSlackChannels (state, channels) { state.slackChannels = channels },
  setRightSideBar (state, rightSideBar) { state.rightSideBar = rightSideBar },
  updateSelectedLanguage (state, language) { state.selectedLanguage = language },
  toggleLeftDrawer (state, toggleLeftDrawer) { state.toggleLeftDrawer = toggleLeftDrawer },
  hideNewHireMenu (state) { state.showNewHireMenu = false },
  setBaseInfo (state, baseInfo) { state.baseInfo = baseInfo },
  setCards (state, cards) { state.cards = cards },
  setWelcomeMessages (state, welcomeMessages) { state.welcomeMessages = welcomeMessages },
  setLanguages (state, languages) { state.languages = languages },
  setOther (state, other) { state.other = other },
  setAdmins (state, admins) {
    state.admins = admins
  },
  setAdmin (state, admin) {
    state.admin = admin
  },
  addStatusToResource (state, payload) {
    const status = state.books.find(a => parseInt(payload.id) === a.id).status
    if (status === payload.index - 1) {
      state.books.find(a => parseInt(payload.id) === a.id).status += 1
    }
  },
  setIntegrations (state, integrations) { state.integrations = integrations },
  setGoogleKey (state) { state.org.google_key = true },
  setGoogleLoginKey (state) { state.org.google_login_key = true }
}

export const actions = {
  showSnackbar ({ state, commit }, text) {
    if (state.snackbar) {
      commit('setSnackbar', text)
      setTimeout(() => {
        commit('setSnackbar', text)
      }, 100)
    } else {
      commit('setSnackbar', text)
    }
  }
}
