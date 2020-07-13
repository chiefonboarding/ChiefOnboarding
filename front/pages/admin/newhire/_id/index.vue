<template>
  <v-container>
    <LoadingIcon :is-loading="loading" />
    <v-timeline v-if="!loading" align-top style="padding-top: 0px;" dense>
      <v-timeline-item
        v-if="beforeStartingDate"
        color="dark"
        icon="fas fa-star"
      >
        <v-card
          color="dark"
          dark
        >
          <v-card-title class="title" style="padding-bottom: 5px; padding-top: 5px;">
            <v-row>
              <v-col>Pre-boarding</v-col>
              <v-col>
                <v-btn @click="dialog = true" color="secondary" small class="ma-0" style="float:right">
                  {{ $t('newhires.preview') }}
                </v-btn>
                <v-btn @click="preboardingDialog = true" color="secondary" small class="ma-0" style="float:right; margin-right: 11px !important;">
                  {{ $t('newhires.giveAccess') }}
                </v-btn>
              </v-col>
            </v-row>
          </v-card-title>
          <v-card-text class="white text--primary pt-3">
            <div v-for="(i, index) in preboardingItems" :key="index" style="height: 25px; cursor: pointer">
              <i class="fas fa-align-left mar7" />{{ i.name }}
            </div>
            <p v-if="preboardingItems.length === 0">
              {{ $t('newhires.noItemsYet') }}
            </p>
          </v-card-text>
        </v-card>
      </v-timeline-item>

      <v-timeline-item
        v-if="itemsOverdue.length"
        class="mb-1"
        small
        right
        color="red"
      >
        <v-card color="#f5f5f5">
          <v-card-title class="title" style="padding-bottom: 5px;">
            {{ $t('newhires.overdue') }}
          </v-card-title>
          <v-card-text class="white text--primary pt-3">
            <CardLine :items="itemsOverdue" :index="0" :removable="false" type="to_do" remind />
          </v-card-text>
        </v-card>
      </v-timeline-item>
      <div v-for="(i, index) in timeline" :key="index">
        <NewHireTimeLine :i="i[0]" />
        <div v-for="j in i[0].follow_up_condition">
          <NewHireTimeLine :i="j" style="margin-left: 20px" hide-dot />
        </div>
      </div>
    </v-timeline>
    <v-dialog v-model="dialog" fullscreen hide-overlay transition="dialog-bottom-transition" class="mt-3">
      <v-card>
        <v-toolbar dark color="dark">
          <v-btn @click="dialog = false" icon dark>
            <v-icon>close</v-icon>
          </v-btn>
          <v-toolbar-title>{{ $t('newhires.preview') }}</v-toolbar-title>
          <v-spacer />
          <v-toolbar-items>
            <v-btn @click="dialog = false" dark text>
              {{ $t('buttons.close') }}
            </v-btn>
          </v-toolbar-items>
        </v-toolbar>
        <PreboardingPage
          :pages="preboardingItems"
          :auth-code="$store.state.admin.authToken"
          :new-hire="$store.state.newhires.all[0]"
          :org="$store.state.org"
        />
      </v-card>
    </v-dialog>
    <div v-if="noItems">
      <p> {{ $t('newhires.noOverviewTasks') }}</p>
    </div>
    <SendPreboardingModal v-model="preboardingDialog" :new-hire="newHire" @changeNewHire="newHire = arguments[0]" />
  </v-container>
</template>

<script>
import moment from 'moment'
import _ from 'lodash'
import NewHireTimeLine from '@/components/admin/newhire/TimeLine'
import SendPreboardingModal from '@/components/admin/preboarding/SendPreboardingModal'
import CardLine from '@/components/admin/sequence/CardLine'
import PreboardingPage from '@/components/preboarding/Page'
export default {
  name: 'NewHireDetailOverview',
  components: { PreboardingPage, NewHireTimeLine, CardLine, SendPreboardingModal },
  data: () => ({
    newHire: {},
    dialog: false,
    loading: true,
    noItems: false,
    preboardingDialog: false,
    items: [],
    tempNoDate: [],
    preboardingItems: [],
    timeline: [],
    itemsOverdue: []
  }),
  computed: {
    beforeStartingDate () {
      return moment(this.newHire.start_day) > moment()
    }
  },
  mounted () {
    this.getNewHire().then((data) => {
      this.getTasksTimeLine()
    })
  },
  methods: {
    getTasksTimeLine () {
      this.$newhires.getTasks(this.$route.params.id).then((items) => {
        this.loading = false
        if (items.to_do.length === 0 && items.conditions.length === 0) {
          this.noItems = true
          return
        }
        this.preboardingItems = items.preboarding
        this.items = items
        items.conditions.forEach((one) => {
          one.follow_up_condition = []
          if (one.condition_type === 0 || one.condition_type === 2) {
            one.date = this.addWeekdays(moment(this.newHire.start_day), one.days - 1).format('YYYY-MM-DD')
          }
          one.to_do_due = []
        })

        let newDate = moment()
        items.to_do.forEach((one) => {
          newDate = this.addWeekdays(moment(this.newHire.start_day), one.due_on_day - 1).format('YYYY-MM-DD')
          if (items.conditions.find(a => a.date === newDate) !== undefined) {
            items.conditions.find(a => a.date === newDate).to_do_due.push(one)
          } else {
            items.conditions.push({
              admin_tasks: [],
              badges: [],
              condition_to_do: [],
              condition_type: 0,
              date: newDate,
              external_messages: [],
              resources: [],
              follow_up_condition: [],
              to_do: [],
              to_do_due: [
                one
              ]
            })
          }
        })
        const conditionsBasedOnTime = items.conditions.filter(a => a.condition_type !== 1)
        const conditionsBasedOnToDo = items.conditions.filter(a => a.condition_type === 1)
        this.itemsOverdue = [].concat.apply([], conditionsBasedOnTime.filter(a => moment().subtract(1, 'days') > moment(a.date)).map(a => a.to_do_due))
        const timeline = conditionsBasedOnTime.filter(a => moment().subtract(1, 'days') <= moment(a.date))
        conditionsBasedOnToDo.forEach((itemBasedOnToDo) => {
          let counter = 0
          let amountOfToDoRequirements = itemBasedOnToDo.condition_to_do.length
          const conditionToDos = itemBasedOnToDo.condition_to_do.map(i => i.id)
          timeline.forEach((timelineItem) => {
            timelineItem.to_do.forEach((toDo) => {
              if (conditionToDos.includes(toDo.id)) {
                counter++
              }
            })
            timelineItem.to_do_due.forEach((toDo) => {
              if (conditionToDos.includes(toDo.id)) {
                counter++
              }
            })
            if (counter === amountOfToDoRequirements) {
              timelineItem.follow_up_condition.push(itemBasedOnToDo)
              amountOfToDoRequirements = 0
            }
          })
        })
        this.timeline = _.groupBy(timeline, 'date')
        this.timeline = Object.fromEntries(Object.entries(this.timeline).sort())
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('newhires.noTasks'))
      })
    },
    getNewHire () {
      return this.$newhires.get(this.$route.params.id).then((newHire) => {
        this.newHire = newHire
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('newhires.noNewHire'))
      })
    },
    addWeekdays (date, days) {
      if (days <= 0) { return date }
      let currentDay = date.isoWeekday()
      let amountDaysToAdd = 0
      while (days !== 0) {
        amountDaysToAdd += 1
        currentDay += 1
        if (currentDay !== 6 && currentDay !== 7) {
          days -= 1
        }
        if (currentDay === 8) { currentDay = 1 }
      }
      return date.add(amountDaysToAdd, 'days')
    }
  }
}
</script>

<style scoped>
.mar7 {
  margin-right: 7px;
  width: 12.25px
}
</style>
