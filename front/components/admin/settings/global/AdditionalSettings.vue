<template>
  <div>
    <v-card class="mb-4">
      <v-card-text>
        <v-tooltip top>
          <template v-slot:activator="{ on }">
            <v-switch
              v-model="company.new_hire_email"
              :label="$t('settings.global.alwaysSendNewHireWelcomeEmail')"
              v-on="on"
            />
          </template>
          <span>{{ $t('settings.global.newHireLoginCred') }}</span>
        </v-tooltip>
        <v-tooltip top>
          <template v-slot:activator="{ on }">
            <v-switch
              v-model="company.google_login"
              :label="$t('settings.global.loginWithGoogleLabel')"
              v-on="on"
            />
          </template>
          <span>{{ $t('settings.global.loginWithGoogle') }}</span>
        </v-tooltip>
        <v-tooltip top>
          <template v-slot:activator="{ on }">
            <v-switch
              v-model="company.new_hire_email_reminders"
              :label="$t('settings.global.sendEmailReminderLabel')"
              v-on="on"
            />
          </template>
          <span> {{ $t('settings.global.sendEmailReminder') }}</span>
        </v-tooltip>
        <v-tooltip top>
          <template v-slot:activator="{ on }">
            <v-switch
              v-model="company.new_hire_email_overdue_reminders"
              :label="$t('settings.global.sendReminderWhenDueLabel')"
              v-on="on"
            />
          </template>
          <span>{{ $t('settings.global.sendReminderWhenDue') }}</span>
        </v-tooltip>
        <div v-if="$store.state.org.slack_key">
          <h2> {{ $t('settings.global.slackOptions') }}</h2>
          <v-tooltip top>
            <template v-slot:activator="{ on }">
              <v-switch
                v-model="company.slack_buttons"
                :label="$t('settings.global.addButtonsLabel')"
                v-on="on"
              />
            </template>
            <span>{{ $t('settings.global.addButtons') }}</span>
          </v-tooltip>
          <v-tooltip top>
            <template v-slot:activator="{ on }">
              <v-switch
                v-model="company.ask_colleague_welcome_message"
                :label="$t('settings.global.askWelcomeMessageLabel')"
                v-on="on"
              />
            </template>
            <span>{{ $t('settings.global.askWelcomeMessage') }} </span>
          </v-tooltip>
          <v-tooltip top>
            <template v-slot:activator="{ on }">
              <v-switch
                v-model="company.send_new_hire_start_reminder"
                :label="$t('settings.global.sendReminderNewHireIsStartingLabel')"
                v-on="on"
              />
            </template>
            <span>{{ $t('settings.global.sendReminderNewHireIsStarting') }}</span>
          </v-tooltip>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn :loading="saving" @click="save" class="success">
          {{ $t('buttons.update') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'AdditionalSettings',
  props: {
    org: {
      type: Object,
      default: () => { return {} }
    }
  },
  data: () => ({
    saving: false,
    company: {}
  }),
  mounted () {
    this.company = JSON.parse(JSON.stringify(this.org))
  },
  methods: {
    save () {
      this.saving = true
      this.$org.updateGeneral(this.company).then((data) => {
        this.$store.dispatch('showSnackbar', this.$t('settings.global.billingSaved'))
      }).catch((error) => {
        this.errors = error
        this.$store.dispatch('showSnackbar', this.$t('settings.global.billingNotSaved'))
      }).finally(() => {
        this.saving = false
      })
    }
  }
}
</script>
