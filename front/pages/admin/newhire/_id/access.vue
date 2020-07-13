<template>
  <div>
    <LoadingIcon :is-loading="loading" />
    <NewHireAccess v-if="!loading" :id="$route.params.id" :new-hire="newhire" />
  </div>
</template>

<script>
import NewHireAccess from '@/components/admin/newhire/Access'
export default {
  layout: 'admin',
  components: { NewHireAccess },
  data: () => ({
    newhire: {},
    loading: true
  }),
  mounted () {
    this.getNewHire()
  },
  methods: {
    getNewHire () {
      this.loading = true
      this.$newhires.get(this.$route.params.id).then((newhire) => {
        this.newhire = newhire
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('newhires.noNewHire'))
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>
