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
          Asana
        </v-card-title>

        <v-card-text>
          <v-form class="mt-3">
            <v-container>
              <v-row>
                <v-text-field
                  v-model="form.token"
                  :label="$t('settings.integrations.token')"
                  class="mt-2 py-0 mb-0"
                  required
                />
              </v-row>
            </v-container>
          </v-form>
        </v-card-text>

        <v-divider />

        <v-card-actions>
          <v-spacer />
          <v-btn
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
  name: 'AsanaDialog',
  data: () => ({
    form: { integration: 4 },
    dialog: false
  }),
  methods: {
    saveIntegration () {
      this.$integrations.saveAsanaToken(this.form).then(() => {
        this.dialog = false
        this.$store.commit('setAsanaKey')
      }).catch((error) => {
        console.log(error)
      })
    }
  }
}
</script>
