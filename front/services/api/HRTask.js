
export default (axios, store) => ({
  getAll () {
    return axios.get('/api/admin_tasks').then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getDoneTasks () {
    return axios.get('/api/admin_tasks/done').then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getDoneByUserTasks () {
    return axios.get('/api/admin_tasks/done_by_user').then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  create (payload) {
    if (payload.date === '' || payload.date === null) {
      delete payload.date
    }
    return axios.post('/api/admin_tasks', payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  get (id) {
    return axios.get(`/api/admin_tasks/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  update (id, payload) {
    if (payload.date === '' || payload.date === null) {
      delete payload.date
    }
    return axios.put(`/api/admin_tasks/${id}`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  addComment (id, payload) {
    return axios.post(`/api/admin_tasks/${id}/add_comment`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  remove (id) {
    return axios.delete(`/api/admin_tasks/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  complete (id) {
    return axios.get(`/api/admin_tasks/${id}/complete`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  }
})
