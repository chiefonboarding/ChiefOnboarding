<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="950"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('sequence.addTask') }}
      </v-card-title>

      <v-card-text>
        <HRTaskForm v-model="hrTask" :errors="errors" :no-new-hire="true" />
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
          @click="addTask"
        >
          <span v-if="Object.entries(task).length">
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
import HRTaskForm from '@/components/admin/admintasks/Form'
export default {
  name: 'HRTaskModal',
  components: { HRTaskForm },
  props: {
    task: {
      type: Object,
      required: true
    },
    index: {
      type: Number,
      required: true
    },
    value: {
      type: Boolean,
      default: false
    }
  },
  data: vm => ({
    loading: false,
    nameError: [],
    errors: {},
    hrTask: { assigned_to: vm.$store.state.admins[0], date: '', todo: '', message: '', priority: 1, option: 0, slack_email: '' }
  }),
  watch: {
    value (value) {
      if (Object.entries(this.task).length === 0) {
        this.hrTask = { assigned_to: this.$store.state.admins[0], date: '', todo: '', message: '', priority: 1, option: '0', slack_email: '' }
      } else {
        this.hrTask = JSON.parse(JSON.stringify(this.task))
        if (this.hrTask.option === 1) {
          this.hrTask.email = this.hrTask.email_slack
        }
        if (this.hrTask.option === 2) {
          this.hrTask.slack = this.hrTask.email_slack
        }
      }
    }
  },
  methods: {
    addTask () {
      this.loading = true
      this.$sequences.createAdminTask(this.hrTask).then((data) => {
        if ('id' in this.task) {
          this.$store.commit('sequences/removeItem', {
            block: this.index,
            type: 'admin_tasks',
            id: this.task.id
          })
        }
        this.$store.commit('sequences/addItem', { block: this.index, type: 'admin_tasks', item: data })
        this.$emit('input', false)
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>
