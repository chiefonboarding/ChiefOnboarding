<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('badge.addNew') }}
      </h1>
    </template>
    <template slot="formpart">
      <BadgeForm v-model="badge" :errors="errors" />
    </template>
    <template slot="footer">
      <v-btn :loading="saving" @click="saveBadge" color="primary" style="float:right">
        {{ $t('buttons.save') }}
      </v-btn>
    </template>
  </TemplateCompInner>
</template>

<script>
import BadgeForm from '@/components/admin/badge/Form'
export default {
  layout: 'admin',
  components: { BadgeForm },
  data: () => ({
    loading: false,
    saving: false,
    errors: {},
    badge: { name: '', image: {}, content: [], tags: [] }
  }),
  methods: {
    saveBadge () {
      this.saving = true
      this.$badges.create(this.badge).then((data) => {
        this.$router.push({ name: 'admin-templates-badges' })
        this.$store.dispatch('showSnackbar', this.$t('badge.created'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    }
  }
}
</script>
