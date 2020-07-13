<template>
  <v-dialog
    v-model="dialog"
    width="600"
  >
    <template v-slot:activator="{ on }">
      <v-btn
        v-on="on"
        class="error"
        style="float:right"
      >
        {{ $t('buttons.remove') }}
      </v-btn>
    </template>
    <v-card>
      <v-card-title class="headline">
        {{ $t('settings.adminModalHeader') }}
      </v-card-title>
      <v-card-text>{{ $t('settings.adminModalDescr') }}</v-card-text>
      <v-divider />
      <v-card-actions>
        <v-spacer />
        <v-btn
          @click="dialog=false"
          color="dark"
          text
        >
          {{ $t('buttons.cancel') }}
        </v-btn>
        <v-btn
          :loading="loading"
          @click="remove()"
          color="error"
        >
          {{ $t('buttons.remove') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
export default {
  name: 'AdminDialog',
  props: {
    id: {
      type: Number,
      required: true
    }
  },
  data: () => ({
    dialog: false,
    loading: false
  }),
  methods: {
    remove () {
      this.loading = true
      this.$org.removeAdmin(this.id).then((data) => {
        this.loading = false
        this.$store.dispatch('showSnackbar', this.$t('settings.adminHasBeenRemoved'))
        this.$org.getAdmins().then((admins) => {
          this.loading = false
        })
      }).finally(() => {
        this.dialog = false
      })
    }
  }
}
</script>
