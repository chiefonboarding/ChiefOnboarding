<template>
  <v-container mt-4>
    <LoadingIcon :color="$store.state.baseInfo.org.base_color" :is-loading="loading" />
    <v-row v-if="!loading">
      <v-col sm="4">
        <v-card outlined class="pa-4">
          <v-btn @click="goToMainPage" text class="mb-2">
            &lt;- go back
          </v-btn>
          <v-divider class="mb-2" />
          <v-treeview
            :items="resource.chapters"
            :color="$store.state.baseInfo.org.base_color"
            @update:active="clickedItem"
            activatable
            open-on-click
            item-key="id"
            item-children="chapters"
          >
            <template v-slot:prepend="{ item }">
              <font-awesome-icon v-if="item.type === 1" :icon="['far', 'folder']" />
              <font-awesome-icon v-else :icon="['far', 'file']" />
            </template>
          </v-treeview>
        </v-card>
      </v-col>
      <v-col sm="8">
        <v-card outlined class="pa-10">
          <h2>{{ item.name }}</h2>
          <ContentDisplay :content="item.content" class="mb-4" />
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import ContentDisplay from '@/components/portal/ContentDisplay'

export default {
  layout: 'newhire',
  name: 'ChapterItem',
  components: { ContentDisplay },
  data: () => ({
    loading: true,
    answers: [],
    select: {},
    item: {},
    resource: [],
    chapters: [],
    tree: [],
    searchResources: []
  }),
  mounted () {
    this.getResources()
  },
  methods: {
    getResources () {
      this.$newhirepart.getResource(this.$route.params.id).then((data) => {
        this.resource = data.organized
        this.chapters = data.original.chapters
        this.item = this.resource.chapters[0]
      }).catch(() => {
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.couldNotGetResources'))
      }).finally(() => {
        this.loading = false
      })
    },
    clickedItem (value) {
      if (value.length === 0) { return }
      this.item = this.chapters.find(a => a.id === value[0])
    },
    goToMainPage () {
      this.$router.push({ name: 'portal-resources' })
    }
  }
}
</script>
