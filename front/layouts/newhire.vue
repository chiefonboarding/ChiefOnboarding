<template>
  <v-app>
    <div :class="{ 'show': isAdmin }" @click="goBack" class="hide">
      {{ $t('newHirePortal.preview') }}
    </div>
    <v-app-bar
      v-if="!loading"
      :color="$store.state.baseInfo.org.base_color"
      absolute
      class="top-bar"
      dark
    >
      <img :src="$store.state.baseInfo.org.logo" style="max-height: 40px; max-width: 100px; margin-right: 20px;">

      <v-toolbar-title>Welcome {{ $store.state.baseInfo.new_hire.first_name }}!</v-toolbar-title>

      <v-spacer />
      <v-toolbar-items>
        <v-btn
          :ripple="false"
          v-if="$store.state.baseInfo.new_hire.has_to_do"
          @click="$router.push({name: 'portal-todo'})"
          text
        >
          {{ $t('newHirePortal.todo') }}
        </v-btn>
        <v-btn
          v-if="$store.state.baseInfo.new_hire.has_resources"
          :ripple="false"
          @click="$router.push({name: 'portal-resources'})"
          text
        >
          {{ $t('newHirePortal.resources') }}
        </v-btn>
        <v-btn
          v-if="!loading"
          :ripple="false"
          @click="$router.push({name: 'portal-colleague'})"
          text
        >
          {{ $t('newHirePortal.colleagues') }}
        </v-btn>
      </v-toolbar-items>
      <v-btn @click="logout" icon>
        <v-icon>fas fa-sign-out-alt</v-icon>
      </v-btn>
    </v-app-bar>
    <div v-if="!loading && $store.state.showNewHireMenu" style="box-shadow: 0 2px 4px hsla(0,0%,74%,.3);" />
    <LoadingIcon :is-loading="loading" :color="this.$store.state.baseInfo.org.base_color" />
    <div v-if="!loading" style="margin-top: 100px">
      <nuxt />
    </div>
  </v-app>
</template>

<script>
import moment from 'moment'
export default {
  name: 'NewHireLayout',
  data: () => ({
    dialog: false,
    drawer: true,
    title: '',
    titleError: '',
    description: '',
    descriptionError: '',
    site: '',
    loading: true,
    tabs: 0,
    siteError: '',
    sites: [],
    items: [],
    select: '',
    search: ''
  }),
  computed: {
    isAdmin () {
      return this.$store.state.baseInfo !== undefined && 'employer' in this.$store.state.baseInfo && this.$store.state.baseInfo.employer
    }
  },
  mounted () {
    this.getBasicInfo()
  },
  methods: {
    logout () {
      this.$auth.logout().then((data) => {
        this.$router.push({ name: 'LoginPage' })
        this.$store.commit('setBaseInfo', {})
      }).catch(() => {})
    },
    getBasicInfo () {
      let code = null
      if ('code' in this.$route.query) {
        code = this.$route.query.code
        return
      }
      this.$newhirepart.getMe(code).then((data) => {
        this.$store.commit('setBaseInfo', data)
        moment.locale(data.language)
        this.$i18n.locale = data.language
        if (this.$router.currentRoute.name === 'portal') {
          if (data.new_hire.has_to_do) {
            this.$router.push({ name: 'portal-todo' })
          } else if (data.new_hire.has_resources) {
            this.$router.push({ name: 'portal-resource' })
          } else {
            this.$router.push({ name: 'portal-colleague' })
          }
        }
        this.loading = false
        if (this.$router.currentRoute.name === 'portal-resources') {
          this.tabs = this.$store.state.baseInfo.todos ? 2 : 1
        } else if (this.$router.currentRoute.name === 'portal-todo') {
          this.tabs = 1
        } else if (this.$router.currentRoute.name === 'portal-colleague') {
          this.tabs = 0
        }
      }).catch(() => {
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.genericError'))
      }).finally(() => {

      })
    },
    goBack () {
      this.$router.push({ name: 'admin-newhire' })
    }
  }
}
</script>

<style scoped>
.badge-back {
  width: min-content;
  padding: 15px 10px;
  margin-right: 10px;
}
.cube {
  border-radius: 50%;
  display: inline-block;
}
.badge-part {
  position: fixed;
  bottom: 0px;
  right: 0px;
}
.show {
  padding: 20px;
  background-color: #4c5f6b;
  color: white;
  display:block !important;
  font-size: 20px;
  cursor: pointer;
}
.hide {
  display: none;
}
.top-bar {
  box-shadow: 0px 2px 4px -1px rgba(0, 0, 0, 0), 0px 4px 5px 0px rgba(0, 0, 0, 0), 0px 1px 10px 0px rgba(0, 0, 0, 0.1)
}
</style>
