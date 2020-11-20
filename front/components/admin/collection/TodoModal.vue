<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="1000"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('todo.item') }}
      </v-card-title>

      <v-card-text>
        <TodoForm ref="form" v-model="tempToDo" :errors="errors" />
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          @click="$emit('input', false)"
          text
        >
          {{ $t('buttons.cancel') }}
        </v-btn>
        <v-btn
          :loading="loading"
          @click="addToDo"
        >
          {{ $t('buttons.add') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import TodoForm from '@/components/admin/todo/Form'
export default {
  name: 'TodoModal',
  components: { TodoForm },
  props: {
    toDo: {
      type: Object,
      required: true
    },
    value: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    loading: false,
    nameError: [],
    errors: {},
    tempToDo: { name: '', due_on_day: 1, content: [], tags: [], form: [], send_back: false, channel: '', template: false }
  }),
  watch: {
    value (value) {
      if (Object.entries(this.toDo).length === 0) {
        this.tempToDo = { name: '', due_on_day: 1, content: [], tags: [], form: [], send_back: false, channel: '', template: false }
      } else {
        this.tempToDo = JSON.parse(JSON.stringify(this.toDo))
        this.tempToDo.template = false
      }
      this.$store.commit('refreshEditor')
    }
  },
  methods: {
    addToDo () {
      let remove = -1
      if (JSON.stringify(this.tempToDo) !== JSON.stringify(this.toDo)) {
        if ('id' in this.tempToDo) {
          remove = this.tempToDo.task_id
          delete this.tempToDo.id
        }
        this.tempToDo.template = false
        this.loading = true
        this.$todos.create(this.tempToDo).then((data) => {
          data.type = 'todo'
          this.$emit('change', { 'add': data, remove })
          this.$emit('input', false)
        }).catch((error) => {
          this.errors = error
          this.$store.dispatch('showSnackbar', this.$t('todo.couldNotSave'))
        }).finally(() => {
          this.loading = false
        })
      } else {
        this.$emit('input', false)
      }
    }
  }
}
</script>
