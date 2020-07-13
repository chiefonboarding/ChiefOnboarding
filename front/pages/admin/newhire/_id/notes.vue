<template>
  <div style="margin: 0 20px;">
    <LoadingIcon :is-loading="loading" />
    <v-timeline v-if="!loading" dense clipped>
      <v-timeline-item
        fill-dot
        class="white--text mb-2"
        color="orange"
        large
      >
        <span slot="icon">{{ $t('newhires.you') }}</span>
        <v-text-field
          v-model="comment"
          :label="$t('newhires.leaveAComment')"
          @keydown.enter="makeComment"
          hide-details
          text
          solo
        >
          <template slot="append">
            <v-btn
              @click="makeComment"
              class="mx-0"
              depressed
            >
              Post
            </v-btn>
          </template>
        </v-text-field>
      </v-timeline-item>
      <v-timeline-item
        v-for="i in comments"
        :key="i.id"
        class="mb-3"
        color="grey"
        small
      >
        <v-row justify-space-between>
          <v-col sm="7" style="vertical-align:middle">
            {{ i.content }}
            <div class="caption">
              - {{ i.admin.first_name }} {{ i.admin.last_name }}
            </div>
          </v-col>
          <v-col sm="5" class="text-right">
            {{ i.created | timeAgo }}
          </v-col>
        </v-row>
      </v-timeline-item>
      <v-timeline-item
        v-if="comments.length === 0"
        class="mb-3"
        color="grey"
        small
      >
        <v-row justify-space-between>
          <v-col>
            {{ $t('newhires.noCommentsYet') }}
          </v-col>
        </v-row>
      </v-timeline-item>
    </v-timeline>
  </div>
</template>

<script>
export default {
  data: () => ({
    input: '',
    comment: '',
    comments: [],
    loading: true
  }),
  computed: {
    errorMessages () {
      return JSON.parse(JSON.stringify(this.errors))
    }
  },
  watch: {
    errors (value) {
      if ('content' in value) {
        this.$store.dispatch('showSnackbar', 'Content: ' + value.content[0])
      }
    }
  },
  mounted () {
    this.$newhires.getNotes(this.$route.params.id).then((response) => {
      this.comments = response
    }).finally(() => {
      this.loading = false
    })
  },
  methods: {
    getAdmin (user) {
      return this.$store.state.admins.find(a => user === a.id).name
    },
    makeComment () {
      this.$newhires.postNote(this.$route.params.id, { 'content': this.comment }).then((response) => {
        this.comments.unshift(response)
        this.comment = ''
        this.$store.dispatch('showSnackbar', this.$t('newhires.noteAdded'))
      })
    }
  }
}
</script>
