<template>
  <v-dialog
    v-model="isOpen"
    :persistent="true"
    max-width="900"
  >
    <template v-slot:activator="{ on }">
      <v-btn
        v-on="on"
      >
        Completed
      </v-btn>
    </template>

    <v-card class="pt-4">
      <v-card-text>
        <template>
          <v-data-table
            :headers="headers"
            :items="tasks"
            :loading="loading"
            :footer-props="{'items-per-page-options':[50, 100, -1]}"
            @click:row="goToPage"
            class="elevation-1 mt-4"
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
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          @click="isOpen = false"
          text
        >
          {{ $t('buttons.close') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
export default {
  name: 'SelectTemplates',
  props: {
    byUser: {
      default: false,
      type: Boolean
    }
  },
  data: vm => ({
    loading: false,
    text: '',
    isOpen: false,
    tasks: [],
    headers: [
      { text: vm.$t('hrTask.newHire'), value: 'new_hire.first_name' },
      { text: vm.$t('hrTask.toDo'), value: 'title' },
      { text: vm.$t('hrTask.assignedTo'), value: 'assigned_to.first_name' },
      { text: vm.$t('hrTask.due'), value: 'date' },
      { text: vm.$t('hrTask.priority'), value: 'priority' }
    ],
    defaultText: vm.$t('selectTemplate.pick')
  }),
  mounted () {
    this.getItems()
  },
  methods: {
    returnItem (item) {
      this.$emit('clickedItem', item)
    },
    getItems () {
      if (this.byUser) {
        this.$hrtasks.getDoneTasks().then((tasks) => {
          this.tasks = tasks
        }).finally((tasks) => {
          this.loading = false
        })
      } else {
        this.$hrtasks.getDoneByUserTasks().then((tasks) => {
          this.tasks = tasks
        }).finally((tasks) => {
          this.loading = false
        })
      }
    },
    goToPage (item, row) {
      this.$router.push({ name: 'admin-hrtasks-id', params: { id: item.id } })
    }
  }
}
</script>
