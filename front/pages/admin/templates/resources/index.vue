<template>
  <TemplateComp :loading="loading" :items="$store.state.resources.all" :name="$t('resource.all')" new-url="admin-templates-resources-add" detail-page="admin-templates-resources-id" />
</template>

<script>
export default {
  layout: 'admin',
  data: () => ({
    loading: false
  }),
  mounted () {
    this.loading = true
    this.$resources.getAll().finally(() => {
      this.loading = false
    })
  }
}
</script>
