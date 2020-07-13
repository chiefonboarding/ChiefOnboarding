<template>
  <div class="v-file mt-2">
    <input ref="inputFile" :accept="['image/png', 'image/jpeg', 'image/gif']" @input="change" name="uploadField" type="file">
    <div v-if="value && Object.keys(value).length">
      <v-img :src="value.file_url" />
    </div>
    <div>
      <v-btn :loading="uploading" @click="$refs.inputFile.click()" class="ma-0 mt-2">
        <v-icon>cloud_upload</v-icon>
      </v-btn>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VFile',
  props: {
    value: {
      type: Object,
      default: () => { return {} }
    },
    logo: {
      default: false,
      type: Boolean
    }
  },
  data: () => ({
    uploading: false,
    uploadedFile: ''
  }),
  methods: {
    change (e) {
      const file = e.target.files[0]
      if (file.type !== 'image/png' && file.type !== 'image/jpg' && file.type !== 'image/jpeg' && file.type !== 'image/gif') {
        alert(this.$t('newHirePortal.notSupported'))
        return
      }
      this.uploading = true
      this.$org.getPreSignedURL({ name: file.name }).then((data) => {
        this.$org.uploadToAWS(data.url, file).then(() => {
          if (this.logo) {
            this.$org.confirmLogoUploaded(data.id).then((fileItem) => {
              this.$emit('input', fileItem)
              this.uploading = false
            })
          } else {
            this.$org.confirmUploaded(data.id).then((fileItem) => {
              this.$emit('input', fileItem)
              this.uploading = false
            })
          }
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
