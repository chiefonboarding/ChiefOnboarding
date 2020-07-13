<template>
  <v-row>
    <v-col sm="12" mb="6" offset-mb="3" md="8" offset-md="2">
      <v-row mb-4>
        <v-col sm="10">
          <h1 class="heading" style="margin-top: 5px;">
            {{ name }}
          </h1>
        </v-col>
        <v-col sm="2" class="text-right">
          <v-btn @click="$router.push({name: newUrl})" color="success" style="margin-right: 0px; margin-top: 12px;">
            {{ $t('buttons.add') }}
          </v-btn>
        </v-col>
      </v-row>
      <v-card class="mb-4">
        <template>
          <v-data-table
            :items="items"
            :loading="loading"
            :headers="headers"
            :footer-props="{'items-per-page-options':[100, -1]}"
            @click:row="goToPage"
          >
            <template v-slot:item.tags="{ item }">
              <v-chip v-for="i in item.tags" :key="i.id" label small class="chip-items">
                {{ i }}
              </v-chip>
            </template>
            <template v-slot:no-data>
              There aren't any templates yet.
            </template>
          </v-data-table>
        </template>
      </v-card>
    </v-col>
  </v-row>
</template>
<script>
export default {
  layout: 'admin',
  props: {
    name: {
      type: String,
      required: true
    },
    newUrl: {
      type: String,
      required: true
    },
    items: {
      type: Array,
      required: true
    },
    loading: {
      type: Boolean,
      default: true
    },
    detailPage: {
      type: String,
      required: true
    }
  },
  data: () => ({
    headers: [
      { text: 'Name', value: 'name' },
      { value: 'tags' }
    ]
  }),
  methods: {
    goToPage (item, row) {
      this.$router.push({ name: this.detailPage, params: { id: item.id } })
    }
  }
}
</script>

<style>
.chip-items {
  float: right;
  margin-left: 4px;
}
</style>
