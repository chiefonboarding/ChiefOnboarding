
export default (axios, store) => ({
  getAll () {
    return axios.get('api/sequences').then((response) => {
      store.commit('sequences/setAllSequences', response.data)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  get (id) {
    return axios.get(`api/sequences/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  update (id, payload) {
    return axios.put(`api/sequences/${id}`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  create (payload) {
    return axios.post(`api/sequences`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  remove (id) {
    return axios.delete(`api/sequences/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  createExternalMessage (payload) {
    return axios.post(`api/external_messages`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  createAdminTask (payload) {
    if (payload.date === '') {
      delete payload.date
    }
    return axios.post(`api/sequence/admin_task`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  duplicate (id) {
    return axios.post(`api/${id}/duplicate`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  }
})
