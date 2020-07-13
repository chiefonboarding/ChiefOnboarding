export default (axios, store) => ({
  getAll () {
    return axios.get('api/users/employee').then((response) => {
      store.commit('employees/setAllEmployees', response.data)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getEmployee (id) {
    return axios.get(`api/users/employee/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  create (payload) {
    return axios.post('/api/users/employee', payload).then((response) => {
      return response.data
    }).catch(function (error) {
      return Promise.reject(error.response.data)
    })
  },
  remove (id) {
    return axios.delete(`/api/users/employee/${id}`).then((response) => {
      return true
    }).catch(function (error) {
      return Promise.reject(error.response.data)
    })
  },
  giveAccessSlack (employee) {
    return axios.post(`/api/users/employee/${employee.id}/give_slack_access`).then((response) => {
      store.dispatch('showSnackbar', 'This person has received a Slack message with more information.')
      return response.data
    }).catch((error) => {
      store.dispatch('showSnackbar', error.response.data.error)
      return Promise.reject(error.response.data)
    })
  },
  revokeAccessSlack (employee) {
    return axios.delete(`/api/users/employee/${employee.id}/revoke_slack_access`).then((response) => {
      store.dispatch('showSnackbar', 'This person has no longer access to our bot in Slack')
      return response.data
    }).catch((error) => {
      store.dispatch('showSnackbar', error.response.data.error)
      return Promise.reject(error.response.data)
    })
  },
  giveAccessPortal (employee) {
    return axios.post(`/api/users/employee/${employee.id}/send_employee_email`).then((response) => {
      store.dispatch('showSnackbar', 'We have send an email with his/her login credentials.')
      return response.data
    }).catch((error) => {
      store.dispatch('showSnackbar', error.response.data.error)
      return Promise.reject(error.response.data)
    })
  },
  addResource (employeeId, resourceId) {
    return axios.post(`/api/users/employee/${employeeId}/add_resource`, { 'resource': resourceId }).then((response) => {
      store.dispatch('showSnackbar', 'Resource has been added.')
      return response.data
    }).catch((error) => {
      store.dispatch('showSnackbar', 'We couldn\'t add this resource to this employee. Please try again.')
    })
  },
  getResources (employeeId) {
    return axios.get(`/api/users/employee/${employeeId}/get_resources`).then((response) => {
      return response.data
    }).catch((error) => {
      store.dispatch('showSnackbar', error.response.data.error)
      return Promise.reject(error.response.data)
    })
  },
  addCollection (employeeId, collectionID) {
    return axios.post(`/api/users/employee/${employeeId}/add_resource`, { 'sequence': collectionID }).then((response) => {
      store.dispatch('showSnackbar', 'Resource has been added.')
      return response.data
    }).catch((error) => {
      store.dispatch('showSnackbar', 'We couldn\'t add this resource to this employee. Please try again.')
    })
  },
  removeResource (id, resourceId) {
    return axios.put(`/api/users/employee/${id}/delete_resource`, { 'resource': resourceId }).then((response) => {
      store.dispatch('showSnackbar', 'Resource has been removed.')
      return response.data
    }).catch((error) => {
      store.dispatch('showSnackbar', 'We couldn\'t remove this resource from this employee. Please try again.')
    })
  },
  submitForm (id, payload) {
    return axios.put(`/api/users/employee/${id}`, payload).then((response) => {
      return true
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  syncSlack () {
    return axios.post('/api/users/employee/sync_slack').then((response) => {
      return true
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  syncGoogle () {
    return axios.post('/api/users/employee/sync_google').then((response) => {
      return true
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  }
})
