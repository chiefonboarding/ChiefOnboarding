<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="900"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('resource.item') }}
      </v-card-title>

      <v-card-text>
        <ResourceForm ref="form" v-model="tempResource" :errors="errors" :inline="true" />
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          @click="$emit('input', false)"
          text
        >
          {{ $t('buttons.cancel') }}
        </v-btn>
        <v-btn
          :loading="loading"
          @click="addResource"
        >
          {{ $t('buttons.add') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import ResourceForm from '@/components/admin/resource/Form'
export default {
  name: 'ResourceModal',
  components: { ResourceForm },
  props: {
    resource: {
      type: Object,
      required: true
    },
    value: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    loading: false,
    nameError: [],
    errors: {},
    tempResource: { 'name': '', 'chapters': [{ 'content': [], 'files': [], 'name': 'Your title', 'parts': [], 'has_questions': false, 'questions': [] }], 'tags': [] }
  }),
  watch: {
    value (value) {
      if (Object.entries(this.resource).length === 0) {
        this.tempResource = { 'name': '', 'chapters': [{ 'content': [], 'files': [], 'name': 'Your title', 'parts': [], 'has_questions': false, 'questions': [] }], 'tags': [] }
      } else {
        this.tempResource1 = JSON.parse(JSON.stringify(this.resource))
        if (this.tempResource1.category !== null) {
          this.tempResource1.category = this.tempResource1.category.name
        }
        const items = []
        this.tempResource1.chapters.forEach((one) => {
          if (one.parent_chapter === null) {
            one.chapters = []
            items.push(one)
          } else {
            items.find(a => a.id === one.parent_chapter).chapters.unshift(one)
          }
        })
        this.tempResource1.chapters = items
        this.tempResource = this.tempResource1
      }
      setTimeout(() => {
        this.$refs.form.getChapter(0, -1, true)
      }, 100)
    }
  },
  methods: {
    addResource () {
      let remove = -1
      if (JSON.stringify(this.tempResource) !== JSON.stringify(this.preboarding)) {
        if ('id' in this.tempResource) {
          remove = this.tempResource.task_id
          delete this.tempResource.id
        }
        this.tempResource.template = false
        this.loading = true
        this.$resources.create(this.tempResource).then((data) => {
          data.type = 'todo'
          this.$emit('change', { 'add': data, remove })
          this.$emit('input', false)
        }).catch((error) => {
          this.errors = error
          this.$store.dispatch('showSnackbar', this.$t('resource.couldNotSave'))
        }).finally(() => {
          this.loading = false
        })
      } else {
        this.$emit('input', false)
      }
    }
  }
}
</script>
