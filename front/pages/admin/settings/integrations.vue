<template>
  <v-container>
    <v-row>
      <v-col offset-sm="1" sm="10">
        <v-row mb-4>
          <v-col sm="6">
            <h1 class="heading" style="margin-top: 5px;">
              {{ $t('settings.integrations.integrations') }}
            </h1>
          </v-col>
        </v-row>
        <v-container pa-0>
          <v-row>
            <IntegrationItem
              :title="$t('settings.integrations.slackBot')"
              :description="$t('settings.integrations.slackBotExpl')"
              :integration="0"
              :connected="$store.state.org.slack_key"
            >
              <SlackConnectDialog :type="0" />
            </IntegrationItem>
            <IntegrationItem
              :title="$t('settings.integrations.slackAccount')"
              :description="$t('settings.integrations.slackAccountExpl')"
              :integration="1"
              :connected="$store.state.org.slack_account_key"
            >
              <SlackConnectDialog :type="1" />
            </IntegrationItem>
            <IntegrationItem
              :title="$t('settings.integrations.googleAccounts')"
              :description="$t('settings.integrations.googleAccountsDescr')"
              :integration="2"
              :connected="$store.state.org.google_key"
            >
              <GoogleAPIConnectDialog />
            </IntegrationItem>
            <IntegrationItem
              :title="$t('settings.integrations.googleLogin')"
              :description="$t('settings.integrations.googleLoginDescr')"
              :integration="3"
              :connected="$store.state.org.google_login_key"
            >
              <GoogleLoginConnectDialog />
            </IntegrationItem>
          </v-row>
        </v-container>
      </v-col>
    </v-row>
  </v-container>
</template>
<script>
import IntegrationItem from '@/components/admin/settings/global/integrations/IntegrationItem'
import SlackConnectDialog from '@/components/admin/settings/global/integrations/SlackConnectDialog'
import GoogleAPIConnectDialog from '@/components/admin/settings/global/integrations/GoogleAPIConnectDialog'
import GoogleLoginConnectDialog from '@/components/admin/settings/global/integrations/GoogleLoginConnectDialog'
export default {
  layout: 'admin',
  components: { GoogleLoginConnectDialog, SlackConnectDialog, IntegrationItem, GoogleAPIConnectDialog },
  data: () => ({
    dialog: false,
    loading: false
  })
}
</script>
