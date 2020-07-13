<template>
  <div>
    <LoadingIcon :is-loading="loading" />
    <div v-if="!loading">
      <p>{{ $t('employee.resourceInstr') }} </p>
      <h2 v-if="resources.data > 0">
        {{ $t('employee.noResources') }}
      </h2>
      <div v-for="i in resources" :key="i.id">
        <div>
          <v-chip @click:close="removeResource(i.id)" close style="margin-bottom: 5px">
            {{ i.name }}
          </v-chip>
        </div>
      </div>
      <v-btn @click="addResources=true">
        {{ $t('employee.addResources') }}
      </v-btn>

      <v-btn @click="addCollections=true">
        {{ $t('employee.addCollection') }}
      </v-btn>
      <SelectTemplates v-if="addCollections" v-model="addCollections" :items="this.$store.state.sequences.all" @clickedItem="addCollectionToEmployee" />
      <SelectTemplates v-if="addResources" v-model="addResources" :items="this.$store.state.resources.all" @clickedItem="addResourceToEmployee" />
      <v-divider class="ma-2" />
      <div v-if="value.slack_user_id" style="display:inline-block">
        <v-btn :loading="slack_loading" @click="revokeAccessSlack()" color="error">
          {{ $t('employee.removeSlackAccess') }}
        </v-btn>
      </div>
      <div v-else style="display:inline-block">
        <v-btn :loading="slack_loading" @click="giveAccessSlack()" color="success">
          {{ $t('employee.giveSlackAccess') }}
        </v-btn>
      </div>
      <div v-if="!value.has_pwd" style="display:inline-block">
        <v-btn :loading="portal_loading" @click="giveAccessPortal()" color="success">
          {{ $t('employee.givePortalAccess') }}
        </v-btn>
      </div>
    </div>
  </div>
</template>

<script>
import SelectTemplates from '@/components/general/SelectTemplates'
export default {
  components: {
    SelectTemplates
  },
  props: {
    value: {
      type: Object,
      required: true
    }
  },
  data: () => ({
    search: '',
    slack_loading: false,
    addResources: false,
    addCollections: false,
    addedResources: [],
    portal_loading: false,
    resources: [],
    loading: true
  }),
  watch: {
    value (value) {
      this.$emit('input', value)
    }
  },
  mounted () {
    this.getEmployeeResources()
  },
  methods: {
    giveAccessPortal () {
      this.portal_loading = true
      this.$employees.giveAccessPortal(this.value).then(() => {
        this.$store.commit('changeEmp', this.value, true)
        this.$store.commit('changeLoading', this.value, false)
      }).finally(() => {
        this.portal_loading = false
      })
    },
    giveAccessSlack () {
      this.slack_loading = true
      this.$employees.giveAccessSlack(this.value).then(() => {
        this.value.slack_user_id = 'set'
      }).finally(() => {
        this.slack_loading = false
      })
    },
    revokeAccessSlack () {
      this.slack_loading = true
      this.$employees.revokeAccessSlack(this.value).then(() => {
        this.value.slack_user_id = null
        this.slack_loading = false
      }).finally(() => {
        this.slack_loading = false
      })
    },
    addResourceToEmployee (value) {
      this.$employees.addResource(this.$route.params.id, value.id).then((data) => {
        this.resources = data
      })
    },
    addCollectionToEmployee (value) {
      this.$employees.addCollection(this.$route.params.id, value.id).then((data) => {
        this.$employees.getEmployee(this.$route.params.id).then((employee) => {
          this.value.tasks = employee.tasks
        }).catch((error) => {
          this.$store.dispatch('showSnackbar', this.$t('employee.addedTasksButNoNewHire'))
        })
      })
    },
    getEmployeeResources () {
      this.loading = true
      this.$employees.getResources(this.$route.params.id).then((data) => {
        this.resources = data
      }).finally(() => {
        this.loading = false
      })
    },
    removeResource (id) {
      this.$employees.removeResource(this.$route.params.id, id).then((data) => {
        this.resources = data
      })
    }
  }
}
</script>
