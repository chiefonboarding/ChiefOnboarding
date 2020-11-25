<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="950"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('sequence.resourceModal') }}
      </v-card-title>

      <v-card-text>
        <ResourceForm v-model="tempResource" :errors="errors" class="form" />
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
          <span v-if="Object.entries(resource).length">
            {{ $t('buttons.update') }}
          </span>
          <span v-else>
            {{ $t('buttons.add') }}
          </span>
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
    index: {
      type: Number,
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
    tempResource: {
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
  watch: {
    value (value) {
      if (Object.entries(this.resource).length === 0) {
        this.tempResource = { name: '', tags: [], chapters: [{ id: 'iower23', name: 'New item', content: [], type: 0, files: [] }], course: false, on_day: 0, category: null, remove_on_complete: false }
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
      this.$store.commit('refreshEditor')
    }
  },
  methods: {
    addResource () {
      this.$resources.create(this.tempResource).then((data) => {
        if (this.index === -1) {
          // unconditioned item
          this.$emit('updateUnconditionedItem', { id: this.tempResource.id || -1, type: 'resources', item: data })
          this.$emit('input', false)
          return
        }
        if ('id' in this.tempResource) {
          this.$store.commit('sequences/removeItem', {
            block: this.index,
            type: 'resources',
            id: this.tempResource.id
          })
        }
        this.$store.commit('sequences/addItem', { block: this.index, type: 'resources', item: data })
        this.$emit('input', false)
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('resource.couldNotSave'))
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>
