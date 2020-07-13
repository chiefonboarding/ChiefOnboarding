<template>
  <div>
    <v-row v-for="(item, _index) in items" :key="_index">
      <v-col :class="{'pointer': removable}" @click="sendToParent(_index, item.id)" sm="11" class="py-0">
        <i :class="icon.icon + ' mar7'" />
        <span v-if="type === 'task'">{{ item.todo }}</span>
        <span v-else>{{ item.name }}</span>
        <v-btn
          v-if="remind && !item.checked"
          :disabled="!('task_id' in item)"
          :loading="item.loading"
          @click="remindNewHire(item)"
          small
          style="margin: 0px 10px"
        >
          {{ $t('sequence.remindNewHire') }}
        </v-btn>
      </v-col>
      <v-col v-if="removable" @click="remove(item.id)" sm="1" class="red-remove py-0">
        <i :class="{'pointer': removable}" class="far fa-times-circle" style="top: 2px;position: relative;" />
      </v-col>
    </v-row>
  </div>
</template>

<script>
export default {
  props: {
    index: {
      type: Number,
      required: true
    },
    type: {
      type: String,
      required: true
    },
    items: {
      type: Array,
      required: true
    },
    removable: {
      default: true,
      type: Boolean
    },
    remind: {
      default: false,
      type: Boolean
    }
  },
  data: () => ({
    icons: [
      { name: 'slack_messages', icon: 'fab fa-slack-hash' },
      { name: 'to_do', icon: 'far fa-check-square' },
      { name: 'resources', icon: 'far fa-folder' },
      { name: 'badges', icon: 'far fa-arrow-alt-circle-right' },
      { name: 'text_messages', icon: 'far fa-comment' },
      { name: 'emails', icon: 'far fa-envelope' },
      { name: 'admin_tasks', icon: 'fas fa-tasks' },
      { name: 'appointments', icon: 'far fa-calendar-alt' },
      { name: 'preboarding', icon: 'fas fa-align-left' },
      { name: 'introductions', icon: 'far fa-user-circle' }
    ]
  }),
  computed: {
    icon () {
      return this.icons.find(a => a.name === this.type)
    }
  },
  methods: {
    remove (itemId) {
      this.$store.commit('sequences/removeItem', { block: this.index, id: itemId, type: this.type })
    },
    sendToParent (index, itemId) {
      this.$emit('openItem', { index: this.index, _index: index, type: this.type, id: itemId })
    },
    remindNewHire (item) {
      item.loading = true
      this.$newhires.remindToDo(item.task_id).then(() => {
        item.reminded = new Date()
        this.$store.dispatch('showSnackbar', this.$t('sequence.reminderSent'))
      }).finally(() => {
        item.loading = false
      })
    }
  }
}
</script>

<style scoped>
.mar7 {
  margin-right: 7px;
  width: 12.25px
}
.pointer {
  cursor: pointer
}
.red-remove {
  margin-top: -2px;
}
</style>
