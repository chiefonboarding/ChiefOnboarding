<template>
  <TemplateComp :loading="loading" :items="$store.state.sequences.all" :name="$t('sequence.all')" new-url="admin-templates-presets-add" detail-page="admin-templates-presets-id" />
</template>

<script>
export default {
  layout: 'admin',
  data: () => ({
    loading: false
  }),
  mounted () {
    this.loading = true
    this.$sequences.getAll().finally(() => {
      this.loading = false
    })
  }
}
</script>
