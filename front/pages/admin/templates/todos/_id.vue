<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('todo.changeHeader') }}
      </h1>
    </template>
    <template slot="header-right">
      <v-btn :loading="duplicating" @click="duplicateTodo" color="secondary">
        {{ $t('buttons.duplicate') }}
      </v-btn>
      <v-btn :loading="removing" @click="removeTodo" color="error" style="margin-right: 0px;">
        {{ $t('buttons.remove') }}
      </v-btn>
    </template>
    <template slot="formpart">
      <LoadingIcon :is-loading="loading" />
      <TodoForm ref="form" v-if="!loading" v-model="todo" :errors="errors" />
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
  data () {
    return {
      loading: true,
      saving: false,
      duplicating: false,
      removing: false,
      submittingForm: false,
      errors: {},
      employee: {},
      todo: {}
    }
  },
  watch: {
    '$route' (to, from) {
      this.getTodo()
    }
  },
  mounted () {
    this.getTodo()
  },
  methods: {
    getTodo () {
      return this.$todos.get(this.$route.params.id).then((data) => {
        this.todo = data
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('todo.couldNotGet'))
      }).finally(() => {
        this.loading = false
      })
    },
    saveTodo () {
      this.saving = true
      this.$todos.update(this.$route.params.id, this.todo).then((data) => {
        this.$router.push({ name: 'admin-templates-todos' })
        this.$store.dispatch('showSnackbar', this.$t('todo.updated'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    },
    removeTodo () {
      this.removing = true
      this.$todos.remove(this.$route.params.id).then((data) => {
        this.$router.push({ name: 'admin-templates-todos' })
        this.$store.dispatch('showSnackbar', this.$t('todo.removed'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.removing = false
      })
    },
    duplicateTodo () {
      this.duplicating = true
      this.$todos.update(this.$route.params.id, this.todo).then((data) => {
        this.$todos.duplicate(this.$route.params.id).then((data) => {
          this.$router.push({ name: 'admin-templates-todos' })
          this.$store.dispatch('showSnackbar', this.$t('todo.savedAndDuplicated'))
        }).catch((error) => {
          this.errors = error
        }).finally(() => {
          this.duplicating = false
        })
      })
    }
  }
}
</script>

<style scoped>
.border-bottom {
  border-bottom: 1px solid rgb(228, 228, 228);
}
.second {
  margin-left: 10px;
}
.first {
  margin-right: 10px;
}
</style>
