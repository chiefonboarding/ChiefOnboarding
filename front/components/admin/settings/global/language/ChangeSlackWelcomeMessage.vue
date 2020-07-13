<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="900"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('settings.welcomeSlackMessageHeader') }} ({{ $store.state.selectedLanguage.language }})
      </v-card-title>

      <v-card-text>
        <p>{{ $t('settings.welcomeSlackMessageDescr') }}</p>
        <VTextAreaEmoji
          v-model="text"
          :label="$t('settings.slackKnowledge')"
          :personalize="true"
          :emoji="true"
        />
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          @click="$emit('input', false)"
          text
        >
          {{ $t('buttons.cancel') }}
        </v-btn>
        <v-btn
          :loading="loading"
          @click="update"
        >
          {{ $t('buttons.update') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
export default {
  name: 'ChangeSlackWelcomeMessage',
  props: {
    value: Boolean
  },
  data () {
    return {
      loading: false,
      text: ''
    }
  },
  mounted () {
    this.text = JSON.parse(JSON.stringify(this.$store.state.welcomeMessages.find(a => a.language === this.$store.state.selectedLanguage.id && a.message_type === 3))).message
  },
  methods: {
    update () {
      this.loading = true
      this.$org.updateSlackMessage(this.text, this.$store.state.selectedLanguage.id).then((data) => {
        this.$emit('input', false)
        this.$emit('emailUpdated')
        this.$store.dispatch('showSnackbar', this.$t('settings.slackWelcomeMessageChanged'))
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('settings.slackWelcomeMessageCouldNotChange'))
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>
