export default function ({ store, route }) {
  if (route.name !== 'admin-templates-presets-id' && route.name !== 'admin-templates-presets-add') {
    store.commit('setRightSideBar', false)
    store.commit('toggleLeftDrawer', false)
  }
}
