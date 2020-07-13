export const state = () => ({
  all: []
})

export const mutations = {
  setAppointments (state, all) {
    state.all = all
  }
}
