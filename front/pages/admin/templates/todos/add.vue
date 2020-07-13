<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('todo.addHeader') }}
      </h1>
    </template>
    <template slot="formpart" v-if="!loading">
      <LoadingIcon :is-loading="loading" />
      <TodoForm v-model="todo" :errors="errors" />
    </template>
    <template slot="footer">
      <v-btn :loading="saving" @click="saveTodo" color="primary" style="float:right">
        {{ $t('buttons.save') }}
      </v-btn>
    </template>
  </TemplateCompInner>
</template>

<script>
import TodoForm from '@/components/admin/todo/Form'
export default {
  layout: 'admin',
  components: { TodoForm },
  data: () => ({
    loading: false,
    saving: false,
    submittingForm: false,
    headers: [
      { text: 'Name', value: 'name' },
      { }
    ],
    errors: {},
    employee: {},
    todo: { name: '', form: [], due_on_day: 1, content: [], tags: [], send_back: false, channel: '' }
  }),
  methods: {
    saveTodo () {
      this.saving = true
      this.$todos.create(this.todo).then((data) => {
        this.$router.push({ name: 'admin-templates-todos' })
        this.$store.dispatch('showSnackbar', this.$t('todo.created'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    }
  }
}
</script>
