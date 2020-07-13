export default (axios, store) => ({
  getPreboardingItems () {
    return axios.get('/api/new_hire/preboarding').then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getOrg () {
    return axios.get(`/api_new_hire/org/`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  authenticate (authToken) {
    return axios.post(`/api/new_hire/authenticate`, { 'token': authToken }).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  uploadFile (payload, url) {
    return axios.post(url, payload, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      responseType: 'json'
    }).then((res) => {
      return res.data
    }).catch((e) => {
      return Promise.reject(e.response.data)
    })
  },
  sendFormBack (sendData) {
    return axios.post('/api/new_hire/preboarding', sendData).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  sendFormBackTodo (sendData) {
    return axios.post('/api_new_hire/send_todo_form/', { 'data': sendData }).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  todoDone () {
    return axios.get('/api_new_hire/preboarding_todo_done/').then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  }
})
