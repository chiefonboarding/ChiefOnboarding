<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('preboarding.addHeader') }}
      </h1>
    </template>
    <template slot="formpart">
      <PreboardingForm v-model="preboarding" :errors="errors" />
    </template>
    <template slot="footer">
      <v-btn :loading="saving" @click="savePreboarding" color="primary" style="float:right">
        {{ $t('buttons.save') }}
      </v-btn>
    </template>
  </TemplateCompInner>
</template>

<script>
import PreboardingForm from '@/components/admin/preboarding/Form'
export default {
  layout: 'admin',
  components: { PreboardingForm },
  data: () => ({
    loading: false,
    saving: false,
    submittingForm: false,
    errors: {},
    employee: {},
    preboarding: { name: '', form: [], content: [], tags: [] }
  }),
  methods: {
    savePreboarding () {
      this.saving = true
      this.$preboarding.create(this.preboarding).then((data) => {
        this.$router.push({ name: 'admin-templates-preboarding' })
        this.$store.dispatch('showSnackbar', this.$t('preboarding.createdPreboarding'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    }
  }
}
</script>

<style scoped>
</style>
