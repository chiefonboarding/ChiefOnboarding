<template>
  <v-container class="pa-6">
    <LoadingIcon :is-loading="loading" />
    <div v-if="!toDoItems.length && !courseItems.length && !loading">
      <p style="margin-bottom: 0px !important;">
        {{ $t('newhires.noProgress') }}
      </p>
    </div>
    <h3 v-if="toDoItems.length" class="mx-4" style="margin-bottom: 10px;">
      {{ $t('newhires.toDoItems') }}
    </h3>
    <v-data-table
      v-if="!loading && toDoItems.length"
      :hide-default-header="true"
      :items="toDoItems"
      :loading="loading"
      disable-pagination
      hide-default-footer
    >
      <template v-slot:body="{ items }">
        <tr v-for="item in items" :key="item.id">
          <td>
            <font-awesome-icon v-if="!item.completed" :icon="['far', 'circle']" />
            <font-awesome-icon v-else :icon="['far', 'check-circle']" />
          </td>
          <td>{{ item.to_do.name }}</td>
          <td>
            <v-tooltip v-if="!item.completed" top>
              <template v-slot:activator="{ on }">
                <v-btn
                  :loading="item.loading"
                  v-on="on"
                  @click="remindToDo(item)"
                  color="primary"
                  style="float:right; margin-right: 0px; margin-bottom: 10px"
                >
                  {{ $t('buttons.remind') }}
                </v-btn>
              </template>
              <span><span v-if="item.reminded !== null">{{ item.reminded }}</span><span v-else>Not yet reminded</span></span>
            </v-tooltip>
            <v-btn
              v-else
              :loading="item.loading"
              @click="openModal(item)"
              style="float:right; margin-right: 0px; margin-bottom: 10px"
            >
              {{ $t('buttons.reopen') }}
            </v-btn>
          </td>
        </tr>
      </template>
    </v-data-table>
    <h3 v-if="courseItems.length" class="mx-4" style="margin-top: 20px; margin-bottom: 10px;">
      {{ $t('newhires.courseItems') }}
    </h3>
    <v-data-table
      v-if="!loading && courseItems.length"
      :hide-default-header="true"
      :items="courseItems"
      :headers="headers"
      :expanded.sync="expanded"
      :loading="loading"
      hide-default-footer
      disable-pagination
      show-expand
    >
      <template v-slot:expanded-item="{ item }">
        <td :colspan="2" style="background-color:#f5f5f5; width: 100%" class="pa-4">
          <v-row>
            <v-col>
              <h2>{{ $t('newhires.answers') }}</h2>
            </v-col>
            <v-col sm="2">
              {{ $t('newhires.score') }}: {{ item.percentageCorrect }}%
            </v-col>
            <v-col sm="3">
              <v-progress-linear :value="item.percentageCorrect" style="position: relative; margin-top: 8px;" color="green" height="5" />
            </v-col>
            <v-col sm="2">
              <v-tooltip v-if="!item.completed_course" top>
                <template v-slot:activator="{ on }">
                  <v-btn
                    :loading="item.loading"
                    v-on="on"
                    @click="remindToDo(item)"
                    color="primary"
                    style="float:right; margin-right: 0px; margin-top: -7px;"
                  >
                    {{ $t('buttons.remind') }}
                  </v-btn>
                </template>
                <span><span v-if="item.reminded !== null">{{ item.reminded }}</span><span v-else>{{ $t('buttons.noRemind') }}</span></span>
              </v-tooltip>
              <v-btn
                v-else
                :loading="item.loading"
                @click="openModal(item)"
                style="float:right; margin-right: 0px; margin-top: -7px;"
              >
                {{ $t('buttons.reopen') }}
              </v-btn>
            </v-col>
          </v-row>
          <div v-for="i in item.questions" :key="i.id">
            <v-row>
              <v-col sm="1">
                <font-awesome-icon v-if="i.userAnswer === i.answer" :icon="['far', 'check-circle']" style="color: green; font-size: 25px;" class="ma-3" />
                <font-awesome-icon v-else :icon="['fas', 'times']" style="color: red" class="ma-3" />
              </v-col>
              <v-col>
                <v-radio-group v-model="i.userAnswer" :label="i.content" disabled>
                  <v-radio
                    v-for="n in i.items"
                    :key="n.id"
                    :label="n.text"
                    :value="n.id"
                  />
                </v-radio-group>
                Correct answer: {{ i.items.find(a => a.id === i.answer).text }}
              </v-col>
            </v-row>
          </div>
          <div v-if="item.answers.length === 0">
            {{ $t('newhires.noAnswers') }}
          </div>
        </td>
      </template>
    </v-data-table>
    <v-dialog v-model="dialog" persistent max-width="590">
      <v-card>
        <v-card-title class="headline">
          {{ $t('newhires.reOpenHeader') }}
        </v-card-title>
        <v-card-text>
          <p>{{ $t('newhires.reOpenDescr') }} </p>
          <v-textarea
            v-model="message"
            :label="$t('forms.messageToNewHire')"
            name="input"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="dialog = false" color="secondary" text>
            {{ $t('buttons.cancel') }}
          </v-btn>
          <v-btn :loading="reopeningTask" @click="reOpenTask()" color="primary">
            {{ $t('buttons.reopen') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import Moment from 'moment-timezone'
export default {
  data: () => ({
    courseItems: [],
    headers: [
      { value: 'resource.name' }
    ],
    answers: [],
    toDoItems: [],
    message: '',
    preboardingItemsDone: [],
    item: {},
    dialog: false,
    reopeningTask: false,
    loading: true,
    expanded: []
  }),
  mounted () {
    this.$newhires.getProgress(this.$route.params.id).then((items) => {
      items.to_do.forEach((item) => {
        if (item.reminded !== null) {
          item.reminded = this.$t('newhires.lastReminded') + ' ' + Moment(item.reminded).format('llll')
        }
      })
      this.toDoItems = items.to_do
      this.courseItems = items.resources
      this.courseItems.forEach((item) => {
        if (item.reminded !== null) {
          item.reminded = this.$t('newhires.lastReminded') + ' ' + Moment(item.reminded).format('llll')
        }
      })
      this.courseItems.forEach((userBook) => {
        let totalQuestions = 0
        let correctAnswers = 0
        userBook.questions = []
        // filter the questions
        userBook.resource.chapters = userBook.resource.chapters.filter(a => a.type === 2)
        userBook.resource.chapters.forEach((resource) => {
          if (userBook.answers.find(a => a.resource === resource.id) !== undefined) {
            resource.answers = userBook.answers.find(a => a.resource === resource.id).answers
            resource.content.forEach((question, index) => {
              question.userAnswer = resource.answers[index]
              userBook.questions.push(question)
              if (question.answer === resource.answers[index]) {
                correctAnswers++
                question.correct = true
              }
              totalQuestions++
            })
          }
        })
        userBook.percentageCorrect = correctAnswers / totalQuestions * 100
      })
    }).finally(() => {
      this.loading = false
    })
  },
  methods: {
    remindToDo (item) {
      item.loading = true
      this.$newhires.remindToDo(item.id).then(() => {
        item.reminded = this.$t('newhires.lastReminded') + ' ' + Moment().tz(this.$store.state.org.timezone).format('llll')
        this.$store.dispatch('showSnackbar', this.$t('newhires.sendReminder'))
      }).finally(() => {
        item.loading = false
      })
    },
    remindResource (item) {
      item.loading = true
      this.$newhires.remindResource(this.$route.params.id).then(() => {
        item.reminded = this.$t('newhires.lastReminded') + ' ' + Moment().tz(this.$store.state.org.timezone).format('llll')
        this.$store.dispatch('showSnackbar', this.$t('newhires.sendReminder'))
      }).finally(() => {
        item.loading = false
      })
    },
    reOpenTask () {
      this.reopeningTask = true
      if ('step' in this.item) {
        this.$newhires.reOpenResource(this.item.id, { 'message': this.message }).then(() => {
          this.item.completed_course = false
          this.item.step = 0
          this.item.resource.chapters = []
          this.dialog = false
        }).finally(() => {
          this.reopeningTask = false
        })
      } else {
        this.$newhires.reOpenToDo(this.item.id, { 'message': this.message }).then(() => {
          this.item.completed = false
          this.dialog = false
        }).finally(() => {
          this.reopeningTask = false
        })
      }
    },
    openModal (item) {
      this.dialog = true
      this.item = item
      this.message = ''
    }
  }
}
</script>
