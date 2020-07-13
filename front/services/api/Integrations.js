
export default (axios, store) => ({
  saveSlackIntegration (payload) {
    return axios.post('api/integrations/slack_token', payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  saveGoogleAPIKey (payload) {
    return axios.post('api/integrations/google', payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  saveGoogleLoginKey (payload) {
    return axios.post('api/integrations/google_login', payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  removeIntegration (id) {
    return axios.delete(`api/integrations/token/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  }
})
