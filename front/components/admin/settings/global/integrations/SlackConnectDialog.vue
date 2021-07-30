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
          Connect Slack
        </v-card-title>

        <v-card-text>
          <v-form v-show="!secondStep" class="mt-3">
            <v-container>
              <v-row>
                <v-text-field
                  v-model="form.app_id"
                  :label="$t('settings.integrations.app_id')"
                  class="mt-2 py-0 mb-0"
                  required
                />
              </v-row>
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
                  v-model="form.signing_secret"
                  :label="$t('settings.integrations.signing_secret')"
                  class="mt-2 py-0 mb-0"
                  required
                />
              </v-row>
              <v-row>
                <v-text-field
                  v-model="form.verification_token"
                  :label="$t('settings.integrations.verification_token')"
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
          </v-form>
          <a v-if="secondStep" :href="'https://slack.com/oauth/authorize?scope=' + scope +'&client_id=' + form.client_id + '&redirect_uri=' + form.redirect_url + '&state=&granular_bot_scope=1&single_channel=0&install_redirect=&tracked=1&team="><img alt="Add to Slack" height="40" width="139" src="https://platform.slack-edge.com/img/add_to_slack.png" srcset="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x"></a>
        </v-card-text>

        <v-divider />

        <v-card-actions>
          <v-spacer />
          <v-btn
            @click="saveIntegration"
            v-if="!secondStep"
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
  name: 'ConnectSlackDialog',
  props: {
    'type': {
      default: 0,
      type: Number
    }
  },
  data: () => ({
    form: { integration: 0 },
    dialog: false,
    secondStep: false,
    scope: 'im:history,im:read,users:read,users:read.email,im:write,chat:write'
  }),
  mounted () {
    if (this.type === 1) {
      this.scope = 'client'
      this.form.integration = 1
    }
  },
  methods: {
    saveIntegration () {
      this.$integrations.saveSlackIntegration(this.form).then(() => {
        this.secondStep = true
      }).catch((error) => {
        console.log(error)
      })
    }
  }
}
</script>
