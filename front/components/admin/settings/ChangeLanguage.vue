<template>
  <v-card class="mb-4">
    <v-card-text>
      <h3>{{ $t('settings.personal.language') }}</h3>
      <v-form class="mt-3">
        <v-select
          v-model="selectedLanguage"
          :items="$store.state.languages"
          :label="$t('settings.global.selectLanguage')"
          item-value="id"
          item-text="language"
        />
      </v-form>
      <p> {{ $t('settings.personal.refreshPage') }} </p>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn
        :loading="loading"
        @click="changeLanguage()"
        color="success"
      >
        {{ $t('buttons.update') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>
<script>
export default {
  name: 'ChangeLanguage',
  data: () => ({
    loading: false,
    selectedLanguage: ''
  }),
  mounted () {
    this.selectedLanguage = (' ' + this.$store.state.admin.language).slice(1)
  },
  methods: {
    changeLanguage () {
      this.loading = true
      this.$user.changeLanguage(this.selectedLanguage).then((response) => {
        this.$i18n.locale = this.selectedLanguage
        this.$store.dispatch('showSnackbar', this.$t('settings.personal.languageChanged'))
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>
