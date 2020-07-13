<template>
  <div>
    <div @click="openToDo" class="item">
      <font-awesome-icon v-if="!toDo.completed" :icon="['far', 'circle']" />
      <font-awesome-icon v-else :icon="['far', 'check-circle']" />
      <span style="margin-left: 10px;position: relative;">{{ mustaching(toDo.name) }}</span>
    </div>
    <ToDoModal :to-do="toDo" :show-modal="showToDoModal" @close="showToDoModal = false" @showBadge="showBadge" />
    <BadgeModal :badge="badge" :showModal="showBadgeModal" @close="showBadgeModal = false" />
  </div>
</template>

<script>
import Mustache from 'mustache'
import ToDoModal from './ToDoModal'
import BadgeModal from '@/components/portal/badge/BadgeModal'

export default {
  name: 'ToDoItem',
  components: { ToDoModal, BadgeModal },
  props: {
    toDo: {
      required: true,
      type: Object
    }
  },
  data: () => ({
    showToDoModal: false,
    showBadgeModal: false,
    badge: []
  }),
  methods: {
    mustaching (content) {
      if (content === undefined) { return '' }
      return Mustache.render(content, this.$store.state.baseInfo)
    },
    openToDo () {
      if (this.toDo.completed) { return }
      this.showToDoModal = true
    },
    showBadge (badges) {
      this.badge = badges
      this.showBadgeModal = true
    }
  }
}
</script>

<style>
.item {
  padding: 12px 10px 9px;
  cursor: pointer;
}
</style>
