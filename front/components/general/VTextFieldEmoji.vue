<template>
  <div>
    <v-text-field
      ref="ta"
      :value="value"
      :label="label"
      :error-messages="errors"
      @input="update"
      @keyup="removeError"
    >
      <template slot="append">
        <CustomInsert @clickedEmoji="addItem" @clickedPersonalize="addItem" />
      </template>
    </v-text-field>
  </div>
</template>

<script>
import CustomInsert from './editor/CustomInsert'
export default {
  name: 'VTextFieldEmoji',
  components: { CustomInsert },
  props: {
    value: {
      type: String,
      default: ''
    },
    label: {
      type: String,
      default: 'empty label'
    },
    errors: {
      type: Array,
      default: () => { return [] }
    }
  },
  data: () => ({
    showItem: false,
    newValue: ''
  }),
  methods: {
    addItem (item) {
      this.$emit('input', this.value.insert(this.$refs.ta.$refs.input.selectionStart, item))
    },
    update (value) {
      this.$emit('input', value)
    },
    removeError (value) {
      this.$emit('removeError', '')
      this.$emit('keyup', value)
    }
  }
}
</script>

<style>

</style>
