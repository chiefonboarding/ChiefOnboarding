<template>
  <v-row
    class="d-flex"
    justify="center"
  >
    <div v-if="url === ''">
      <v-btn @click="$refs.inputFile.click()" :loading="uploadingFile" class="secondary">
        {{ $t('Upload image') }}
      </v-btn>
    </div>
    <v-menu
      v-model="showMenu"
      v-else
      absolute
      offset-y
      style="max-width: 600px"
    >
      <template v-slot:activator="{ on }">
        <v-card
          :img="url"
          v-on="on"
          height="300"
          width="600"
        >
          <LoadingIcon :is-loading="uploadingFile" />
        </v-card>
      </template>

      <v-list>
        <v-list-item
          @click="$refs.inputFile.click()"
        >
          <v-list-item-title>{{ $t('Upload picture') }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
    <input
      ref="inputFile"
      :name="name"
      :accept="fileTypes"
      @input="change"
      type="file"
      style="display:none"
    >
  </v-row>
</template>

<script>
export default {
  name: 'ImageUploader',
  props: {
    value: {
      type: Array,
      default: () => { return [] }
    }
  },
  data: vm => ({
    fileTypes: ['image/jpg', 'image/jpeg', 'image/png'],
    url: '',
    uploadingFile: false,
    showMenu: false,
    name: 'uploader'
  }),
  watch: {
    value: {
      handler (value) {
        this.$emit('input', value)
      },
      deep: true
    }
  },
  mounted () {
    if (this.value.length) {
      this.url = this.value[0].file_url
    }
  },
  methods: {
    change (e) {
      Array.from(e.target.files).forEach((item) => {
        if (!this.fileTypes.includes(item.type)) {
          alert(this.$t('form.multiFileNotSupported'))
        } else {
          this.uploadingFile = true
          this.$org.getPreSignedURL({ name: item.name }).then((data) => {
            this.$org.uploadToAWS(data.url, item).then(() => {
              this.$org.confirmUploaded(data.id).then((fileItem) => {
                this.url = fileItem.file_url
                this.uploadingFile = false
                this.value = [fileItem]
              })
            })
          })
        }
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
