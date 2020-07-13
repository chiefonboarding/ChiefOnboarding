<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('badge.change') }}
      </h1>
    </template>
    <template slot="header-right">
      <v-btn :loading="duplicating" @click="duplicateBadge" color="secondary">
        {{ $t('buttons.duplicate') }}
      </v-btn>
      <v-btn :loading="removing" @click="removeBadge" color="error" style="margin-right: 0px;">
        {{ $t('buttons.remove') }}
      </v-btn>
    </template>
    <template slot="formpart">
      <LoadingIcon :is-loading="loading" />
      <div v-if="!loading">
        <BadgeForm v-model="badge" :errors="errors" />
      </div>
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
  data () {
    return {
      loading: true,
      saving: false,
      removing: false,
      duplicating: false,
      submittingForm: false,
      errors: {},
      employee: {},
      badge: {}
    }
  },
  watch: {
    '$route' (to, from) {
      this.getBadge()
    }
  },
  mounted () {
    this.getBadge()
  },
  methods: {
    getBadge () {
      this.$badges.get(this.$route.params.id).then((data) => {
        this.badge = data
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('badge.noBadge'))
      }).finally(() => {
        this.loading = false
      })
    },
    saveBadge () {
      this.saving = true
      this.$badges.update(this.$route.params.id, this.badge).then((data) => {
        this.$router.push({ name: 'admin-templates-badges' })
        this.$store.dispatch('showSnackbar', this.$t('badge.updated'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    },
    removeBadge () {
      this.removing = true
      this.$badges.remove(this.$route.params.id).then((data) => {
        this.$router.push({ name: 'admin-templates-badges' })
        this.$store.dispatch('showSnackbar', this.$t('badge.removed'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.removing = false
      })
    },
    duplicateBadge () {
      this.duplicating = true
      this.$badges.update(this.$route.params.id, this.badge).then((data) => {
        this.$badges.duplicate(this.$route.params.id).then((data) => {
          this.$router.push({ name: 'admin-templates-badges' })
          this.$store.dispatch('showSnackbar', this.$t('badge.savedAndDuplicated'))
        }).catch((error) => {
          this.errors = error
        }).finally(() => {
          this.duplicating = false
        })
      })
    }
  }
}
</script>

<style scoped>
.border-bottom {
  border-bottom: 1px solid rgb(228, 228, 228);
}
.second {
  margin-left: 10px;
}
.first {
  margin-right: 10px;
}
</style>
