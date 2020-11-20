<template>
  <div class="grid-list-md fluid wrap">
    <LoadingIcon :is-loading="loading" />
    <div v-if="!loading">
      <CollectionForm
        ref="form"
        v-model="items"
        :errors="errors"
        @onAdd="addingItem"
        @onChange="changeItem"
        @removeItem="removeItem"
      />
    </div>
  </div>
</template>

<script>
import CollectionForm from '@/components/admin/collection/Form'
export default {
  components: { CollectionForm },
  data: () => ({
    items: [],
    loading: true,
    errors: {},
    dates: [],
    conditionItems: [],
    item: {}
  }),
  mounted () {
    this.$newhires.getTasks(this.$route.params.id).then((items) => {
      delete items.conditions
      this.items = items
    }).finally(() => {
      this.loading = false
    })
  },
  methods: {
    addingItem (item) {
      this.$newhires.addTask(this.$route.params.id, item).then((data) => {
        this.items[item.type].push(data)
      })
    },
    changeItem (value) {
      this.removeItem(value.remove)
      this.addingItem(value.add)
    },
    removeItem (item) {
      this.$newhires.deleteTask(this.$route.params.id, item).catch(() => {
        this.$store.dispatch('showSnackbar', this.$t('newhires.notRemoved'))
      })
    }
  }
}
</script>
