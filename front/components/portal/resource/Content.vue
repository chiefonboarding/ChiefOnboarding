<template>
  <div>
    <h1 style="margin-bottom: 20px">
      {{ resourceItem.name }}
    </h1>
    <h3 style="margin-bottom: 20px">
      {{ item.name }}
    </h3>
    <div v-if="!item.has_questions" v-html="mustaching(item.content)" />
    <div v-else>
      <QuestionsForm :id="item.id" :questions="item.questions" @addedAnswers="getAnswers" />
    </div>
    <DownloadFiles :files="item.files" />
    <v-divider v-if="resourceItem.resource.length !== 1" :color="$store.state.baseInfo.color" style="margin: 30px 10% 10px" />
    <v-row>
      <v-col sm="6">
        <v-row @click="prevOne()" class="hover">
          <v-col sm="1" style="margin-left: 10px;">
            <div v-if="index !== 0">
              <i class="fas fa-chevron-left" style="font-size: 30px;color: rgb(216, 216, 216); margin-top: 10px;" />
            </div>
          </v-col>
          <v-col sm="11">
            <div v-if="index !== 0">
              <p style="margin-top:14px">
                {{ previous.name }}
              </p>
            </div>
          </v-col>
        </v-row>
      </v-col>
      <v-col sm="6">
        <v-row @click="nextOne()" class="hover">
          <v-col sm="11" style="text-align:right">
            <div v-if="notMax">
              <p style="margin-top:14px; margin-right: 10px;">
                {{ next.name }}
              </p>
            </div>
          </v-col>
          <v-col sm="1" style="margin-right: 10px;">
            <div v-if="notMax">
              <i class="fas fa-chevron-right" style="font-size: 30px;color: rgb(216, 216, 216); margin-top: 10px;" />
            </div>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import Mustache from 'mustache'
import $ from 'jquery'
import QuestionsForm from './QuestionsForm'
import DownloadFiles from '@/components/preboarding/DownloadFiles'
export default {
  components: { DownloadFiles, QuestionsForm },
  data: () => ({
    answers: [],
    gettingAnswers: true,
    questions: [],
    loading: false,
    submitting: false
  }),
  computed: {
    resourceItem () {
      if (this.$route.query.id !== undefined) { return this.$store.state.resources.find(a => parseInt(this.$route.query.id) === a.id) }
      return {}
    },
    index () {
      if (this.$route.query.chapter !== undefined) { return this.$route.query.chapter }
      return 0
    },
    item () {
      return this.resourceItem.resources[this.index].chapter
    },
    previous () {
      return this.resourceItem.resources[this.index - 1].chapter
    },
    next () {
      if (this.resourceItem.resources[this.index + 1] !== undefined) { return this.resourceItem.resources[this.index + 1].chapter }
      return undefined
    },
    notMax () {
      return this.resourceItem.resources[this.index + 1] !== undefined
    }
  },
  watch: {
    '$route' (to, from) {
      this.$newhirepart.seenResource(this.item.id, this.index)
      this.questions = this.item.questions
      setTimeout(() => {
        $('iframe').wrap('<div class="video-container"></div>')
      }, 100)
    }
  },
  mounted () {
    setTimeout(() => {
      this.$newhirepart.seenResource(this.item.id, this.item.index)
      this.questions = this.item.questions
    }, 100)
    setTimeout(() => {
      $('iframe').wrap('<div class="video-container"></div>')
    }, 100)
  },
  methods: {
    mustaching (content) {
      return Mustache.render(content, this.$store.state.baseInfo)
    },
    nextOne () {
      this.$router.push({ name: 'portal-resource', query: { id: this.$route.query.id, chapter: this.index + 1 } })
      this.$store.commit('addStatusToResource', { id: this.$route.query.id, index: this.index + 1 })
    },
    prevOne () {
      this.$router.push({ name: 'portal-resource', query: { id: this.$route.query.id, chapter: this.index - 1 } })
    },
    getAnswers () {
      if (this.resourceItem.resources.find(a => a.resource.index === this.index + 1) !== undefined) {
        this.nextOne()
      } else {
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.courseCompleted'))
        this.$router.push({ 'name': 'portal-todo' })
      }
    }
  }
}
</script>

<style scoped>
.hover {
  cursor: pointer;
}
.hover:hover {
  background-color: #f3f3f3;
}
</style>
