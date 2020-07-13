<template>
  <v-container mt-4>
    <LoadingIcon :color="$store.state.baseInfo.org.base_color" :is-loading="loading" />
    <v-row v-if="!loading">
      <v-col sm="12">
        <v-card outlined class="pa-10">
          <h2>{{ item.name }}</h2>
          <div v-if="item.type === 2">
            <QuestionsForm
              :questions="item.content"
              :id="resource_user_id"
              :resourceId="item.id"
              :org="$store.state.baseInfo.org"
              @completed="registerStep"
            />
          </div>
          <div v-else>
            <ContentDisplay :content="item.content" class="mb-10" />
            <v-container>
              <v-row>
                <v-btn
                  :color="$store.state.baseInfo.org.base_color"
                  v-if="resource.course && step !== 0"
                  dark
                >
                  Previous
                </v-btn>
                <v-spacer />
                <v-btn
                  :color="$store.state.baseInfo.org.base_color"
                  v-if="resource.course && step !== resource.length"
                  @click="registerStep"
                  dark
                >
                  Next
                </v-btn>
              </v-row>
            </v-container>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import ContentDisplay from '@/components/portal/ContentDisplay'
import QuestionsForm from '@/components/portal/resource/QuestionsForm'

export default {
  layout: 'newhire',
  name: 'ResourceItem',
  components: { ContentDisplay, QuestionsForm },
  data: () => ({
    loading: true,
    answers: [],
    select: {},
    resource: [],
    resources: [],
    tree: [],
    step: 0,
    resource_user_id: 0,
    searchResources: []
  }),
  computed: {
    item () {
      if (this.chapters.length) { return this.chapters[this.step] }
      return {}
    }
  },
  mounted () {
    this.getResources()
  },
  methods: {
    getResources () {
      this.$newhirepart.getCourse(this.$route.params.id).then((data) => {
        this.resource = data.organized.resource
        this.chapters = data.original.resource.chapters
        if (data.organized.step === this.resource.length) {
          this.$router.push({ name: 'portal-resources' })
        }
        this.step = data.organized.step
        this.resource_user_id = data.original.id
      }).catch(() => {
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.couldNotGetResources'))
      }).finally(() => {
        this.loading = false
      })
    },
    registerStep () {
      this.$newhirepart.registerStep(this.resource_user_id, this.step + 1)
      if (this.step === this.resource.length - 1) {
        this.$router.push({ name: 'portal-resources' })
      }
      this.step += 1
    }
  }
}
</script>
