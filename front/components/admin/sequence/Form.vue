<template>
  <div>
    <v-container class="py-0">
      <v-row>
        <v-col sm="12">
          <v-text-field
            :value="$store.state.sequences.item.name"
            :label="$t('forms.title')"
            :error-messages="tempErrors.name"
            @keyup="updateSequenceName"
          />
        </v-col>
      </v-row>
      <v-row v-if="!$store.state.sequences.sequence.length && !$store.state.sequences.hasPreboarding && !$store.state.sequences.hasAutoAdd" align="center" justify="center" row fill-height>
        <p> {{ $t('sequence.startByAdding') }}</p>
      </v-row>
      <v-timeline v-else align-top style="padding-top: 0px;" dense>
        <v-timeline-item
          fill-dot
          class="white--text mb-5"
          color="primary"
          large
        >
          <span slot="icon">{{ $t('sequence.start') }}</span>
        </v-timeline-item>
        <PreboardingPart
          v-model="collection.preboarding"
          v-if="$store.state.sequences.hasPreboarding"
          @openPreview="dialog = true"
          @openAccessModal="preboardingDialog = true"
        />
        <drop @drop="handleUnconditionedDrop(...arguments)">
          <AutoAddTimeLineItem
            v-model="collection"
            v-if="$store.state.sequences.hasAutoAdd"
            @sendBack="openItem"
          />
        </drop>
        <div v-for="(i, index) in $store.state.sequences.sequence" :key="index">
          <drop @drop="handleDrop(index, ...arguments)">
            <TimelineItem :i="i" :index="index" @sendBack="openItem" />
          </drop>
        </div>
        <v-timeline-item
          fill-dot
          class="white--text mt-5"
          color="primary"
          large
        >
          <span slot="icon">{{ $t('sequence.end') }}</span>
        </v-timeline-item>
      </v-timeline>
    </v-container>
    <ExternalMessageModal v-model="openExternalMessageModal" :item="item" :send-via="externalType" :index="index" />
    <TaskModal v-model="openTaskModal" :task="adminTask" :index="index" :child-index="childIndex" />
    <ToDoModal v-model="openToDoModal" :to-do="toDo" :index="index" :child-index="childIndex" />
    <BadgeModal v-model="openBadgeModal" :badge="badge" :index="index" :child-index="childIndex" />
    <ResourceModal v-model="openResourceModal" :resource="resource" :index="index" :child-index="childIndex" />
  </div>
</template>

<script>
import TimelineItem from './TimelineItem'
import TaskModal from './modals/TaskModal'
import ResourceModal from './modals/ResourceModal'
import BadgeModal from './modals/BadgeModal'
import ExternalMessageModal from './modals/ExternalMessageModal'
import ToDoModal from './modals/ToDoModal'
import PreboardingPart from './PreboardingPart'
import AutoAddTimeLineItem from './AutoAddTimeLineItem'
export default {
  components: { ExternalMessageModal, TimelineItem, TaskModal, ResourceModal, BadgeModal, ToDoModal, PreboardingPart, AutoAddTimeLineItem },
  props: {
    errors: {
      required: true,
      type: Object
    }
  },
  data: vm => ({
    upHere: true,
    tempErrors: [],
    right: true,
    openTaskModal: false,
    openExternalMessageModal: false,
    openBadgeModal: false,
    openResourceModal: false,
    openToDoModal: false,
    adminTask: {},
    preboardingItem: [],
    childIndex: -1,
    index: -1,
    active: 0,
    items: { name: '', collection_items: [] },
    item: {},
    toDo: {},
    resource: {},
    badge: {},
    externalType: 0,
    collection: {
      preboarding: JSON.parse(JSON.stringify(vm.$store.state.sequences.item.preboarding)) || [],
      to_do: JSON.parse(JSON.stringify(vm.$store.state.sequences.item.to_do)) || [],
      resources: JSON.parse(JSON.stringify(vm.$store.state.sequences.item.resources)) || [],
      appointments: JSON.parse(JSON.stringify(vm.$store.state.sequences.item.appointments)) || [],
      introductions: JSON.parse(JSON.stringify(vm.$store.state.sequences.item.introductions)) || []
    }
  }),
  mounted () {
    this.$store.commit('setRightSideBar', true)
    this.$store.commit('toggleLeftDrawer', true)
    this.$store.commit('sequences/resetPreboarding')
    if (this.$store.state.sequences.item.preboarding.length) {
      this.$store.commit('sequences/hasPreboarding')
    }
  },
  watch: {
    errors (value) {
      this.tempErrors = JSON.parse(JSON.stringify(value))
    }
  },
  methods: {
    updateSequenceName (value) {
      this.tempErrors.name = []
      this.$store.commit('sequences/setSequenceName', value.target.value)
    },
    handleDrop (index, data) {
      if (data.type === 'introductions') {
        this.$store.dispatch('showSnackbar', 'You can\'t add introductions here')
        return
      }
      this.index = index
      this.childIndex = -1
      const conditionType = this.$store.state.sequences.sequence[index].condition_type
      if (conditionType === 2 && (['to_do', 'resources', 'badges'].includes(data.type))) {
        this.$store.dispatch('showSnackbar', this.$t('sequence.beforeStart'))
        return false
      }
      if (data.type === 'admin_tasks') {
        this.openTaskModal = true
        this.adminTask = {}
      } else if ([0, 1, 2].includes(data.type)) {
        this.item = {}
        this.externalType = data.type
        this.openExternalMessageModal = true
      } else if (data.type === 'to_do' && data.item.id === -1) {
        this.openToDoModal = true
        this.toDo = {}
      } else if (data.type === 'resources' && data.item.id === -1) {
        this.resource = {}
        this.openResourceModal = true
      } else if (data.type === 'badges' && data.item.id === -1) {
        this.openBadgeModal = true
        this.badge = {}
      } else {
        this.$store.commit('sequences/addItem', { block: this.index, item: data.item, type: data.type })
      }
    },
    handleUnconditionedDrop (data) {
      if (!(['to_do', 'resources', 'introductions'].includes(data.type))) {
        this.$store.dispatch('showSnackbar', this.$t('sequence.unconditionedError'))
        return false
      }
      if (data.type === 'to_do' && data.item.id === -1) {
        this.$store.dispatch('showSnackbar', 'You can\'t do this right now. Soon!')
      } else if (data.type === 'resources' && data.item.id === -1) {
        this.$store.dispatch('showSnackbar', 'You can\'t do this right now. Soon!')
      } else if (data.type === 'introductions' && data.item.id === -1) {
        this.$store.dispatch('showSnackbar', 'You can\'t do this right now. Soon!')
      } else {
        this.collection[data.type].push(data.item)
      }
    },
    openItem (item) {
      if (item.index === -1) {
        return
      }
      this.index = item.index
      this.childIndex = item._index
      if (item.type === 'text_messages' || item.type === 'emails' || item.type === 'slack_messages') {
        this.item = this.$store.state.sequences.sequence[item.index].external_messages.find(a => a.id === item.id)
        if (item.type === 'text_messages') { this.externalType = 2 }
        if (item.type === 'slack_messages') { this.externalType = 1 }
        if (item.type === 'emails') { this.externalType = 0 }
        this.openExternalMessageModal = true
      } else if (item.type === 'admin_tasks') {
        this.adminTask = this.$store.state.sequences.sequence[item.index][item.type].find(a => a.id === item.id)
        this.openTaskModal = true
      } else if (item.type === 'to_do') {
        this.toDo = this.$store.state.sequences.sequence[item.index][item.type].find(a => a.id === item.id)
        this.openToDoModal = true
      } else if (item.type === 'resources') {
        this.resource = this.$store.state.sequences.sequence[item.index][item.type].find(a => a.id === item.id)
        this.openResourceModal = true
      } else if (item.type === 'badges') {
        this.badge = this.$store.state.sequences.sequence[item.index][item.type].find(a => a.id === item.id)
        this.openBadgeModal = true
      }
    }
  }
}
</script>

<style scoped>

</style>
