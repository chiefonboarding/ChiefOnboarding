<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('appointment.changeHeader') }}
      </h1>
    </template>
    <template slot="header-right">
      <v-btn :loading="duplicating" @click="duplicateAppointment" color="secondary">
        {{ $t('buttons.duplicate') }}
      </v-btn>
      <v-btn :loading="removing" @click="removeAppointment" color="error" style="margin-right: 0px;">
        {{ $t('buttons.remove') }}
      </v-btn>
    </template>
    <template slot="formpart">
      <LoadingIcon :is-loading="loading" />
      <div v-if="!loading">
        <AppointmentForm ref="form" v-model="appointment" :errors="errors" />
      </div>
    </template>
    <template slot="footer">
      <v-btn :loading="saving" @click="saveAppointment" color="primary" style="float:right">
        {{ $t('buttons.save') }}
      </v-btn>
    </template>
  </TemplateCompInner>
</template>

<script>
import AppointmentForm from '@/components/admin/appointment/Form'
export default {
  layout: 'admin',
  components: { AppointmentForm },
  data () {
    return {
      loading: true,
      saving: false,
      removing: false,
      duplicating: false,
      submittingForm: false,
      errors: {},
      employee: {},
      appointment: {}
    }
  },
  watch: {
    '$route' (to, from) {
      this.getAppointment()
    }
  },
  mounted () {
    this.getAppointment()
  },
  methods: {
    getAppointment () {
      this.$appointments.get(this.$route.params.id).then((data) => {
        this.appointment = data
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('appointment.noAppointment'))
      }).finally(() => {
        this.loading = false
      })
    },
    saveAppointment () {
      this.saving = true
      this.$appointments.update(this.$route.params.id, this.appointment).then((data) => {
        this.$router.push({ name: 'admin-templates-appointments' })
        this.$store.dispatch('showSnackbar', this.$t('appointment.updated'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    },
    removeAppointment () {
      this.removing = true
      this.$appointments.remove(this.$route.params.id).then((data) => {
        this.$router.push({ name: 'admin-templates-appointments' })
        this.$store.dispatch('showSnackbar', this.$t('appointment.removed'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.removing = false
      })
    },
    duplicateAppointment () {
      this.duplicating = true
      this.$appointments.update(this.$route.params.id, this.appointment).then((data) => {
        this.$appointments.duplicate(this.$route.params.id).then((data) => {
          this.$router.push({ name: 'admin-templates-appointments' })
          this.$store.dispatch('showSnackbar', this.$t('appointment.savedAndDuplicated'))
        }).catch((error) => {
          this.errors = error
        }).finally(() => {
          this.duplicating = false
        })
      })
    }
  }
}
</script>

<style scoped>
</style>
