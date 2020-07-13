<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('resource.addHeader') }}
      </h1>
    </template>
    <template slot="formpart" v-if="!loading">
      <LoadingIcon :is-loading="loading" />
      <ResourceForm v-model="resource" :errors="errors" />
    </template>
    <template slot="footer">
      <v-btn :loading="saving" @click="saveResource" color="primary" style="float:right">
        {{ $t('buttons.save') }}
      </v-btn>
    </template>
  </TemplateCompInner>
</template>

<script>
import ResourceForm from '@/components/admin/resource/Form'
export default {
  layout: 'admin',
  components: { ResourceForm },
  data: vm => ({
    loading: false,
    saving: false,
    errors: { name: [] },
    resource: {
      name: '',
      tags: [],
      chapters: [{
        id: 'iower23',
        name: 'New item',
        content: [],
        type: 0,
        files: []
      }],
      course: false,
      on_day: 0,
      category: null,
      remove_on_complete: false
    }
  }),
  methods: {
    saveResource () {
      this.saving = true
      this.resource.template = true
      this.$resources.create(this.resource).then((data) => {
        this.$router.push({ name: 'admin-templates-resources' })
        this.$store.dispatch('showSnackbar', this.$t('resource.created'))
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
