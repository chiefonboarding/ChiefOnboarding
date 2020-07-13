<template>
  <TemplateComp :loading="loading" :items="$store.state.badges.all" :name="$t('badge.allBadges')" new-url="admin-templates-badges-add" detail-page="admin-templates-badges-id" />
</template>

<script>
export default {
  layout: 'admin',
  data: () => ({
    loading: false
  }),
  mounted () {
    this.loading = true
    this.$badges.getAll().finally(() => {
      this.loading = false
    })
  }
}
</script>
