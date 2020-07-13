<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="900"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('appointment.item') }}
      </v-card-title>

      <v-card-text>
        <AppointmentForm ref="form" v-model="tempAppoint" :errors="errors" :inline="true" />
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          @click="$emit('input', false)"
          text
        >
          {{ $t('buttons.cancel') }}
        </v-btn>
        <v-btn
          :loading="loading"
          @click="addAppointment"
        >
          {{ $t('buttons.add') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import AppointmentForm from '@/components/admin/appointment/Form'
export default {
  name: 'IntroModal',
  components: { AppointmentForm },
  props: {
    appointment: {
      type: Object,
      required: true
    },
    value: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    loading: false,
    nameError: [],
    errors: {},
    tempAppoint: { name: '', data: [], when: '', content: '', tags: [], time: '', days: 0, fixed_date: false }
  }),
  watch: {
    value (value) {
      if (Object.entries(this.appointment).length === 0) {
        this.tempAppoint = { name: '', data: [], when: '', content: '', tags: [], time: '', days: 0, fixed_date: false }
      } else {
        this.tempAppoint = JSON.parse(JSON.stringify(this.appointment))
      }
    }
  },
  methods: {
    addAppointment () {
      let remove = -1
      if (JSON.stringify(this.tempAppoint) !== JSON.stringify(this.appointment)) {
        if ('id' in this.tempAppoint) {
          remove = this.tempAppoint.task_id
          delete this.tempAppoint.id
        }
        this.tempAppoint.template = false
        this.loading = true
        this.$appointments.create(this.tempAppoint).then((data) => {
          data.type = 'appointment'
          this.$emit('change', { 'add': data, remove })
          this.$emit('input', false)
        }).catch((error) => {
          this.errors = error
          this.$store.dispatch('showSnackbar', this.$t('appointment.couldNotSave'))
        }).finally(() => {
          this.loading = false
        })
      } else {
        this.$emit('input', false)
      }
    }
  }
}
</script>
