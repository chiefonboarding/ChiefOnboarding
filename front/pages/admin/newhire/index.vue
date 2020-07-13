<template>
  <v-row>
    <v-col sm="12" mb="6" offset-mb="3" md="8" offset-sm="2">
      <v-row class="my-4">
        <v-col sm="6">
          <h1 class="heading">
            {{ $t('newhires.newHires') }}
          </h1>
        </v-col>
        <v-col sm="6" class="mt-1 text-right">
          <v-btn @click="$router.push({name: 'admin-newhire-add'})" color="success">
            {{ $t('newhires.addNewHire') }}
          </v-btn>
        </v-col>
      </v-row>
      <v-card class="mb-4">
        <template>
          <v-data-table
            :headers="headers"
            :items="all"
            :footer-props="{'items-per-page-options':[50, 100, -1]}"
            @click:row="goToPage"
          >
            <template v-slot:no-data>
              There are currently no new hires. Start by adding one.
            </template>
            <template v-slot:item.first_name="{ item }">
              {{ item.full_name }}
            </template>
            <template v-slot:item.start="{ item }">
              {{ item.start | dateTimeFormat }}
            </template>
            <template v-slot:item.percentage="{ item }">
              <v-tooltip top>
                <template v-slot:activator="{ on }">
                  <v-progress-linear :value="item.percentage" v-on="on" color="success" height="5" />
                </template>
                <span>{{ Math.ceil(item.percentage) }}%</span>
              </v-tooltip>
            </template>
          </v-data-table>
        </template>
      </v-card>
    </v-col>
  </v-row>
</template>

<script>
import { mapState } from 'vuex'
export default {
  layout: 'admin',
  data: vm => ({
    loading: false,
    headers: [
      { text: vm.$t('forms.name'), value: 'first_name' },
      { text: vm.$t('forms.startingDate'), value: 'start' },
      { text: vm.$t('forms.position'), value: 'position' },
      { text: vm.$t('forms.progress'), value: 'percentage' }
    ]
  }),
  computed: mapState('newhires', [
    'all'
  ]),
  mounted () {
    this.loading = true
    this.$newhires.getAll().finally(() => {
      this.loading = false
    })
  },
  methods: {
    goToPage (item, row) {
      this.$router.push({ name: 'admin-newhire-id', params: { id: item.id } })
    }
  }
}
</script>
