<template>
  <v-combobox
    :value="value"
    :items="$store.state.tags"
    :label="$t('forms.tags')"
    @change="update"
    chips
    clearable
    multiple
    small-chips
  >
    <template slot="selection" slot-scope="data">
      <v-chip
        :input-value="data.selected"
        @click:close="remove(data.index)"
        close
      >
        <strong>{{ data.item }}</strong>
      </v-chip>
    </template>
  </v-combobox>
</template>

<script>
export default {
  name: 'TagSelector',
  props: {
    value: {
      type: Array | String,
      default: ''
    }
  },
  methods: {
    remove (index) {
      this.value.splice(index, 1)
    },
    update (value) {
      this.$emit('input', value)
    }
  }
}
</script>
