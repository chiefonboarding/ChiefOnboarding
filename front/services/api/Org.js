import moment from 'moment'

export default (axios, store) => ({
  getOrganisation () {
    return axios.get('/api/org/').then(function (response) {
      moment.locale(response.data.language)
      axios.defaults.headers['Accept-Language'] = response.data.language
      if (response.data.language === 'nl') {
        response.data.locale = 'nl-nl'
      } else {
        response.data.locale = 'us-en'
      }
      store.commit('setOrg', response.data)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getBaseOrgInfo () {
    return axios.get('api/org/').then((response) => {
      moment.locale(response.data.language)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getDetailOrgInfo () {
    return axios.get('api/org/detail').then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getAdmins () {
    return axios.get('api/users/admin').then((response) => {
      store.commit('setAdmins', response.data)
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getAdmin () {
    return axios.get('api/users/admin/me').then((response) => {
      store.commit('setAdmin', response.data)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  removeAdmin (id) {
    return axios.delete(`api/users/admin/${id}`).then((response) => {
      store.commit('removeAdmin', id)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  addAdmin (payload) {
    return axios.post(`api/users/admin`, payload).then((response) => {
      store.commit('addAdmin', response.data)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getToken () {
    return axios.get(`api/settings/token/`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  updateGeneral (payload) {
    return axios.patch('api/org/detail', payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getOther () {
    return axios.get('api/settings/other/').then((response) => {
      store.commit('setOther', response.data)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  getEmails () {
    return axios.get('api/org/welcome_message').then((response) => {
      store.commit('setWelcomeMessages', response.data)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  updatePreboardingEmail (email, id) {
    return axios.post('/api/settings/email_without/', { 'text': email, id }).then((res) => {
      return true
    }).catch((e) => {
      store.dispatch('showSnackbar', 'Oh no. We couldn\'t change this template')
      return false
    })
  },
  updateNewHireEmail (email, id) {
    return axios.post('/api/settings/email/', { 'text': email, id }).then((res) => {
      return true
    }).catch((e) => {
      store.dispatch('showSnackbar', 'Oh no. We couldn\'t change this template')
      return false
    })
  },
  updateText (text, id) {
    return axios.post('/api/settings/text_message/', { text, id: 'id' }).then((res) => {
      return true
    }).catch((e) => {
      store.dispatch('showSnackbar', 'Oh no. We couldn\'t change this template')
      return false
    })
  },
  updateSlackMessage (text, id) {
    return axios.post('/api/settings/slack_message/', { text, id }).then((res) => {
      return true
    }).catch((e) => {
      store.dispatch('showSnackbar', 'Oh no. We couldn\'t change this slack message')
      return false
    })
  },
  updateSlackKnowMessage (text, id) {
    return axios.post('/api/settings/slack_know_message/', { text, id }).then((res) => {
      return true
    }).catch((e) => {
      store.dispatch('showSnackbar', 'Oh no. We couldn\'t change this slack message')
      return false
    })
  },
  getTags () {
    return axios.get('/api/org/tags').then((res) => {
      store.commit('setTags', res.data)
    }).catch((e) => {
      store.dispatch('showSnackbar', 'Oh no. We couldn\'t get the tags.')
      return false
    })
  },
  getCategories () {
    return axios.get('/api/category/').then((res) => {
      store.commit('setCategories', res.data)
    }).catch((e) => {
      store.dispatch('showSnackbar', 'Oh no. We couldn\'t get the resource categories.')
      return false
    })
  },
  getSlackChannels () {
    return axios.get('/api/slack/channels').then((res) => {
      store.commit('setSlackChannels', res.data)
    }).catch((e) => {
      store.dispatch('showSnackbar', 'Oh no. We couldn\'t get the Slack channels.')
      return false
    })
  },
  getPreSignedURL (payload) {
    return axios.post('/api/org/file', payload).then((res) => {
      return res.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  uploadToAWS (url, e) {
    const reader = new FileReader()
    return new Promise((resolve, reject) => {
      reader.onload = (file) => {
        return axios.put(url, reader.result, {
          headers: {
            'Content-Type': e.type
          }
        }).then((response) => {
          resolve(response)
        }).catch((error) => {
          reject(error)
        })
      }
      reader.readAsArrayBuffer(e)
    })
  },
  confirmUploaded (fileId) {
    return axios.put(`/api/org/file/${fileId}`).then((res) => {
      return res.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  confirmLogoUploaded (fileId) {
    return axios.put(`/api/org/logo/${fileId}`).then((res) => {
      return res.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  removeFile (fileId) {
    return axios.delete(`/api/org/file/${fileId}`).then((res) => {
      return res.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  }
})
