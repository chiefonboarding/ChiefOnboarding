<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('preboarding.change') }}
      </h1>
    </template>
    <template slot="header-right">
      <v-btn :loading="duplicating" @click="duplicatePreboarding" color="secondary">
        {{ $t('buttons.duplicate') }}
      </v-btn>
      <v-btn :loading="removing" @click="removePreboarding" color="error" style="margin-right: 0px;">
        {{ $t('buttons.remove') }}
      </v-btn>
    </template>
    <template slot="formpart">
      <LoadingIcon :is-loading="loading" />
      <div v-if="!loading">
        <PreboardingForm ref="form" v-model="preboarding" :errors="errors" />
      </div>
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
  data () {
    return {
      loading: true,
      saving: false,
      removing: false,
      duplicating: false,
      submittingForm: false,
      errors: {},
      employee: {},
      preboarding: {}
    }
  },
  watch: {
    '$route' (to, from) {
      this.getPreboarding()
    }
  },
  mounted () {
    this.getPreboarding()
  },
  methods: {
    getPreboarding () {
      return this.$preboarding.get(this.$route.params.id).then((data) => {
        this.preboarding = data
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('preboarding.couldNotGet'))
      }).finally(() => {
        this.loading = false
      })
    },
    savePreboarding () {
      this.saving = true
      this.$preboarding.update(this.$route.params.id, this.preboarding).then((data) => {
        this.$router.push({ name: 'admin-templates-preboarding' })
        this.$store.dispatch('showSnackbar', this.$t('preboarding.updated'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    },
    duplicatePreboarding () {
      this.duplicating = true
      this.$preboarding.update(this.$route.params.id, this.preboarding).then((data) => {
        this.$preboarding.duplicate(this.$route.params.id).then((data) => {
          this.$router.push({ name: 'admin-templates-preboarding' })
          this.$store.dispatch('showSnackbar', this.$t('preboarding.savedAndDuplicated'))
        }).catch((error) => {
          this.errors = error
        }).finally(() => {
          this.duplicating = false
        })
      })
    },
    removePreboarding () {
      this.removing = true
      this.$preboarding.remove(this.$route.params.id).then((data) => {
        this.$router.push({ name: 'admin-templates-preboarding' })
        this.$store.dispatch('showSnackbar', this.$t('preboarding.removed'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.removing = false
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
