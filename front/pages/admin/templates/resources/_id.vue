<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('resource.changeHeader') }}
      </h1>
    </template>
    <template slot="header-right">
      <v-btn :loading="duplicating" @click="duplicateResource" color="secondary">
        {{ $t('buttons.duplicate') }}
      </v-btn>
      <v-btn :loading="removing" @click="removeResource" color="error" style="margin-right: 0px;">
        {{ $t('buttons.remove') }}
      </v-btn>
    </template>
    <template slot="formpart">
      <LoadingIcon :is-loading="loading" />
      <div v-if="!loading">
        <ResourceForm ref="form" v-model="resource" :errors="errors" class="form" />
      </div>
    </template>
    <template slot="footer">
      <v-btn :loading="saving" @click="updateResource" color="primary" style="float:right">
        {{ $t('buttons.update') }}
      </v-btn>
    </template>
  </TemplateCompInner>
</template>

<script>
import ResourceForm from '@/components/admin/resource/Form'
export default {
  layout: 'admin',
  components: { ResourceForm },
  data: () => ({
    loading: true,
    saving: false,
    removing: false,
    duplicating: false,
    errors: {},
    resource: {
      chapters: [{
        id: 'iower23',
        name: 'New item',
        content: [],
        type: 0,
        files: []
      }]
    }
  }),
  watch: {
    '$route' (to, from) {
      this.getResource()
    }
  },
  mounted () {
    this.getResource()
  },
  methods: {
    getResource () {
      return this.$resources.get(this.$route.params.id).then((data) => {
        this.resource = data
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('resource.noResource'))
      }).finally(() => {
        this.loading = false
      })
    },
    updateResource () {
      this.saving = true
      this.$resources.update(this.$route.params.id, this.resource).then((data) => {
        this.$router.push({ name: 'admin-templates-resources' })
        this.$store.dispatch('showSnackbar', this.$t('resource.updated'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    },
    removeResource () {
      this.removing = true
      this.$resources.remove(this.$route.params.id).then((data) => {
        this.$router.push({ name: 'admin-templates-resources' })
        this.$store.dispatch('showSnackbar', this.$t('resource.removed'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.removing = false
      })
    },
    duplicateResource () {
      this.duplicating = true
      const newData = JSON.parse(JSON.stringify(this.resource))
      delete newData.id
      this.$resources.update(this.$route.params.id, this.resource).then((data) => {
        this.$resources.create(this.resource).then((newData) => {
          this.$router.push({ name: 'admin-templates-resources' })
          this.$store.dispatch('showSnackbar', this.$t('resource.savedAndDuplicated'))
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
</style>
