<template>
  <v-timeline-item
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
            @change="changeTodos"
            item-text="name"
            item-value="id"
            multiple
            chips
          />
        </div>
        <div v-if="i.condition_type === 0">
          <span style="font-size: 15px;"> {{ $t('sequence.onDay') }}
            <v-text-field
              :value="i.days"
              @change="changeDays"
              required
              type="number"
              style="display:inline-block; margin: 0px 5px; padding: 0px; width: 50px;"
            />
          </span>
        </div>
        <div v-if="i.condition_type === 2">
          <span style="font-size: 15px;">
            <v-text-field
              :value="i.days"
              @change="changeDays"
              required
              type="number"
              style="display:inline-block; margin: 0px 5px; padding: 0px; width: 50px;"
            />
            <span v-if="i.days > 1">{{ $t('sequence.daysBeforeStarting') }}</span>
            <span v-else> {{ $t('sequence.dayBeforeStarting') }} </span>
          </span>
        </div>
        <div @click="selfRemove" class="red-remove" style="position: absolute; top: 10px; right: 15px;">
          <i style="cursor:pointer;" class="far fa-times-circle" />
        </div>
      </v-card-title>
      <v-card-text class="white text--primary">
        <v-chip v-if="hasNewHireItems" label small style="margin: 5px 0px;">
          {{ $t('sequence.addToNewHire') }}
        </v-chip>
        <CardLine :index="index" :items="i.to_do" @openItem="openModal" type="to_do" />
        <CardLine :index="index" :items="i.resources" @openItem="openModal" type="resources" />
        <CardLine :index="index" :items="i.badges" @openItem="openModal" type="badges" />
        <CardLine :index="index" :items="i.introductions" @openItem="openModal" type="introductions" />
        <CardLine :index="index" :items="getNewHireItems(1)" @openItem="openModal" type="slack_messages" />
        <CardLine :index="index" :items="getNewHireItems(2)" @openItem="openModal" type="text_messages" />
        <CardLine :index="index" :items="getNewHireItems(0)" @openItem="openModal" type="emails" />

        <v-chip v-if="hasAdminItems" label small style="margin: 5px 0px;">
          {{ $t('sequence.addToAdmin') }}
        </v-chip>
        <CardLine :index="index" :items="i.admin_tasks" @openItem="openModal" type="admin_tasks" />
        <CardLine :index="index" :items="getAdminItems(2)" @openItem="openModal" type="text_messages" />
        <CardLine :index="index" :items="getAdminItems(0)" @openItem="openModal" type="emails" />
        <CardLine :index="index" :items="getAdminItems(1)" @openItem="openModal" type="slack_messages" />

        <v-row v-if="!someItems">
          <v-col sm="12">
            {{ $t('sequence.startByDropping') }}
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-timeline-item>
</template>

<script>
import CardLine from './CardLine'
export default {
  name: 'TimelineItem',
  components: { CardLine },
  props: {
    i: {
      type: Object,
      required: true
    },
    index: {
      type: Number,
      default: -1
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
    errors: {}
  }),
  computed: {
    hasNewHireItems () {
      return this.i.to_do.length || this.i.resources.length || this.i.badges.length || this.i.introductions.length ||
        this.i.external_messages.filter(a => a.person_type === 0).length
    },
    hasAdminItems () {
      return this.i.admin_tasks.length || this.i.external_messages.filter(a => a.person_type !== 0).length
    },
    someItems () {
      return this.hasNewHireItems || this.hasAdminItems
    }
  },
  methods: {
    getAdminItems (type) {
      return this.i.external_messages.filter(a => a.person_type !== 0 && a.send_via === type)
    },
    getNewHireItems (type) {
      return this.i.external_messages.filter(a => a.person_type === 0 && a.send_via === type)
    },
    selfRemove () {
      this.$store.commit('sequences/removeTimeLineItem', { index: this.index })
    },
    openModal (item) {
      this.$emit('sendBack', item)
    },
    changeTodos (value) {
      this.$store.commit('sequences/changeCondition', { 'index': this.index, 'conditions': value })
    },
    changeDays (value) {
      this.$store.commit('sequences/changeConditionDay', { 'index': this.index, 'day': value })
    }
  }
}
</script>

<style scoped>
</style>
