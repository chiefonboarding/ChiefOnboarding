import Cookies from 'js-cookie'
import Appointment from '~/services/api/Appointment'
import Badge from '~/services/api/Badge'
import Employee from '~/services/api/Employee'
import HRTask from '~/services/api/HRTask'
import Introduction from '~/services/api/Introduction'
import NewHire from '~/services/api/NewHire'
import NewHirePart from '~/services/api/NewHirePart'
import NewHirePreboarding from '~/services/api/NewHirePreboarding'
import Org from '~/services/api/Org'
import Preboarding from '~/services/api/Preboarding'
import Resource from '~/services/api/Resource'
import Sequence from '~/services/api/Sequence'
import Todo from '~/services/api/Todo'
import User from '~/services/api/User'
import Integrations from '~/services/api/Integrations'

export default function ({ store, $axios, redirect }, inject) {
  $axios.interceptors.request.use(
    function (config) {
      config.headers['x-csrftoken'] = store.state.token
      config.headers['Content-Language'] = store.state.org.user_language
      delete config.headers.common.Authorization
      return config
    },
    function (error) {
      return Promise.reject(error)
    }
  )

  $axios.interceptors.response.use(
    function (response) {
      if (Cookies.get('csrftoken') !== undefined) { store.commit('setCSRFToken', Cookies.get('csrftoken')) }
      return response
    },
    function (error) {
      if (error.response.status === 403) {
        redirect('/')
        store.dispatch('showSnackbar', this.$t('login.authenticateYourself'))
      } else if (error.response.status === 500) {
        store.dispatch('showSnackbar', this.$t('login.error500'))
      } else if ('error' in error.response.data) {
        store.dispatch('showSnackbar', error.response.data.error)
      } else if ('detail' in error.response.data) {
        store.dispatch('showSnackbar', error.response.data.detail)
      }
      return Promise.reject(error)
    }
  )
  const a = Appointment($axios, store)
  inject('appointments', a)
  const b = Badge($axios, store)
  inject('badges', b)
  const e = Employee($axios, store)
  inject('employees', e)
  const hrtask = HRTask($axios, store)
  inject('hrtasks', hrtask)
  const u = Introduction($axios, store)
  inject('introductions', u)
  const newhire = NewHire($axios, store)
  inject('newhires', newhire)
  const newhirepreboarding = NewHirePreboarding($axios, store)
  inject('newhirepreboarding', newhirepreboarding)
  const org = Org($axios, store)
  inject('org', org)
  const preboarding = Preboarding($axios, store)
  inject('preboarding', preboarding)
  const resource = Resource($axios, store)
  inject('resources', resource)
  const sequence = Sequence($axios, store)
  inject('sequences', sequence)
  const todo = Todo($axios, store)
  inject('todos', todo)
  const newhirepart = NewHirePart($axios, store)
  inject('newhirepart', newhirepart)
  const intro = Introduction($axios, store)
  inject('intros', intro)
  const user = User($axios, store)
  inject('user', user)
  const int = Integrations($axios, store)
  inject('integrations', int)
}
