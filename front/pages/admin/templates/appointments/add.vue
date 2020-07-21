<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('appointment.newHeader') }}
      </h1>
    </template>
    <template slot="formpart">
      <AppointmentForm v-model="appointment" :errors="errors" />
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
      loading: false,
      saving: false,
      errors: {},
      employee: {},
      appointment: { name: '', date: '', content: [], tags: [], time: '', on_day: 0, fixed_date: false }
    }
  },
  methods: {
    saveAppointment () {
      this.saving = true
      this.$appointments.create(this.appointment).then((data) => {
        this.$router.push({ name: 'admin-templates-appointments' })
        this.$store.dispatch('showSnackbar', this.$t('appointment.created'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    }
  }
}
</script>
