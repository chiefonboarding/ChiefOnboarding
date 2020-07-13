<template>
  <div>
    <LoadingIcon :is-loading="loading" />
    <div v-if="!loading" class="container grid-list-md fluid wrap">
      <NewHireForm v-model="newHire" :errors="errors" />
      <v-btn @click="updateNewHire" class="success">
        Save
      </v-btn>
    </div>
  </div>
</template>

<script>
import NewHireForm from '@/components/admin/newhire/Form'
export default {
  layout: 'admin',
  components: { NewHireForm },
  data: () => ({
    updatingAccount: false,
    loading: false,
    dialog: false,
    errors: { details: {} },
    newHire: { details: {} }
  }),
  mounted () {
    this.getNewHire()
  },
  methods: {
    getNewHire () {
      this.$newhires.get(this.$route.params.id).then((newHire) => {
        this.newHire = newHire
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('newhires.noNewHire'))
      }).finally(() => {
        this.loading = false
      })
    },
    updateNewHire () {
      this.updatingAccount = true
      this.$newhires.update(this.$route.params.id, this.newHire).then((newHire) => {
        this.$store.dispatch('showSnackbar', this.$t('newhires.newHireUpdated'))
      }).catch((errors) => {
        this.errors = errors
      }).finally(() => {
        this.updatingAccount = false
      })
    }
  }
}
</script>
