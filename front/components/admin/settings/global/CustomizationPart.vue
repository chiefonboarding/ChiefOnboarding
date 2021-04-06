<template>
  <div>
    <v-row class="mb-4">
      <v-col sm="12">
        <h1 class="heading" style="margin-top: 5px;">
          {{ $t('settings.global.custom') }}
        </h1>
      </v-col>
    </v-row>
    <v-card class="mb-4">
      <v-card-text>
        <v-menu
          :close-on-content-click="false"
          :nudge-width="200"
          offset-x
        >
          <template v-slot:activator="{ on }">
            <v-btn
              v-on="on"
              color="dark"
              dark
            >
              {{ $t('settings.global.backgroundColor') }}
            </v-btn>
          </template>
          <v-card>
            <v-color-picker v-model="company.base_color" mode="hexa" />
          </v-card>
        </v-menu>
        <v-menu
          :close-on-content-click="false"
          :nudge-width="200"
          offset-x
        >
          <template v-slot:activator="{ on }">
            <v-btn
              v-on="on"
              color="dark"
              dark
            >
              {{ $t('settings.global.textColor') }}
            </v-btn>
          </template>
          <v-card>
            <v-color-picker v-model="company.accent_color" mode="hexa" />
          </v-card>
        </v-menu>
        <v-menu
          v-if="$store.state.org.slack_key"
          :close-on-content-click="false"
          :nudge-width="200"
          offset-x
        >
          <template v-slot:activator="{ on }">
            <v-btn
              v-on="on"
              color="dark"
              dark
            >
              {{ $t('settings.global.botColor') }}
            </v-btn>
          </template>
          <v-card>
            <v-color-picker v-model="company.bot_color" mode="hexa" />
          </v-card>
        </v-menu>
        <v-file v-model="company.logo" logo />
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
    <v-row class="mb-4">
      <v-col sm="12">
        <h1 class="heading" style="margin-top: 5px;">
          {{ $t('settings.global.otherSettings') }}
        </h1>
      </v-col>
    </v-row>
  </div>
</template>

<script>
export default {
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
    this.company = {
      base_color: this.org.base_color,
      accent_color: this.org.accent_color,
      bot_color: this.org.bot_color,
      logo: this.org.logo
    }
  },
  methods: {
    save () {
      this.savingCustom = true
      this.$org.updateGeneral(this.company).then((data) => {
        this.$store.dispatch('showSnackbar', this.$t('settings.global.customSaved'))
        this.$org.getOrganisation().then((data) => {
          this.savingCustom = false
        })
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('settings.global.customNotSaved'))
        this.savingCustom = false
      })
    }
  }
}
</script>
