<template>
  <v-container class="pa-4">
    <LoadingIcon :is-loading="loading" />
    <p v-if="items.length === 0 && !loading" style="margin-bottom: 0px;">
      {{ $t('newhires.noWelcomeMessage') }}
    </p>
    <div v-for="i in items" :key="i.id" style="margin-bottom: 20px;">
      <p style="margin-bottom: 5px;">
        {{ i.message }}
      </p>
      <span class="grey--text">- {{ i.colleague.full_name }}</span>
    </div>
  </v-container>
</template>

<script>
export default {
  data: () => ({
    items: [],
    loading: true
  }),
  mounted () {
    this.$newhires.getWelcomeMessages(this.$route.params.id).then((items) => {
      this.items = items
    }).finally(() => {
      this.loading = false
    })
  }
}
</script>
