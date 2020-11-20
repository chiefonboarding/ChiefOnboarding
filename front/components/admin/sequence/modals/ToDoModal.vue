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

      <v-card-text class="pa-0">
        <TodoForm v-model="tempToDo" :errors="errors" :inline="true" />
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
          @click="addToDoItem"
        >
          <span v-if="Object.entries(toDo).length">
            {{ $t('buttons.update') }}
          </span>
          <span v-else>
            {{ $t('buttons.add') }}
          </span>
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import TodoForm from '@/components/admin/todo/Form'
export default {
  name: 'ToDoModal',
  components: { TodoForm },
  props: {
    toDo: {
      type: Object,
      default: () => { return {} }
    },
    index: {
      type: Number,
      required: true
    },
    value: {
      type: Boolean,
      required: true
    }
  },
  data: () => ({
    loading: false,
    errors: {},
    tempToDo: { name: '', data: [], due_on_day: 0, content: [], tags: [], form: [], send_back: false, channel: '' }
  }),
  watch: {
    value (value) {
      if (Object.entries(this.toDo).length === 0) {
        this.tempToDo = {
          name: '',
          form: [],
          content: [],
          due_on_day: '',
          tags: [],
          send_back: false,
          channel: ''
        }
      } else {
        this.tempToDo = JSON.parse(JSON.stringify(this.toDo))
        delete this.tempToDo.id
      }
      this.$store.commit('refreshEditor')
    }
  },
  methods: {
    addToDoItem () {
      this.tempToDo.template = false
      this.loading = true
      this.$todos.create(this.tempToDo).then((data) => {
        if ('id' in this.toDo) {
          this.$store.commit('sequences/removeItem', {
            block: this.index,
            type: 'to_do',
            id: this.toDo.id
          })
        }
        this.$store.commit('sequences/addItem', { block: this.index, type: 'to_do', item: data })
        this.$emit('input', false)
      }).catch((error) => {
        this.errors = error
        this.$store.dispatch('showSnackbar', this.$t('todo.couldNotSave'))
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>
