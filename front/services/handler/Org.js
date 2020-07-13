import store from '../../store'

export default {
  getAdmins () {
    return this.$org.getAdmins().then((admins) => {
      store.commit('setAdmins', admins)
    }).catch(function (error) {
      return Promise.reject(error)
    })
  },
  removeAdmin (id) {
    return this.$org.removeAdmin(id).then((data) => {
      store.commit('removeAdmin', id)
      return true
    }).catch(function (error) {
      return Promise.reject(error)
    })
  },
  addAdmin (payload) {
    return this.$org.addAdmin(payload).then((data) => {
      store.commit('addAdmin', data)
      return true
    }).catch(function (error) {
      return Promise.reject(error)
    })
  },
  getOther () {
    return this.$org.getOther().then((data) => {
      store.commit('setOther', data)
      return true
    }).catch(function (error) {
      return Promise.reject(error)
    })
  }
}
