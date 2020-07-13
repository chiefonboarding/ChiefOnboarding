export const state = () => ({
  all: []
})

export const mutations = {
  setTodos (state, all) {
    state.all = all
  }
}
