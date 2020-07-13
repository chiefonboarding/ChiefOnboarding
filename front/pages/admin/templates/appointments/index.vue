<template>
  <TemplateComp :loading="loading" :items="$store.state.appointments.all" :name="$t('appointment.all')" new-url="admin-templates-appointments-add" detail-page="admin-templates-appointments-id" />
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
    this.$appointments.getAll().finally(() => {
      this.loading = false
    })
  }
}
</script>
