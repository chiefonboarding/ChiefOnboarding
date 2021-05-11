<template>
  <div>
    <v-form>
      <v-col v-show="!showTOTPForm" sm="12" class="pb-0">
        <v-text-field
          v-model="username"
          :label="$t('forms.email')"
          :color="$store.state.org.accent_color"
          prepend-icon="person"
          class="my-0"
          name="Email"
          type="text"
        />
      </v-col>
      <v-col v-show="!showTOTPForm" sm="12" class="py-0">
        <v-text-field
          id="password"
          v-model="password"
          :label="$t('forms.password')"
          :color="$store.state.org.accent_color"
          @keyup.enter="login"
          type="password"
          class="my-0"
          prepend-icon="lock"
          name="password"
        />
      </v-col>
      <v-col v-show="showTOTPForm" sm="12" class="py-0">
        <v-text-field
          id="totp"
          v-model="totp"
          :color="$store.state.org.accent_color"
          @keyup.enter="login"
          label="2FA - TOTP"
          class="my-0"
          prepend-icon="lock"
        />
      </v-col>
      <v-col v-show="!showTOTPForm" sm="12" class="py-0">
        <nuxt-link :style="`color: ${$store.state.org.accent_color}`" to="pass/reset">
          {{ $t('admin.forgotPass') }}
        </nuxt-link>
      </v-col>
    </v-form>
    <v-col sm="12" class="py-0">
      <v-btn
        :loading="loading"
        :color="$store.state.org.base_color"
        @click="login"
        style="width: 100%; color: white; margin: 5px 0"
      >
        {{ $t('buttons.login') }}
      </v-btn>
    </v-col>
    <v-col sm="12" class="pt-0">
      <v-btn
        v-if="$store.state.org.google_login_key && $store.state.org.google_login"
        :href="google_url"
        style="width: 100%; margin: 5px 0; border: 1px solid #dedede !important"
        color="white"
      >
        <div class="first_part google">
          <img src="https://d2c76c1p4pk74e.cloudfront.net/static/google.png" style="width: 30px;" class="google_image">
        </div>
        <div class="second_part google_text">
          {{ $t('admin.loginWithGoogle') }}
        </div>
      </v-btn>
    </v-col>
  </div>
</template>

<script>
export default {
  data: () => ({
    username: '',
    loading: false,
    password: '',
    totp: '',
    showTOTPForm: false
  }),
  computed: {
    google_url () {
      return 'https://accounts.google.com/o/oauth2/auth?protocol=oauth2&response_type=code&client_id=' +
        this.$store.state.org.google_login_client_id + '&redirect_uri=' +
        encodeURIComponent(this.$store.state.org.base_url + '/api/auth/google_login') + '&scope=email'
    }
  },
  methods: {
    login () {
      this.loading = true
      this.$user.login({ username: this.username, password: this.password, totp: this.totp }).then((data) => {
        if (data.role === 1 || data.role === 2) {
          this.$router.push({ name: 'admin' })
        } else {
          this.$router.push({ name: 'portal' })
        }
      }).catch((error) => {
        if ('totp' in error) {
          this.showTOTPForm = true
        }
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>

<style scoped>
.first_part {
  margin-top: -4px;
  display: inline-block;
}
.button_class {
  display: block;
}
.second_part {
  display: inline-block;
  position: relative;
  width: 82%;
  text-align: center;
  top: -14px;
}
.google_image {
  width: 30px;
  margin-top: 10px;
  margin-left: 5px;
  margin-right: 5px;
}
.google_text {
  top:0px;
}
</style>
