<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="900"
    scrollable
  >
    <v-card>
      <v-card-title class="headline">
        <span v-if="title !== ''">{{ title }}</span><span v-else>{{ defaultText }}</span>
        <v-text-field
          v-model="search"
          :label="$t('admin.search')"
          append-icon="search"
          single-line
          hide-details
          style="margin-left: 60px;"
        />
      </v-card-title>

      <v-card-text>
        <v-data-table
          v-model="resourceSelected"
          :headers="headers"
          :items="items"
          :search="search"
          @click:row="returnItem"
          item-key="id"
          disable-pagination
          hide-default-footer
        >
          <template v-slot:item.tags="{ item }">
            <div style="text-align: right">
              <v-chip v-for="i in item.tags" :key="i.id" label small>
                {{ i }}
              </v-chip>
            </div>
          </template>
        </v-data-table>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          @click="$emit('input', false)"
          text
        >
          {{ $t('buttons.cancel') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
export default {
  name: 'SelectTemplates',
  props: {
    value: {
      type: Boolean,
      default: false
    },
    items: {
      type: Array,
      required: true
    },
    title: {
      type: String,
      default: ''
    }
  },
  data: vm => ({
    loading: false,
    text: '',
    headers: [{ value: 'name', text: 'Name' }, { value: 'text' }],
    resourceSelected: [],
    search: '',
    defaultText: vm.$t('selectTemplate.pick')
  }),
  methods: {
    returnItem (item, row) {
      this.$emit('clickedItem', item)
    }
  }
}
</script>
