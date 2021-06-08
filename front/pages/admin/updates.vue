<template>
  <v-col sm="12" mb="6" offset-mb="3" md="8" offset-md="2">
    <v-row class="mb-4">
      <v-col sm="12">
        <h1 class="heading" style="margin-top: 5px;">
          All the new stuff!
        </h1>
      </v-col>
    </v-row>
    <v-card class="mb-4">
      <v-list-item v-for="i in items" :key="i.title" @click="goToDetails(i)" three-line class="pa-2 px-8">
        <v-list-item-icon v-if="isBeforeLastCheck(i.date)">
          <v-icon color="primary">
            far fa-dot-circle
          </v-icon>
        </v-list-item-icon>
        <v-list-item-content>
          <v-list-item-title>{{ i.title }}</v-list-item-title>
          <v-list-item-subtitle>{{ i.description }}</v-list-item-subtitle>
          <v-list-item-subtitle>This update has been added on {{ formatDate(i.date) }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </v-card>
  </v-col>
</template>

<script>
import moment from 'moment'
export default {
  layout: 'admin',
  data: () => ({
    items: [
      { date: '2021-06-08', title: 'Updated editor and adding native video option', description: 'Some global updates to the Editor (tiptap 2 now) and there is an option for videos now', href: 'new-editor-and-video-support' },
      { date: '2021-06-08', title: '2FA support', description: 'You can now use TOTP (timed one time tokens), so get your andOTP, Google Authenticator, Authy...', href: 'totp-2fa-support' },
      { date: '2021-06-08', title: 'SMTP support', description: 'You can now use SMTP as the email delivering protocal. This should be your last resort.', href: 'smtp-support' },
      { date: '2021-04-02', title: 'Add custom email subject to sequence messages', description: 'Defaults to "Here is an update", but you can now change it to whatever you want.', href: 'subject-to-email-message' },
      { date: '2021-04-02', title: 'Automatically add new hires when they join Slack.', description: 'Either do this automatically or with manual approval and automatically add sequences to this new hire.', href: 'automatically-add-new-hires-when-they-join-slack' },
      { date: '2021-04-02', title: 'Set default sequences for new hires', description: 'Through the settings, you can set default sequences, which are then automatically filled in the add new hire form.', href: 'default-sequences' }
    ],
    lastCheck: ''
  }),
  mounted () {
    this.lastCheck = this.$store.state.admin.seen_updates.repeat(1)
    this.$user.seenUpdates().then((admin) => {
      this.$store.commit('setAdmin', admin)
    })
  },
  methods: {
    goToDetails (item) {
      window.open('https://docs.chiefonboarding.com/Changelog.html#' + item.href, '_blank')
    },
    formatDate (date) {
      return moment(date).format('LL')
    },
    isBeforeLastCheck (date) {
      return moment(this.lastCheck).isBefore(date)
    }
  }
}
</script>
