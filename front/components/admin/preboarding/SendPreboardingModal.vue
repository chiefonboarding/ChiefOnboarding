<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="650"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('newhires.sendPreEmailHeader') }}
      </v-card-title>
      <v-card-text>
        <p>
          {{ $t('newhires.sendPreEmailDescr') }}
        </p>
        <v-radio-group v-model="medium" color="primary">
          <v-radio
            :label="$t('newhires.email')"
            :value="1"
            color="primary"
          />
          <v-radio
            :label="$t('newhires.textMessage')"
            :value="2"
            color="primary"
          />
        </v-radio-group>
        <div v-if="medium === 1">
          <v-text-field
            v-model="email"
            :label="$t('forms.sendEmailMessageTo')"
          />
        </div>
        <div v-else>
          <v-text-field
            v-model="phone"
            :label="$t('forms.sendTextMessageTo')"
          />
        </div>
        <div v-if="newHire.send_preboarding_details">
          <b>{{ $t('newhires.alreadySendNotification') }}</b>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="$emit('input', false)" color="primary" text>
          {{ $t('buttons.cancel') }}
        </v-btn>
        <v-btn :loading="sendingPreboardingDetails" @click="sendPreboardingDetails" color="primary" dark>
          {{ $t('buttons.send') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  props: {
    newHire: {
      type: Object,
      default: () => { return {} }
    },
    value: {
      type: Boolean,
      required: true
    }
  },
  data: vm => ({
    sendingPreboardingDetails: false,
    phone: '',
    medium: 1,
    email: vm.newHire.email
  }),
  methods: {
    sendPreboardingDetails () {
      this.sendingPreboardingDetails = true
      const payload = {}
      payload.type = (this.medium === 1) ? 'email' : 'phone'
      payload.value = (this.medium === 1) ? this.email : this.phone
      this.$newhires.sendPreboardingDetails(this.$route.params.id, payload).then(() => {
        this.$emit('detailsSend', true)
        this.$emit('input', false)
        this.$store.dispatch('showSnackbar', this.$t('newhires.hasBeenNotified'))
      }).catch((errors) => {
        this.$store.dispatch('showSnackbar', this.$t('newhires.couldNotSendMessage'))
      }).finally(() => {
        this.sendingPreboardingDetails = false
      })
    }
  }
}
</script>
