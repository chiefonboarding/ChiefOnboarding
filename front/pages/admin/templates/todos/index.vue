<template>
  <TemplateComp :loading="loading" :items="$store.state.todos.all" :name="$t('todo.all')" new-url="admin-templates-todos-add" detail-page="admin-templates-todos-id" />
</template>

<script>
export default {
  layout: 'admin',
  data () {
    return {
      loading: false
    }
  },
  mounted () {
    this.loading = true
    this.$todos.getAll().finally(() => {
      this.loading = false
    })
  }
}
</script>
