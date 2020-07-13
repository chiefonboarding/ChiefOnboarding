<template>
  <div class="v-file">
    <div class="items">
      <v-chip v-for="(i, index) in value" :key="index" @click:close="removeFile(i, index)" close style="margin: 4px 4px 0px 0px;">
        <v-progress-circular v-if="i.loading" indeterminate color="primary" style="width: 17px;margin-right: 10px;" />{{ i.name }}
      </v-chip>
      <v-btn @click="$refs.inputFile.click()" icon style="margin: 5px 0 0 0">
        <v-icon>cloud_upload</v-icon>
      </v-btn>
    </div>
    <input
      ref="inputFile"
      :name="name"
      :accept="accept"
      @input="change"
      type="file"
      multiple
      style="display:none"
    >
  </div>
</template>

<script>
export default {
  name: 'VFile',
  props: {
    value: {
      type: Array,
      default: () => { return [] }
    },
    accept: {
      type: String,
      default: 'image/png;image/jpg;image/jpeg;image/gif;application/msword;application/vnd.openxmlformats-officedocument.wordprocessingml.document;application/vnd.ms-excel;application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;application/vnd.ms-powerpoint;application/vnd.openxmlformats-officedocument.presentationml.presentationc;application/pdf'
    },
    name: {
      type: String,
      default: 'file'
    },
    forTemplate: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    filetypes: ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentationc', 'application/pdf', 'image/jpg', 'image/jpeg', 'image/png']
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
    change (e) {
      Array.from(e.target.files).forEach((item) => {
        if (!this.filetypes.includes(item.type)) {
          alert(this.$t('form.multiFileNotSupported'))
        } else {
          this.value.push({ 'name': item.name, 'id': -1, 'loading': true })
          this.$org.getPreSignedURL({ name: item.name }).then((data) => {
            this.$org.uploadToAWS(data.url, item).then(() => {
              this.$org.confirmUploaded(data.id).then((fileItem) => {
                const fileIndex = this.value.findIndex(a => fileItem.name === a.name)
                this.value.splice(fileIndex, 1, fileItem)
              })
            })
          })
        }
      })
    },
    removeFile (item, index) {
      if (item.loading) {
        alert(this.$t('forms.errors.uploading'))
        return
      }
      item.loading = true
      this.$org.removeFile(item.id).then(() => {
        item.loading = false
        this.value.splice(index, 1)
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
