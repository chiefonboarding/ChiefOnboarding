<template>
  <div>
    <div v-for="(i, index) in content" :key="index">
      <p v-if="i.type === 'p'">
        <span v-html="mustaching(i.content)" />
      </p>
      <h1 v-if="i.type === 'h1'">
        <span v-html="mustaching(i.content)" />
      </h1>
      <h2 v-if="i.type === 'h2'">
        <span v-html="mustaching(i.content)" />
      </h2>
      <h3 v-if="i.type === 'h3'">
        <span v-html="mustaching(i.content)" />
      </h3>
      <ul v-if="i.type === 'ul'" class="mb-3">
        <li v-for="j in i.items">
          <span v-html="mustaching(j.content)" />
        </li>
      </ul>
      <h3 v-if="i.type === 'file'">
        <label>Files</label><br>
        <v-chip v-for="(file, _index) in i.files" :key="_index" @click="downloadFile(file)">
          {{ file.name }}
        </v-chip>
      </h3>
      <h3 v-if="i.type === 'image' && i.files.length">
        <v-img :src="i.files[0].file_url" />
      </h3>
      <div v-if="i.type === 'youtube'">
        <iframe
          v-if="getYoutubeLink(i.content) !== ''"
          :src="getYoutubeLink(i.content)"
          width="560"
          height="315"
          frameborder="0"
          allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen
        />
      </div>
      <blockquote
        v-if="i.type === 'quote'"
        :style="'border-left-color: ' + $store.state.baseInfo.org.base_color"
      >
        {{ i.content }}
      </blockquote>
    </div>
  </div>
</template>

<script>
import Mustache from 'mustache'
export default {
  name: 'ContentDisplay',
  props: {
    content: {
      default: () => { return [] },
      type: Array
    },
    disableMustache: {
      default: false,
      type: Boolean
    }
  },
  methods: {
    getYoutubeLink (value) {
      // eslint-disable-next-line no-useless-escape
      const youtubeReg = /.*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]*).*/
      if (value.trim().match(youtubeReg) !== null && value.trim().match(youtubeReg).length === 2) {
        return 'https://youtube.com/embed/' + value.trim().match(youtubeReg)[1]
      }
      return ''
    },
    mustaching (content) {
      if (this.disableMustache) { return content }
      if (content === undefined) { return '' }
      return Mustache.render(content, this.$store.state.baseInfo.new_hire || this.$store.state.admins[0])
    },
    downloadFile (file) {
      this.$newhirepart.getFileURL(file.id, file.uuid).then((item) => {
        window.open(item, '_blank')
      })
    }
  }
}
</script>

<style>
h1, h2, h3 {
  margin-bottom: 10px;
}
blockquote {
  margin-top: 10px;
  margin-bottom: 10px;
  padding: 20px 30px;
  background: #f9f9f9;
  border-left: 2px solid #ffbb42;
}
p {
  margin-bottom: 20px !important;
}
</style>
