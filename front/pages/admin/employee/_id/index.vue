<template>
  <v-row>
    <v-col sm="12" mb="8" offset-mb="2" md="10" offset-sm="1">
      <div>
        <v-row class="mb-4">
          <v-col sm="6">
            <h1 class="heading" style="margin-top: 10px;">
              {{ employee.first_name }} {{ employee.last_name }}
            </h1>
          </v-col>
          <v-col sm="6">
            <v-btn :loading="removing" @click="removeEmployee" style="float:right; margin-top: 14px; margin-right: 0px;" class="error">
              {{ $t('buttons.remove') }}
            </v-btn>
          </v-col>
        </v-row>
        <v-container class="md pa-0">
          <v-row class="mb-4">
            <v-col sm="6">
              <v-card class="mb-4 first">
                <LoadingIcon :is-loading="loading" />
                <v-col v-if="!loading">
                  <v-container grid-list-md fluid wrap>
                    <v-row wrap>
                      <EmployeeForm v-model="employee" :errors="errors" />
                      <v-col sm="12" mt-2>
                        <v-btn :loading="submittingForm" @click="submitForm" class="success" style="float:right">
                          {{ $t('buttons.save') }}
                        </v-btn>
                      </v-col>
                    </v-row>
                  </v-container>
                </v-col>
              </v-card>
            </v-col>
            <v-col sm="6">
              <v-card class="mb-4 second pa-3">
                <LoadingIcon :is-loading="loading" />
                <v-col v-if="!loading">
                  <EmployeeResources v-model="employee" />
                </v-col>
              </v-card>
            </v-col>
          </v-row>
        </v-container>
      </div>
    </v-col>
  </v-row>
</template>

<script>
import { mapState } from 'vuex'
import EmployeeForm from '@/components/admin/employee/Form'
import EmployeeResources from '@/components/admin/employee/EmployeeResources'
export default {
  layout: 'admin',
  components: { EmployeeForm, EmployeeResources },
  data: () => ({
    loading: true,
    removing: false,
    submittingForm: false,
    headers: [
      { text: 'Name', value: 'name' },
      { }
    ],
    errors: {},
    employee: {}
  }),
  computed: mapState([
    'employees'
  ]),
  watch: {
    '$route' (to, from) {
      this.getEmployee()
    }
  },
  mounted () {
    this.getEmployee()
    this.$resources.getAll()
  },
  methods: {
    getEmployee () {
      return this.$employees.getEmployee(this.$route.params.id).then((employee) => {
        this.employee = employee
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('employee.NotExists'))
      }).finally(() => {
        this.loading = false
      })
    },
    submitForm () {
      this.submittingForm = true
      this.$employees.submitForm(this.$route.params.id, this.employee).then((employee) => {
        this.$store.dispatch('showSnackbar', this.$t('employee.updated'))
      }).catch((error) => {
        this.errors = error
        this.$store.dispatch('showSnackbar', this.$t('employee.couldNotUpdate'))
      }).finally(() => {
        this.submittingForm = false
      })
    },
    removeEmployee () {
      this.removing = true
      this.$employees.remove(this.$route.params.id).then((data) => {
        this.$store.dispatch('showSnackbar', this.$t('employee.removed'))
        this.$router.push({ name: 'admin-employee' })
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('employee.couldNotBeRemoved'))
      }).finally(() => {
        this.removing = false
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
