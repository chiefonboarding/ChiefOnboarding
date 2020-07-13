<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('intro.changeHeader') }}
      </h1>
    </template>
    <template slot="header-right">
      <v-btn :loading="removing" @click="removeIntro" color="error" style="margin-right: 0px;">
        {{ $t('buttons.remove') }}
      </v-btn>
    </template>
    <template slot="formpart">
      <LoadingIcon :is-loading="loading" />
      <div v-if="!loading">
        <IntroForm v-model="intro" :loading="loading" :errors="errors" />
      </div>
    </template>
    <template slot="footer">
      <v-btn :loading="saving" @click="saveIntro" color="primary" style="float:right">
        {{ $t('buttons.save') }}
      </v-btn>
    </template>
  </TemplateCompInner>
</template>

<script>
import IntroForm from '@/components/admin/intro/Form'
export default {
  layout: 'admin',
  components: { IntroForm },
  data () {
    return {
      loading: true,
      saving: false,
      removing: false,
      submittingForm: false,
      errors: {},
      employee: {},
      intro: {}
    }
  },
  watch: {
    '$route' (to, from) {
      this.getIntro()
    }
  },
  mounted () {
    this.getIntro()
  },
  methods: {
    getIntro () {
      this.$intros.get(this.$route.params.id).then((data) => {
        this.intro = data
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('intro.couldNotRemove'))
      }).finally(() => {
        this.loading = false
      })
    },
    saveIntro () {
      this.saving = true
      this.$intros.update(this.$route.params.id, this.intro).then((data) => {
        this.$router.push({ name: 'admin-templates-intros' })
        this.$store.dispatch('showSnackbar', this.$t('intro.updated'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    },
    removeIntro () {
      this.removing = true
      this.$intros.remove(this.$route.params.id).then((data) => {
        this.$router.push({ name: 'admin-templates-intros' })
        this.$store.dispatch('showSnackbar', this.$t('intro.removed'))
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
