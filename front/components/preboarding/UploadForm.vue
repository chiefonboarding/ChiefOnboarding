<template>
  <v-file-input
    v-model="files"
    :color="color"
    :label="label"
    @change="upload"
    class="mt-2"
    placeholder="Select your file"
    prepend-icon="mdi-paperclip"
    outlined
  />
</template>

<script>
export default {
  name: 'UploadNewHireFile',
  props: {
    value: {
      type: Array,
      default: () => { return [] }
    },
    label: {
      type: String,
      default: 'File input'
    },
    color: {
      required: true,
      type: String
    }
  },
  data: vm => ({
    uploadingFile: false
  }),
  watch: {
    value: {
      handler (value) {
        this.$emit('input', value)
      },
      deep: true
    }
  },
  methods: {
    upload (item) {
      this.uploadingFile = true
      this.$org.getPreSignedURL({ name: item.name }).then((data) => {
        this.$org.uploadToAWS(data.url, item).then(() => {
          this.$org.confirmUploaded(data.id).then((fileItem) => {
            this.value = fileItem
          })
        })
      })
    }
  }
}
</script>

<style scoped>
.v-file input[type='file'] {
  display: none;
}
</style>
