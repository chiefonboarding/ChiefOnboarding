export const state = () => ({
  all: []
})

export const mutations = {
  setAllEmployees (state, all) {
    state.all = all
  },
  setSlackLoading (state, id) {
    const emp = state.all.find(a => a.id === id)
    if (emp) {
      emp.slack_loading = !emp.slack_loading
    }
  },
  setEmailAccessLoading (state, id) {
    const emp = state.all.find(a => a.id === id)
    if (emp) {
      emp.email_loading = !emp.email_loading
    }
  },
  setSlackId (state, id) {
    const emp = state.all.find(a => a.id === id)
    if (emp) {
      emp.slack_user_id = 'set'
    }
  },
  setHasPassword (state, id) {
    const emp = state.all.find(a => a.id === id)
    if (emp) {
      emp.has_psw = true
    }
  },
  unsetSlackId (state, id) {
    const emp = state.all.find(a => a.id === id)
    if (emp) {
      emp.slack_user_id = null
    }
  }
}
