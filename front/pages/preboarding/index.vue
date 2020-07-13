<template>
  <PreboardingPage :pages="pages" :new-hire="newHire" :org="org" :completed-todos="completedTodos" />
</template>

<script>
import PreboardingPage from '@/components/preboarding/Page'
export default {
  name: 'PreboardingBase',
  layout: 'preboarding',
  components: { PreboardingPage },
  data: () => ({
    pages: [],
    newHire: {},
    completedTodos: [],
    org: {}
  }),
  mounted () {
    this.$newhirepreboarding.getPreboardingItems().then((data) => {
      data.forEach((one) => {
        one.preboarding.page_id = one.id
        one.preboarding.completed = one.completed
      })
      this.pages = data.map(a => a.preboarding)
      this.$newhirepart.getMe().then((data) => {
        this.$i18n.locale = data.new_hire.language
        this.$store.commit('setBaseInfo', data)
        this.newHire = data.new_hire
        this.org = data.org
      }).catch(() => {
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.notAuthorized'))
        this.$router.push({ name: 'index' })
      })
    }).catch(() => {
      this.$store.dispatch('showSnackbar', this.$t('newHirePortal.notAuthorized'))
    })
  }
}
</script>
