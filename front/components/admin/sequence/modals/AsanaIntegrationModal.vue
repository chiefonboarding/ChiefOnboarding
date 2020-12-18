<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="1000"
  >
    <v-card>
      <v-card-title class="headline">
        Asana
      </v-card-title>

      <v-card-text class="pa-0">
        <v-container class="px-6">
          <v-select
            :items="teams"
            :loading="loadingTeams"
            multiple
            label="Pick team to add a new hire to"
            v-model="tempAsana.additional_data.teams"
            return-object
            item-text="name"
          ></v-select>
        </v-container>
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
          @click="AddAsanaIntegration"
        >
          <span v-if="Object.entries(asana).length">
            {{ $t('buttons.update') }}
          </span>
          <span v-else>
            {{ $t('buttons.add') }}
          </span>
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
export default {
  name: 'AsanaIntegrationModal',
  props: {
    asana: {
      type: Object,
      default: () => { return {} }
    },
    index: {
      type: Number,
      required: true
    },
    value: {
      type: Boolean,
      required: true
    }
  },
  data: () => ({
    loading: false,
    errors: {},
    teams: [],
    selectedTeams: [],
    tempAsana: { additional_data: { teams: [] }, type: 'asana', integration_type: 'asana' },
    loadingTeams: false
  }),
  watch: {
    value (value) {
      if (Object.entries(this.asana).length === 0) {
        this.tempAsana = { additional_data: { teams: [] }, integration_type: 'asana', type: 'asana' }
      } else {
        this.tempAsana = JSON.parse(JSON.stringify(this.asana))
      }
    }
  },
  mounted () {
    this.loadingTeams = true
    this.$integrations.getAsanaTeams().then((data) => {
      this.teams = data
      this.loadingTeams = false
    })
  },
  methods: {
    AddAsanaIntegration () {
      this.loading = true
      if (this.tempAsana.additional_data.teams.length === 0) {
        this.$store.dispatch('showSnackbar', this.$t('integrations.asana.missingTeams'))
        return
      }
      delete this.tempAsana.id
      this.$sequences.createAsana(this.tempAsana).then((data) => {
        if (this.index === -1) {
          // unconditioned item
          this.$emit('updateUnconditionedItem', { id: this.asana.id || -1, type: 'integrations', item: data })
          this.$emit('input', false)
          return
        }
        if ('id' in this.asana) {
          this.$store.commit('sequences/removeItem', {
            block: this.index,
            type: 'integrations',
            id: this.asana.id
          })
        }
        this.$store.commit('sequences/addItem', { block: this.index, type: 'integrations', item: data })
        this.$emit('input', false)
      }).catch((error) => {
        this.errors = error
        this.$store.dispatch('showSnackbar', this.$t('integrations.asana.couldNotSave'))
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>
