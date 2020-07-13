<template>
  <div>
    <v-dialog
      v-model="dialog"
      width="500"
    >
      <template v-slot:activator="{ on }" style="width:100%">
        <v-btn
          v-on="on"
          color="primary"
          dark
        >
          Connect
        </v-btn>
      </template>

      <v-card>
        <v-card-title
          class="headline"
          primary-title
        >
          Connect Google
        </v-card-title>

        <v-card-text>
          <v-form class="mt-3">
            <v-container v-if="stepOne">
              <v-row>
                <v-text-field
                  v-model="form.client_id"
                  :label="$t('settings.integrations.client_id')"
                  class="mt-2 py-0 mb-0"
                  required
                />
              </v-row>
              <v-row>
                <v-text-field
                  v-model="form.client_secret"
                  :label="$t('settings.integrations.client_secret')"
                  class="mt-2 py-0 mb-0"
                  required
                />
              </v-row>
              <v-row>
                <v-text-field
                  v-model="form.redirect_url"
                  :label="$t('settings.integrations.redirect_url')"
                  class="mt-2 py-0 mb-0"
                  required
                />
              </v-row>
            </v-container>
            <v-container v-else>
              <v-row>
                {{ $t('settings.integrations.completeGoogle') }} &nbsp;
                <a :href="'https://accounts.google.com/signin/oauth/oauthchooseaccount?response_type=code&client_id=' + form.client_id + '&redirect_uri=' + form.redirect_url + '&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.user&prompt=consent&state=' + state + '&access_type=offline&flowName=GeneralOAuthFlow'">Google</a>
              </v-row>
            </v-container>
          </v-form>
        </v-card-text>

        <v-divider />

        <v-card-actions>
          <v-spacer />
          <v-btn
            v-if="stepOne"
            @click="saveIntegration"
            color="primary"
          >
            {{ $t('buttons.submit') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
export default {
  name: 'GoogleAPIConnectDialog',
  data: () => ({
    form: { integration: 2 },
    dialog: false,
    stepOne: true,
    state: ''
  }),
  methods: {
    saveIntegration () {
      this.$integrations.saveGoogleAPIKey(this.form).then((data) => {
        this.stepOne = false
        this.state = data.one_time_auth_code
      }).catch((error) => {
        console.log(error)
      })
    }
  }
}
</script>
