<template>
  <TemplateComp :loading="loading" :items="$store.state.preboarding.all" new-url="admin-templates-preboarding-add" name="All pre-boarding templates" detail-page="admin-templates-preboarding-id" />
</template>

<script>
export default {
  layout: 'admin',
  data: () => ({
    loading: false
  }),
  mounted () {
    this.loading = true
    this.$preboarding.getAll().finally(() => {
      this.loading = false
    })
  }
}
</script>
