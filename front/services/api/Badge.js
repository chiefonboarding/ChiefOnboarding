
export default (axios, store) => ({
  getAll () {
    return axios.get('api/badges').then((response) => {
      store.commit('badges/setAllBadges', response.data)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  get (id) {
    return axios.get(`api/badges/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  update (id, payload) {
    return axios.put(`api/badges/${id}`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  duplicate (id) {
    return axios.post(`api/badges/${id}/duplicate`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  create (payload) {
    return axios.post(`api/badges`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  remove (id) {
    return axios.delete(`api/badges/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  }
})
