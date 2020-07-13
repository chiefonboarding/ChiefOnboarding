<template>
  <v-card class="mb-4">
    <v-card-text>
      <h3>{{ $t('settings.personal.changePassword') }}</h3>
      <v-form class="mt-3">
        <v-text-field
          v-model="passwords.old_password"
          :label="$t('settings.personal.oldPass')"
          :error-messages="oldPasswordError"
          @keyup="oldPasswordError=''"
          type="password"
          prepend-icon="lock"
        />
        <v-text-field
          v-model="passwords.new_password1"
          :label="$t('settings.personal.newPass')"
          :error-messages="newPassword1Error"
          @keyup="newPassword1Error=''"
          class="mt-2"
          type="password"
          prepend-icon="lock"
        />
        <v-text-field
          v-model="passwords.new_password2"
          :label="$t('settings.personal.confirmPass')"
          :error-messages="newPassword2Error"
          @keyup="newPassword2Error=''"
          class="mt-2"
          type="password"
          prepend-icon="lock"
        />
      </v-form>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn
        :loading="loading"
        @click="changePassword()"
        color="success"
      >
        {{ $t('buttons.update') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>
<script>
export default {
  name: 'ResetPasswordForm',
  data () {
    return {
      passwords: { 'old_password': '', 'new_password1': '', 'new_password2': '' },
      oldPasswordError: '',
      newPassword1: '',
      newPassword1Error: '',
      newPassword2: '',
      newPassword2Error: '',
      loading: false
    }
  },
  methods: {
    changePassword (id) {
      this.loading = true
      this.$user.changePassword(this.passwords).then((response) => {
        this.$store.dispatch('showSnackbar', this.$t('settings.personal.changed'))
        this.passwords = { 'old_password': '', 'new_password1': '', 'new_password2': '' }
      }).catch((error) => {
        if ('old_password' in error) {
          this.oldPasswordError = error.old_password[0]
        }
        if ('new_password1' in error) {
          this.newPassword1Error = error.new_password1[0]
        }
        if ('new_password2' in error) {
          this.newPassword2Error = error.new_password2[0]
        }
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>
