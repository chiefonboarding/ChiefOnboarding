<template>
  <v-row>
    <v-col sm="12" mb="6" offset-mb="3" md="8" offset-sm="2">
      <v-row class="my-4">
        <v-col sm="3">
          <h1 class="heading">
            {{ $t('admin.employees') }}
          </h1>
        </v-col>
        <v-col sm="9" class="mt-1 text-right">
          <v-btn v-if="$store.state.org.google_key" :loading="syncingGoogle" @click="syncGoogle">
            {{ $t('employee.syncWithGoogle') }}
          </v-btn>
          <v-btn v-if="$store.state.org.slack_key" :loading="syncingSlack" @click="syncSlack">
            {{ $t('employee.syncWithSlack') }}
          </v-btn>
          <v-btn @click="$router.push({name: 'admin-employee-add'})" color="success" style="margin-right: 0px">
            {{ $t('employee.add') }}
          </v-btn>
        </v-col>
      </v-row>
      <v-card class="mb-4">
        <template>
          <v-data-table
            :headers="headers"
            :items="$store.state.employees.all"
            :footer-props="{'items-per-page-options':[50, 100, -1]}"
            @click:row="goToPage"
          >
            <template v-slot:item.first_name="{ item }">
              {{ item.first_name }} {{ item.last_name }}
            </template>
            <template v-slot:item.has_pwd="{ item }" class="text-right">
              <v-btn
                :loading="item.email_loading"
                v-if="!item.has_pwd"
                @click.stop="giveAccessPortal(item)"
                color="success"
                small
                style="float:right; margin-left: 5px"
              >
                {{ $t('employee.sendLoginEmail') }}
              </v-btn>
              <div v-if="$store.state.org.slack_key" style="float:right">
                <div v-if="!item.slack_user_id">
                  <v-btn
                    :loading="item.slack_loading"
                    @click.stop="giveAccessSlack(item)"
                    color="success"
                    small
                  >
                    {{ $t('newhires.giveAccess') }}
                  </v-btn>
                </div>
                <div v-else>
                  <v-btn
                    :loading="item.slack_loading"
                    @click.stop="removeAccessSlack(item)"
                    color="info"
                    small
                  >
                    {{ $t('employee.hasAccess') }}
                  </v-btn>
                </div>
              </div>
            </template>
          </v-data-table>
        </template>
      </v-card>
    </v-col>
  </v-row>
</template>

<script>
export default {
  layout: 'admin',
  data: () => ({
    loading: false,
    syncingGoogle: false,
    syncingSlack: false,
    headers: [
      { text: 'Name', value: 'first_name' },
      { value: 'has_pwd' }
    ]
  }),
  mounted () {
    this.getEmployees()
  },
  methods: {
    getEmployees () {
      this.loading = true
      this.$employees.getAll().finally(() => {
        this.loading = false
      })
    },
    giveAccessPortal (employee) {
      this.$store.commit('employees/setEmailAccessLoading', employee.id)
      this.$employees.giveAccessPortal(employee).then(() => {
        this.$store.commit('employees/setEmailAccessLoading', employee.id)
        this.$store.commit('employees/setHasPassword', employee, false)
      })
    },
    giveAccessSlack (employee) {
      this.$store.commit('employees/setSlackLoading', employee.id)
      employee.slack_loading = true
      this.$employees.giveAccessSlack(employee).then(() => {
        this.$store.commit('employees/setSlackId', employee.id)
        this.$store.commit('employees/setSlackLoading', employee.id)
      })
    },
    removeAccessSlack (employee) {
      this.$store.commit('employees/setSlackLoading', employee.id)
      this.$employees.revokeAccessSlack(employee).then(() => {
        this.$store.commit('employees/unsetSlackId', employee.id)
        this.$store.commit('employees/setSlackLoading', employee.id)
      })
    },
    syncGoogle () {
      this.syncingGoogle = true
      this.$employees.syncGoogle().then(() => {
        this.$store.dispatch('showSnackbar', this.$t('employee.googleSynced'))
        this.syncingGoogle = false
        this.getEmployees()
      })
    },
    syncSlack () {
      this.syncingSlack = true
      this.$employees.syncSlack().then(() => {
        this.$store.dispatch('showSnackbar', this.$t('employee.slackSynced'))
        this.syncingSlack = false
        this.getEmployees()
      })
    },
    goToPage (item, row) {
      this.$router.push({ name: 'admin-employee-id', params: { id: item.id } })
    }
  }
}
</script>
