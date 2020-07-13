<template>
  <TemplateComp
    :loading="loading"
    :items="$store.state.intros.all"
    :name="$t('intro.all')"
    new-url="admin-templates-intros-add"
    detail-page="admin-templates-intros-id"
  />
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
    this.$intros.getAll().finally(() => {
      this.loading = false
    })
  }
}
</script>
