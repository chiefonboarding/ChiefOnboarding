
export default (axios, store) => ({
  getAll () {
    return axios.get('api/resource').then((response) => {
      store.commit('resources/setAllResources', response.data)
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  get (id) {
    return axios.get(`api/resource/${id}`).then((response) => {
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
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  create (payload) {
    return axios.post('api/resource', payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  update (id, payload) {
    return axios.put(`api/resource/${id}`, payload).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  },
  remove (id) {
    return axios.delete(`api/resource/${id}`).then((response) => {
      return response.data
    }).catch((error) => {
      return Promise.reject(error.response.data)
    })
  }
})
