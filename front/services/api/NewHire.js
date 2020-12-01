
export default (axios, store) => ({
  getAll () {
    return axios.get('api/users/new_hire').then((response) => {
      response.data.forEach((one) => {
        if (one.completed_tasks !== 0 && one.total_tasks !== 0) {
          one.percentage = one.completed_tasks / one.total_tasks * 100
        } else {
          one.percentage = 0
        }
      })
      store.commit('newhires/setNewhires', response.data)
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  create (payload) {
    return axios.post('/api/users/new_hire', payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  update (id, payload) {
    return axios.put(`/api/users/new_hire/${id}`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  remove (id) {
    return axios.delete(`/api/users/new_hire/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  get (id) {
    return axios.get(`/api/users/new_hire/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getTasks (id) {
    return axios.get(`/api/users/new_hire/${id}/tasks`).then((response) => {
      response.data.to_do.forEach((item) => {
        item.to_do.completed = item.completed
        item.to_do.reminded = item.reminded
        item.to_do.task_id = item.id
      })
      response.data.resources.forEach((item) => {
        item.resource.step = item.step
        item.resource.task_id = item.id
      })
      response.data.preboarding.forEach((item) => {
        item.preboarding.completed = item.completed
        item.preboarding.task_id = item.id
      })
      response.data.to_do = response.data.to_do.map(a => a.to_do)
      response.data.resources = response.data.resources.map(a => a.resource)
      response.data.preboarding = response.data.preboarding.map(a => a.preboarding)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  addTask (id, payload) {
    return axios.post(`/api/users/new_hire/${id}/tasks`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  addSequence (id, payload) {
    return axios.post(`/api/users/new_hire/${id}/add_sequence`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getProgress (id) {
    return axios.get(`/api/users/new_hire/${id}/progress`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  checkPastSequenceItems (id, payload) {
    return axios.post(`/api/users/new_hire/${id}/check_past_sequence`, { sequence_ids: payload }).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  triggerItems (id, payload) {
    return axios.post(`/api/users/new_hire/${id}/trigger_conditions`, { condition_ids: payload }).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  deleteTask (id, payload) {
    return axios.put(`/api/users/new_hire/${id}/tasks`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getFilledInForms (id) {
    return axios.get(`/api/users/new_hire/${id}/forms`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getWelcomeMessages (id) {
    return axios.get(`/api/users/new_hire/${id}/welcome_messages`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getNotes (id) {
    return axios.get(`/api/users/new_hire/${id}/notes`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  postNote (id, payload) {
    return axios.post(`/api/users/new_hire/${id}/notes`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getAccess (id, integrationType) {
    return axios.post(`/api/users/new_hire/${id}/access`, { 'integration': integrationType }).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  downloadFile (id, uuid) {
    return axios.get(`/api/org/file/${id}/${uuid}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  scheduleAccess (id, payload) {
    return axios.put(`/api/users/new_hire/${id}/access`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  revokeAccess (id, payload) {
    return axios.put(`/api/users/new_hire/${id}/revoke_access`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  remindToDo (id, payload) {
    return axios.post(`/api/users/to_do/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  remindResource (id) {
    return axios.post(`/api/users/resource/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  reOpenToDo (id, payload) {
    return axios.put(`/api/users/to_do/${id}`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  reOpenResource (id, payload) {
    return axios.put(`/api/users/resource/${id}`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  sendPreboardingDetails (id, payload) {
    return axios.post(`api/users/new_hire/${id}/send_preboarding_details`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  sendLoginEmail (id) {
    return axios.post(`api/users/new_hire/${id}/send_login_email`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  changePreboardingOrder (id, payload) {
    return axios.post(`api/users/new_hire/${id}/change_preboarding_order`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  }
})
