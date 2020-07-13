<template>
  <v-data-table
    :headers="headers"
    :items="tasks"
    :loading="loading"
    @click:row="goTo"
    hide-default-footer
    class="elevation-1"
    disable-pagination
  >
    <template v-slot:item.assigned_to.assigned_to="{ item }">
      {{ item.assigned_to.full_name }}
    </template>
    <template v-slot:no-data>
      There are no to do items for this new hire (yet).
    </template>
  </v-data-table>
</template>

<script>
export default {
  data: vm => ({
    loading: false,
    admin: {},
    tasks: [],
    headers: [
      { text: vm.$t('forms.toDoItem'), value: 'name' },
      { text: vm.$t('forms.assignedTo'), value: 'assigned_to.assigned_to' }
    ]
  }),
  mounted () {
    this.loading = true
    this.$hrtasks.getAll().then((tasks) => {
      this.tasks = tasks.filter(a => parseInt(this.$route.params.id) === a.new_hire_id)
    }).finally((tasks) => {
      this.loading = false
    })
  },
  methods: {
    goTo (item, row) {
      this.$router.push({ name: 'admin-hrtasks-id', params: { 'id': item.id } })
    }
  }
}
</script>
