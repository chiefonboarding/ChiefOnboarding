<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('hrTask.addNewAdminTask') }}
      </h1>
    </template>
    <template slot="formpart">
      <v-container grid-list-md fluid wrap>
        <v-row wrap>
          <HRTaskForm v-model="adminTask" :errors="errors" />
        </v-row>
      </v-container>
    </template>
    <template slot="footer">
      <v-btn :loading="saving" @click="saveAdminTask" color="primary" style="float:right">
        {{ $t('buttons.add') }}
      </v-btn>
    </template>
  </TemplateCompInner>
</template>

<script>
import HRTaskForm from '@/components/admin/admintasks/Form'
export default {
  layout: 'admin',
  components: { HRTaskForm },
  data () {
    return {
      loading: false,
      saving: false,
      submittingForm: false,
      errors: {},
      employee: {},
      adminTask: { user: this.$store.state.newhires.all[0], assigned_to: this.$store.state.admins[0], date: '', priority: 1, option: '0', slack_email: '' }
    }
  },
  methods: {
    saveAdminTask () {
      this.saving = true
      this.$hrtasks.create(this.adminTask).then((data) => {
        this.$router.push({ name: 'admin-hrtasks-id', params: { id: data.id } })
        this.$store.dispatch('showSnackbar', this.$t('hrTask.created'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    }
  }
}
</script>

<style scoped>
</style>
