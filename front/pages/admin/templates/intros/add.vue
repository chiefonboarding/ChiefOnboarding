<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('intro.addHeader') }}
      </h1>
    </template>
    <template slot="formpart" v-if="!loading">
      <LoadingIcon :is-loading="loading" />
      <IntroForm v-model="intro" :errors="errors" />
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
      loading: false,
      saving: false,
      errors: {},
      employee: {},
      intro: { name: '', intro_person: '', tags: [] }
    }
  },
  methods: {
    saveIntro () {
      this.saving = true
      this.$intros.create(this.intro).then((data) => {
        this.$router.push({ name: 'admin-templates-intros' })
        this.$store.dispatch('showSnackbar', this.$t('intro.created'))
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
