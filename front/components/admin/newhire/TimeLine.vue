<template>
  <v-timeline-item
    :hide-dot="hideDot"
    class="mb-1"
    right
  >
    <v-card color="#f5f5f5">
      <v-card-title class="title" style="padding-bottom: 0px; padding-top: 5px; max-height: 70px">
        <div v-if="i.condition_type === 1" style="width: 90%">
          <v-combobox
            :value="i.condition_to_do"
            :items="$store.state.todos.all"
            :label="$t('sequence.waitFor')"
            item-text="name"
            item-value="id"
            multiple
            chips
            disabled
          />
        </div>
        <div v-if="i.condition_type === 0">
          <span style="font-size: 15px;">{{ i.date | toDate }}</span>
        </div>
        <div v-if="i.condition_type === 2">
          <span style="font-size: 15px;">
            {{ i.date | toDate }}
          </span>
        </div>
      </v-card-title>
      <v-card-text class="white text--primary">
        <v-chip v-if="hasNewHireItems" label small style="margin: 5px 0px;">
          {{ $t('sequence.addToNewHire') }}
        </v-chip>
        <CardLine :index="index" :removable="false" :items="i.to_do" type="to_do" />
        <CardLine :index="index" :removable="false" :items="i.resources" type="resources" />
        <CardLine :index="index" :removable="false" :items="i.badges" type="badges" />
        <CardLine :index="index" :removable="false" :items="getNewHireItems(1)" type="slack_messages" />
        <CardLine :index="index" :removable="false" :items="getNewHireItems(2)" type="text_messages" />
        <CardLine :index="index" :removable="false" :items="getNewHireItems(0)" type="emails" />

        <v-chip v-if="hasAdminItems" label small style="margin: 5px 0px;">
          {{ $t('sequence.addToAdmin') }}
        </v-chip>
        <CardLine :index="index" :removable="false" :items="i.admin_tasks" type="admin_tasks" />
        <CardLine :index="index" :removable="false" :items="getAdminItems(2)" type="text_messages" />
        <CardLine :index="index" :removable="false" :items="getAdminItems(0)" type="emails" />
        <CardLine :index="index" :removable="false" :items="getAdminItems(1)" type="slack_messages" />

        <v-chip v-if="i.to_do_due.length" label small style="margin: 7px 0px;">
          {{ $t('newhires.due') }}
        </v-chip>
        <CardLine :index="index" :removable="false" :items="i.to_do_due" remind type="to_do" />
      </v-card-text>
    </v-card>
  </v-timeline-item>
</template>

<script>
import moment from 'moment'
import CardLine from '../sequence/CardLine'

export default {
  name: 'TimelineItem',
  components: { CardLine },
  filters: {
    toDate (value) {
      return moment(value).format('dddd, MMMM D')
    }
  },
  props: {
    i: {
      type: Object,
      required: true
    },
    hideDot: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    amountOfDays: 1,
    childIndex: 0,
    openTimeModal: false,
    openTaskModal: false,
    openEmailModal: false,
    openTextModal: false,
    openResourceModal: false,
    openTodoModal: false,
    openSlackModal: false,
    openBadgeModal: false,
    newText: false,
    newTime: false,
    newEmail: false,
    newTodo: false,
    errors: {},
    index: 0
  }),
  computed: {
    hasNewHireItems () {
      return this.i.to_do.length || this.i.resources.length || this.i.badges.length ||
        this.i.external_messages.filter(a => a.person_type === 0).length
    },
    hasAdminItems () {
      return this.i.admin_tasks.length || this.i.external_messages.filter(a => a.person_type !== 0).length
    }
  },
  methods: {
    getAdminItems (type) {
      return this.i.external_messages.filter(a => a.person_type !== 0 && a.send_via === type)
    },
    getNewHireItems (type) {
      return this.i.external_messages.filter(a => a.person_type === 0 && a.send_via === type)
    }
  }
}
</script>

<style scoped>
</style>
