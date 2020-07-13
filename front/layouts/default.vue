<template>
  <v-app>
    <v-main class="login-base">
      <v-container fluid fill-height>
        <v-row align="center" justify="center">
          <v-col sm="12" md="8" lg="4">
            <v-card>
              <LoadingIcon :is-loading="loading" />
              <v-card-text v-if="!loading">
                <v-row v-if="'brandiamge' in $store.state.org" align="center" justify="center" fill-height>
                  <img :src="$store.state.org.brandimage" style="max-width:100%;" alt="logo">
                </v-row>
                <nuxt />
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
      <SnackbarNot />
    </v-main>
  </v-app>
</template>

<script>
import SnackbarNot from '~/components/general/SnackbarNotification'
export default {
  components: { SnackbarNot },
  data: () => ({
    loading: true
  }),
  mounted () {
    this.$org.getBaseOrgInfo().then((data) => {
      this.$store.commit('setOrg', data)
      this.loading = false
      this.$i18n.locale = data.language
    })
    this.$user.getCSRFToken()
  }
}
</script>
