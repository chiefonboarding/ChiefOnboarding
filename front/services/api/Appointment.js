export default (axios, store) => ({
  getAll () {
    return axios.get('api/appointment').then((response) => {
      store.commit('appointments/setAppointments', response.data)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  get (id) {
    return axios.get(`api/appointment/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  update (id, payload) {
    return axios.put(`api/appointment/${id}`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  create (payload) {
    return axios.post(`api/appointment`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  remove (id) {
    return axios.delete(`api/appointment/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  duplicate (id) {
    return axios.post(`api/appointment/${id}/duplicate`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  }
})
