<template>
  <div>
    <v-form>
      <v-text-field
        v-model="passwords.new_password1"
        :label="$t('forms.password')"
        :error-messages="errors.new_password1"
        :color="$store.state.org.base_color"
        @keyup="errors.new_password1=''"
        class="mt-2"
        prepend-icon="lock"
        type="password"
      />
      <v-text-field
        v-model="passwords.new_password2"
        :label="$t('settings.personal.confirmPass')"
        :error-messages="errors.new_password2"
        :color="$store.state.org.base_color"
        @keyup="errors.new_password2=''"
        class="mt-2"
        type="password"
        prepend-icon="lock"
      />
    </v-form>
    <v-col>
      <v-btn
        :loading="loading"
        :color="$store.state.org.base_color"
        @click="confirmPass"
        style="width: 100%; color: white; margin: 5px 0"
      >
        {{ $t('buttons.submit') }}
      </v-btn>
    </v-col>
  </div>
</template>

<script>
export default {
  data: () => ({
    loading: false,
    errors: {},
    passwords: {}
  }),
  methods: {
    confirmPass () {
      this.loading = true
      this.$user.confirmPass({ uid: this.$route.params.uid, token: this.$route.params.token, new_password1: this.passwords.new_password1, new_password2: this.passwords.new_password2 }).then((data) => {
        this.$router.push({ name: 'index' })
        this.$store.dispatch('showSnackbar', data.detail)
      }).catch((error) => {
        this.errors = error
        if ('token' in error) {
          this.$store.dispatch('showSnackbar', this.$t('admin.linkNotValid'))
        }
      }).finally(() => {
        this.loading = false
      })
    },
    updatePasswords (value) {
      this.passwords = value
    }
  }
}
</script>
