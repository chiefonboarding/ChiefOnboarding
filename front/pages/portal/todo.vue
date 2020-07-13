<template>
  <v-container style="max-width: 800px">
    <v-card class="px-10 pb-10" outlined>
      <LoadingIcon :color="$store.state.baseInfo.org.base_color" :is-loading="loading" class="mt-4" />
      <v-row v-if="!loading && overdueToDoItems.length > 0">
        <v-col>
          <v-subheader class="list-header" style="color:indianred;">
            {{ $t('newHirePortal.overdue') }}
          </v-subheader>
          <div v-for="i in overdueToDoItems" :key="i.id" class="upper">
            <ToDoItem :to-do="i" />
            <v-divider />
          </div>
        </v-col>
      </v-row>
      <v-row v-for="(value, preopertyName) in toDoItems" :key="preopertyName">
        <v-col xs="12" mb="4">
          <v-subheader class="list-header">
            {{ preopertyName | toCalendar }}
          </v-subheader>
          <div v-for="i in value" :key="i.id" class="upper">
            <ToDoItem :to-do="i" />
            <v-divider />
          </div>
        </v-col>
      </v-row>
      <v-dialog v-model="reward" persistent max-width="690">
        <v-card>
          <v-card-title class="headline">
            {{ badge.name }}
          </v-card-title>
          <v-card-text>
            <div v-if="badge.url !== ''" style="text-align:center">
              <img :src="badge.url" style="max-width: 40px; max-height: 40px; margin: 0 auto">
            </div>
            <div>{{ badge.content }}</div>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn :color="$store.state.baseInfo.color" @click="reward = false" style="color: white">
              {{ $t('buttons.close') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-card>
    <v-card v-if="badges.length" class="pa-4 px-10 mt-10" outlined>
      <LoadingIcon :color="$store.state.baseInfo.org.base_color" :is-loading="loadingBadges" />
      <div v-for="i in badges">
        <v-img
          v-if="i.image != ''"
          :max-width="30"
          :max-height="30"
          :key="i.name"
          :src="i.image"
          @click="badge=i; showBadgeModal=true"
          @close="showBadgeModal=false"
          style="cursor:pointer"
        />
        <font-awesome-icon
          v-else
          :icon="['fas', 'certificate']"
          @click="badge=[i]; showBadgeModal=true"
          :color="$store.state.baseInfo.org.base_color"
          style="cursor:pointer"
        />
      </div>
    </v-card>
    <BadgeModal :badge="badge" :showModal="showBadgeModal" @close="showBadgeModal = false" />
  </v-container>
</template>

<script>
import moment from 'moment'
import _ from 'lodash'
import ToDoItem from '@/components/portal/todo/ToDoItem'
import BadgeModal from '@/components/portal/badge/BadgeModal'

export default {
  layout: 'newhire',
  name: 'ToDoPart',
  components: { ToDoItem, BadgeModal },
  filters: {
    toCalendar (value) {
      return moment(value).calendar(null, {
        sameDay: '[Today]',
        nextDay: '[Tomorrow]',
        nextWeek: 'dddd',
        lastDay: '[Yesterday]',
        lastWeek: '[Last] dddd',
        sameElse: 'MM/DD/YYYY'
      })
    }
  },
  data: () => ({
    loading: true,
    loadingBadges: true,
    todos: [],
    upcommingTodos: [],
    overdueToDoItems: [],
    toDoItems: [],
    reward: false,
    badges: [],
    badge: {},
    showBadgeModal: false
  }),
  mounted () {
    this.getNewHireTodos()
    this.getBadges()
  },
  methods: {
    getNewHireTodos () {
      const start = moment(this.$store.state.baseInfo.new_hire.start_day)
      this.$newhirepart.getToDo().then((data) => {
        data.forEach((a) => {
          a.to_do.due_date = this.addWeekdays(start, a.to_do.due_on_day - 1).format('YYYY-MM-DD')
          a.to_do.completed = a.completed
          a.to_do.to_do_user_id = a.id
        })
        data = data.map(a => a.to_do)
        this.overdueToDoItems = data.filter(a => a.due_date < moment().format('YYYY-MM-DD'))
        this.toDoItems = data.filter(a => a.due_date >= moment().format('YYYY-MM-DD'))
        this.toDoItems = _.groupBy(this.toDoItems, 'due_date')
      }).catch(() => {
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.couldNotGetTasks'))
      }).finally(() => {
        this.loading = false
      })
    },
    getBadges () {
      this.loadingBadges = true
      this.$newhirepart.getBadges().then((data) => {
        this.badges = data
      }).finally(() => {
        this.loadingBadges = false
      })
    },
    addWeekdays (date, days) {
      if (days <= 0) { return date }
      let currentDay = date.isoWeekday()
      let amountDaysToAdd = 0
      while (days !== 0) {
        if (currentDay !== 6 && currentDay !== 7) {
          days -= 1
        }
        amountDaysToAdd += 1
        currentDay += 1
        if (currentDay === 8) { currentDay = 1 }
      }
      return date.add(amountDaysToAdd, 'days')
    }
  }
}
</script>

<style scoped>
.upper:hover {
  background-color: #f3f3f3;
}
.item svg {
  color: #909090;
  font-size: 19px !important;
}
</style>
