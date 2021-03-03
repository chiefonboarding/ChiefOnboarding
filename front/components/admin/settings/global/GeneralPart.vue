<template>
  <div>
    <v-row class="mb-4">
      <v-col sm="12">
        <h1 class="heading" style="margin-top: 5px;">
          {{ $t('settings.global.billing') }}
        </h1>
      </v-col>
    </v-row>
    <v-card class="mb-4 pt-2">
      <v-card-text>
        <v-text-field
          v-model="company.name"
          :label="$t('settings.global.businessName')"
          :error-messages="errors.name"
          @keyup="errors.name=[]"
          :disabled="saving"
        />
        <v-select
          v-model="company.language"
          :items="$store.state.languages"
          :label="$t('settings.global.selectLanguage')"
          :disabled="saving"
          item-value="id"
          item-text="language"
        />
        <v-autocomplete
          v-model="company.timezone"
          :items="this.$store.state.timezones"
          :search-input.sync="search"
          :label="$t('settings.global.timezone')"
          :error-messages="errors.timezone"
          @keyup="errors.timezone=[]"
          :disabled="saving"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn
          :loading="saving"
          @click="save"
          color="success"
        >
          {{ $t('buttons.update') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'GeneralPart',
  props: {
    org: {
      type: Object,
      default: () => { return {} }
    }
  },
  data: () => ({
    loading: false,
    saving: false,
    errors: {},
    company: {},
    search: ''
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
