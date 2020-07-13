<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="900"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('settings.newHireEmail') }} ({{ $store.state.selectedLanguage.language }})
      </v-card-title>

      <v-card-text>
        <p> {{ $t('settings.loginAdded') }}</p>
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
  name: 'ChangeNewHireModal',
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
    this.text = JSON.parse(JSON.stringify(this.$store.state.welcomeMessages.find(a => a.language === this.$store.state.selectedLanguage.id && a.message_type === 1))).message
  },
  methods: {
    update () {
      this.loading = true
      this.$org.updateNewHireEmail(this.text, this.$store.state.selectedLanguage.id).then((data) => {
        this.$emit('input', false)
        this.$emit('emailUpdated')
        this.$store.dispatch('showSnackbar', this.$t('settings.newHireEmailChanged'))
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('settings.newHireEmailCouldNotChange'))
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>
