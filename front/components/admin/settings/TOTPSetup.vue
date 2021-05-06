<template>
  <v-card class="mb-4">
    <v-card-text>
      <h3>{{ $t('settings.personal.TOTPSetup') }}</h3>
      <p v-if="$store.state.admin.requires_otp" class="mt-2">
        {{ $t('settings.personal.TOTPOK') }}
      </p>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn
        v-if="!$store.state.admin.requires_otp"
        @click="getTOTPQR"
        :loading="loading"
        color="success"
      >
        {{ $t('buttons.enable') }}
      </v-btn>
    </v-card-actions>
    <v-dialog
      v-model="dialog"
      persistent
      max-width="690"
    >
      <v-card>
        <v-card-title class="headline">
          TOTP QR
        </v-card-title>
        <v-card-text>
          <div v-if="!showRecoveryKey">
            <img :src="qrImage">
            <v-text-field
              v-model="otp"
              label="OTP code"
            />
          </div>
          <div v-else>
            {{ $t('settings.personal.recoveryKeyMessage') }}
            <p><b> {{ recoveryKey }} </b></p>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            v-if="showRecoveryKey"
            @click="dialog = false"
            :disabled="holdTimer"
            text
          >
            {{ $t('buttons.complete') }}
          </v-btn>
          <v-btn
            v-if="!showRecoveryKey"
            @click="dialog = false"
            text
          >
            Cancel
          </v-btn>
          <v-btn
            v-if="!showRecoveryKey"
            @click="validateTOTP"
            :loading="dialogLoading"
            color="primary"
            text
          >
            {{ $t('buttons.enable') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>
<script>
import QRCode from 'qrcode'

export default {
  name: 'TOTPSetup',
  data: () => ({
    loading: false,
    otpURL: '',
    dialog: false,
    dialogLoading: false,
    otp: '',
    holdTimer: false,
    showRecoveryKey: false,
    recoveryKey: '',
    qrImage: ''
  }),
  methods: {
    getTOTPQR () {
      this.loading = true
      this.$user.getTOTPQR().then((response) => {
        this.otpURL = response.otp_url
        QRCode.toDataURL(this.otpURL).then((url) => {
          this.qrImage = url
        }).catch((err) => {
          console.error(err)
        }).finally(() => {
          this.loading = false
        })
        this.dialog = true
      })
    },
    validateTOTP () {
      this.dialogLoading = true
      this.$user.validateTOTP(this.otp).then((response) => {
        this.holdTimer = true
        this.recoveryKey = response.recovery_key
        this.showRecoveryKey = true
        setTimeout(() => {
          this.holdTimer = false
        }, 10000)
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('admin.TOTPNotMatch'))
      }).finally(() => {
        this.dialogLoading = false
      })
    }
  }
}
</script>
