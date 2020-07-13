<template>
  <v-container mt-4>
    <LoadingIcon :color="$store.state.baseInfo.org.base_color" :is-loading="loading" />
    <v-row v-if="!loading">
      <v-col sm="3">
        <v-card outlined class="pa-4">
          <div v-for="(value, propertyValue) in resources">
            <v-subheader v-if="propertyValue !== 'null'">
              {{ propertyValue }}
            </v-subheader>
            <v-treeview
              :items="value"
              :color="$store.state.baseInfo.org.base_color"
              @update:active="clickedItem"
              activatable
              hoverable
              item-key="id"
            >
              <template v-slot:prepend="{ item }">
                <font-awesome-icon v-if="item.course" :icon="['far', 'bookmark']" />
                <font-awesome-icon v-else-if="item.item === null" :icon="['far', 'folder']" />
                <font-awesome-icon v-else :icon="['far', 'file']" />
              </template>
            </v-treeview>
          </div>
        </v-card>
      </v-col>
      <v-col sm="9">
        <v-card outlined class="pa-10">
          <div v-if="Object.keys(item).length === 0">
            <h2>
              {{ $t('newHirePortal.SelectAnItem') }}
            </h2>
            <v-autocomplete
              v-model="select"
              :items="searchResources"
              :label="$t('newHirePortal.searchHere')"
              item-text="name"
              return-object
              style="width: 300px;"
            />
          </div>
          <div v-else>
            <h2>{{ item.item.name }}</h2>
            <ContentDisplay :content="item.item.content" />
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import _ from 'lodash'
import ContentDisplay from '@/components/portal/ContentDisplay'

export default {
  layout: 'newhire',
  name: 'ResourcesOverview',
  components: { ContentDisplay },
  data: () => ({
    loading: true,
    answers: [],
    select: {},
    item: {},
    resources: [],
    tree: [],
    searchResources: []
  }),
  mounted () {
    this.getResources()
  },
  methods: {
    getResources () {
      this.$newhirepart.getResources().then((data) => {
        this.resources = _.groupBy(data, 'category')
        this.searchResources = data
      }).catch(() => {
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.couldNotGetResources'))
      }).finally(() => {
        this.loading = false
      })
    },
    clickedItem (value) {
      const item = this.searchResources.find(a => a.id === value[0])
      if (item.item) {
        this.item = item
      } else if (item.course) {
        this.$router.push({ name: 'portal-course-id', params: { id: item.id } })
      } else {
        this.$router.push({ name: 'portal-resources-id', params: { id: item.id } })
      }
    }
  }
}
</script>

<style scoped>
</style>
