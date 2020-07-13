<template>
  <div>
    <v-textarea
      ref="ta"
      :value="value"
      :label="label"
      :error-messages="errors"
      :auto-grow="true"
      @input="update"
      @keyup="removeError"
      style="width:100%"
    >
      <template slot="append">
        <CustomInsert @clickedEmoji="addItem" @clickedPersonalize="addItem" disable-emoji />
      </template>
    </v-textarea>
  </div>
</template>

<script>
import CustomInsert from './editor/CustomInsert'
export default {
  name: 'VTextAreaEmoji',
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
    },
    personalize: {
      type: Boolean,
      default: false
    },
    emoji: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    newValue: '',
    isActive: false
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
    },
    addPersonalize (item) {
      this.$emit('input', this.value.insert(this.$refs.ta.$refs.input.selectionStart, item))
    }
  }
}
</script>
