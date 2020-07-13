<template>
  <div>
    <LoadingIcon :is-loading="gettingAnswers" :color="$store.state.baseInfo.org.base_color" />
    <div v-if="!gettingAnswers">
      <div v-if="answers.find(a => a === id) !== undefined">
        {{ $t('newHirePortal.theseQuestions') }}
      </div>
      <div v-else>
        <div v-for="i in changedQuestions" :key="i.id">
          {{ i.content }}
          <v-radio-group v-model="i.answer" :label="i.text">
            <v-radio
              v-for="n in i.items"
              :key="n.id"
              :label="n.text"
              :value="n.id"
              :color="$store.state.baseInfo.org.base_color"
            />
          </v-radio-group>
        </div>
        <v-btn
          :color="$store.state.baseInfo.org.base_color"
          :loading="submitting"
          @click="submitAnswers"
          dark
          style="margin-top: 10px !important;"
        >
          {{ $t('buttons.submit') }}
        </v-btn>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'QuestionsForm',
  props: {
    questions: {
      type: Array,
      default: () => { return [] }
    },
    org: {
      type: Object,
      default: () => { return {} }
    },
    resourceId: {
      type: Number,
      required: true
    },
    id: {
      type: Number,
      required: true
    }
  },
  data: () => ({
    answers: [],
    submitting: false,
    gettingAnswers: false,
    changedQuestions: []
  }),
  mounted () {
    this.changedQuestions = JSON.parse(JSON.stringify(this.questions))
  },
  methods: {
    submitAnswers () {
      this.submitting = true
      const newHireAnswers = []
      this.changedQuestions.forEach((one) => {
        if ('answer' in one) {
          newHireAnswers.push(one.answer)
        }
      })
      this.$newhirepart.addCourseAnswer(this.id, { id: this.resourceId, answers: newHireAnswers }).then(() => {
        this.$emit('completed')
      }).catch(() => {
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.couldNotSendAnswers'))
      }).finally(() => {
        this.submitting = false
      })
    }
  }
}
</script>
