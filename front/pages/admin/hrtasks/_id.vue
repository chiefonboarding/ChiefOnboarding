<template>
  <v-col xs="12" mb="8" offset-mb="2" sm="10" offset-sm="1">
    <div>
      <v-row class="mb-4">
        <v-col sm="6">
          <h1 class="heading" style="margin-top: 10px;">
            {{ adminTask.name }}
          </h1>
        </v-col>
        <v-col sm="6">
          <v-btn v-if="$store.state.admin.fullAccess" :loading="removing" @click="removeAdminTask" style="float:right; margin-top: 14px; margin-right: 0px;" class="error">
            {{ $t('buttons.remove') }}
          </v-btn>
          <v-btn :loading="completing" @click="completeAdminTask" style="float:right; margin-top: 14px; margin-right: 0px;" color="secondary">
            <span v-if="!adminTask.completed">{{ $t('buttons.complete') }}</span><span v-else>{{ $t('buttons.reopen') }}</span>
          </v-btn>
        </v-col>
      </v-row>
      <v-container class="md pa-0">
        <v-row class="mb-4">
          <v-col xs="4">
            <v-card class="mb-4 first">
              <LoadingIcon :is-loading="loading" />
              <v-col v-if="!loading">
                <v-container grid-list-md fluid wrap>
                  <v-row wrap>
                    <AdminTaskForm
                      v-model="adminTask"
                      :errors="errors"
                      :new-hire-read-only="true"
                      :show-last-field="false"
                      :full-read-only="adminTask.completed"
                    />
                    <v-col xs="12" mt-2>
                      <v-btn
                        v-if="!adminTask.completed"
                        :loading="submittingForm"
                        @click="submitForm"
                        class="success"
                        style="float:right;margin-right:0px"
                      >
                        {{ $t('buttons.save') }}
                      </v-btn>
                    </v-col>
                  </v-row>
                </v-container>
              </v-col>
            </v-card>
          </v-col>
          <v-col xs="8">
            <v-card class="mb-4 second pa-3">
              <LoadingIcon :is-loading="loading" />
              <v-col v-if="!loading">
                <AdminTaskUpdates
                  v-model="adminTask"
                  :full-read-only="adminTask.completed"
                />
              </v-col>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </div>
  </v-col>
</template>

<script>
import AdminTaskForm from '@/components/admin/admintasks/Form'
import AdminTaskUpdates from '@/components/admin/admintasks/Updates'
export default {
  layout: 'admin',
  components: { AdminTaskForm, AdminTaskUpdates },
  data () {
    return {
      loading: true,
      submittingForm: false,
      completing: false,
      removing: false,
      errors: {},
      adminTask: {}
    }
  },
  mounted () {
    this.getAdminTask()
  },
  methods: {
    getAdminTask () {
      this.$hrtasks.get(this.$route.params.id).then((adminTask) => {
        this.adminTask = adminTask
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('hrTask.noTask'))
      }).finally(() => {
        this.loading = false
      })
    },
    submitForm () {
      this.submittingForm = true
      this.$hrtasks.update(this.$route.params.id, this.adminTask).then((task) => {
        this.$store.dispatch('showSnackbar', this.$t('hrTask.updated'))
      }).catch((error) => {
        this.errors = error
        this.$store.dispatch('showSnackbar', this.$t('hrTask.couldNotUpdate'))
      }).finally(() => {
        this.submittingForm = false
      })
    },
    removeAdminTask () {
      this.removing = true
      this.$hrtasks.remove(this.$route.params.id).then((data) => {
        this.$store.dispatch('showSnackbar', this.$t('hrTask.removed'))
        this.$router.push({ name: 'admin-hrtasks-mine' })
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('hrTask.couldNotRemove'))
      }).finally(() => {
        this.removing = false
      })
    },
    completeAdminTask () {
      this.completing = true
      this.$hrtasks.complete(this.$route.params.id).then((data) => {
        if (data.completed) {
          this.$store.dispatch('showSnackbar', this.$t('hrTask.closed'))
        } else {
          this.$store.dispatch('showSnackbar', this.$t('hrTask.reopened'))
        }
        this.adminTask.completed = data.completed
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('hrTask.couldNotReopen'))
      }).finally(() => {
        this.completing = false
      })
    }
  }
}
</script>

<style scoped>
.border-bottom {
  border-bottom: 1px solid rgb(228, 228, 228);
}
.second {
  margin-left: 10px;
}
.first {
  margin-right: 10px;
}
</style>
