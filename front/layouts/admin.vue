<template>
  <v-app>
    <v-navigation-drawer
      v-model="drawer"
      :clipped="$vuetify.breakpoint.lgAndUp"
      :mini-variant="$store.state.toggleLeftDrawer"
      :width="230"
      fixed
      app
    >
      <v-list dense>
        <template v-for="item in items">
          <v-list-group
            v-if="item.children"
            :key="item.text"
            v-model="item.model"
            :prepend-icon="item.model ? item.icon : item['icon-alt']"
            append-icon=""
          >
            <v-list-item slot="activator">
              <v-list-item-content @click="goTo(item)">
                <v-list-item-title>
                  {{ item.text }}
                </v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            <v-list-item
              v-for="(child, i) in item.children"
              :key="i"
              @click="goTo(child)"
            >
              <v-list-item-content>
                <v-list-item-title>
                  {{ child.text }}
                </v-list-item-title>
              </v-list-item-content>
            </v-list-item>
          </v-list-group>
          <v-list-item
            v-else
            :key="item.text"
            @click="goTo(item)"
            class="theme--light"
          >
            <v-list-item-action>
              <span>
                <v-icon v-if="item.model" color="primary">{{ item.icon }}</v-icon>
                <v-icon v-else>{{ item.icon }}</v-icon>
              </span>
            </v-list-item-action>
            <v-list-item-content style="margin-left: 16px;">
              <v-list-item-title>
                {{ item.text }}
              </v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </template>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar
      :clipped-left="$vuetify.breakpoint.lgAndUp"
      :clipped-right="$vuetify.breakpoint.lgAndUp"
      color="#4C5F6B"
      dark
      app
      fixed
    >
      <v-toolbar-title style="width: 300px;" class="ml-0 pl-3">
        <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
        <span class="hidden-sm-and-down" style="top: 3px;position: relative;">{{ $t('admin.portal') }}</span>
      </v-toolbar-title>
      <v-autocomplete
        v-model="select"
        :items="allItems"
        :placeholder="$t('admin.search')"
        class="mx-3"
        text
        return-object
        hide-no-data
        clearable
        item-text="name"
        solo-inverted
        style="top: 15px;"
      >
        <template
          slot="item"
          slot-scope="{ item }"
        >
          <v-list-item-content>
            <v-list-item-title v-text="item.name" />
            <v-list-item-subtitle class="search-tags">
              <v-chip v-for="(i, index) in item.tags" :key="item.name + '' + index" label small class="search-tag">
                {{ i }}
              </v-chip>
            </v-list-item-subtitle>
          </v-list-item-content>
          <v-list-item-action>
            <v-chip label color="secondary" text-color="white" small>
              {{ getType(item) }}
            </v-chip>
          </v-list-item-action>
        </template>
      </v-autocomplete>
      <v-spacer />
      <v-btn @click="goToUpdates" icon>
        <v-badge :value="showBadge" dot overlap>
          <v-icon>fas fa-bell</v-icon>
        </v-badge>
      </v-btn>
      <v-btn @click="logout" icon>
        <v-icon>fas fa-sign-out-alt</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main v-if="loading">
      <v-container fluid fill-height>
        <v-row justify="center">
          <LoadingIcon :is-loading="loading" />
        </v-row>
      </v-container>
    </v-main>
    <v-main v-else>
      <v-container>
        <v-row>
          <router-view />
        </v-row>
      </v-container>
    </v-main>

    <div v-if="!loading">
      <RightSideBar />
      <SnackbarNot />
    </div>
  </v-app>
</template>

<script>
import moment from 'moment'
import SnackbarNot from '~/components/general/SnackbarNotification'
import RightSideBar from '~/components/admin/sequence/RightSideBar'

export default {
  name: 'DashboardLayout',
  components: { SnackbarNot, RightSideBar },
  data: vm => ({
    dialog: false,
    drawer: true,
    title: '',
    titleError: '',
    description: '',
    descriptionError: '',
    site: '',
    loading: true,
    addingAllResourcesToAdmin: false,
    ready: 0,
    siteError: '',
    sites: [],
    items: [],
    select: '',
    search: '',
    searchItems: [
      { type: 'to_do', text: vm.$t('templates.todo'), url: 'admin-templates-todos-id' },
      { type: 'resource', text: vm.$t('templates.resource'), url: 'admin-templates-resources-id' },
      { type: 'appointment', text: vm.$t('templates.appointment'), url: 'admin-templates-appointments-id' },
      { type: 'introduction', text: vm.$t('templates.intro'), url: 'admin-templates-intros-id' },
      { type: 'badge', text: vm.$t('templates.badge'), url: 'admin-templates-badges-id' },
      { type: 'new_hire', text: vm.$t('sequence.newHire'), url: 'admin-newhire-id' },
      { type: 'sequence', text: vm.$t('templates.sequence'), url: 'admin-templates-presets-id' },
      { type: 'preboarding', text: vm.$t('templates.preboarding'), url: 'admin-templates-preboarding-id' },
      { type: 'employee', text: vm.$t('sequence.employee'), url: 'admin-employee-id' }
    ]
  }),
  computed: {
    allItems () {
      return this.$store.state.todos.all.concat(this.$store.state.resources.all).concat(this.$store.state.intros.all).concat(this.$store.state.sequences.all).concat(this.$store.state.badges.all).concat(this.$store.state.preboarding.all).concat(this.$store.state.appointments.all).concat(this.$store.state.newhires.all).concat(this.$store.state.employees.all)
    },
    showBadge () {
      return moment(this.$store.state.admin.seen_updates).isBefore('2021-04-02')
    }
  },
  watch: {
    select (value) {
      if (value === undefined) { return }
      const id = value.id
      const item = this.searchItems.find(a => a.type === value.search_type)
      this.$router.push({ name: item.url, params: { id } })
    },
    ready (value) {
      if (
        value === 11 ||
        (value === 3 && 'is_admin' in this.$store.state.admin && this.$store.state.admin.is_admin === false)
      ) {
        this.loading = false
      }
    }
  },
  mounted () {
    this.$org.getDetailOrgInfo().then((data) => {
      this.$i18n.locale = data.language
      this.$store.commit('setOrg', data)
      this.$store.commit('setLanguages', [
        { id: 'en', language: this.$t('forms.english') },
        { id: 'nl', language: this.$t('forms.dutch') },
        { id: 'fr', language: this.$t('forms.french') },
        { id: 'de', language: this.$t('forms.deutsch') },
        { id: 'tr', language: this.$t('forms.turkish') },
        { id: 'pt', language: this.$t('forms.portuguese') },
        { id: 'es', language: this.$t('forms.spanish') },
        { id: 'jp', language: this.$t('forms.japanese') }
      ])
      moment.locale(data.language)
      this.ready++
      this.$org.getAdmin().then((data) => {
        this.$newhires.getAll().finally(() => { this.ready++ })
        if (this.$store.state.admin.role === 1) {
          this.$org.getTags().finally(() => { this.ready++ })
          this.$org.getSlackChannels().finally(() => { this.ready++ })
          this.$employees.getAll().finally(() => { this.ready++ })
          this.$todos.getAll().finally(() => { this.ready++ })
          this.$resources.getAll().finally(() => { this.ready++ })
          this.$appointments.getAll().finally(() => { this.ready++ })
          this.$intros.getAll().finally(() => { this.ready++ })
          this.$sequences.getAll().finally(() => { this.ready++ })
          this.$preboarding.getAll().finally(() => { this.ready++ })
          this.$badges.getAll().finally(() => { this.ready++ })
          this.$org.getAdmins().finally(() => { this.ready++ })
          this.items = [
            {
              icon: 'fas fa-users',
              'icon-alt': 'fas fa-users',
              text: this.$t('admin.people'),
              model: true,
              children: [
                { text: this.$t('admin.newHires'), to: 'admin-newhire' },
                { text: this.$t('admin.employees'), to: 'admin-employee' }
              ]
            },
            { icon: 'fas fa-project-diagram', text: this.$t('admin.sequences'), to: 'admin-templates-presets', 'icon-alt': 'fas fa-project-diagram' },
            {
              icon: 'fas fa-cube',
              'icon-alt': 'fas fa-cube',
              text: this.$t('admin.templates'),
              model: false,
              children: [
                { text: this.$t('admin.todo'), to: 'admin-templates-todos' },
                { text: this.$t('admin.resources'), to: 'admin-templates-resources' },
                { text: this.$t('admin.introductions'), to: 'admin-templates-intros' },
                { text: this.$t('admin.appointments'), to: 'admin-templates-appointments' },
                { text: this.$t('admin.preboarding'), to: 'admin-templates-preboarding' },
                { text: this.$t('admin.badges'), to: 'admin-templates-badges' }
              ]
            },
            { icon: 'fas fa-tasks',
              'icon-alt': 'fas fa-tasks',
              text: this.$t('admin.yourTasks'),
              model: false,
              children: [
                { text: this.$t('admin.yourTasks'), to: 'admin-hrtasks-mine' },
                { text: this.$t('admin.allTasks'), to: 'admin-hrtasks-all' }
              ] },
            {
              icon: 'fas fa-cog',
              'icon-alt': 'fas fa-cog',
              text: this.$t('admin.settings'),
              model: false,
              children: [
                { text: this.$t('admin.global'), to: 'admin-settings-global' },
                { text: this.$t('admin.personal'), to: 'admin-settings-personal' },
                { text: this.$t('admin.integrations'), to: 'admin-settings-integrations' },
                { text: this.$t('settings.admin'), to: 'admin-settings-admin' }
              ]
            }
          ]
        } else {
          // this.$employees.getAll().finally(() => { this.ready++ })
          this.$org.getAdmins().finally(() => { this.ready++ })
          this.items = [{
            icon: 'fas fa-tasks',
            'icon-alt': 'fas fa-tasks',
            text: this.$t('admin.yourTasks'),
            model: false,
            children: [
              { text: this.$t('admin.yourTasks'), to: 'admin-hrtasks-mine' },
              { text: this.$t('admin.allTasks'), to: 'admin-hrtasks-all' }
            ]
          }]
          this.loading = false
          this.$router.push({ name: 'admin-hrtasks-all' })
        }
      })
    })
    if (this.$router.currentRoute.name === 'admin') {
      this.$router.push({ name: 'admin-newhire' })
    }
    /* eslint no-extend-native: 0 */
    String.prototype.insert = function (index, string) {
      if (index > 0) { return this.substring(0, index) + string + this.substring(index, this.length) } else { return string + this }
    }
  },
  methods: {
    logout () {
      this.$auth.logout().then((data) => {
        this.$router.push({ name: 'index' })
      })
    },
    getType (item) {
      if (this.searchItems.find(a => a.type === item.search_type) !== undefined) {
        return this.searchItems.find(a => a.type === item.search_type).text
      }
      return ''
    },
    goTo (item) {
      if ('to' in item) {
        this.$router.push({ name: item.to })
      } else if (item.text !== 'Sequences') {
        this.$router.push({ name: item.children[0].to })
      }
      if (item.text === 'Sequences') {
        this.items.forEach((one) => {
          one.model = false
        })
      }
    },
    goToUpdates () {
      this.$router.push({ name: 'admin-updates' })
    }
  }
}
</script>

<style>
.search-tags .search-tag:nth-of-type(1) {
  margin-left: 0px;
}
</style>
