export default (axios, store) => ({
  getMe () {
    return axios.get('api/new_hire/me').then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getToDo () {
    return axios.get('/api/new_hire/to_do').then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getBadges () {
    return axios.get('/api/new_hire/badges').then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getPreSignedURL (payload) {
    return axios.post('/api/new_hire/file', payload).then((res) => {
      return res.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  requestPass (payload) {
    return axios.post('api/password/reset', payload)
  },
  submitForm (taskId, data) {
    return axios.post(`/api/new_hire/to_do/${taskId}`, { data }).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  registerStep (resourceUserId, progress) {
    return axios.post(`/api/new_hire/change_step/${resourceUserId}`, { step: progress }).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getFileURL (fileId, token) {
    return axios.get(`/api/new_hire/file/${fileId}/${token}`).then((res) => {
      return res.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  confirmPass (payload) {
    return axios.post('api/password/reset/confirm', payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getResources () {
    return axios.get(`api/new_hire/resources`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getEmployees () {
    return axios.get(`api/new_hire/colleagues`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getResource (resourceId) {
    return axios.get(`api/new_hire/resource/${resourceId}`).then((response) => {
      const originalItems = JSON.parse(JSON.stringify(response.data))
      let item
      response.data.chapters.slice().reverse().forEach((i, index) => {
        if (i.parent_chapter !== null) {
          item = response.data.chapters.find(a => a.id === i.parent_chapter)
          if (!('chapters' in item)) {
            item.chapters = []
          }
          item.chapters.unshift(i)
        }
      })
      response.data.chapters = response.data.chapters.filter(a => a.parent_chapter === null)
      return { 'organized': response.data, 'original': originalItems }
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getCourse (resourceId) {
    return axios.get(`api/new_hire/course/${resourceId}`).then((response) => {
      const originalItems = JSON.parse(JSON.stringify(response.data))
      let item
      response.data.resource.chapters.slice().reverse().forEach((i, index) => {
        if (i.parent_chapter !== null) {
          item = response.data.resource.chapters.find(a => a.id === i.parent_chapter)
          if (!('resources' in item)) {
            item.resources = []
          }
          item.resources.unshift(i)
        }
      })
      response.data.resource.chapters = response.data.resource.chapters.filter(a => a.parent_chapter === null)
      return { 'organized': response.data, 'original': originalItems }
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  addCourseAnswer (resourceId, payload) {
    return axios.post(`api/new_hire/course/${resourceId}`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getIntroductions () {
    return axios.get(`api/new_hire/introductions`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getSlackToDoItem (id) {
    return axios.get(`api/new_hire/slack/to_do/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  submitSlackToDoForm (taskId, dataForm) {
    return axios.post(`/api/new_hire/slack/to_do/${taskId}`, { data: dataForm }).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  }
})
