<template>
  <div>
    <h3 v-if="files !== undefined && files.length > 0">
      {{ $t('newHirePortal.files') }}
    </h3>
    <a v-for="(i, index) in files" :key="index" :style="'color: ' + $store.state.baseInfo.color" @click="downloadFile(i)" target="_blank">
      <div>
        <span v-if="i.ext === 'png'" class="image-setoff"><i class="far fa-image" /></span>
        <span v-if="i.ext === 'jpg'" class="image-setoff"><i class="far fa-image" /></span>
        <span v-if="i.ext === 'jpeg'" class="image-setoff"><i class="far fa-image" /></span>
        <span v-if="i.ext === 'docx'" class="image-setoff"><i class="far fa-file-word" /></i></span>
        <span v-if="i.ext === 'doc'" class="image-setoff"><i class="far fa-file-word" /></i></span>
        <span v-if="i.ext === 'pdf'" class="image-setoff"><i class="far fa-file-pdf" /></span>
        <span v-if="i.ext === 'ppt'" class="image-setoff"><i class="far fa-file-powerpoint" /></span>
        <span v-if="i.ext === 'pptx'" class="image-setoff"><i class="far fa-file-powerpoint" /></span>
        <span v-if="i.ext === 'xls'" class="image-setoff"><i class="far fa-file-excel" /></span>
        <span v-if="i.ext === 'xlsx'" class="image-setoff"><i class="far fa-file-excel" /></span>
        <span v-if="i.ext === 'txt'" class="image-setoff"><i class="far fa-file-alt" /></span>
        {{ i.name | truncate }}
      </div>
    </a>
  </div>
</template>

<script>
export default {
  name: 'Files',
  filters: {
    truncate (string) {
      return (string.length > 25) ? string.substring(0, 25) + '...' : string
    }
  },
  props: {
    files: {
      required: true,
      type: Array
    }
  },
  data: () => ({
    url: '',
    loading: false
  }),
  methods: {
    downloadFile (item) {
      this.$newhirepart.downloadFile(item.id).then((data) => {
        window.open(data.url, '_blank').focus()
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.couldNotGetFile'))
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.image-setoff {
  margin-right: 10px;
}
</style>
