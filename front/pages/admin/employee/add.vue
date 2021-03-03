<template>
  <v-row>
    <v-col sm="12" mb="8" offset-mb="2" md="10" offset-sm="1">
      <div>
        <v-row class="mb-4">
          <v-col sm="6">
            <h1 class="heading" style="margin-top: 10px;">
              {{ employee.name }}
            </h1>
          </v-col>
        </v-row>
        <v-container class="md pa-0">
          <v-row class="mb-4">
            <v-col sm="6" offset-sm="3">
              <v-card class="mb-4 first">
                <LoadingIcon :is-loading="loading" />
                <v-col v-if="!loading">
                  <v-container grid-list-md fluid wrap>
                    <v-row wrap>
                      <EmployeeForm v-model="employee" :errors="errors" />
                      <v-col sm="12" mt-2>
                        <v-btn :loading="submittingForm" @click="submitForm" class="success" style="float:right">
                          {{ $t('buttons.submit') }}
                        </v-btn>
                      </v-col>
                    </v-row>
                  </v-container>
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
export default {
  layout: 'admin',
  components: { EmployeeForm },
  data: () => ({
    loading: false,
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
    this.$resources.getAll()
  },
  methods: {
    submitForm () {
      this.submittingForm = true
      this.$employees.create(this.employee).then((employee) => {
        this.$store.dispatch('showSnackbar', this.$t('employee.created'))
        this.$router.push({ name: 'admin-employee' })
      }).catch((error) => {
        this.errors = error
        this.$store.dispatch('showSnackbar', this.$t('employee.couldNotCreate'))
      }).finally(() => {
        this.submittingForm = false
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
