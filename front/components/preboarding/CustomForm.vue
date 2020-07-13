<template>
  <div class="mt-3 formpart">
    <div v-for="(i, index) in value" :key="index">
      <div v-if="i.type === 'input'">
        <v-text-field
          v-model="i.value"
          :color="org.base_color"
          :label="i.text"
          class="my-0"
          outline
        />
      </div>
      <div v-if="i.type === 'upload'">
        <UploadForm :id="id" v-model="i.value" :label="i.text" :color="org.base_color" />
      </div>
      <div v-if="i.type === 'text'">
        <v-textarea
          v-model="i.value"
          :color="org.base_color"
          :label="i.text"
          class="my-0"
          outline
        />
      </div>
      <div v-if="i.type === 'check'">
        <p style="color: rgba(0,0,0,.54);">
          {{ i.text }}
        </p>
        <v-checkbox
          v-for="n in i.items"
          :key="n.name"
          v-model="n.value"
          :color="org.base_color"
          :label="n.name"
          class="my-0"
        />
      </div>
      <div v-if="i.type === 'select'">
        <v-radio-group v-model="i.value" :label="i.text" :color="org.base_color">
          <v-radio
            v-for="n in i.options"
            :key="n.name"
            :color="org.base_color"
            :label="n.name"
            :value="n.name"
          />
        </v-radio-group>
      </div>
    </div>
  </div>
</template>

<script>
import UploadForm from './UploadForm'
export default {
  name: 'CustomForm',
  components: { UploadForm },
  props: {
    value: {
      type: Array,
      required: true
    },
    org: {
      type: Object,
      required: true
    },
    id: {
      type: Number,
      required: true
    },
    external: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    formPart: []
  }),
  watch: {
    formPart: {
      handler (value) {
        this.$emit('input', value)
      },
      deep: true
    }
  },
  mounted () {
    setTimeout(() => {
      this.formPart = JSON.parse(JSON.stringify(this.value))
    }, 200)
  }
}
</script>
