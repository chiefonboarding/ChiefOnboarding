<template>
  <v-row>
    <v-col sm="12" mb="6" offset-mb="3" md="8" offset-md="2">
      <v-row mb-4>
        <v-col sm="6">
          <h1 class="heading" style="margin-top: 5px;">
            {{ $t('hrTask.all') }}
          </h1>
        </v-col>
        <v-col sm="6" class="text-right mt-2">
          <CompletedTasksDialog />
          <v-btn @click="$router.push({name: 'admin-hrtasks-add'})" color="success" style="margin-right: 0px;">
            {{ $t('hrTask.add') }}
          </v-btn>
        </v-col>
      </v-row>
      <v-card class="mb-4">
        <template>
          <v-data-table
            :headers="headers"
            :items="tasks"
            :loading="loading"
            @click:row="goToPage"
            :footer-props="{'items-per-page-options':[50, 100, -1]}"
            class="elevation-1"
          >
            <template v-slot:no-data>
              There aren't any to do items (yet).
            </template>
            <template v-slot:item.new_hire.first_name="{ item }">
              {{ item.new_hire.first_name }} {{ item.new_hire.last_name }}
            </template>
            <template v-slot:item.assigned_to.first_name="{ item }">
              {{ item.assigned_to.first_name }} {{ item.assigned_to.last_name }}
            </template>
            <template v-slot:item.date="{ item }">
              {{ item.date | timeAgo }}
            </template>
            <template v-slot:item.priority="{ item }">
              {{ item.priority | prio }}
            </template>
          </v-data-table>
        </template>
      </v-card>
    </v-col>
  </v-row>
</template>

<script>
import CompletedTasksDialog from '@/components/admin/admintasks/CompletedTasksDialog'
export default {
  layout: 'admin',
  components: { CompletedTasksDialog },
  data: vm => ({
    loading: false,
    tasks: [],
    admin: {},
    allTasks: [],
    headers: [
      { text: vm.$t('hrTask.newHire'), value: 'new_hire.first_name' },
      { text: vm.$t('hrTask.toDo'), value: 'name' },
      { text: vm.$t('hrTask.assignedTo'), value: 'assigned_to.first_name' },
      { text: vm.$t('hrTask.due'), value: 'date' },
      { text: vm.$t('hrTask.priority'), value: 'priority' }
    ]
  }),
  mounted () {
    this.loading = true
    this.$hrtasks.getAll().then((tasks) => {
      this.allTasks = tasks
      this.tasks = tasks.filter(a => !a.completed)
    }).finally((tasks) => {
      this.loading = false
    })
  },
  methods: {
    goToPage (item, row) {
      this.$router.push({ name: 'admin-hrtasks-id', params: { id: item.id } })
    }
  }
}
</script>

<style scoped>
.border-bottom {
  border-bottom: 1px solid rgb(228, 228, 228);
}
</style>
